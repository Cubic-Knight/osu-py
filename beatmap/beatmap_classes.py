"""
To see what each property does, check the osu!wiki: https://osu.ppy.sh/wiki/sk/osu!_File_Formats/Osu_(file_format)
"""


import hashlib
from typing import Tuple, Union
from dataclasses import dataclass
from .storyboard_classes import Event
from ..helpers import Vector, segment_fraction, split_get, zigzag_function


# ----------------------------------------------------------------------------------------------------------------------
# Some functions, meant for use in other modules
# ----------------------------------------------------------------------------------------------------------------------


def get_hit_object_type_str(obj_type: int) -> str:
    if obj_type & 0b_0000_0001:
        return "circle"
    if obj_type & 0b_0000_0010:
        return "slider"
    if obj_type & 0b_0000_1000:
        return "spinner"
    if obj_type & 0b_1000_0000:
        return "hold"

    return "unknown"


# ----------------------------------------------------------------------------------------------------------------------
# SliderAdditionalData and SliderTick dataclasses. They are used in the Slider dataclass to hold data that is not
#   directly given by the beatmap file.
# Their properties use lowerCamelCase
# ----------------------------------------------------------------------------------------------------------------------


@dataclass
class SliderTick:
    time: float
    pos: Vector


@dataclass
class SliderAdditionalPoint:
    x: int = None
    y: int = None
    pos: Vector = None
    time: float = None


# ----------------------------------------------------------------------------------------------------------------------
# Settings dataclasses. They are used in the Beatmap dataclass to keep things easily accessible
# Their properties use UpperCamelCase
# ----------------------------------------------------------------------------------------------------------------------


@dataclass
class Settings:
    InitDict: dict = None

    def __post_init__(self):
        if self.InitDict is not None:
            for key, value in self.InitDict.items():
                setattr(self, key, value)
        del self.InitDict


@dataclass
class GeneralSettings(Settings):
    AudioFilename: str = None
    AudioLeadIn: int = 0
    AudioHash: str = None  # Deprecated
    PreviewTime: int = -1
    Countdown: int = 1  # 0: no countdown, 1: normal, 2: half, 3: double
    SampleSet: str = "Normal"  # Can be "Normal", "Soft" or "Drum"
    StackLeniency: float = 0.7
    Mode: int = 0  # 0: osu!, 1: osu!taiko, 2: osu!catch, 3: osu!mania
    LetterboxInBreaks: bool = 0
    StoryFireInFront: bool = 1  # Deprecated
    UseSkinSprites: bool = 0
    AlwaysShowPlayfield: bool = 0  # Deprecated
    OverlayPosition: str = "NoChange"  # Can be "NoChange", "Below" or "Above"
    SkinPreference: str = None
    EpilepsyWarning: bool = 0
    CountdownOffset: int = 0
    SpecialStyle: bool = 0
    WidescreenStoryboard: bool = 0
    SamplesMatchPlaybackRate: bool = 0

    def osu_format(self) -> str:
        return (
            "[General]\n" +
            "\n".join(
                f"{key}: {value}" for key, value in self.__dict__.items()
                if value is not None
            )
        )


@dataclass
class EditorSettings(Settings):
    Bookmarks: list[int] = None
    DistanceSpacing: float = 1.0
    BeatDivisor: float = 4.0
    GridSize: int = 1
    TimelineZoom: float = 1.0

    def __post_init__(self):
        super().__post_init__()
        if self.Bookmarks is None:
            self.Bookmarks = []

    def osu_format(self) -> str:
        return (
            "[Editor]\n" +
            f"Bookmarks: {','.join( str(i) for i in self.Bookmarks )}\n" +
            "\n".join(
                f"{key}: {value}" for key, value in self.__dict__.items()
                if key != "Bookmarks" and value is not None
            )
        )


@dataclass
class MetadataSettings(Settings):
    Title: str = ""
    TitleUnicode: str = ""
    Artist: str = ""
    ArtistUnicode: str = ""
    Creator: str = ""
    Version: str = ""
    Source: str = ""
    Tags: str = ""
    BeatmapID: int = 0
    BeatmapSetID: int = 0

    def __post_init__(self):
        super().__post_init__()
        self.Tags = [tag for tag in self.Tags.split(" ")]

    def osu_format(self) -> str:
        return (
            "[Metadata]\n" +
            f"Tags: {' '.join( str(i) for i in self.Tags )}\n" +
            "\n".join(
                f"{key}:{value}" for key, value in self.__dict__.items()
                if key != "Tags" and value is not None
            )
        )


