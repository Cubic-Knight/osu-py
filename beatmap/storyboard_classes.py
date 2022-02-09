"""
To see what each property does, check the osu!wiki: https://osu.ppy.sh/wiki/sk/Storyboard_Scripting
"""


from typing import Union
from dataclasses import dataclass


# ----------------------------------------------------------------------------------------------------------------------
# Some constants and tables that are useful
# ----------------------------------------------------------------------------------------------------------------------

EVENT_TYPE_INT_TO_STR = {
    0: "Image",
    1: "Video",
    2: "Break",
    3: "BackgroundColor",
    4: "Sprite",
    5: "Sample",
    6: "Animation"
}

EVENT_TYPE_STR_TO_INT = {
    "Image": 0,
    "Video": 1,
    "Break": 2,
    "BackgroundColor": 3,
    "Sprite": 4,
    "Sample": 5,
    "Animation": 6
}

EVENT_LAYER_INT_TO_STR = {
    0: "Background",
    1: "Fail",
    2: "Pass",
    3: "Foreground"
}

EVENT_ORIGIN_INT_TO_STR = {
    0: "TopLeft",
    1: "Centre",
    2: "CentreLeft",
    3: "TopRight",
    4: "BottomCentre",
    5: "TopCentre",
    6: "Custom",  # Same as TopLeft, should not be used
    7: "CentreRight",
    8: "BottomLeft",
    9: "BottomRight"
}

# ----------------------------------------------------------------------------------------------------------------------
# Some functions, meant for use in other modules
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Event dataclasses
# Their properties use lowerCamelCase
# ----------------------------------------------------------------------------------------------------------------------


@dataclass
class Event:
    type: Union[int, str]

    def __post_init__(self):
        if isinstance(self.type, int):
            self.type = EVENT_TYPE_INT_TO_STR[self.type]

    @classmethod
    def from_params(cls, *args):
        event_type = EVENT_TYPE_INT_TO_STR[args[0]] if isinstance(args[0], int) else args[0]
        if event_type == "Image":           return Image(*args)
        if event_type == "Video":           return Video(*args)
        if event_type == "Break":           return Break(*args)
        if event_type == "BackgroundColor": return BackgroundColor(*args)
        if event_type == "Sprite":          return Sprite(*args)
        if event_type == "Sample":          return Sample(*args)
        if event_type == "Animation":       return Animation(*args)
        raise ValueError(f"Unknown event type '{event_type}'")

    def type_int(self) -> int:
        return EVENT_TYPE_STR_TO_INT[self.type]

    def osu_format(self) -> str:
        """ Is overridden in child classes """
        return ""


@dataclass
class Image(Event):
    startTime: int
    filename: str
    xOffset: int = 0
    yOffset: int = 0

    def __post_init__(self):
        super().__post_init__()
        self.commands = []

    def osu_format(self) -> str:
        return f"0,{self.startTime},{self.filename},{self.xOffset},{self.yOffset}"


@dataclass
class Video(Event):
    startTime: int
    filename: str
    xOffset: int = 0
    yOffset: int = 0

    def __post_init__(self):
        super().__post_init__()
        self.commands = []

    def osu_format(self) -> str:
        return f"1,{self.startTime},{self.filename},{self.xOffset},{self.yOffset}"


@dataclass
class Break(Event):
    startTime: int
    endTime: int

    def osu_format(self) -> str:
        return f"2,{self.startTime},{self.endTime}"


@dataclass
class BackgroundColor(Event):  # Very obscure class, not sure of its use
    startTime: int
    r: int
    g: int
    b: int

    def __post_init__(self):
        super().__post_init__()
        self.color = (self.r, self.g, self.b)

    def osu_format(self) -> str:
        return f"3,{self.startTime},{self.r},{self.g},{self.b}"


@dataclass
class Sprite(Event):
    layer: Union[int, str]
    origin: Union[int, str]
    filepath: str
    x: int
    y: int

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.layer, int):
            self.layer = EVENT_LAYER_INT_TO_STR[self.layer]
        if isinstance(self.origin, int):
            self.origin = EVENT_ORIGIN_INT_TO_STR[self.origin]
        self.commands = []

    def osu_format(self) -> str:
        return f"4,{self.layer},{self.origin},{self.filepath},{self.x},{self.y}"


@dataclass
class Sample(Event):
    time: int
    layer: Union[int, str]
    filepath: str
    volume: int = 100

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.layer, int):
            self.layer = EVENT_LAYER_INT_TO_STR[self.layer]

    def osu_format(self) -> str:
        return f"4,{self.time},{self.layer},{self.filepath},{self.volume}"


