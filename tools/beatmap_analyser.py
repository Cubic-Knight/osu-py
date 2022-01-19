from ..beatmap.beatmap_classes import *
from .slider_analyser import analyse_slider
from .conversions import ar_to_ms, cs_to_radius
from my_tools import dist, Vector


def analyse_beatmap(beatmap: Beatmap, loop_ms: int = 10, bezier_precision: int = 50):
    # Values that are used later in the function
    stack_leniency_time = ar_to_ms(beatmap.Difficulty.ApproachRate) * beatmap.General.StackLeniency
    stack_leniency_offset = cs_to_radius(beatmap.Difficulty.CircleSize) / 10
    stacked = Vector(-stack_leniency_offset, -stack_leniency_offset)

    # Evaluate comboNumber, comboIndex and additionalData (for sliders only)
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
            obj: Slider
            analyse_slider(beatmap, obj, loop_ms, bezier_precision)
            obj.additionalData.endPos = Vector(
                obj.additionalData.endX,
                obj.additionalData.endY
            )

    # Scan for stacks
    last_hit_objects: list[HitObject] = []
    for obj in beatmap.HitObjects[::-1]:
        obj: HitObject

        if obj.type in ["spinner", "hold"]:  # Spinners and hold do not create stacks
            continue

        # Delete expired hit objects
        while len(last_hit_objects) > 0 and last_hit_objects[0].time > obj.time + stack_leniency_time:
            last_hit_objects.pop(0)

        # Check if obj can be stacked
        obj.stack = ("none", 0)
        for o in last_hit_objects[::-1]:
            if dist(Vector(o.x, o.y), Vector(obj.x, obj.y)) < 2.9:
                if o.stack[0] == "stack":
                    obj.stack = ("stack", o.stack[1] + 1)
                    break
                if o.type == "slider" or o.stack[0] == "up":
                    obj.stack = ("up", o.stack[1] + 1)
                    break
                if o.type == "circle":
                    obj.stack = ("stack", 1)
                    break
                break

        if obj.type == "slider":
            obj: Slider
            slider_end = HitObject(
                obj.additionalData.endX,
                obj.additionalData.endY,
                obj.additionalData.endTime,
                1,
                0
            )
            # Check if slider_end can be stacked
            obj.additionalData.endStack = ("none", 0)
            for o in last_hit_objects[::-1]:
                if dist(Vector(o.x, o.y), Vector(slider_end.x, slider_end.y)) < 2.9:
                    if o.stack[0] == "stack":
                        obj.additionalData.endStack = ("down", 0)
                        break
                    if o.type == "slider" or o.stack[0] == "up":
                        obj.stack = ("up", o.stack[1] + 1)
                        obj.additionalData.endStack = ("up", o.stack[1] + 1)
                        break
                    if o.type == "circle":
                        obj.additionalData.endStack = ("down", 0)
                        break
                    break

        to_append = HitObject(obj.x, obj.y, obj.time, 1, 0)
        to_append.type = obj.type
        to_append.stack = obj.stack
        last_hit_objects.append(to_append)

    # Apply stack values to the positions
    last_hit_objects: list[HitObject] = []
    for obj in beatmap.HitObjects:
        obj: HitObject

        if obj.type in ["spinner", "hold"]:  # Spinners and hold do not create stacks
            continue

        # Delete expired hit objects
        while len(last_hit_objects) > 0 and last_hit_objects[0].time > obj.time + stack_leniency_time:
            last_hit_objects.pop(0)

        if obj.stack[0] == "stack":
            # Determine if obj is part of a up or a down stack
            for o in last_hit_objects:
                if dist(Vector(o.x, o.y), Vector(obj.x, obj.y)) < 2.9 and o.stack[0] == "down":
                    obj.stack = ("down", o.stack[1] - 1)
                    break

            if obj.stack[0] == "stack":  # If obj is not part of a down stack
                obj.stack = ("up", obj.stack[1])

        if obj.stack[0] == "down":  # Add obj so it can be detected as a down stack
            to_append = HitObject(obj.x, obj.y, obj.type, 1, 0)
            to_append.stack = obj.stack
            last_hit_objects.append(to_append)

        if obj.type == "slider" and obj.additionalData.endStack[0] == "down":  # Same but for slider ends
            obj: Slider
            to_append = HitObject(
                obj.additionalData.endX,
                obj.additionalData.endY,
                obj.additionalData.endTime,
                1,
                0
            )
            to_append.stack = obj.additionalData.endStack
            last_hit_objects.append(to_append)

        obj.pos += obj.stack[1] * stacked
        if obj.type == "slider":  # Sliders have more data to modify
            obj: Slider
            obj.additionalData.endPos += obj.stack[1] * stacked

            for time, point in obj.additionalData.path.items():
                obj.additionalData.path[time] = point + obj.stack[1] * stacked

            for tick in obj.additionalData.ticksPos:
                tick.pos += obj.stack[1] * stacked
