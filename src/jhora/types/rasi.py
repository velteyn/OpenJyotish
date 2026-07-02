from enum import IntEnum
from typing import Optional


class Rasi(IntEnum):
    ARIES = 0
    TAURUS = 1
    GEMINI = 2
    CANCER = 3
    LEO = 4
    VIRGO = 5
    LIBRA = 6
    SCORPIO = 7
    SAGITTARIUS = 8
    CAPRICORN = 9
    AQUARIUS = 10
    PISCES = 11

    @property
    def lord(self):
        return _RASI_LORDS[self]

    @property
    def element(self):
        return _RASI_ELEMENTS[self]

    @property
    def is_movable(self) -> bool:
        return self in (Rasi.ARIES, Rasi.CANCER, Rasi.LIBRA, Rasi.CAPRICORN)

    @property
    def is_fixed(self) -> bool:
        return self in (Rasi.TAURUS, Rasi.LEO, Rasi.SCORPIO, Rasi.AQUARIUS)

    @property
    def is_dual(self) -> bool:
        return self in (Rasi.GEMINI, Rasi.VIRGO, Rasi.SAGITTARIUS, Rasi.PISCES)

    @property
    def is_male(self) -> bool:
        return self in (Rasi.ARIES, Rasi.GEMINI, Rasi.LEO, Rasi.LIBRA, Rasi.SAGITTARIUS, Rasi.AQUARIUS)

    @property
    def is_female(self) -> bool:
        return not self.is_male

    @property
    def is_even(self) -> bool:
        return (self.value + 1) % 2 == 0

    @property
    def is_odd(self) -> bool:
        return not self.is_even

    @property
    def short_name(self) -> str:
        return _RASI_SHORT[self]

    @property
    def full_name(self) -> str:
        return _RASI_FULL[self]

    def to_angle(self) -> float:
        return float(self.value * 30)

    @staticmethod
    def from_longitude(lon: float) -> "Rasi":
        return Rasi(int(lon // 30) % 12)


_RASI_SHORT = {
    Rasi.ARIES: "Ar", Rasi.TAURUS: "Ta", Rasi.GEMINI: "Ge",
    Rasi.CANCER: "Cn", Rasi.LEO: "Le", Rasi.VIRGO: "Vi",
    Rasi.LIBRA: "Li", Rasi.SCORPIO: "Sc", Rasi.SAGITTARIUS: "Sg",
    Rasi.CAPRICORN: "Cp", Rasi.AQUARIUS: "Aq", Rasi.PISCES: "Pi",
}

_RASI_FULL = {
    Rasi.ARIES: "Aries", Rasi.TAURUS: "Taurus", Rasi.GEMINI: "Gemini",
    Rasi.CANCER: "Cancer", Rasi.LEO: "Leo", Rasi.VIRGO: "Virgo",
    Rasi.LIBRA: "Libra", Rasi.SCORPIO: "Scorpio", Rasi.SAGITTARIUS: "Sagittarius",
    Rasi.CAPRICORN: "Capricorn", Rasi.AQUARIUS: "Aquarius", Rasi.PISCES: "Pisces",
}

_RASI_LORDS = {
    Rasi.ARIES: "Mars", Rasi.TAURUS: "Venus", Rasi.GEMINI: "Mercury",
    Rasi.CANCER: "Moon", Rasi.LEO: "Sun", Rasi.VIRGO: "Mercury",
    Rasi.LIBRA: "Venus", Rasi.SCORPIO: "Mars", Rasi.SAGITTARIUS: "Jupiter",
    Rasi.CAPRICORN: "Saturn", Rasi.AQUARIUS: "Saturn", Rasi.PISCES: "Jupiter",
}

_RASI_ELEMENTS = {
    Rasi.ARIES: "fire", Rasi.LEO: "fire", Rasi.SAGITTARIUS: "fire",
    Rasi.TAURUS: "earth", Rasi.VIRGO: "earth", Rasi.CAPRICORN: "earth",
    Rasi.GEMINI: "air", Rasi.LIBRA: "air", Rasi.AQUARIUS: "air",
    Rasi.CANCER: "water", Rasi.SCORPIO: "water", Rasi.PISCES: "water",
}
