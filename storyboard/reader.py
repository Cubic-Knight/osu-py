from itertools import zip_longest, tee
from re import findall, match, sub
from .classes import StoryBoard, BaseCommand, Loop, Trigger, Parameter, Event, Image, Video, Sprite, Animation
from ..helpers import split_get, osu_fp, complete_path


EVENT_ARG_COUNTS = {  # {command_name}: ({min_args}, {max_args})
        "F":  (1, 2),
        "M":  (2, 4),
        "MX": (1, 2),
        "MY": (1, 2),
        "S":  (1, 2),
        "V":  (2, 4),
        "R":  (1, 2),
        "C":  (3, 6),
        "P":  (1, 1)
    }

def grouper(n, iterable, fillvalue=None):  # From https://docs.python.org/3.1/library/itertools.html#recipes
    # grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def pairwise(iterable):  # From https://docs.python.org/3.1/library/itertools.html#recipes
    # s -> (s0,s1), (s1,s2), (s2, s3), ...
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def get_commands(command: str) -> list[BaseCommand]:
    cmd, data_str = split_get(command.replace(" ", "_"), ",", [str, str], max_split=1)
    indent = cmd.count("_")
    event = cmd.replace("_", " ").strip()

    if event == "L": return [ Loop(indent, event, *split_get(data_str, ",", [int, int])) ]
    elif event == "T": return [ Trigger(indent, event, *split_get(data_str, ",", [str, int, int])) ]

    easing, start_time, end_time, params_str = split_get(
        data_str, ",", [int, int, int, str], defaults=[..., ..., None, ...], max_split=3
    )
    end_time = start_time if end_time is None else end_time
    duration = end_time - start_time

    if event == "P": return [
        Parameter(
            indent, event, easing,
            start_time + i*duration,
            end_time + i*duration,
            p
        )
        for i, p in enumerate(split_get(params_str, ",", [[str]]))
    ]

    min_args, max_args = EVENT_ARG_COUNTS[event]
    params = [
        group for group in grouper(min_args, split_get(params_str, ",", [[int, str]]), fillvalue=None)
    ]
    if len(params) < max_args // min_args:  # Test if all the necessary args are there: if not, duplicate the first ones
        params += params.copy()
    params = [
        [val if val is not None else p[i-1] for i, val in enumerate(p)]  # Fill missing arguments
        for p in params
    ]

    return [
        BaseCommand.from_params(
            indent,
            event,
            easing,
            start_time + i*duration,
            end_time + i*duration,
            *p1, *p2)
        for i, (p1, p2) in enumerate(pairwise(params))
    ]


def get_events(lines: list[str]) -> StoryBoard[Event]:
    events = StoryBoard()
    for line in lines:
        if line.startswith(" ") or line.startswith("_"):  # Storyboard command
            if not isinstance(events[-1], (Image, Video, Sprite, Animation)):
                raise TypeError("command assigned to an event that doesn't support commands")

            cmd = get_commands(line)
            indent = cmd[0].indentation
            target_list = events[-1].commands
            while target_list and hasattr(target_list[-1], "commands") and indent > target_list[-1].indentation:
                # Search where (aka how far) the commands should be embedded
                target_list = target_list[-1].commands

            target_list.extend(cmd)
        else:
            events.append(
                Event.from_params(*split_get(line, ",", [[int, str]]))
            )
    return events


def read_storyboard_file(path: str) -> StoryBoard[Event]:
    path = complete_path(path, root=osu_fp.get(), folder="Songs\\", ext=".osb")  # Be sure the path is correct
    with open(path, "r", encoding="utf-8") as file:
        file_content = file.read()

    sections = {
        name: [line for line in content.split("\n") if line != "" and not line.startswith("//")]
        for name, content in findall(r"(?:^|\n)\[(\w+)\]\n((?:[^\[]+|(?<!\n)\[)+)(?=\n\[|$)", file_content)
    }
    variables = {
        name: value
        for line in sections.get("Variables", [])
        for name, value in [ match(r"([$]\w+)=(.+)", line).groups() ]
    }

    return get_events([
        sub(r"[$]\w+", lambda m: variables[m.group(0)], line)
        for line in sections.get("Events", [])
    ])
