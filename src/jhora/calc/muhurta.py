"""Muhurta (Electional Astrology) — find auspicious times for new ventures.

Evaluates a proposed time against panchanga (5 limbs), Tara Bala,
inauspicious periods (Rahu Kalam, Gulika Kalam, Yama Gandam),
Abhijit Muhurta, and task-specific criteria from Table 79.

References:
  - "Vedic Astrology: An Integrated Approach" by P.V.R. Narasimha Rao, Ch. 36
  - Dr. B.V. Raman's "Muhurta" (electional astrology)
  - Standard panchanga calculation formulas
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra
from jhora.types.rasi import Rasi


# ── Task types ─────────────────────────────────────────────────────────────────

class MuhurtaTask(Enum):
    GENERAL = "general"
    WEDDING = "wedding"
    NEW_JOB = "new_job"
    HOUSEWARMING = "housewarming"
    NAMING_CHILD = "naming_child"
    FIRST_RICE = "first_rice"
    TEACHING_ALPHABET = "teaching_alphabet"
    SACRED_THREAD = "sacred_thread"
    NEW_VEHICLE = "new_vehicle"
    PLACING_IDOLS = "placing_idols"
    HOUSE_CONSTRUCTION = "house_construction"

    @property
    def label(self) -> str:
        return {
            "general": "General / Any",
            "wedding": "Wedding (Vivaha)",
            "new_job": "New Job / Career Start",
            "housewarming": "Entering a New House (Griha Pravesh)",
            "naming_child": "Naming a Child (Namakarana)",
            "first_rice": "Baby's First Rice (Annaprashana)",
            "teaching_alphabet": "Teaching Alphabet (Vidyarambha)",
            "sacred_thread": "Sacred Thread Ceremony (Upanayana)",
            "new_vehicle": "Buying a New Vehicle",
            "placing_idols": "Placing New Idols in Pooja",
            "house_construction": "House Construction (Bhoomi Pooja)",
        }[self.value]


# ── Task-specific criteria (from Table 79) ─────────────────────────────────────

@dataclass(frozen=True)
class TaskCriteria:
    preferred_tithis: List[int]
    preferred_weekdays: List[int]
    preferred_lagnas: List[int]
    preferred_nakshatras: List[int]
    comments: str = ""

_TASK_CRITERIA: Dict[MuhurtaTask, TaskCriteria] = {
    MuhurtaTask.HOUSE_CONSTRUCTION: TaskCriteria(
        preferred_tithis=[2, 3, 5, 7, 11, 13, 15],
        preferred_weekdays=[1, 3, 4, 5],  # Mon, Wed, Thu, Fri
        preferred_lagnas=[1, 2, 5, 8, 9, 10, 11],  # Ta, Ge, Vi, Sg, Cp, Aq, Pi
        preferred_nakshatras=[0, 4, 5, 7, 11, 13, 14, 15, 17, 20, 21, 23, 24, 25, 26],
        comments="8th house should be empty",
    ),
    MuhurtaTask.HOUSEWARMING: TaskCriteria(
        preferred_tithis=[2, 3, 5, 7, 10, 11, 13, 15],
        preferred_weekdays=[1, 3, 4, 5],
        preferred_lagnas=[1, 2, 4, 5, 8, 9, 10, 11],
        preferred_nakshatras=[4, 5, 11, 13, 17, 20, 23, 24, 25, 26],
        comments="8th should be empty; 4th should be strong",
    ),
    MuhurtaTask.NAMING_CHILD: TaskCriteria(
        preferred_tithis=[2, 3, 5, 7, 10, 11, 13],
        preferred_weekdays=[0, 1, 3, 4, 6],  # Sun, Mon, Wed, Thu, Sat
        preferred_lagnas=[],
        preferred_nakshatras=[0, 4, 5, 7, 8, 11, 13, 14, 15, 17, 20, 21, 23, 24, 25, 26],
        comments="Benefic planet owned lagna; 8th house empty",
    ),
    MuhurtaTask.FIRST_RICE: TaskCriteria(
        preferred_tithis=[2, 3, 5, 7, 10, 13, 15],
        preferred_weekdays=[3, 4, 5],
        preferred_lagnas=[],
        preferred_nakshatras=[0, 4, 5, 7, 8, 11, 13, 14, 15, 17, 20, 21, 23, 24, 25, 26],
        comments="Even/odd month running for boys/girls",
    ),
    MuhurtaTask.TEACHING_ALPHABET: TaskCriteria(
        preferred_tithis=[2, 3, 5, 10, 11, 12],
        preferred_weekdays=[1, 3, 4, 5],
        preferred_lagnas=[1, 2, 5, 9, 11],  # Ge, Vi, Sg, Aq, Pi
        preferred_nakshatras=[0, 4, 5, 7, 8, 11, 13, 14, 15, 17, 20, 21, 23, 24, 25, 26],
        comments="8th house empty; Uttarayana is better",
    ),
    MuhurtaTask.SACRED_THREAD: TaskCriteria(
        preferred_tithis=[2, 3, 5, 10, 11, 6, 12],
        preferred_weekdays=[1, 3, 4, 5],
        preferred_lagnas=[],
        preferred_nakshatras=[0, 7, 13, 14, 15, 17, 21, 26],
        comments="Benefic planet owned lagna; 8th empty",
    ),
    MuhurtaTask.WEDDING: TaskCriteria(
        preferred_tithis=[2, 3, 5, 7, 10, 11, 12, 13, 15],
        preferred_weekdays=[1, 3, 4, 5],
        preferred_lagnas=[],
        preferred_nakshatras=[0, 7, 13, 14, 15, 17, 21, 26, 5, 6, 23, 24],
        comments="Benefic planet owned lagna; 7th house clean",
    ),
    MuhurtaTask.PLACING_IDOLS: TaskCriteria(
        preferred_tithis=[2, 3, 5, 7, 8, 10, 11, 12, 13],
        preferred_weekdays=[0, 1, 3, 4, 5],
        preferred_lagnas=[1, 2, 4, 5, 8, 9, 10, 11],
        preferred_nakshatras=[0, 4, 5, 10, 11, 13, 14, 17, 18, 19, 20, 23, 25, 26],
        comments="Uttarayana for gentle deities; Dakshinayana for aggressive",
    ),
    MuhurtaTask.NEW_VEHICLE: TaskCriteria(
        preferred_tithis=[2, 3, 5, 7, 10, 11, 12, 13, 15],
        preferred_weekdays=[0, 1, 3, 4, 5],
        preferred_lagnas=[1, 2, 4, 5, 8, 9, 10, 11],
        preferred_nakshatras=[5, 7, 8, 13, 14, 15, 17, 20, 21, 23, 24, 25],
        comments="",
    ),
    MuhurtaTask.NEW_JOB: TaskCriteria(
        preferred_tithis=[2, 3, 5, 7, 10, 11, 13, 15],
        preferred_weekdays=[0, 1, 3, 4, 6],
        preferred_lagnas=[1, 2, 4, 5, 8, 9, 10, 11],
        preferred_nakshatras=[0, 4, 5, 7, 8, 11, 13, 14, 15, 17, 20, 21, 23, 24, 25, 26],
        comments="Sun/benefic owned lagna; see D-10",
    ),
    MuhurtaTask.GENERAL: TaskCriteria(
        preferred_tithis=[1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 15],
        preferred_weekdays=[0, 1, 3, 4, 5, 6],
        preferred_lagnas=[],
        preferred_nakshatras=[0, 4, 5, 7, 8, 11, 13, 14, 15, 17, 20, 21, 23, 24, 25, 26],
        comments="Avoid Rahu Kalam, Gulika Kalam, Yama Gandam",
    ),
}


# ── Weekday mapping ────────────────────────────────────────────────────────────

_WEEKDAY_NAMES: List[str] = [
    "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday",
]

_WEEKDAY_PLANET: List[Graha] = [
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
    Graha.JUPITER, Graha.VENUS, Graha.SATURN,
]


# ── Rahu Kalam — inauspicious periods each day ────────────────────────────────
# Duration = 1/8th of daytime (from sunrise to sunset).
# Each weekday has a specific period ruled by a planet in sequence.
# Sequence: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn (from Sunday).
# Rahu's period = 8 - lord_index (1-indexed) counted from sunrise.

_RAHU_PERIOD_INDEX: List[int] = [
    7,  # Sunday:    period 8 (Sun→Moon→Mars→Mercury→Jupiter→Venus→Saturn→RAHU)
    6,  # Monday:    period 7
    5,  # Tuesday:   period 6
    4,  # Wednesday: period 5
    3,  # Thursday:  period 4
    2,  # Friday:    period 3
    1,  # Saturday:  period 2
]


# ── Gulika Kalam — inauspicious periods ───────────────────────────────────────
# Similar to Rahu Kalam but for Gulika (Saturn's son).

_GULIKA_PERIOD_INDEX: List[int] = [
    2,  # Sunday:    period 3
    1,  # Monday:    period 2
    0,  # Tuesday:   period 1
    7,  # Wednesday: period 8
    6,  # Thursday:  period 7
    5,  # Friday:    period 6
    4,  # Saturday:  period 5
]


# ── Yama Gandam — inauspicious periods ────────────────────────────────────────

_YAMAGANDA_PERIOD_INDEX: List[int] = [
    4,  # Sunday
    3,  # Monday
    2,  # Tuesday
    1,  # Wednesday
    0,  # Thursday
    7,  # Friday
    6,  # Saturday
]


# ── Durmuhurta — day/night avoided windows (15 equal muhurtas) ────────────────
# Day (sunrise→sunset) is split into 15 equal day-muhurtas; the weekday lord of the
# day picks one muhurta (1-based): Sun→14th, Mon→9th, Tue→4th, Wed→8th, Thu→6th,
# Fri→4th, Sat→1st. Values below are 0-based indexes into the 15 muhurtas.
# Source: classical 15-muhurta Dur Muhurtam rule (Kalaprakashika / Muhurta
# Chintamani, via https://panchangtime.com/methodology/dur-muhurtam). The reference
# daily-adjuncts table prints DurMuhurta1Start/End and DurMuhurta2Start/End;
# DurMuhurta1 is the day window and DurMuhurta2 is modelled as the same weekday
# index applied to the 15 equal night-muhurtas (sunset→next sunrise).

_DURMUHURTA_DAY_MUHURTA_INDEX: List[int] = [
    13,  # Sunday    → 14th day-muhurta
    8,   # Monday    →  9th
    3,   # Tuesday   →  4th
    7,   # Wednesday →  8th
    5,   # Thursday  →  6th
    3,   # Friday    →  4th
    0,   # Saturday  →  1st
]

_DURMUHURTA_NIGHT_MUHURTA_INDEX: List[int] = [
    13,  # Sunday    → 14th night-muhurta
    8,   # Monday    →  9th
    3,   # Tuesday   →  4th
    7,   # Wednesday →  8th
    5,   # Thursday  →  6th
    3,   # Friday    →  4th
    0,   # Saturday  →  1st
]


# ── Varjya (Nakshatra Varjyam / Visha Ghatis) — avoided nakshatra windows ─────
# The ~96-minute avoid window inside a running nakshatra. Each nakshatra has a fixed
# starting hour X (measured into a nakshatra normalized to 24 hours) at which the
# window begins; the window lasts 1/15 of the nakshatra's span (≈1.6 h per 24 h
# nakshatra). Up to two windows (Varjya1/2) can fall in one day — the day nakshatra's
# and, when it also intersects daytime, the next nakshatra's.
# Source: Drik Panchang "Nakshatra Thyajyam | Varjyam" table — start times for all
# 27 nakshatras (https://www.drikpanchang.com/tutorials/panchang-utilities/nakshatra-thyajyam.html);
# duration method per PanchangamCalculations.pdf (archive.org item PanchangamCalculations);
# cross-checked against panchangtime.com Varjyam guide ("Varjyam is based on that
# day's nakshatra"). Values are hours, keyed by Nakshatra enum (ASVINI=0 … REVATI=26).

_NAKSHATRA_VARJYA_START_HOURS: List[float] = [
    20.0,  # Ashwini
    9.6,   # Bharani
    12.0,  # Krittika
    16.0,  # Rohini
    5.6,   # Mrigasira
    8.4,   # Ardra
    12.0,  # Punarvasu
    8.0,   # Pushya
    12.8,  # Ashlesha
    12.0,  # Magha
    8.0,   # Purva Phalguni
    7.2,   # Uttara Phalguni
    8.4,   # Hasta
    8.0,   # Chitra
    5.6,   # Swati
    5.6,   # Vishakha
    4.0,   # Anuradha
    5.6,   # Jyeshtha
    8.4,   # Mula
    9.6,   # Purva Ashadha
    8.0,   # Uttara Ashadha
    4.0,   # Shravana
    4.0,   # Dhanishta
    7.2,   # Shatabhisha
    6.4,   # Purva Bhadrapada
    9.6,   # Uttara Bhadrapada
    12.0,  # Revati
]

_NAKSHATRA_SPAN_DEG = 360.0 / 27.0      # 13°20' per nakshatra
_VARJYA_FRACTION = 1.0 / 15.0           # window length = 1/15 of the nakshatra span
_MOON_SPEED_DEG_PER_DAY = 360.0 / 27.321661  # mean sidereal Moon motion (°/day)


# ── Panchaka Rahita — five avoided types over the day (B.V. Raman mod-9 rule) ──
# For a candidate moment: category = (Tithi# + Vara# + Nakshatra# + Lagna#) mod 9,
# where Tithi# is 1..15 within its paksha, Vara# is Sun=1..Sat=7, Nakshatra# is
# Ashwini=1..Revati=27, and Lagna# is the ascending rashi Aries=1..Pisces=12.
# Remainder → category: 0,3,5,7 Rahita (good); 1 Mrityu; 2 Agni; 4 Raja; 6 Chora;
# 8 Roga. Source: Dr. B.V. Raman's "Muhurta" (mapping per RVA muhurta notes at
# https://www.rahasyavedicastrology.com/muhurat-panchaka-rahitam); verified
# segment-by-segment against Drik Panchang "Panchaka Rahita Muhurta for the day"
# for Chennai 2026-09-16 (all 13 segments reproduce exactly).

_PANCHAKA_CATEGORY_BY_REMAINDER: Dict[int, Tuple[str, bool]] = {
    0: ("Rahita", True),
    1: ("Mrityu", False),
    2: ("Agni", False),
    3: ("Rahita", True),
    4: ("Raja", False),
    5: ("Rahita", True),
    6: ("Chora", False),
    7: ("Rahita", True),
    8: ("Roga", False),
}


# ── Chandra Bala — personal Moon strength from the Janma rashi ─────────────────
# Count inclusively from the person's Janma rashi (derived from the Janma nakshatra)
# to the day's Moon rashi; the resulting house maps to a grade:
#   GOOD    on 1st, 3rd, 6th, 7th, 10th, 11th — favorable for beginnings
#   NEUTRAL on 2nd, 5th, 9th                  — middling, not relied upon
#   BAD     on 4th, 8th, 12th                 — weakest, avoided
# Source: Drik Panchang "Good Chandrabalam … rashi borns" lists,
# PanchangTime Chandrabala methodology (https://panchangtime.com/methodology/chandrabala),
# AstroShruti "1-3-6-7-10-11 rule", mypanchang.mypanchang.com chandra-bala note.

_CHANDRA_BALA_GOOD_HOUSES: Tuple[int, ...] = (1, 3, 6, 7, 10, 11)
_CHANDRA_BALA_NEUTRAL_HOUSES: Tuple[int, ...] = (2, 5, 9)
_CHANDRA_BALA_BAD_HOUSES: Tuple[int, ...] = (4, 8, 12)


# ── Abhijit Muhurta — the daily 48-minute auspicious window ──────────────────
# Around local noon (when Sun is at the meridian).
# Standard: 24 minutes before local noon to 24 minutes after.


# ── Result types ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TithiInfo:
    index: int
    name: str
    is_shukla: bool

@dataclass(frozen=True)
class InauspiciousPeriod:
    kind: str
    start: float
    end: float

@dataclass(frozen=True)
class PanchangaInfo:
    tithi: TithiInfo
    weekday: int
    weekday_name: str
    nakshatra: Nakshatra
    yoga_index: int
    karana_index: int

@dataclass(frozen=True)
class TaskEvaluation:
    task: MuhurtaTask
    datetime: datetime
    panchanga: PanchangaInfo
    lagna_rasi: Optional[Rasi]
    inauspicious_periods: List[InauspiciousPeriod]
    in_abhijit: bool
    tithi_ok: bool
    weekday_ok: bool
    nakshatra_ok: bool
    lagna_ok: bool
    score: float
    score_detail: str = ""

    @property
    def is_good(self) -> bool:
        return self.score >= 0.6

    @property
    def summary_line(self) -> str:
        parts = []
        if self.tithi_ok:
            parts.append("Tithi✓")
        if self.weekday_ok:
            parts.append("Vara✓")
        if self.nakshatra_ok:
            parts.append("Nak✓")
        if self.lagna_ok:
            parts.append("Lagna✓")
        if self.in_abhijit:
            parts.append("Abhijit!")
        return f"{self.datetime.strftime('%H:%M')} score={self.score:.2f} {' '.join(parts)}"


# ── Adjunct grades ─────────────────────────────────────────────────────────────

class Tara(Enum):
    """Tara Bala — 9-fold star strength counted Janma→target inclusive, mod 9."""

    JANMA = "Janma"
    SAMPAT = "Sampat"
    VIPAT = "Vipat"
    KSHEMA = "Kshema"
    PRATYARI = "Pratyari"
    SADHAKA = "Sadhaka"
    NIDHANA = "Nidhana"
    MITRA = "Mitra"
    PARAMA_MITRA = "Parama Mitra"

    @property
    def auspicious(self) -> bool:
        return self in (
            Tara.SAMPAT, Tara.KSHEMA, Tara.SADHAKA, Tara.MITRA, Tara.PARAMA_MITRA,
        )

    @classmethod
    def from_janma(cls, janma: Nakshatra, target: Nakshatra) -> Tuple["Tara", bool]:
        """Classify `target` relative to the Janma nakshatra (inclusive 9-count)."""
        count = (target.value - janma.value) % 27 + 1
        remainder = count % 9
        by_remainder = {
            1: Tara.JANMA, 2: Tara.SAMPAT, 3: Tara.VIPAT, 4: Tara.KSHEMA,
            5: Tara.PRATYARI, 6: Tara.SADHAKA, 7: Tara.NIDHANA, 8: Tara.MITRA,
            0: Tara.PARAMA_MITRA,
        }
        tara = by_remainder[remainder]
        return tara, tara.auspicious


class ChandraBala(Enum):
    """Chandra Bala grade from the house count Janma-rashi → day Moon-rashi.

    GOOD houses 1,3,6,7,10,11; NEUTRAL 2,5,9; BAD 4,8,12; UNAVAILABLE without Janma.
    """

    GOOD = "Good"
    NEUTRAL = "Neutral"
    BAD = "Bad"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class AdjunctsInfo:
    """Bundle of Durmuhurta/Varjya/Panchaka windows plus Bala grades for a day."""

    durmuhurta: Tuple[InauspiciousPeriod, ...]
    varjya: Tuple[InauspiciousPeriod, ...]
    panchaka: Tuple[InauspiciousPeriod, ...]
    chandra_bala: ChandraBala
    tara_bala: Optional[Tara]
    tara_auspicious: bool


# ── Core helpers ───────────────────────────────────────────────────────────────

def _sunrise_sunset(date: datetime, lat: float, lon: float, tz_offset: float
                     ) -> Tuple[float, float]:
    from jhora.ephemeris.swe import SweEngine, SE_SUN
    swe = SweEngine()
    # Start from local midnight (0h local time → UTC)
    jd_midnight = swe.julday(date.year, date.month, date.day, -tz_offset)
    try:
        sunrise = swe.rise_trans(jd_midnight, SE_SUN, lat, lon, rise=True)
        sunset = swe.rise_trans(jd_midnight, SE_SUN, lat, lon, rise=False)
        if sunrise is None:
            sunrise = jd_midnight + 0.2
        if sunset is None:
            sunset = jd_midnight + 0.5
    except Exception:
        sunrise = jd_midnight + 0.2
        sunset = jd_midnight + 0.5
    return sunrise, sunset


def sunrise_sunset_hours(date: datetime, lat: float, lon: float,
                         tz_offset_east: float) -> Tuple[float, float]:
    """Sunrise/sunset as local decimal hours (single precise source).

    Wraps the verified swe-based engine. tz_offset_east is signed hours EAST
    of UTC (e.g. +5.5 for IST), matching the JHD/DB convention. Falls back
    gracefully when swe has no data.
    """
    sunrise_jd, sunset_jd = _sunrise_sunset(date, lat, lon, tz_offset_east)
    base = _datetime_to_jd(date.replace(hour=0, minute=0, second=0,
                                        microsecond=0), tz_offset_east)
    return ((sunrise_jd - base) * 24.0 % 24.0,
            (sunset_jd - base) * 24.0 % 24.0)


def _tithi(sun_lon: float, moon_lon: float) -> TithiInfo:
    diff = (moon_lon - sun_lon) % 360.0
    tithi_num = int(diff // 12)
    # tithi_num 0-14 → Shukla (waxing), 15-29 → Krishna (waning)
    is_shukla = tithi_num < 15
    display_num = (tithi_num % 15) + 1
    tithi_names = [
        "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
        "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
        "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Poornima/Amavasya",
    ]
    name = tithi_names[display_num - 1]
    return TithiInfo(index=tithi_num, name=name, is_shukla=is_shukla)


UNUSED_NAKSHATRA_YOGA_NAMES: List[str] = [
    "Vishkumbha", "Preeti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarman", "Dhrithi", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Varigha", "Paridha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]


def _yoga(sun_lon: float, moon_lon: float) -> int:
    total = (sun_lon + moon_lon) % 360.0
    return int(total // (360.0 / 27))


def _karana(tithi_index: int) -> int:
    return tithi_index * 2 % 11


def _inauspicious_periods(date: datetime, lat: float, lon: float, tz_offset: float
                           ) -> List[InauspiciousPeriod]:
    sunrise, sunset = _sunrise_sunset(date, lat, lon, tz_offset)
    day_length = (sunset - sunrise) * 24.0  # in hours
    period_len = day_length / 8.0

    weekday = date.weekday()
    # Python weekday: Mon=0, Sun=6. Convert to Sun=0
    wd = (weekday + 1) % 7

    periods = []

    # Rahu Kalam
    rahu_start = sunrise + _RAHU_PERIOD_INDEX[wd] * period_len / 24.0
    periods.append(InauspiciousPeriod(
        kind="Rahu Kalam",
        start=rahu_start,
        end=rahu_start + period_len / 24.0,
    ))

    # Gulika Kalam
    guli_start = sunrise + _GULIKA_PERIOD_INDEX[wd] * period_len / 24.0
    periods.append(InauspiciousPeriod(
        kind="Gulika Kalam",
        start=guli_start,
        end=guli_start + period_len / 24.0,
    ))

    # Yama Gandam
    yama_start = sunrise + _YAMAGANDA_PERIOD_INDEX[wd] * period_len / 24.0
    periods.append(InauspiciousPeriod(
        kind="Yama Gandam",
        start=yama_start,
        end=yama_start + period_len / 24.0,
    ))

    return periods


# ── Moon position helper ───────────────────────────────────────────────────────

def _get_moon_longitude(date: datetime, tz_offset: float) -> float:
    from jhora.ephemeris.swe import SweEngine, SE_MOON
    swe = SweEngine()
    gmt = date.hour - tz_offset
    jd = swe.julday(date.year, date.month, date.day, gmt)
    swe.set_sidereal_mode("lahiri")
    moon_data = swe.calc_planet(SE_MOON, jd)
    return moon_data.longitude


def _get_sun_longitude(date: datetime, tz_offset: float) -> float:
    from jhora.ephemeris.swe import SweEngine, SE_SUN
    swe = SweEngine()
    gmt = date.hour - tz_offset
    jd = swe.julday(date.year, date.month, date.day, gmt)
    swe.set_sidereal_mode("lahiri")
    sun_data = swe.calc_planet(SE_SUN, jd)
    return sun_data.longitude


# ── Public API ─────────────────────────────────────────────────────────────────

def compute_panchanga(date: datetime, lat: float, lon: float, tz_offset: float = 0.0
                      ) -> PanchangaInfo:
    sun_lon = _get_sun_longitude(date, tz_offset)
    moon_lon = _get_moon_longitude(date, tz_offset)

    tithi = _tithi(sun_lon, moon_lon)
    py_wd = date.weekday()
    weekday = (py_wd + 1) % 7  # Sun=0, Mon=1, ..., Sat=6
    weekday_name = date.strftime("%A")

    nakshatra, _ = Nakshatra.from_longitude(moon_lon)
    yoga_idx = _yoga(sun_lon, moon_lon)
    karana_idx = _karana(tithi.index)

    return PanchangaInfo(
        tithi=tithi,
        weekday=weekday,
        weekday_name=weekday_name,
        nakshatra=nakshatra,
        yoga_index=yoga_idx,
        karana_index=karana_idx,
    )


def evaluate_time(
    dt: datetime,
    lat: float,
    lon: float,
    tz_offset: float = 0.0,
    task: MuhurtaTask = MuhurtaTask.GENERAL,
    jnama_nakshatra: Optional[Nakshatra] = None,
) -> TaskEvaluation:
    panchanga = compute_panchanga(dt, lat, lon, tz_offset)
    criteria = _TASK_CRITERIA.get(task, _TASK_CRITERIA[MuhurtaTask.GENERAL])

    sun_lon = _get_sun_longitude(dt, tz_offset)
    asc = sun_lon + 90.0  # rough approximation without full houses
    lagna_rasi = Rasi.from_longitude(asc)

    inauspicious = _inauspicious_periods(dt, lat, lon, tz_offset)
    in_rahukalam = False
    in_gulika = False
    in_yamaganda = False
    jd_dt = _datetime_to_jd(dt, tz_offset)
    for p in inauspicious:
        if p.start <= jd_dt <= p.end:
            if p.kind == "Rahu Kalam":
                in_rahukalam = True
            elif p.kind == "Gulika Kalam":
                in_gulika = True
            elif p.kind == "Yama Gandam":
                in_yamaganda = True

    in_abhijit = _is_abhijit(dt, lat, lon, tz_offset)

    display_tithi = (panchanga.tithi.index % 15) + 1
    tithi_ok = display_tithi in criteria.preferred_tithis
    weekday_ok = panchanga.weekday in criteria.preferred_weekdays
    nakshatra_ok = panchanga.nakshatra.value in criteria.preferred_nakshatras
    lagna_ok = not criteria.preferred_lagnas or lagna_rasi.value in criteria.preferred_lagnas

    score = 0.0
    detail_parts = []

    if tithi_ok:
        score += 0.25
    else:
        dt_name = panchanga.tithi.name
        detail_parts.append(f"tithi({dt_name}) bad")

    if weekday_ok:
        score += 0.15
    else:
        detail_parts.append(f"weekday({panchanga.weekday_name}) bad")

    if nakshatra_ok:
        score += 0.20
    else:
        detail_parts.append(f"nakshatra({panchanga.nakshatra.name}) bad")

    if lagna_ok:
        score += 0.10
    elif criteria.preferred_lagnas:
        detail_parts.append(f"lagna({lagna_rasi.short_name}) bad")

    if in_rahukalam:
        score -= 0.15
        detail_parts.append("Rahu Kalam!")
    if in_gulika:
        score -= 0.10
        detail_parts.append("Gulika Kalam!")
    if in_yamaganda:
        score -= 0.10
        detail_parts.append("Yama Gandam!")
    if in_abhijit:
        score += 0.15
        detail_parts.append("Abhijit!")

    # Daily adjuncts: Durmuhurta/Varjya/Panchaka avoidance, Chandra GOOD and
    # auspicious Tara rewards (Tara/Chandra need a Janma nakshatra).
    adjuncts = _day_adjuncts(dt, lat, lon, tz_offset, jnama_nakshatra)
    if any(win.start <= jd_dt <= win.end for win in adjuncts.durmuhurta):
        score -= 0.15
        detail_parts.append("Durmuhurta!")
    if any(win.start <= jd_dt <= win.end for win in adjuncts.varjya):
        score -= 0.15
        detail_parts.append("Varjya!")
    _pan_kind, pan_rahita = _segments_kind_at(adjuncts.panchaka, jd_dt)
    if _pan_kind is not None and not pan_rahita:
        score -= 0.10
        detail_parts.append(f"{_pan_kind} Panchaka!")
    if adjuncts.chandra_bala is ChandraBala.GOOD:
        score += 0.10
        detail_parts.append("Chandra Bala Good")
    if adjuncts.tara_auspicious:
        score += 0.10
        detail_parts.append("Tara Bala Good")

    score = max(0.0, min(1.0, score))

    return TaskEvaluation(
        task=task,
        datetime=dt,
        panchanga=panchanga,
        lagna_rasi=lagna_rasi,
        inauspicious_periods=inauspicious,
        in_abhijit=in_abhijit,
        tithi_ok=tithi_ok,
        weekday_ok=weekday_ok,
        nakshatra_ok=nakshatra_ok,
        lagna_ok=lagna_ok,
        score=score,
        score_detail="; ".join(detail_parts) if detail_parts else "All good",
    )


def _is_abhijit(dt: datetime, lat: float, lon: float, tz_offset: float) -> bool:
    sunrise, sunset = _sunrise_sunset(dt, lat, lon, tz_offset)
    solar_noon = (sunrise + sunset) / 2.0
    abhijit_start = solar_noon - 0.0166666667  # 24 min before noon
    abhijit_end = solar_noon + 0.0166666667    # 24 min after noon
    jd_time = _datetime_to_jd(dt, tz_offset)
    return abhijit_start <= jd_time <= abhijit_end


def _datetime_to_jd(dt: datetime, tz_offset: float) -> float:
    from jhora.ephemeris.swe import SweEngine
    swe = SweEngine()
    gmt = (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) - tz_offset
    return swe.julday(dt.year, dt.month, dt.day, gmt)


# ── Adjunct computations ───────────────────────────────────────────────────────

def _moon_longitude_at_jd(jd: float) -> float:
    from jhora.ephemeris.swe import SweEngine, SE_MOON
    swe = SweEngine()
    swe.set_sidereal_mode("lahiri")
    return swe.calc_planet(SE_MOON, jd).longitude


def _nakshatra_rasi(nakshatra: Nakshatra) -> Rasi:
    """Rashi that contains the nakshatra's starting longitude."""
    return Rasi.from_longitude(nakshatra.value * _NAKSHATRA_SPAN_DEG)


