from itertools import accumulate, chain
from math import dist, floor, sin, cos, atan2
from .classes import Beatmap, Slider, SliderTick, Spinner, Hold
from ..tools.conversions import ar_to_ms, cs_to_radius
from ..helpers import Vector, find_circle_center, angles_are_rotating_clockwise, bezier


def analyse_linear_slider(slider: Slider):
    curve_points = Vector(slider.x, slider.y), *slider.curvePoints
    slider_velocity = slider.length / slider.slideDuration  # Velocity in px/ms

    point_distances = [0] + [dist(p1, p2) for p1, p2 in zip(curve_points, curve_points[1:])]

    slider.path = {
        round(tot_dist / slider_velocity): pos
        for pos, tot_dist in zip(curve_points, accumulate(point_distances))
    }


def analyse_perfect_slider(slider: Slider, loop_ms: int):
    curve_points = Vector(slider.x, slider.y), *slider.curvePoints

    center = find_circle_center(*curve_points)
    if center is None:  # If an error occurs when searching the circle center
        analyse_linear_slider(slider)  # Treat the slider as linear, and exit the function
        return

    curve_points_angle = [atan2(*point-center) for point in curve_points]

    radius = dist(center, curve_points[0])
    rotation_angle = (
        -slider.length / radius  # Clockwise rotation
        if angles_are_rotating_clockwise(*curve_points_angle) else
        slider.length / radius  # Anti-clockwise rotation
    )

    slider.path = {
        t: Vector(sin(ball_angle), cos(ball_angle)) * radius + center
        for t in chain(range(0, floor(slider.slideDuration), loop_ms), [slider.slideDuration])
        for ball_angle in [ curve_points_angle[0] + rotation_angle*(t / slider.slideDuration) ]
    }


def analyse_bezier_slider(slider: Slider, bezier_precision: int):
    curve_points = Vector(slider.x, slider.y), *slider.curvePoints
    slider_velocity = slider.length / slider.slideDuration  # Velocity in px/ms

    if curve_points[0] == curve_points[1]:
        curve_points = curve_points[1:]  # This prevents problems if the slider starts with a red anchor
    current_curve = []
    separated_curves = []
    for point in curve_points:
        if len(current_curve) >= 2 and point == current_curve[-1]:
            separated_curves.append(current_curve)
            current_curve = []  # reset the current curve
        current_curve.append(point)
    if len(current_curve) == 1:  # Special case: slider ends with a red anchor
        separated_curves[-1].append(*current_curve)
    else:
        separated_curves.append(current_curve)  # Add the last curve to the list

    curves_path = [
        curve if len(curve) == 2
        else [bezier(i/bezier_precision, *curve) for i in range(bezier_precision + 1)]
        for curve in separated_curves
    ]
    whole_curve_path = list(chain.from_iterable(curves_path))  # Flatten curves_path
    distances = [0] + [dist(p1, p2) for p1, p2, in zip(whole_curve_path, whole_curve_path[1:])]
    slider.path = {
        (t_dist / slider_velocity): pos for t_dist, pos in zip(accumulate(distances), whole_curve_path)
    }


def analyse_catmull_slider(slider: Slider):  # Catmull sliders are deprecated in osu! and are barely used anyway
    raise ValueError(f"catmull sliders not yet supported")


def analyse_slider(beatmap: Beatmap, slider: Slider, loop_ms: int, bezier_precision: int):
    """Writes more info in the additionalData attribute of slider"""

    slide_duration = slider.length / beatmap.slider_velocity(slider.time)
    full_duration = slide_duration * slider.slides

    slider.slideDuration = slide_duration
    slider.duration = full_duration
    slider.tail.time = slider.time + full_duration
    slider.end.time = slider.time + full_duration

    # Compute slider's path
    if slider.curveType == "L": analyse_linear_slider(slider)
    elif slider.curveType == "P": analyse_perfect_slider(slider, loop_ms)
    elif slider.curveType == "B": analyse_bezier_slider(slider, bezier_precision)
    elif slider.curveType == "C": analyse_catmull_slider(slider)
    else:
        raise ValueError(f"Unknown curve type '{slider.curveType}'")

    slider.tail.pos = slider.ball_pos(slider.time + slider.slideDuration)
    slider.tail.x, slider.tail.y = slider.tail.pos
    slider.end.pos = slider.pos if slider.slides % 2 == 0 else slider.tail.pos
    slider.end.x, slider.end.y = slider.end.pos

    # Get the position of the slider ticks
    # Slider ticks happen SliderTickRate times per beat
    time_between_ticks = beatmap.beat_length(slider.time) / beatmap.Difficulty.SliderTickRate
    slider.ticksPos = [
        SliderTick(time=i*time_between_ticks, pos=slider.ball_pos(slider.time + i*time_between_ticks))
        for i in range(1, floor(slider.slideDuration / time_between_ticks))
    ]



