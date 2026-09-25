"""Avakahada Chakra — birth identity: rasi, nakshatra, pada, name.

The child's name begins with the syllable of the Moon's nakshatra
pada at birth. The 108-syllable table below is the standard
most-used set (Lahiri/Raman panchanga convention); gana/yoni/nadi
are read off the shared matchmaking tables. Paya (foot-metal) is
not included: its sign table varies by school and is held for
sourcing under the Tradition Rule.
"""

from typing import Dict

from jhora.calc.kuta import _GANA, _NADI, _YONI
from jhora.types.nakshatra import Nakshatra
from jhora.types.rasi import Rasi

#: Nama syllables per nakshatra index: (pada 1..4).
_SYLLABLES = {
    0: ("Chu", "Che", "Cho", "La"),
    1: ("Li", "Lu", "Le", "Lo"),
    2: ("A", "I", "U", "E"),
    3: ("O", "Va", "Vi", "Vu"),
    4: ("Ve", "Vo", "Ka", "Ki"),
    5: ("Ku", "Gha", "Nga", "Chha"),
    6: ("Ke", "Ko", "Ha", "Hi"),
    7: ("Hu", "He", "Ho", "Da"),
    8: ("Di", "Du", "De", "Do"),
    9: ("Ma", "Mi", "Mu", "Me"),
    10: ("Mo", "Ta", "Ti", "Tu"),
    11: ("Te", "To", "Pa", "Pi"),
    12: ("Pu", "Sha", "Na", "Tha"),
    13: ("Pe", "Po", "Ra", "Ri"),
    14: ("Ru", "Re", "Ro", "Ta"),
    15: ("Ti", "Tu", "Te", "To"),
    16: ("Na", "Ni", "Nu", "Ne"),
    17: ("No", "Ya", "Yi", "Yu"),
    18: ("Ye", "Yo", "Bha", "Bhi"),
    19: ("Bhu", "Dha", "Pha", "Dha"),
    20: ("Bhe", "Bho", "Ja", "Ji"),
    21: ("Khi", "Khu", "Khe", "Kho"),
    22: ("Ga", "Gi", "Gu", "Ge"),
    23: ("Go", "Sa", "Si", "Su"),
    24: ("Se", "So", "Da", "Di"),
    25: ("Du", "Tha", "Jha", "Na"),
    26: ("De", "Do", "Cha", "Chi"),
}


def nama_syllable(nak_idx: int, pada: int) -> str:
    """Naming syllable for a nakshatra index (0-26) and pada (1-4)."""
    return _SYLLABLES[nak_idx][pada - 1]


def avakahada(moon_lon: float) -> Dict[str, str]:
    """Birth-identity attributes from the Moon's longitude."""
    nak, pada = Nakshatra.from_longitude(moon_lon)
    yoni = _YONI[nak]
    return {
        "rasi": Rasi.from_longitude(moon_lon).full_name,
        "nakshatra": nak.name.replace("_", " ").title(),
        "pada": str(pada),
        "nama_syllable": nama_syllable(int(nak), pada),
        "gana": _GANA[nak],
        "yoni": f"{yoni.animal} ({'male' if yoni.is_male else 'female'})",
        "nadi": _NADI[nak],
    }