@dataclass
class DifficultySettings(Settings):
    HPDrainRate: float = None
    CircleSize: float = None
    OverallDifficulty: float = None
    ApproachRate: float = None
    SliderMultiplier: float = 1.0
    SliderTickRate: float = 1.0

    def __post_init__(self):
        super().__post_init__()
        if self.OverallDifficulty is None:
            raise BeatmapError("Beatmap has no OD set")
        if self.HPDrainRate is None:
            self.HPDrainRate = self.OverallDifficulty
        if self.CircleSize is None:
            self.CircleSize = self.OverallDifficulty
        if self.ApproachRate is None:
            self.ApproachRate = self.OverallDifficulty

    def osu_format(self) -> str:
        return (
            "[Difficulty]\n" +
            "\n".join(
                f"{key}:{value}" for key, value in self.__dict__.items()
                if value is not None
            )
        )


@dataclass
class ColorSettings(Settings):
    Combo1: Tuple[int, int, int] = None
    Combo2: Tuple[int, int, int] = None
    Combo3: Tuple[int, int, int] = None
    Combo4: Tuple[int, int, int] = None
    Combo5: Tuple[int, int, int] = None
    Combo6: Tuple[int, int, int] = None
    Combo7: Tuple[int, int, int] = None
    Combo8: Tuple[int, int, int] = None
    SliderTrackOverride: Tuple[int, int, int] = None
    SliderBorder: Tuple[int, int, int] = None

    def __post_init__(self):
        super().__post_init__()
        self.ComboColors = [
            color for i in range(1, 9)
            if (color := getattr(self, f"Combo{i}", None)) is not None
        ]

    def osu_format(self) -> str:
        return (
            "[Colours]\n" +
            "\n".join(
                f"{key} : {value[0]},{value[1]},{value[2]}" for key, value in self.__dict__.items()
                if key != "ComboColors" and value is not None
            )
        )


# ----------------------------------------------------------------------------------------------------------------------
# Object dataclasses. Same as the Settings dataclasses, but are intended to be stored in a list in the Beatmap dataclass
# Their properties use lowerCamelCase
# ----------------------------------------------------------------------------------------------------------------------


@dataclass
class HitSample:
    normalSet: int
    additionSet: int
    index: int
    volume: int
    filename: str

    def osu_format(self) -> str:
        return f"{self.normalSet}:{self.additionSet}:{self.index}:{self.volume}:{self.filename}"


@dataclass
class TimingPoint:
    time: int
    beatLength: float
    meter: int = 4
    sampleSet: int = 0
    sampleIndex: int = 0
    volume: int = 100
    uninherited: bool = 1
    effects: int = 0

    def __post_init__(self):
        self.time = int(self.time)
        self.uninherited = int(self.beatLength > 0)

    def osu_format(self) -> str:
        return (
            f"{self.time},{self.beatLength},{self.meter},{self.sampleSet},{self.sampleIndex},"
            f"{self.volume},{self.uninherited},{self.effects}"
        )


