from .beatmap_classes import *
from .storyboard_classes import *
from ..globals import OSU_FOLDER_PATH
from my_tools import split_get, complete_path, ListWithIndentation


def get_commands(command):
    cmd, *data = split_get(command, ",", [str, [int, float, str]], def_emp="")
    indent, event = cmd.replace(" ", "_").count("_"), cmd.replace("_", " ").strip()

    if event == "L":  # Loop
        start_time, loop_count = data
        return [
            Loop( indent, event, start_time, loop_count )
        ]

    if event == "T":  # Trigger
        trigger_type, start_time, end_time = data
        return [
            Trigger( indent, event, trigger_type, start_time, end_time )
        ]

    cmd_class, arg_count = get_command_class_and_arg_count(event)
    arg_count_halved = (arg_count + 1) // 2
    easing, start_time, end_time, *params = data

    # This adds empty values so the length of params is divisible by arg_count
    params += [""] * ( arg_count_halved - (len(params) % arg_count_halved) )

    if end_time == "":
        end_time = start_time
    for i, param in enumerate(params):
        if param == "":
            params[i] = params[i-1]

    organised_params = [params[i:i+arg_count] for i in range(0, len(params) - arg_count_halved, arg_count_halved)]
    duration = end_time - start_time

    return [
        cmd_class(
            indent,
            event,
            easing,
            start_time + i*duration,
            end_time + i*duration,
            *p) for i, p in enumerate(organised_params)
    ]


def decompress_beatmap(path):
    path = complete_path(path, root=OSU_FOLDER_PATH, folder="Songs\\", extension=".osu")  # Be sure the path is correct
    with open(path, "r", encoding="utf-8") as file:
        lines = (i[:-1] for i in file.readlines())

    line = next(lines)  # "osu file format v#"
    file_format = int(line[17:] if line[0] == 'o' else line[18:])

    # Initialise the dicts and lists
    general = {}
    editor = {}
    metadata = {}
    difficulty = {}
    events = ListWithIndentation()
    timing_points = ListWithIndentation()
    colors = {}
    hit_objects = ListWithIndentation()

    section = None
    for line in lines:
        if line == "" or line.startswith("//"):  # Empty line or comment
            continue

        if line.startswith("["):  # Section change
            section = line
            continue

        # Evaluate the line depending on the section
        if section == "[General]":
            key, value = split_get(line, ":", [str, (int, float, str)], def_emp="")
            general[key] = value
            continue

        if section == "[Editor]":
            key, value = split_get(line, ":", [str, (int, float, str)], def_emp="")
            if key == "Bookmarks":
                value = split_get(str(value), ",", [[int]])
            editor[key] = value
            continue

        if section == "[Metadata]":
            key, *value = split_get(line, ":", [str, [int, str]], def_emp="")
            metadata[key] = ":".join(str(i) for i in value)  # .join is to avoid errors due to ":" in strings
            continue

        if section == "[Difficulty]":
            key, value = split_get(line, ":", [str, float])
            difficulty[key] = value
            continue

        if section == "[Events]":
            if line.startswith(" ") or line.startswith("_"):  # Storyboard command
                if not isinstance(events[-1], (Image, Video, Sprite, Animation)):
                    raise BeatmapError("command assigned to an event that doesn't support commands")

                cmd = get_commands(line)
                indentation = cmd[0].indentation
                target_list = events[-1].commands

                while len(target_list) > 0 and target_list[-1].indentation > indentation:
                    if isinstance(target_list[-1], Loop):
                        target_list = target_list[-1].loopCommands
                        continue

                    if isinstance(target_list[-1], Trigger):
                        target_list = target_list[-1].triggerCommands
                        continue

                    break

                target_list.extend(cmd)
                continue

            event_type, *params = split_get(line, ",", [[int, str]])
            events.append(
                get_event_class(event_type)(event_type, *params)
            )
            continue

        if section == "[TimingPoints]":
            timing_points.append(
                TimingPoint( *split_get(line, ",", [[int, float]]) )
            )
            continue

        if section == "[Colours]":
            key, value = split_get(line, ":", [str, str])
            r, g, b = split_get(value, ",", [int, int, int])
            colors[key] = (r, g, b)
            continue

        if section == "[HitObjects]":
            params = split_get(line, ",", [[int, float, str]], def_emp="")
            hit_objects.append(
                get_hit_object_class(params[3])(*params)
            )
            continue

        raise ValueError(f"Unknown section '{section}'")

    return Beatmap(
        FileFormat=file_format,
        General=GeneralSettings(general),
        Editor=EditorSettings(editor),
        Metadata=MetadataSettings(metadata),
        Difficulty=DifficultySettings(difficulty),
        Events=events,
        TimingPoints=timing_points,
        Colors=ColorSettings(colors),
        HitObjects=hit_objects,
        Path=path
    )


class BeatmapError(Exception):
    pass
