from dataclasses import dataclass
from typing import Dict, List, Tuple
from jhora.types.graha import Graha


_CHARA_PLANETS = [
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
    Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU,
]

_KARAKA_NAMES = [
    ("AK", "Atma Karaka", "Self, soul, life direction"),
    ("AmK", "Amatya Karaka", "Advisor, minister, career"),
    ("BK", "Bhratru Karaka", "Siblings, courage"),
    ("MK", "Matru Karaka", "Mother, home, emotions"),
    ("PiK", "Pitru Karaka", "Father, authority, past karma"),
    ("PutK", "Putra Karaka", "Children, creativity, intellect"),
    ("GnK", "Gnati Karaka", "Cousins, clan, disputes"),
    ("DK", "Dara Karaka", "Spouse, relationships"),
]


@dataclass
class CharaKaraka:
    graha: Graha
    longitude: float
    rank: int
    short_name: str
    full_name: str
    meaning: str


def _ranking_degrees(graha: Graha, longitude: float) -> float:
    """Effective degrees for karaka ranking (in-sign position).

    Rahu moves retrograde, so it is ranked by mirrored degrees
    (30° minus in-sign longitude) — the mainstream PVR reading,
    verified against the published labels 16/16 on two charts and PVR-book
    examples. Ketu is excluded from the ranking entirely.
    """
    in_sign = longitude % 30
    if graha == Graha.RAHU:
        return 30.0 - in_sign
    return in_sign


def compute_chara_karakas(planets: Dict[Graha, Dict]) -> List[CharaKaraka]:
    """Rank planets by degrees traversed within their sign (highest first).

    Classical Chara Karaka rule: only the position inside the rasi counts
    (longitude % 30), never the absolute longitude — except Rahu, ranked
    mirrored (see ``_ranking_degrees``). Exact ties keep input order
    (real ephemeris longitudes essentially never tie).
    """
    graha_data = []
    for g in _CHARA_PLANETS:
        if g in planets:
            graha_data.append((g, planets[g]["longitude"]))

    graha_data.sort(key=lambda x: _ranking_degrees(x[0], x[1]),
                    reverse=True)

    karakas = []
    for rank, (g, lon) in enumerate(graha_data):
        short, full, meaning = _KARAKA_NAMES[rank]
        karakas.append(CharaKaraka(
            graha=g,
            longitude=lon,
            rank=rank + 1,
            short_name=short,
            full_name=full,
            meaning=meaning,
        ))
    return karakas


def get_atma_karaka(planets: Dict[Graha, Dict]) -> CharaKaraka:
    return compute_chara_karakas(planets)[0]


def karaka_dict(karakas: List[CharaKaraka]) -> Dict[str, CharaKaraka]:
    return {k.short_name: k for k in karakas}
