from enum import IntEnum
from typing import List, Optional, Tuple


class Nakshatra(IntEnum):
    ASVINI = 0
    BHARANI = 1
    KRITTIKA = 2
    ROHINI = 3
    MRIGASHIRA = 4
    ARDRA = 5
    PUNARVASU = 6
    PUSHYA = 7
    ASHLESHA = 8
    MAGHA = 9
    PURVA_PHALGUNI = 10
    UTTARA_PHALGUNI = 11
    HASTA = 12
    CHITRA = 13
    SWATI = 14
    VISHAKHA = 15
    ANURADHA = 16
    JYESHTHA = 17
    MULA = 18
    PURVA_SHADHA = 19
    UTTARA_SHADHA = 20
    SHRAVANA = 21
    DHANISHTA = 22
    SHATABHISHA = 23
    PURVA_BHADRAPADA = 24
    UTTARA_BHADRAPADA = 25
    REVATI = 26

    @property
    def lord(self):
        return _NAKSHATRA_LORDS[self]

    @property
    def pada_count(self) -> int:
        return 4

    @property
    def start_longitude(self) -> float:
        return float(self.value * 13 + (self.value * 20 // 60))  # ~13°20' per nakshatra

    @property
    def span(self) -> float:
        return 360.0 / 27.0  # 13°20'

    @staticmethod
    def from_longitude(lon: float) -> Tuple["Nakshatra", int]:
        lon_norm = lon % 360
        ns = int(lon_norm // (360.0 / 27.0))
        if ns > 26:
            ns = 26
        pada_size = (360.0 / 27.0) / 4.0
        pada = int((lon_norm % (360.0 / 27.0)) // pada_size) + 1
        return Nakshatra(ns), pada

    @property
    def vimsottari_sequence(self) -> int:
        return _VIMSOTTARI_SEQ[self]


_NAKSHATRA_LORDS = {
    Nakshatra.ASVINI: "Ketu",
    Nakshatra.BHARANI: "Venus",
    Nakshatra.KRITTIKA: "Sun",
    Nakshatra.ROHINI: "Moon",
    Nakshatra.MRIGASHIRA: "Mars",
    Nakshatra.ARDRA: "Rahu",
    Nakshatra.PUNARVASU: "Jupiter",
    Nakshatra.PUSHYA: "Saturn",
    Nakshatra.ASHLESHA: "Mercury",
    Nakshatra.MAGHA: "Ketu",
    Nakshatra.PURVA_PHALGUNI: "Venus",
    Nakshatra.UTTARA_PHALGUNI: "Sun",
    Nakshatra.HASTA: "Moon",
    Nakshatra.CHITRA: "Mars",
    Nakshatra.SWATI: "Rahu",
    Nakshatra.VISHAKHA: "Jupiter",
    Nakshatra.ANURADHA: "Saturn",
    Nakshatra.JYESHTHA: "Mercury",
    Nakshatra.MULA: "Ketu",
    Nakshatra.PURVA_SHADHA: "Venus",
    Nakshatra.UTTARA_SHADHA: "Sun",
    Nakshatra.SHRAVANA: "Moon",
    Nakshatra.DHANISHTA: "Mars",
    Nakshatra.SHATABHISHA: "Rahu",
    Nakshatra.PURVA_BHADRAPADA: "Jupiter",
    Nakshatra.UTTARA_BHADRAPADA: "Saturn",
    Nakshatra.REVATI: "Mercury",
}

_VIMSOTTARI_SEQ = {
    Nakshatra.ASVINI: 0, Nakshatra.BHARANI: 1, Nakshatra.KRITTIKA: 2,
    Nakshatra.ROHINI: 3, Nakshatra.MRIGASHIRA: 4, Nakshatra.ARDRA: 5,
    Nakshatra.PUNARVASU: 6, Nakshatra.PUSHYA: 7, Nakshatra.ASHLESHA: 8,
    Nakshatra.MAGHA: 0, Nakshatra.PURVA_PHALGUNI: 1, Nakshatra.UTTARA_PHALGUNI: 2,
    Nakshatra.HASTA: 3, Nakshatra.CHITRA: 4, Nakshatra.SWATI: 5,
    Nakshatra.VISHAKHA: 6, Nakshatra.ANURADHA: 7, Nakshatra.JYESHTHA: 8,
    Nakshatra.MULA: 0, Nakshatra.PURVA_SHADHA: 1, Nakshatra.UTTARA_SHADHA: 2,
    Nakshatra.SHRAVANA: 3, Nakshatra.DHANISHTA: 4, Nakshatra.SHATABHISHA: 5,
    Nakshatra.PURVA_BHADRAPADA: 6, Nakshatra.UTTARA_BHADRAPADA: 7, Nakshatra.REVATI: 8,
}
