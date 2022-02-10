from .classes import Beatmap, TimingPoint, HitObject,  \
    GeneralSettings, EditorSettings, MetadataSettings, DifficultySettings, ColorSettings
from ..storyboard.reader import get_events
from ..storyboard import SpriteCommand, Loop, Trigger
from ..helpers import osu_fp, complete_path, split_get
from re import match, findall
from typing import Union


def read_beatmap_file(path: str) -> Beatmap:
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
    events = get_events(sections.get("Events", []))
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


# ----------------------------------------------------------------------------------------------------------------------


def format_sprite_command(cmd: Union[SpriteCommand, Loop, Trigger]) -> str:
    if isinstance(cmd, SpriteCommand):
        return cmd.osu_format()
    return "\n".join(
        [cmd.osu_format()] + [format_sprite_command(sub_cmd) for sub_cmd in cmd.commands]
    )


def write_beatmap_file(beatmap: Beatmap, output_path=None) -> str:
    events = "[Events]"
    for event in beatmap.Events:
        events += "\n"
        events += event.osu_format()
        if hasattr(event, "commands"):
            events += "\n".join( format_sprite_command(cmd) for cmd in event.commands )

    timing_points = (
        "[TimingPoints]\n" +
        "\n".join(point.osu_format() for point in beatmap.TimingPoints)
    )
    hit_objects = (
        "[HitObjects]\n" +
        "\n".join(obj.osu_format() for obj in beatmap.HitObjects)
    )

    beatmap_str = (
        f"osu file format v{beatmap.FileFormat}\n\n"
        f"{beatmap.General.osu_format()}\n\n"
        f"{beatmap.Editor.osu_format()}\n\n"
        f"{beatmap.Metadata.osu_format()}\n\n"
        f"{beatmap.Difficulty.osu_format()}\n\n"
        f"{events}\n\n"
        f"{timing_points}\n\n"
        f"{beatmap.Colors.osu_format()}\n\n"
        f"{hit_objects}\n"
    )

    if output_path is not None:
        # Write the return value to a file
        output_path = complete_path(output_path, root=osu_fp.get(), folder="Songs\\", ext=".osu")
        with open(output_path, 'w', encoding="utf-8") as output_file:
            output_file.write(beatmap_str)

    return beatmap_str