def _durmuhurta_windows(date: datetime, lat: float, lon: float, tz_offset: float
                        ) -> Tuple[InauspiciousPeriod, ...]:
    """Day + night Durmuhurta windows from the weekday → 15-muhurta index tables.

    DurMuhurta1 spans the weekday's day-muhurta; DurMuhurta2 the same index in the
    15 equal night-muhurtas (sunset → next sunrise), matching the two columns of the
    reference daily-adjuncts table.
    """
    sunrise, sunset = _sunrise_sunset(date, lat, lon, tz_offset)
    next_sunrise, _next_sunset = _sunrise_sunset(date + timedelta(days=1), lat, lon, tz_offset)

    wd = (date.weekday() + 1) % 7  # Sun=0
    day_idx = _DURMUHURTA_DAY_MUHURTA_INDEX[wd]
    night_idx = _DURMUHURTA_NIGHT_MUHURTA_INDEX[wd]

    day_span = (sunset - sunrise) / 15.0
    night_span = (next_sunrise - sunset) / 15.0

    return (
        InauspiciousPeriod(kind="Durmuhurta",
                           start=sunrise + day_idx * day_span,
                           end=sunrise + (day_idx + 1) * day_span),
        InauspiciousPeriod(kind="Durmuhurta",
                           start=sunset + night_idx * night_span,
                           end=sunset + (night_idx + 1) * night_span),
    )


