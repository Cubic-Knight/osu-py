from my_tools import complete_path
from .beatmap_classes import *
from .storyboard_classes import *
from ..globals import OSU_FOLDER_PATH


def format_sprite_command(cmd):
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


def compress_beatmap(beatmap: Beatmap, output_path=None):
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

    if output_path is None:
        return beatmap_str

    # Create the file
    output_path = complete_path(output_path, root=OSU_FOLDER_PATH, folder="Songs\\", extension=".osu")
    with open(output_path, 'w', encoding="utf-8") as output_file:
        output_file.write(beatmap_str)
