from math import *
from ..beatmap.beatmap_classes import *
from my_tools import *


def analyse_linear_slider(slider: Slider):
    curve_points = Vector(slider.x, slider.y), *slider.curvePoints
    slider_velocity = slider.length / slider.additionalData.slideDuration  # Velocity in px/ms

    path, times = [], []
    length_travelled = 0
    for i in range(len(curve_points) - 1):
        next_length = dist(curve_points[i], curve_points[i + 1])

        path.append(curve_points[i])
        times.append(round(length_travelled / slider_velocity))

        if length_travelled + next_length >= slider.length or \
                i == len(curve_points) - 2:  # Last element
            path.append(segment_fraction(
                (slider.length - length_travelled) / next_length,
                curve_points[i],
                curve_points[i + 1]
            ))
            times.append(slider.additionalData.slideDuration)
            break

        length_travelled += next_length

    slider.additionalData.path = dict(zip(times, path))
    slider.additionalData.endX, slider.additionalData.endY = path[-1]


def analyse_perfect_slider(slider: Slider, loop_ms: int):
    curve_points = Vector(slider.x, slider.y), *slider.curvePoints

    center = find_circle_center(*curve_points)
    if center is None:  # If an error occurs when searching the circle center
        analyse_linear_slider(slider)  # Treat the slider as linear, and exit the function
        return

    radius = dist(center, curve_points[0])

    curve_points_angle = []
    for point in curve_points:
        curve_points_angle.append(angle(*point, *center))

    rotation_angle = slider.length / radius  # Angle(r) for anti-clockwise rotation
    if angles_are_rotating_clockwise(*curve_points_angle):
        rotation_angle *= -1  # Then the slider turns clockwise

    path = []
    times = [
        i for i in range(0, floor(slider.additionalData.slideDuration), loop_ms)
            ] + [slider.additionalData.slideDuration]
    for time in times:
        ball_angle = curve_points_angle[0] + (rotation_angle * (time/slider.additionalData.slideDuration))
        path.append(Vector(
            center[0] + radius * sin(ball_angle),
            center[1] + radius * cos(ball_angle)
        ))

    slider.additionalData.path = dict(zip(times, path))
    slider.additionalData.endX, slider.additionalData.endY = path[-1]


def analyse_bezier_slider(slider: Slider, bezier_precision: int):
    curve_points = Vector(slider.x, slider.y), *slider.curvePoints
    slider_velocity = slider.length / slider.additionalData.slideDuration  # Velocity in px/ms

    # [list1] >< [list2] means that any element of list1 has some property in list2, at the same index
    #
    # curve: list[Vector]
    # separated_curves: list[curves]
    # curves_duration: list[float] >< separated_curves
    # curve_path: list[{"time": int,"pos": Vector}]
    # separated_curves_path = list[curve_path] >< separated_curves

    def separate_curves(points: list[Vector]):
        current_curve = []
        separated_curves = []
        for point in points:
            if len(current_curve) >= 2 and point == current_curve[-1]:
                separated_curves.append(current_curve)
                current_curve = []  # reset the current curve
            current_curve.append(point)
        separated_curves.append(current_curve)  # Add the last curve to the list

        # Delete curves with a single point
        i = 0
        while i < len(separated_curves):
            if len(separated_curves[i]) < 2:
                separated_curves.pop(i)
                i -= 1
            i += 1

        return separated_curves

    def get_curve_path(curve: list[Vector], precision: int):
        if len(curve) == 2:  # Special case: faster calculation
            return [
                {"pos": curve[0], "time": 0},
                {"pos": curve[1], "time": dist(*curve)/slider_velocity}
            ]

        length_travelled = 0.0
        prev_pos = curve[0]
        curve_path = []
        for i in range(0, precision + 1):
            pos = bezier(i/precision, *curve)
            length_travelled += dist(prev_pos, pos)
            curve_path.append({"pos": pos, "time": length_travelled/slider_velocity})
            prev_pos = pos

        return curve_path

    def get_last_point(p1: Dict, p2: Dict, slider_duration: float):
        return {
            "time": slider_duration,
            "pos": segment_fraction(
                (slider_duration - p1["time"]) / (p2["time"] - p1["time"]),
                p1["pos"],
                p2["pos"]
            )
        }

    curves = separate_curves(curve_points)
    curves_path = [get_curve_path(curve, bezier_precision) for curve in curves]
    curves_duration = [path[-1]["time"] for path in curves_path]

    # Compute the whole curve's path
    whole_curve_path = []
    curve_begin_time = 0
    for curve_path, duration in zip(curves_path, curves_duration):
        for point in curve_path:
            whole_curve_path.append(
                {"time": point["time"] + curve_begin_time, "pos": point["pos"]}
            )

        curve_begin_time += duration

    # Compute slider path based on the whole curve's path
    last_point = get_last_point(curves_path[-1][-2], curves_path[-1][-1], slider.additionalData.slideDuration)
    prev_point = curves_path[0][0]
    path = []
    times = []
    for point in whole_curve_path:
        if point["time"] >= slider.additionalData.slideDuration:  # Slider ends before the curve
            # In this case, last_point is incorrect, so we recompute it
            last_point = get_last_point(prev_point, point, slider.additionalData.slideDuration)
            break

        path.append(point["pos"])
        times.append(point["time"])
        prev_point = point

    path.append(last_point["pos"])
    times.append(last_point["time"])

    slider.additionalData.path = dict(zip(times, path))
    slider.additionalData.endX, slider.additionalData.endY = path[-1]


def analyse_catmull_slider(slider: Slider):  # TODO: catmull sliders support
    raise ValueError(f"catmull sliders not yet supported")


def analyse_slider(beatmap: Beatmap, slider: Slider, loop_ms: int, bezier_precision: int):
    """Writes more info in the additionalData attribute of slider"""

    slide_duration = slider.length / beatmap.slider_velocity(slider.time)
    full_duration = slide_duration * slider.slides

    slider.additionalData.slideDuration = slide_duration
    slider.additionalData.duration = full_duration
    slider.additionalData.endTime = slider.time + full_duration

    if slider.curveType == "L":
        analyse_linear_slider(slider)

    elif slider.curveType == "P":
        analyse_perfect_slider(slider, loop_ms)

    elif slider.curveType == "B":
        analyse_bezier_slider(slider, bezier_precision)

    elif slider.curveType == "C":
        analyse_catmull_slider(slider)

    else:
        raise ValueError(f"Unknown curve type '{slider.curveType}'")

    # Get the position of the slider ticks
    # Slider ticks happen SliderTickRate times per beat
    time_between_ticks = beatmap.beat_length(slider.time) / beatmap.Difficulty.SliderTickRate

    time = time_between_ticks
    ticks = ListWithIndentation()
    while time < slider.additionalData.slideDuration:
        ticks.append(SliderTick(
            time=time,
            pos=slider.ball_pos(time)
        ))
        time += time_between_ticks

    slider.additionalData.ticksPos = ticks