def _nakshatra_varjya_windows(date: datetime, lat: float, lon: float, tz_offset: float
                              ) -> Tuple[InauspiciousPeriod, ...]:
    """Nakshatra Varjyam windows (Visha Ghatis) inside the civil day.

    Windows of the nakshatras the Moon occupies during the day (the one at the civil
    day start and the next) are each clamped to the civil day 00:00–24:00 local and
    returned as Varjya1/Varjya2, matching the two Varjya columns of the reference
    table (Drik lists night Varjyam windows, so no daylight clipping is applied).
    Moon position is referenced at the civil-day start.
    """
    day_start_dt = date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_start_jd = _datetime_to_jd(day_start_dt, tz_offset)
    day_end_jd = day_start_jd + 1.0

    moon0 = _moon_longitude_at_jd(day_start_jd)
    moon1 = _moon_longitude_at_jd(day_end_jd)
    rate = (moon1 - moon0) % 360.0
    if rate > 180.0:
        rate -= 360.0

    day_nak, _pada = Nakshatra.from_longitude(moon0)

    def _crossing_jd(target_lon: float) -> Optional[float]:
        frac = (target_lon - moon0) % 360.0 / rate if rate else float("inf")
        return day_start_jd + frac if 0.0 <= frac <= 1.0 else None

    windows = []
    for nak in (day_nak, Nakshatra((day_nak.value + 1) % 27)):
        nak_start_lon = nak.value * _NAKSHATRA_SPAN_DEG
        start_fraction = _NAKSHATRA_VARJYA_START_HOURS[nak.value] / 24.0
        start_lon = nak_start_lon + start_fraction * _NAKSHATRA_SPAN_DEG
        end_lon = start_lon + _VARJYA_FRACTION * _NAKSHATRA_SPAN_DEG

        start_jd = _crossing_jd(start_lon)
        end_jd = _crossing_jd(end_lon)
        if start_jd is None or end_jd is None:
            continue

        clipped_start = max(start_jd, day_start_jd)
        clipped_end = min(end_jd, day_end_jd)
        if clipped_end > clipped_start:
            windows.append(InauspiciousPeriod(
                kind="Varjya",
                start=clipped_start,
                end=clipped_end,
            ))

    return tuple(windows)


