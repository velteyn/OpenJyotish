from enum import IntEnum, auto
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


class DasaSystem(IntEnum):
    VIMSOTTARI = auto()
    ASHTOTTARI = auto()
    KALACHAKRA = auto()
    YOGINI = auto()
    DWI_SAPTATI_SAMA = auto()
    SHAT_TRIMSAMSA = auto()
    DWADASOTTARI = auto()
    CHATURASEETI_SAMA = auto()
    SATAABDIKA = auto()
    SHODASOTTARI = auto()
    PANCHOTTARI = auto()
    SHASHTI_HAYANI = auto()
    SAPTARSHI = auto()
    NARAYANA = auto()
    CHARA = auto()
    CHARA_PARYAYA = auto()
    SUDASA = auto()
    DRIGDASA = auto()
    NIRYANA_SHOOLA = auto()
    SHOOLA = auto()
    SUDARSANA = auto()
    MOOLA = auto()
    NAVAMSA = auto()
    VARNADA = auto()
    BRAHMA = auto()
    STHIRA = auto()
    MANDOOKA = auto()
    AK_KENDRADI_GRAHA = auto()
    AK_KENDRADI_RASI = auto()
    MUDDA = auto()
    BUDDHI_GATI = auto()
    AYUR_NARAYANA = auto()


class PeriodLevel(IntEnum):
    MAHADASA = 0
    ANTARDASA = 1
    PRATYANTARDASA = 2
    SUKSHMA = 3
    PRANA = 4
    DEHA = 5


@dataclass
class DasaPeriod:
    """A single period in a dasa sequence."""
    lord_index: int           # Graha ID or Rasi index
    lord_name: str
    start_jd: float
    end_jd: float
    duration_years: float
    level: PeriodLevel = PeriodLevel.MAHADASA
    sub_periods: List["DasaPeriod"] = None

    @property
    def start_date(self) -> datetime:
        from jhora.ephemeris.swe import SweEngine
        se = SweEngine()
        y, m, d, h = se.revjul(self.start_jd)
        return datetime(int(y), int(m), int(d))

    @property
    def end_date(self) -> datetime:
        from jhora.ephemeris.swe import SweEngine
        se = SweEngine()
        y, m, d, h = se.revjul(self.end_jd)
        return datetime(int(y), int(m), int(d))
