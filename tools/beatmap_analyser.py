from ..beatmap.beatmap_classes import *
from .slider_analyser import analyse_slider
from .conversions import ar_to_ms, cs_to_radius
from math import dist
from ..helpers import Vector


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