def _panchaka_category_for(tithi_no: int, vara_no: int, nak_no: int, lagna_no: int
                           ) -> Tuple[str, bool]:
    """Panchaka category for the remainder (Tithi# + Vara# + Nakshatra# + Lagna#) mod 9."""
    remainder = (tithi_no + vara_no + nak_no + lagna_no) % 9
    return _PANCHAKA_CATEGORY_BY_REMAINDER[remainder]


def _panchaka_category(dt: datetime, lat: float, lon: float, tz_offset: float
                       ) -> Tuple[str, bool]:
    from jhora.ephemeris.swe import SweEngine
    panchanga = compute_panchanga(dt, lat, lon, tz_offset)
    tithi_no = (panchanga.tithi.index % 15) + 1
    vara_no = panchanga.weekday + 1
    nak_no = panchanga.nakshatra.value + 1
    swe = SweEngine()
    ascendant = swe.houses(_datetime_to_jd(dt, tz_offset), lat, lon).ascendant
    lagna_no = Rasi.from_longitude(ascendant).value + 1
    return _panchaka_category_for(tithi_no, vara_no, nak_no, lagna_no)


def _panchaka_segments(date: datetime, lat: float, lon: float, tz_offset: float
                       ) -> Tuple[InauspiciousPeriod, ...]:
    """Panchaka-Rahita segments over the civil day, grouped at 10-minute resolution.

    Consecutive candidate moments sharing a category form one segment; Rahita (good)
    segments carry kind "Rahita", the five avoid types carry "<Name> Panchaka".
    """
    step = timedelta(minutes=10)
    day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = date.replace(hour=23, minute=59)

    segments = []
    seg_start = day_start
    seg_kind = None
    seg_cat = None
    dt = day_start
    while dt < day_end:
        cat = _panchaka_category(dt, lat, lon, tz_offset)
        if cat != seg_cat:
            if seg_kind is not None:
                label = seg_kind if seg_cat[1] else f"{seg_kind} Panchaka"
                segments.append(InauspiciousPeriod(
                    kind=label,
                    start=_datetime_to_jd(seg_start, tz_offset),
                    end=_datetime_to_jd(dt, tz_offset),
                ))
            seg_cat = cat
            seg_kind, _rahita = cat
            seg_start = dt
        dt += step

    label = seg_kind if seg_cat[1] else f"{seg_kind} Panchaka"
    segments.append(InauspiciousPeriod(
        kind=label,
        start=_datetime_to_jd(seg_start, tz_offset),
        end=_datetime_to_jd(day_end, tz_offset),
    ))
    return tuple(segments)


