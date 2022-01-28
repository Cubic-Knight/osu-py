from .beatmap_classes import *
from .storyboard_classes import *
from ..helpers import osu_fp, complete_path
from typing import Union


def format_sprite_command(cmd: Union[SpriteCommand, Loop, Trigger]) -> str:
    if isinstance(cmd, SpriteCommand):
        return cmd.osu_format()

    if isinstance(cmd, Loop):
        return "\n".join(
            [cmd.osu_format()] + [format_sprite_command(sub_cmd) for sub_cmd in cmd.loopCommands]
        )

    if isinstance(cmd, Trigger):
        return "\n".join(
            [cmd.osu_format()] + [format_sprite_command(sub_cmd) for sub_cmd in cmd.triggerCommands]
        )


def compress_beatmap(beatmap: Beatmap, output_path=None) -> str:
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
