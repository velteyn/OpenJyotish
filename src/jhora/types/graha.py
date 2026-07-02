from enum import IntEnum, auto
from typing import List


class Graha(IntEnum):
    SUN = 0
    MOON = 1
    MARS = 2
    MERCURY = 3
    JUPITER = 4
    VENUS = 5
    SATURN = 6
    RAHU = 7
    KETU = 8

    @property
    def is_benefic(self) -> bool:
        return self in (Graha.JUPITER, Graha.VENUS, Graha.MERCURY)

    @property
    def is_malefic(self) -> bool:
        return self in (Graha.SUN, Graha.MARS, Graha.SATURN, Graha.RAHU, Graha.KETU)

    @property
    def is_planet(self) -> bool:
        return self != Graha.RAHU and self != Graha.KETU

    @property
    def is_node(self) -> bool:
        return self in (Graha.RAHU, Graha.KETU)

    @property
    def lordship_signs(self) -> List[int]:
        return _GRAHA_LORDSHIP[self]

    @property
    def short_name(self) -> str:
        return _GRAHA_SHORT[self]

    @property
    def full_name(self) -> str:
        return _GRAHA_FULL[self]

    @property
    def vimsottari_years(self) -> float:
        return _VIMSOTTARI_YEARS[self]

    @property
    def ashtottari_years(self) -> float:
        return _ASHTOTTARI_YEARS.get(self, 0.0)


_GRAHA_SHORT = {
    Graha.SUN: "Su", Graha.MOON: "Mo", Graha.MARS: "Ma",
    Graha.MERCURY: "Me", Graha.JUPITER: "Ju", Graha.VENUS: "Ve",
    Graha.SATURN: "Sa", Graha.RAHU: "Ra", Graha.KETU: "Ke",
}

_GRAHA_FULL = {
    Graha.SUN: "Sun", Graha.MOON: "Moon", Graha.MARS: "Mars",
    Graha.MERCURY: "Mercury", Graha.JUPITER: "Jupiter", Graha.VENUS: "Venus",
    Graha.SATURN: "Saturn", Graha.RAHU: "Rahu", Graha.KETU: "Ketu",
}

_GRAHA_LORDSHIP = {
    Graha.SUN: [5],
    Graha.MOON: [4],
    Graha.MARS: [1, 8],
    Graha.MERCURY: [3, 6],
    Graha.JUPITER: [9, 12],
    Graha.VENUS: [2, 7],
    Graha.SATURN: [10, 11],
    Graha.RAHU: [],
    Graha.KETU: [],
}

_VIMSOTTARI_YEARS = {
    Graha.SUN: 6, Graha.MOON: 10, Graha.MARS: 7,
    Graha.RAHU: 18, Graha.JUPITER: 16, Graha.SATURN: 19,
    Graha.MERCURY: 17, Graha.KETU: 7, Graha.VENUS: 20,
}

_ASHTOTTARI_YEARS = {
    Graha.SUN: 6, Graha.MOON: 15, Graha.MARS: 8,
    Graha.MERCURY: 17, Graha.JUPITER: 19, Graha.VENUS: 21,
    Graha.SATURN: 10, Graha.RAHU: 12,
}
