from .beatmap_classes import *
from .storyboard_classes import *
from ..helpers import osu_fp, complete_path, split_get
from re import match, findall

def get_commands(command: str) -> list[BaseCommand]:
    """ Extract of code from previous version:
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
    """

    cmd, *data = split_get(command, ",", [str, [int, float, str]])
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
            *p)
        for i, p in enumerate(organised_params)
    ]


def decompress_beatmap(path: str) -> Beatmap:
    path = complete_path(path, root=osu_fp.get(), folder="Songs\\", ext=".osu")  # Be sure the path is correct
    with open(path, "r", encoding="utf-8") as file:
        file_content = file.read()

    file_format = int( match(r"^[^o]?osu file format v(\d+)", file_content).group(1) )
    sections = {
        name: [line for line in content.split("\n") if line != "" and not line.startswith("//")]
        for name, content in findall(r"\n\[(\w+)\]\n((?:[^\[]+|(?<!\n)\[)+)(?=\n\[|$)", file_content)
    }

    general = {
        key: value
        for line in sections.get("General", [])
        for key, value in [ split_get(line, ":", [str, (int, float, str)]) ]
    }
    editor = {
        key: value if key != "Bookmarks" else split_get(str(value), ",", [[int]])
        for line in sections.get("Editor", [])
        for key, value in [ split_get(line, ":", [str, (int, float, str)]) ]
    }
    metadata = {
        key: value
        for line in sections.get("Metadata", [])
        for key, value in [ split_get(line, ":", [str, (int, float, str)], max_split=1) ]
    }
    difficulty = {
        key: value
        for line in sections.get("Difficulty", [])
        for key, value in [ split_get(line, ":", [str, float]) ]
    }
    events = [
        ...  # TODO: handle events
    ]
    timing_points = [
        TimingPoint( *split_get(line, ",", [[int, float]]) )
        for line in sections.get("TimingPoints", [])
    ]
    colors = {
        key: split_get(value, ",", [int, int, int])
        for line in sections.get("Colours", [])
        for key, value in [ split_get(line, ":", [str, str]) ]
    }
    hit_objects = [
        HitObject.from_params(*split_get(line, ",", [[int, float, str]]))
        for line in sections.get("HitObjects", [])
    ]

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