def analyse_beatmap(beatmap: Beatmap, loop_ms: int = 10, bezier_precision: int = 50):
    # Values that are used later in the function
    stack_leniency_time = ar_to_ms(beatmap.Difficulty.ApproachRate) * beatmap.General.StackLeniency
    stack_leniency_offset = cs_to_radius(beatmap.Difficulty.CircleSize) / 10
    stack_offset_unit = Vector(-stack_leniency_offset, -stack_leniency_offset)

    # Evaluate comboNumber and comboIndex
    combo_index = 0
    combo_number = 0
    for obj in beatmap.HitObjects:
        combo_number += 1
        if obj.newCombo:
            combo_index += 1
            combo_number = 1

        obj.pos = Vector(obj.x, obj.y)
        obj.comboIndex = combo_index
        obj.comboNumber = combo_number

        if obj.type == "slider":
            analyse_slider(beatmap, obj, loop_ms, bezier_precision)

    # Scan for stacks
    # The stacking rules are complex and obscure, so I won't be explaining them. Good luck find them out :)
    # In case you really want to know, look into "osu!stacks.py" (I don't know if that will help, but you can try)
    for i in reversed(range(len(beatmap.HitObjects))):  # We iterate through the hit objects in reversed order
        current = beatmap.HitObjects[i]
        if isinstance(current, (Spinner, Hold)) or current.stack is not None:  # Those are not part of stacks
            # Spinners and holds are not part of stacks
            # If stack is not None, that means the stack offset for this object has already been computed
            continue
        current.stack = 0  # This must be a stack base
        slider_stack = isinstance(current, Slider)  # Stacks ignore sliders is the first object is itself a slider
        total_stack = 0
        for j in reversed(range(i)):  # We try to find the first object that might be stacked on top of current
            obj = beatmap.HitObjects[j]
            if isinstance(obj, (Spinner, Hold)): continue
            if isinstance(obj, Slider):  # Sliders are special because they have an end that could be part of a stack
                if obj.end.time + stack_leniency_time < current.time:  # Too far in time; the stack stops here
                    break
                if dist((current.x, current.y), (obj.end.x, obj.end.y)) < 2.9:
                    total_stack += 1
                    current = obj
                    current.stack = total_stack
                    if not slider_stack:
                        # Tail stack: we want the slider to base the base, so we are shifting everything back
                        current2 = current.end
                        current.stack = 0  # This slider is now the base of the stack
                        for k in range(j+1, len(beatmap.HitObjects)):
                            obj2 = beatmap.HitObjects[k]
                            if isinstance(obj2, (Spinner, Hold)): continue
                            if current2.time + stack_leniency_time < obj2.time:  # Too far in time; the stack stops here
                                break
                            if dist((current.end.x, current.end.y), (obj2.x, obj2.y)) < 2.9:
                                current2 = obj2
                                if current2.stack is None: current2.stack = 0
                                current2.stack -= total_stack
                        total_stack = 0
                        slider_stack = True
                elif dist((current.x, current.y), (obj.x, obj.y)) < 2.9:
                    if slider_stack: break  # Sliders break the stack if their head is on it
                    total_stack += 1
                    current = obj
                    current.stack = total_stack
            else:  # obj is a Circle
                if obj.time + stack_leniency_time < current.time:  # Too far in time; the stack stops here
                    break
                if dist((current.x, current.y), (obj.x, obj.y)) < 2.9:
                    total_stack += 1
                    current = obj
                    current.stack = total_stack

    # Apply stacks values
    for obj in beatmap.HitObjects:
        if obj.stack is None: continue
        stack_offset = obj.stack * stack_offset_unit
        obj.pos += stack_offset
        if isinstance(obj, Slider):  # Sliders have more data to modify than regular Circles
            obj.tail.pos += stack_offset
            obj.end.pos += stack_offset
            for time in obj.path:
                obj.path[time] += stack_offset
            for tick in obj.ticksPos:
                tick.pos += stack_offset
