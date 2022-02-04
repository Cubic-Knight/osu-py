from itertools import accumulate, chain
from math import dist, floor, sin, cos, atan2
from ..beatmap.beatmap_classes import Beatmap, Slider, SliderTick
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


def analyse_catmull_slider(slider: Slider):  # TODO: catmull sliders support
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