def _chandra_bala_grade_for(moon_rasi_value: int, janma_nakshatra: Optional[Nakshatra]
                            ) -> ChandraBala:
    if janma_nakshatra is None:
        return ChandraBala.UNAVAILABLE
    janma_rasi = _nakshatra_rasi(janma_nakshatra)
    house = (moon_rasi_value - janma_rasi.value) % 12 + 1
    if house in _CHANDRA_BALA_GOOD_HOUSES:
        return ChandraBala.GOOD
    if house in _CHANDRA_BALA_BAD_HOUSES:
        return ChandraBala.BAD
    return ChandraBala.NEUTRAL


def _tara_bala_for(day_nakshatra: Nakshatra,
                   janma_nakshatra: Optional[Nakshatra]) -> Tuple[Optional[Tara], bool]:
    if janma_nakshatra is None:
        return None, False
    tara, auspicious = Tara.from_janma(janma_nakshatra, day_nakshatra)
    return tara, auspicious


def compute_adjuncts(
    date: datetime,
    lat: float,
    lon: float,
    tz_offset: float = 0.0,
    janma_nakshatra: Optional[Nakshatra] = None,
) -> AdjunctsInfo:
    """Single-source day-level adjunct bundle shared by CLI, GUI, JSON, and AI.

    Durmuhurta/Varjya/Panchaka are returned as spans in JD hours (reusing
    InauspiciousPeriod); Chandra Bala uses the Moon at sunrise; Tara Bala is graded
    against the day nakshatra (the panchang nakshatra at sunrise) and is UNAVAILABLE
    when no Janma nakshatra is supplied.
    """
    sunrise, _sunset = _sunrise_sunset(date, lat, lon, tz_offset)
    moon_at_sunrise = _moon_longitude_at_jd(sunrise)
    day_nak, _pada = Nakshatra.from_longitude(moon_at_sunrise)
    moon_rasi = Rasi.from_longitude(moon_at_sunrise)

    tara, tara_auspicious = _tara_bala_for(day_nak, janma_nakshatra)

    return AdjunctsInfo(
        durmuhurta=_durmuhurta_windows(date, lat, lon, tz_offset),
        varjya=_nakshatra_varjya_windows(date, lat, lon, tz_offset),
        panchaka=_panchaka_segments(date, lat, lon, tz_offset),
        chandra_bala=_chandra_bala_grade_for(moon_rasi.value, janma_nakshatra),
        tara_bala=tara,
        tara_auspicious=tara_auspicious,
    )


