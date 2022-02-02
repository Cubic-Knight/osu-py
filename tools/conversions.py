from math import ceil


def ar_to_ms(ar: float) -> int:
    if ar < 5:
        return round(1200 + 120*(5-ar))
    else:
        return round(1200 - 150*(ar-5))


def od_to_win300(od: float) -> int:
    return ceil(160 - 12*od)


def od_to_win100(od: float) -> int:
    return ceil(280 - 16*od)


def od_to_win50(od: float) -> int:
    return ceil(400 - 20*od)


def cs_to_radius(cs: float) -> float:
    return 54.4225 - 4.4819*cs


def ms_to_ar(ms: int) -> float:
    if ms < 1200:
        return 5 - (ms-1200) / 150
    else:
        return 5 + (1200-ms) / 120


def win300_to_od(ms: float) -> float:
    return (ceil(ms)-160) / -12


def win100_to_od(ms: float) -> float:
    return (ceil(ms)-280) / -16


def win50_to_od(ms: float) -> float:
    return (ceil(ms)-400) / -20


def radius_to_cs(pxl: float) -> float:
    return (pxl-54.4225) / -4.4819
