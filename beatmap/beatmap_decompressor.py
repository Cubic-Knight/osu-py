from .beatmap_classes import Beatmap, TimingPoint, HitObject,  \
    GeneralSettings, EditorSettings, MetadataSettings, DifficultySettings, ColorSettings
from .storyboard_decompressor import get_events
from ..helpers import osu_fp, complete_path, split_get
from re import match, findall


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