# Bounded per-day adjunct cache: Durmuhurta/Varjya windows, Panchaka segments, and
# the Chandra/Tara day grades depend only on (date, lat, lon, tz, Janma), so the
# per-moment scorer reuses them across the 10-minute scan without recomputation.
_DAY_ADJUNCTS_CACHE: Dict[Tuple, AdjunctsInfo] = {}
_DAY_ADJUNCTS_CACHE_MAX = 64


def _day_adjuncts(date: datetime, lat: float, lon: float, tz_offset: float,
                  janma_nakshatra: Optional[Nakshatra]) -> AdjunctsInfo:
    key = (date.date(), round(lat, 6), round(lon, 6), tz_offset, janma_nakshatra)
    cached = _DAY_ADJUNCTS_CACHE.get(key)
    if cached is None:
        cached = compute_adjuncts(date, lat, lon, tz_offset, janma_nakshatra)
        if len(_DAY_ADJUNCTS_CACHE) >= _DAY_ADJUNCTS_CACHE_MAX:
            _DAY_ADJUNCTS_CACHE.pop(next(iter(_DAY_ADJUNCTS_CACHE)))
        _DAY_ADJUNCTS_CACHE[key] = cached
    return cached


def _segments_kind_at(segments: Tuple[InauspiciousPeriod, ...], jd: float
                      ) -> Tuple[Optional[str], bool]:
    """Panchaka (name, rahita) for the segment containing `jd`, else (None, False)."""
    for seg in segments:
        if seg.start <= jd <= seg.end:
            if seg.kind == "Rahita":
                return "Rahita", True
            return seg.kind.split()[0], False
    return None, False


def find_muhurta(
    date: datetime,
    lat: float,
    lon: float,
    tz_offset: float = 0.0,
    task: MuhurtaTask = MuhurtaTask.GENERAL,
    jnama_nakshatra: Optional[Nakshatra] = None,
    step_minutes: int = 10,
) -> List[TaskEvaluation]:
    results = []
    for minute in range(0, 24 * 60, step_minutes):
        h = minute // 60
        m = minute % 60
        dt = date.replace(hour=h, minute=m, second=0, microsecond=0)
        try:
            eval_result = evaluate_time(dt, lat, lon, tz_offset, task, jnama_nakshatra)
            results.append(eval_result)
        except Exception:
            continue
    results.sort(key=lambda r: r.score, reverse=True)
    return results