@dataclass
class Animation(Event):
    layer: Union[int, str]
    origin: Union[int, str]
    filepath: str
    x: int
    y: int
    frameCount: int
    frameDelay: int
    loopType: str

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.layer, int):
            self.layer = EVENT_LAYER_INT_TO_STR[self.layer]
        if isinstance(self.origin, int):
            self.origin = EVENT_ORIGIN_INT_TO_STR[self.origin]
        self.commands = []

    def osu_format(self) -> str:
        return (
            f"4,{self.layer},{self.origin},{self.filepath},{self.x},{self.y},"
            f"{self.frameCount},{self.frameDelay},{self.loopType}"
        )


# ----------------------------------------------------------------------------------------------------------------------
# SpriteCommand dataclass. They represent storyboard commands
# Their properties use lowerCamelCase
# ----------------------------------------------------------------------------------------------------------------------


@dataclass
class BaseCommand:
    indentation: int
    event: str

    @classmethod
    def from_params(cls, *args):
        cmd = args[1]
        if cmd == "F":  return Fade(*args)
        if cmd == "M":  return Move(*args)
        if cmd == "MX": return MoveX(*args)
        if cmd == "MY": return MoveY(*args)
        if cmd == "S":  return Scale(*args)
        if cmd == "V":  return VectorScale(*args)
        if cmd == "R":  return Rotate(*args)
        if cmd == "C":  return Color(*args)
        if cmd == "P":  return Parameter(*args)
        if cmd == "L":  return Loop(*args)
        if cmd == "T":  return Trigger(*args)
        raise ValueError(f"Unknown command '{cmd}'")

    def cmd(self) -> str:
        return (" " * self.indentation) + self.event

    def osu_format(self) -> str:
        """ Is overridden in child classes """
        return ""


@dataclass
class SpriteCommand(BaseCommand):
    easing: int = 0
    startTime: int = 0
    endTime: int = 0

    def head(self) -> str:
        return f"{self.cmd()},{self.easing},{self.startTime},{self.endTime}"


@dataclass
class Fade(SpriteCommand):
    startOpacity: float = 0.0
    endOpacity: float = 0.0

    def osu_format(self) -> str:
        return f"{self.head()},{self.startOpacity},{self.endOpacity}"


@dataclass
class Move(SpriteCommand):
    startX: int = 0
    startY: int = 0
    endX: int = 0
    endY: int = 0

    def osu_format(self) -> str:
        return f"{self.head()},{self.startX},{self.startY},{self.endX},{self.endY}"


@dataclass
class MoveX(SpriteCommand):
    startX: int = 0
    endX: int = 0

    def osu_format(self) -> str:
        return f"{self.head()},{self.startX},{self.endX}"


@dataclass
class MoveY(SpriteCommand):
    startY: int = 0
    endY: int = 0

    def osu_format(self) -> str:
        return f"{self.head()},{self.startY},{self.endY}"


@dataclass
class Scale(SpriteCommand):
    startScale: float = 1.0
    endScale: float = 0

    def osu_format(self) -> str:
        return f"{self.head()},{self.startScale},{self.endScale}"


@dataclass
class VectorScale(SpriteCommand):
    startScaleX: float = 1.0
    startScaleY: float = 1.0
    endScaleX: float = 0
    endScaleY: float = 0

    def osu_format(self) -> str:
        return f"{self.head()},{self.startScaleX},{self.startScaleY},{self.endScaleX},{self.endScaleY}"


@dataclass
class Rotate(SpriteCommand):
    startRotate: float = 0.0
    endRotate: float = 0.0

    def osu_format(self) -> str:
        return f"{self.head()},{self.startRotate},{self.endRotate}"


@dataclass
class Color(SpriteCommand):
    startR: Union[int, str] = 0
    startG: Union[int, str] = 0
    startB: Union[int, str] = 0
    endR: Union[int, str] = 0
    endG: Union[int, str] = 0
    endB: Union[int, str] = 0

    def __post_init__(self):
        for param in self.__dict__:
            if param.startswith("start") or param.startswith("end"):
                val = getattr(self, param)
                if isinstance(val, str):
                    setattr(self, param, int(val, base=16))

    def osu_format(self) -> str:
        return f"{self.head()},{self.startR},{self.startG},{self.startB},{self.endR},{self.endG}{self.endB}"


@dataclass
class Parameter(SpriteCommand):
    parameter: str = ''

    def osu_format(self) -> str:
        return f"{self.head()},{self.parameter}"


@dataclass
class Loop(BaseCommand):
    startTime: int = 0
    loopCount: int = 0
    commands: list = None

    def __post_init__(self):
        if self.commands is None:
            self.commands = []

    def osu_format(self) -> str:
        return f"{self.cmd()},{self.startTime},{self.loopCount}"


@dataclass
class Trigger(BaseCommand):
    triggerType: str
    startTime: int = 0
    endTime: int = 0
    commands: list = None

    def __post_init__(self):
        if self.commands is None:
            self.commands = []

    def osu_format(self) -> str:
        return f"{self.cmd()},{self.triggerType},{self.startTime},{self.endTime}"
