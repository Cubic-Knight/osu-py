from math import *
from typing import Union


def ar_to_ms(ar: Union[int, float]) -> int:
    if ar < 5:
        return round(1200 + 120*(5-ar))
    if ar > 5:
        return round(1200 - 150*(ar-5))
    return 1200


def od_to_win300(od: Union[int, float]) -> int:
    return ceil(160 - 12*od)


def od_to_win100(od: Union[int, float]) -> int:
    return ceil(280 - 16*od)


def od_to_win50(od: Union[int, float]) -> int:
    return ceil(400 - 20*od)


def cs_to_radius(cs: Union[int, float]) -> float:
    return 54.4225 - 4.4819*cs


def ms_to_ar(ms: int) -> float:
    if ms < 1200:
        return 5 - (ms-1200) / 150
    if ms > 1200:
        return 5 + (1200-ms) / 120
    return 5.0


def win300_to_od(ms: Union[int, float]) -> float:
    return (ceil(ms)-160) / -12


def win100_to_od(ms: Union[int, float]) -> float:
    return (ceil(ms)-280) / -16


def win50_to_od(ms: Union[int, float]) -> float:
    return (ceil(ms)-400) / -20


def radius_to_cs(pxl: Union[int, float]) -> float:
    return (pxl-54.4225) / -4.4819