@dataclass
class HitObject:
    x: int
    y: int
    time: int
    type: int
    hitSound: int

    def __post_init__(self):
        self.type_int = self.type
        self.newCombo = bool((self.type & 0b100) // 0b100)
        self.comboSkip = (self.type & 0b111_0000) // 0b1_0000

        type_str = get_hit_object_type_str(self.type)

        if type_str == "unknown":
            raise BeatmapError(f"Unknown HitObject of type {bin(self.type)}")
        self.type = type_str

        # This is for beatmap analysis (see tools/beatmap_analyser.py)
        self.comboIndex = None
        self.comboNumber = None
        self.pos = None
        self.stack = None

    @classmethod
    def from_params(cls, *args):
        obj_type = args[3]
        if obj_type & 0b_0000_0001:
            return Circle(*args)
        if obj_type & 0b_0000_0010:
            return Slider(*args)
        if obj_type & 0b_0000_1000:
            return Spinner(*args)
        if obj_type & 0b_1000_0000:
            return Hold(*args)
        raise ValueError(f"Unknown object of type {obj_type}")

    def head(self) -> str:
        return f"{self.x},{self.y},{self.time},{self.type_int},{self.hitSound}"

    def osu_format(self) -> str:
        """ Is overridden in child classes """
        return self.head()


@dataclass
class Circle(HitObject):
    hitSample: Union[str, HitSample] = "0:0:0:0:"

    def __post_init__(self):
        super().__post_init__()

        if self.hitSample == "":
            self.hitSample = "0:0:0:0:"
        self.hitSample = HitSample(
            *split_get(self.hitSample, ":", [int, int, int, int, str], [0, 0, 0, 0, ""], min_len=5)
        )

    def osu_format(self) -> str:
        return f"{self.head()},{self.hitSample.osu_format()}"


@dataclass
class Slider(HitObject):
    curve: str
    slides: int
    length: float
    edgeSounds: str = None
    edgeSets: str = None
    hitSample: Union[str, HitSample] = "0:0:0:0:"

    def __post_init__(self):
        super().__post_init__()
        self.curveType, *self.curvePoints = split_get(self.curve, "|", [[str]])
        self.curvePoints = [ Vector( *split_get(point, ":", [int, int]) ) for point in self.curvePoints ]

        self.edgeSounds = (
            [0]*self.slides if self.edgeSounds is None else
            split_get(str(self.edgeSounds), "|", [[int]])
        )
        self.edgeSets = (
            [(0, 0)]*self.slides if self.edgeSets is None else
            [tuple(split_get(i, ":", [int, int])) for i in self.edgeSets.split("|")]
        )

        self.hitSample = HitSample(
            *split_get(self.hitSample, ":", [int, int, int, int, str], [0, 0, 0, 0, ""], min_len=5)
        )

        # This is for slider analysis (see tools/slider_analyser.py)
        self.tail = SliderAdditionalPoint()
        self.end = SliderAdditionalPoint()
        self.slideDuration = None
        self.duration = None
        self.ticksPos = None
        self.path = None

    def osu_format(self) -> str:
        edge_sounds = "|".join( str(edge_sound) for edge_sound in self.edgeSounds )
        edge_sets = "|".join( "{}:{}".format(*edge_set) for edge_set in self.edgeSets )
        return (
            f"{self.head()},{self.curve},{self.slides},{self.length},"
            f"{edge_sounds},{edge_sets},{self.hitSample.osu_format()}"
        )

    def ball_pos(self, time: float) -> Vector:
        if self.path is None:
            raise ValueError("path has not yet been calculated")

        slide_duration = self.slideDuration
        relative_time = zigzag_function(slide_duration, start_x=self.time)(time)

        timestamps = list(self.path.keys())
        for i, timestamp in enumerate(timestamps):
            if timestamp < relative_time and i != len(timestamps)-1: continue

            return segment_fraction(
                (timestamp - relative_time) / (timestamp - timestamps[i-1]),
                self.path[timestamp],
                self.path[timestamps[i-1]]
            )


@dataclass
class Spinner(HitObject):
    endTime: int
    hitSample: Union[str, HitSample] = "0:0:0:0:"

    def __post_init__(self):
        super().__post_init__()
        self.hitSample = HitSample(
            *split_get(self.hitSample, ":", [int, int, int, int, str], [0, 0, 0, 0, ""], min_len=5)
        )

    def osu_format(self) -> str:
        return f"{self.head()},{self.endTime},{self.hitSample.osu_format()}"


@dataclass
class Hold(HitObject):
    params: str

    def __post_init__(self):
        super().__post_init__()
        self.endTime, *sample = split_get(self.params, ":", [int, int, int, int, int, str], [0, 0, 0, 0, 0, ""], min_len=6)
        self.hitSample = HitSample(*sample)

    def osu_format(self) -> str:
        return f"{self.head()},{self.params}"


# ----------------------------------------------------------------------------------------------------------------------
# Main Beatmap class. This is the object that should be returned by the decompress_beatmap function
# Its properties use UpperCamelCase
# ----------------------------------------------------------------------------------------------------------------------


@dataclass
class Beatmap:
    FileFormat: int
    General: GeneralSettings
    Editor: EditorSettings
    Metadata: MetadataSettings
    Difficulty: DifficultySettings
    Events: list[Event]
    TimingPoints: list[TimingPoint]
    Colors: ColorSettings
    HitObjects: list[HitObject]
    Path: str

    def get_hash(self) -> str:
        return hashlib.md5( open(self.Path, "rb").read() ).hexdigest()

    def beat_length(self, time: int) -> float:
        beat_length = 500  # Default value
        for point in self.TimingPoints:
            if point.time > time: break
            if point.uninherited:
                beat_length = point.beatLength
        return beat_length

    def slider_velocity(self, time: int) -> float:
        beat_length = 500  # Default value
        # Look for base beat length
        for point in self.TimingPoints:
            if point.uninherited:
                beat_length = point.beatLength
                break

        velocity_multiplier = -100  # Default value
        # Get current timing point settings
        for point in self.TimingPoints:
            if point.time > time: break
            if point.uninherited:
                beat_length = point.beatLength
                velocity_multiplier = -100
            else:
                velocity_multiplier = point.beatLength

        return 100 * self.Difficulty.SliderMultiplier * (-100 / velocity_multiplier) * (1 / beat_length)


class BeatmapError(Exception):
    pass
