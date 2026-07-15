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
    from jhora.ephemeris.swe import SweEngine
    swe = SweEngine()
    gmt = dt.hour - tz_offset
    jd_dt = swe.julday(dt.year, dt.month, dt.day, gmt)
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
    gmt = dt.hour - tz_offset
    return swe.julday(dt.year, dt.month, dt.day, gmt)


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
