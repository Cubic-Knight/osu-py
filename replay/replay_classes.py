"""
To see what each property does, check the osu!wiki: https://osu.ppy.sh/wiki/cs/osu!_File_Formats/Osr_(file_format)
"""


from typing import Union
from dataclasses import dataclass
from ..helpers import split_get


# ----------------------------------------------------------------------------------------------------------------------
# Some constants and tables that are useful
# ----------------------------------------------------------------------------------------------------------------------

DATA_TYPES = {
    'gameMode': 'byte',
    'version': 'int',
    'beatmapHash': 'str',
    'playerName': 'str',
    'replayHash': 'str',
    'count300': 'short',
    'count100': 'short',
    'count50': 'short',
    'countGeki': 'short',
    'countKatu': 'short',
    'countMiss': 'short',
    'score': 'int',
    'maxCombo': 'short',
    'fullCombo': 'byte',
    'mods': 'int',
    'lifeGraph': 'str',
    'time': 'long',
    'replayLength': 'int',
    'replay': 'array',
    'scoreID': 'long',
    'additionalModInfo': 'double'
}

NUMBER_TYPES = {
        "byte": "B",
        "short": "H",
        "int": "I",
        "long": "Q",
        "double": "d"
    }

MODS_INDEX_TO_STR = {
    0: "NoFail",
    1: "Easy",
    2: "TouchDevice",
    3: "Hidden",
    4: "HardRock",
    5: "SuddenDeath",
    6: "DoubleTime",
    7: "Relax",
    8: "HalfTime",
    9: "Nightcore",
    10: "Flashlight",
    11: "Autoplay",
    12: "SpunOut",
    13: "Autopilot",
    14: "Perfect",
    15: "Key4",
    16: "Key5",
    17: "Key6",
    18: "Key7",
    19: "Key8",
    20: "FadeIn",
    21: "Random",
    22: "Cinema",
    23: "TargetPractice",
    24: "Key9",
    25: "Coop",
    26: "Key1",
    27: "Key3",
    28: "Key2"
}

# ----------------------------------------------------------------------------------------------------------------------
# Some functions, meant for use in other modules
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# ReplayFrame dataclass. Define a frame in a replay
# Their properties use lowerCamelCase
# ----------------------------------------------------------------------------------------------------------------------


@dataclass
class ReplayFrame:
    time: int
    x: float
    y: float
    action: int


# ----------------------------------------------------------------------------------------------------------------------
# Main Replay class. This is the object that should be returned by the decompress_replay function
# Its properties use lowerCamelCase
# ----------------------------------------------------------------------------------------------------------------------


@dataclass
class Replay:
    gameMode: int  # 0: osu!, 1: osu!taiko, 2: osu!catch, 3: osu!mania
    version: int
    beatmapHash: str
    playerName: str
    replayHash: str
    count300: int
    count100: int
    count50: int
    countGeki: int
    countKatu: int
    countMiss: int
    score: int
    maxCombo: int
    fullCombo: int
    mods: Union[int, list[str]]
    lifeGraph: Union[str, dict[int, float]]
    time: int
    replayLength: int
    replay: Union[str, list[ReplayFrame]]
    scoreID: int
    additionalModInfo: float

    def __post_init__(self):
        if isinstance(self.mods, int):
            self.mods = [
                mod for index, mod in MODS_INDEX_TO_STR.items()
                if (self.mods & (1 << index))
            ]

        if self.lifeGraph == "":
            self.lifeGraph = {}
        elif isinstance(self.lifeGraph, str):
            self.lifeGraph = {
                time: health
                for point in split_get(self.lifeGraph[:-1], ",", [[str]])
                for time, health in [ split_get(point, "|", [int, float]) ]
            }

        if isinstance(self.replay, str):
            self.replay = [
                ReplayFrame(time, x, y, action)
                for frame in split_get(self.replay[:-1], ",", [[str]])
                for time, x, y, action in [ split_get(frame, "|", [int, float, float, int]) ]
            ]

    def add_frame(self, time: int, x: float, y: float, action: int = 0):
        frame = ReplayFrame(
            time=round(time),
            x=x,
            y=y if "HardRock" not in self.mods else 384-y,
            action=action
        )
        self.replay.append(frame)
