
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra
from jhora.types.rasi import Rasi


# ── Prasna mode enum ────────────────────────────────────────────────────────────

class PrasnaMode(Enum):
    MODE_108 = 108
    MODE_249 = 249
    NADI = 1800

    @property
    def max_number(self) -> int:
        return self.value

    @property
    def label(self) -> str:
        return {
            108: "Prasna-108",
            249: "Prasna-249 (KP)",
            1800: "Nadi Prasna",
        }[self.value]


# ── Result types ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PrasnaSubdivision:
    index: int
    lord: Graha
    start: float
    end: float

@dataclass(frozen=True)
class PrasnaResult:
    number: int
    mode: PrasnaMode
    prasna_lagna: float
    rasi: Rasi
    degrees_in_rasi: float
    nakshatra: Nakshatra
    nakshatra_pada: int
    navamsa_rasi: Optional[Rasi] = None
    sub_lord: Optional[Graha] = None
    description: str = ""

    @property
    def label(self) -> str:
        return f"{self.mode.label} (#{self.number})"


# ── Vimsottari table for KP mode (mode 249) ─────────────────────────────────────
# Proportions from the 9 planets' Vimsottari dasa years:
#   Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16,
#   Saturn 19, Mercury 17, Ketu 7, Venus 20
# Each nakshatra (13°20' = 800') is divided into 9 unequal subs
# with sizes proportional to these years / 120.

_VIMSOTTARI_YEARS: List[Tuple[Graha, int]] = [
    (Graha.SUN, 6),
    (Graha.MOON, 10),
    (Graha.MARS, 7),
    (Graha.RAHU, 18),
    (Graha.JUPITER, 16),
    (Graha.SATURN, 19),
    (Graha.MERCURY, 17),
    (Graha.KETU, 7),
    (Graha.VENUS, 20),
]
_VIMSOTTARI_TOTAL = sum(y for _, y in _VIMSOTTARI_YEARS)  # 120

_NAKSHATRA_ARC = 800.0 / 60.0  # 13.333... degrees
_NAKSHATRA_ARC_MIN = 800.0  # arcminutes

# Pre-compute the 9 sub sizes for each nakshatra (in degrees)
_KP_SUB_SIZES: List[float] = [
    (y / _VIMSOTTARI_TOTAL) * _NAKSHATRA_ARC
    for _, y in _VIMSOTTARI_YEARS
]

# 27 nakshatras × 9 subs = 243 standard KP subdivisions
# For Prasna-249, the extra 6 positions are from the first 6 subs
# of the next cycle, accounting for the starting offset.


# ── Core calculation ────────────────────────────────────────────────────────────

def compute_prasna_lagna(number: int, mode: PrasnaMode) -> float:
    if mode == PrasnaMode.MODE_108:
        return _compute_108(number)
    elif mode == PrasnaMode.MODE_249:
        return _compute_249(number)
    elif mode == PrasnaMode.NADI:
        return _compute_nadi(number)
    else:
        raise ValueError(f"Unknown Prasna mode: {mode}")


def _compute_108(number: int) -> float:
    n = number - 1
    rasi_index = n // 9
    navamsa_index = n % 9
    return rasi_index * 30.0 + navamsa_index * (30.0 / 9.0)


def _compute_249(number: int) -> float:
    n = number - 1

    nakshatra_index = n // 9
    sub_index = n % 9

    safe_nakshatra = nakshatra_index % 27

    longitude = safe_nakshatra * _NAKSHATRA_ARC
    for i in range(sub_index):
        longitude += _KP_SUB_SIZES[i]
    longitude += _KP_SUB_SIZES[sub_index] / 2.0

    return longitude


def _compute_nadi(number: int) -> float:
    n = number - 1
    rasi_index = n // 150
    sub_index = n % 150
    return rasi_index * 30.0 + sub_index * 0.2 + 0.1


# ── Result builder ──────────────────────────────────────────────────────────────

def compute_prasna(number: int, mode: PrasnaMode) -> PrasnaResult:
    if number < 1 or number > mode.max_number:
        raise ValueError(
            f"Number {number} out of range for {mode.label} "
            f"(1-{mode.max_number})"
        )

    pl = compute_prasna_lagna(number, mode)
    pl = pl % 360.0

    rasi = Rasi.from_longitude(pl)
    deg_in_rasi = pl % 30.0
    nakshatra, pada = Nakshatra.from_longitude(pl)

    navamsa_rasi = None
    sub_lord = None
    description = ""

    if mode == PrasnaMode.MODE_108:
        n = number - 1
        navamsa_rasi = _navamsa_rasi_from_prasna_108(number)
        description = (
            f"Rasi #{n // 9 + 1}, Navamsa #{n % 9 + 1} — "
            f"fixes rasi + navamsa of Prasna Lagna"
        )
    elif mode == PrasnaMode.MODE_249:
        n = number - 1
        safe_nak_id = (n // 9) % 27
        sub_id = n % 9
        sub_lord = _VIMSOTTARI_YEARS[sub_id][0]
        sub_lord_name = sub_lord.name.title()
        nakshatra_name = Nakshatra(safe_nak_id).name.replace("_", " ").title()
        description = (
            f"Nakshatra #{safe_nak_id + 1} ({nakshatra_name}), "
            f"Sub #{sub_id + 1} ({sub_lord_name}) — "
            f"fixes rasi + nakshatra + sub of Prasna Lagna"
        )
    elif mode == PrasnaMode.NADI:
        n = number - 1
        rasi_id = n // 150
        sub_id = n % 150
        nadyamsa = sub_id + 1
        description = (
            f"Rasi #{rasi_id + 1}, Nadyamsa #{nadyamsa} — "
            f"fixes all shodasa vargas of Prasna Lagna"
        )

    return PrasnaResult(
        number=number,
        mode=mode,
        prasna_lagna=pl,
        rasi=rasi,
        degrees_in_rasi=deg_in_rasi,
        nakshatra=nakshatra,
        nakshatra_pada=pada,
        navamsa_rasi=navamsa_rasi,
        sub_lord=sub_lord,
        description=description,
    )


def _navamsa_rasi_from_prasna_108(number: int) -> Rasi:
    n = number - 1
    rasi_index = n // 9
    navamsa_index = n % 9
    if rasi_index % 2 == 0:
        target = (rasi_index + navamsa_index) % 12
    else:
        target = (rasi_index + 4 + navamsa_index) % 12
    return Rasi(target)


# ── Convenience: all 108 / 249 / 1800 positions ────────────────────────────────

def all_prasna_results(mode: PrasnaMode) -> List[PrasnaResult]:
    return [compute_prasna(i + 1, mode) for i in range(mode.max_number)]


# ── Chart integration ──────────────────────────────────────────────────────────

def make_prasna_lagna_data(
    prasna_lagna: float,
) -> dict:
    from jhora.charts.chart import PlanetChartData

    pl = prasna_lagna % 360.0
    rasi = Rasi.from_longitude(pl)
    naks, pada = Nakshatra.from_longitude(pl)

    return PlanetChartData(
        graha=Graha.SUN,
        longitude=pl,
        latitude=0.0,
        speed=0.0,
        is_retrograde=False,
        rasi=rasi,
        degrees_in_rasi=pl % 30,
        nakshatra=naks,
        nakshatra_pada=pada,
        dignity="prasna_lagna",
    )
