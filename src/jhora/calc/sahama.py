from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Union

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.calc.karaka import _CHARA_PLANETS


_RASI_LORDS: Dict[int, Graha] = {
    0: Graha.MARS, 1: Graha.VENUS, 2: Graha.MERCURY,
    3: Graha.MOON, 4: Graha.SUN, 5: Graha.MERCURY,
    6: Graha.VENUS, 7: Graha.MARS, 8: Graha.JUPITER,
    9: Graha.SATURN, 10: Graha.SATURN, 11: Graha.JUPITER,
}


@dataclass
class Sahama:
    name: str
    meaning: str
    longitude: float


@dataclass
class _FormulaArg:
    type: str
    value: Union[str, int, float, None] = None


def _house_cusp(lagna_lon: float, house_num: int) -> float:
    return (lagna_lon + (house_num - 1) * 30.0) % 360.0


def _rasi_of(lon: float) -> int:
    return int(lon // 30) % 12


def _lord_lon(rasi_idx: int, planets: Dict[Graha, Dict]) -> float:
    lord = _RASI_LORDS[rasi_idx]
    return planets[lord]["longitude"]


def _is_between(b: float, a: float, x: float) -> bool:
    a %= 360.0
    b %= 360.0
    x %= 360.0
    if a >= b:
        return b <= x <= a
    return x >= b or x <= a


def _resolve(
    arg, lagna_lon: float, planets: Dict, sahamas: Dict[str, float]
) -> float:
    if isinstance(arg, str):
        if arg == "lagna":
            return lagna_lon
        return 0.0
    typ, val = arg
    if typ == "planet":
        return planets[val]["longitude"]
    if typ == "lagna":
        return lagna_lon
    if typ == "house":
        return _house_cusp(lagna_lon, val)
    if typ == "sahama":
        return sahamas[val]
    if typ == "fixed":
        return float(val)
    if typ == "lord":
        if val is None:
            rasi_idx = _rasi_of(lagna_lon)
        elif isinstance(val, int):
            rasi_idx = val
        else:
            rasi_idx = _rasi_of(planets[val]["longitude"])
        return _lord_lon(rasi_idx, planets)
    if typ == "house_lord":
        rasi_idx = _rasi_of(_house_cusp(lagna_lon, val))
        return _lord_lon(rasi_idx, planets)
    return 0.0


def _sahama_raw(lon_a: float, lon_b: float, lon_c: float, check_c: bool = True) -> float:
    result = (lon_a - lon_b + lon_c) % 360.0
    if check_c and not _is_between(lon_b, lon_a, lon_c):
        result = (result + 30.0) % 360.0
    return result


_SAHAMA_DEFS: List[dict] = [
    {"name": "Punya",     "meaning": "Fortune, good deeds",
     "a": ("planet", Graha.MOON),  "b": ("planet", Graha.SUN),   "c": "lagna"},
    {"name": "Vidya",     "meaning": "Education, knowledge",
     "a": ("planet", Graha.SUN),   "b": ("planet", Graha.MOON),  "c": "lagna"},
    {"name": "Yasas",     "meaning": "Fame, reputation",
     "a": ("planet", Graha.JUPITER), "b": ("sahama", "Punya"),   "c": "lagna"},
    {"name": "Mitra",     "meaning": "Friend, companionship",
     "a": ("planet", Graha.JUPITER), "b": ("sahama", "Punya"),   "c": ("planet", Graha.VENUS)},
    {"name": "Mahatmya",  "meaning": "Greatness, magnificence",
     "a": ("sahama", "Punya"),  "b": ("planet", Graha.MARS),     "c": "lagna"},
    {"name": "Asha",      "meaning": "Desires, hopes",
     "a": ("planet", Graha.SATURN),"b": ("planet", Graha.MARS),  "c": "lagna"},
    {"name": "Samartha",  "meaning": "Enterprise, ability",
     "a": ("planet", Graha.MARS), "b": ("lord", None),           "c": "lagna"},
    {"name": "Bhratri",   "meaning": "Brothers, siblings",
     "a": ("planet", Graha.JUPITER), "b": ("planet", Graha.SATURN), "c": "lagna", "no_rev": True},
    {"name": "Gaurava",   "meaning": "Respect, regard",
     "a": ("planet", Graha.JUPITER), "b": ("planet", Graha.MOON), "c": ("planet", Graha.SUN)},
    {"name": "Pitri",     "meaning": "Father",
     "a": ("planet", Graha.SATURN),"b": ("planet", Graha.SUN),   "c": "lagna"},
    {"name": "Rajya",     "meaning": "Kingdom, authority",
     "a": ("planet", Graha.SATURN),"b": ("planet", Graha.SUN),   "c": "lagna"},
    {"name": "Matri",     "meaning": "Mother",
     "a": ("planet", Graha.MOON), "b": ("planet", Graha.VENUS),  "c": "lagna"},
    {"name": "Putra",     "meaning": "Children",
     "a": ("planet", Graha.JUPITER), "b": ("planet", Graha.MOON),"c": "lagna"},
    {"name": "Jeeva",     "meaning": "Life, vitality",
     "a": ("planet", Graha.SATURN),"b": ("planet", Graha.JUPITER),"c": "lagna"},
    {"name": "Karma",     "meaning": "Action, work, career",
     "a": ("planet", Graha.MARS), "b": ("planet", Graha.MERCURY),"c": "lagna"},
    {"name": "Roga",      "meaning": "Disease, illness",
     "a": "lagna",  "b": ("planet", Graha.MOON),              "c": "lagna", "no_rev": True},
    {"name": "Kali",      "meaning": "Great misfortune, strife",
     "a": ("planet", Graha.JUPITER), "b": ("planet", Graha.MARS),"c": "lagna"},
    {"name": "Sastra",    "meaning": "Sciences, scriptures",
     "a": ("planet", Graha.JUPITER), "b": ("planet", Graha.SATURN),"c": ("planet", Graha.MERCURY)},
    {"name": "Bandhu",    "meaning": "Relatives, kin",
     "a": ("planet", Graha.MERCURY), "b": ("planet", Graha.MOON),"c": "lagna"},
    {"name": "Mrityu",    "meaning": "Death",
     "a": ("house", 8),  "b": ("planet", Graha.MOON),            "c": "lagna", "no_rev": True},
    {"name": "Paradesa",  "meaning": "Foreign countries, travel",
     "a": ("house", 9),  "b": ("house_lord", 9),                 "c": "lagna", "no_rev": True},
    {"name": "Artha",     "meaning": "Money, wealth",
     "a": ("house", 2),  "b": ("house_lord", 2),                 "c": "lagna", "no_rev": True},
    {"name": "Paradara",  "meaning": "Adultery, illicit relationships",
     "a": ("planet", Graha.VENUS), "b": ("planet", Graha.SUN),   "c": "lagna"},
    {"name": "Vanik",     "meaning": "Commerce, trade",
     "a": ("planet", Graha.MOON), "b": ("planet", Graha.MERCURY),"c": "lagna"},
    {"name": "Karyasiddhi", "meaning": "Success in endeavours",
     "a": ("planet", Graha.SATURN), "b": ("planet", Graha.SUN),
     "c": ("lord", Graha.SUN),
     "night": {"b": ("planet", Graha.MOON), "c": ("lord", Graha.MOON)}},
    {"name": "Vivaha",    "meaning": "Marriage",
     "a": ("planet", Graha.VENUS), "b": ("planet", Graha.SATURN),"c": "lagna"},
    {"name": "Santapa",   "meaning": "Sadness, grief",
     "a": ("planet", Graha.SATURN),"b": ("planet", Graha.MOON),  "c": ("house", 6)},
    {"name": "Sraddha",   "meaning": "Devotion, sincerity",
     "a": ("planet", Graha.VENUS), "b": ("planet", Graha.MARS),  "c": "lagna"},
    {"name": "Preeti",    "meaning": "Love, attachment",
     "a": ("sahama", "Sastra"), "b": ("sahama", "Punya"),        "c": "lagna"},
    {"name": "Jadya",     "meaning": "Chronic disease, lethargy",
     "a": ("planet", Graha.MARS), "b": ("planet", Graha.SATURN), "c": ("planet", Graha.MERCURY)},
    {"name": "Vyapara",   "meaning": "Business, commerce",
     "a": ("planet", Graha.MARS), "b": ("planet", Graha.SATURN), "c": "lagna", "no_rev": True},
    {"name": "Satru",     "meaning": "Enemy, opposition",
     "a": ("planet", Graha.MARS), "b": ("planet", Graha.SATURN), "c": "lagna", "no_rev": True},
    {"name": "Jalapatana","meaning": "Crossing oceans, sea voyage",
     "a": ("fixed", 105.0), "b": ("planet", Graha.SATURN),       "c": "lagna"},
    {"name": "Bandhana",  "meaning": "Imprisonment, confinement",
     "a": ("sahama", "Punya"), "b": ("planet", Graha.SATURN),    "c": "lagna"},
    {"name": "Apamrityu", "meaning": "Bad death, untimely death",
     "a": ("house", 8), "b": ("planet", Graha.MARS),             "c": "lagna"},
    {"name": "Labha",     "meaning": "Material gains, profit",
     "a": ("house", 11), "b": ("house_lord", 11),                "c": "lagna", "no_rev": True},
]


def compute_sahamas(
    lagna_lon: float, planets: Dict[Graha, Dict], day: bool = True
) -> List[Sahama]:
    sahamas: Dict[str, float] = {}
    result: List[Sahama] = []

    for sd in _SAHAMA_DEFS:
        try:
            no_rev = sd.get("no_rev", False)
            night = sd.get("night", {})

            a_def = sd["a"]
            b_def = sd["b"]
            c_def = sd["c"]

            if not day and not no_rev:
                if night:
                    b_def = night.get("b", b_def)
                    c_def = night.get("c", c_def)
                else:
                    a_def, b_def = b_def, a_def

            lon_a = _resolve(a_def, lagna_lon, planets, sahamas)
            lon_b = _resolve(b_def, lagna_lon, planets, sahamas)
            lon_c = _resolve(c_def, lagna_lon, planets, sahamas)

            raw = _sahama_raw(lon_a, lon_b, lon_c)
            sahamas[sd["name"]] = raw
            result.append(Sahama(name=sd["name"], meaning=sd["meaning"], longitude=raw))
        except (KeyError, IndexError) as e:
            sahamas[sd["name"]] = 0.0
            result.append(Sahama(name=sd["name"], meaning=sd["meaning"], longitude=0.0))

    return result


def compute_punya_sahama(lagna_lon: float, planets: Dict, day: bool = True) -> Sahama:
    return compute_sahamas(lagna_lon, planets, day)[0]
