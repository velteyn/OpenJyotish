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
    ("GK", "Gnati Karaka", "Cousins, clan, disputes"),
    ("DK", "Dara Karaka", "Spouse, relationships"),
    ("StK", "Sthira Karaka", "Longevity, death, endurance"),
]


@dataclass
class CharaKaraka:
    graha: Graha
    longitude: float
    rank: int
    short_name: str
    full_name: str
    meaning: str


def compute_chara_karakas(planets: Dict[Graha, Dict]) -> List[CharaKaraka]:
    graha_data = []
    for g in _CHARA_PLANETS:
        if g in planets:
            graha_data.append((g, planets[g]["longitude"]))

    graha_data.sort(key=lambda x: x[1], reverse=True)

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
