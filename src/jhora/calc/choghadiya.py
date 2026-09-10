"""Choghadiya (Chogadia) — auspicious/inauspicious time slots for each day.

Divides daytime (sunrise → sunset) into 8 equal slots and nighttime
(sunset → next sunrise) into 8 equal slots. Each slot is ruled by a
planet in the Chaldean planetary-hour cycle, producing a classic name
and a Good / Neutral / Bad rating.

Tables derived from drikpanchang.com (live rendering, verified against
Sun and Thu sites). The 7-slot cycle uses Chaldean planetary-hour order:

    Cycle:  Sun → Venus → Mercury → Moon → Saturn → Jupiter → Mars

Day  step = +1 (ascending cycle), seeded by the weekday lord.
Night step = +5 (mod 7) (= −2 mod 7), seeded at (day_start + 5) mod 7.

References:
  - drikpanchang.com tutorial: "Choghadiya Muhurat"
  - Dr. B.V. Raman, "Muhurta" (electional astrology)
  - Standard planetary-hour / Chaldean cycle derivation
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from jhora.types.graha import Graha


# ── Planetary-hour cycle (Chaldean order) ──────────────────────────────────────

_CYCLE: List[Graha] = [
    Graha.SUN,      # 0
    Graha.VENUS,    # 1
    Graha.MERCURY,  # 2
    Graha.MOON,     # 3
    Graha.SATURN,   # 4
    Graha.JUPITER,  # 5
    Graha.MARS,     # 6
]

# Weekday lord index into the cycle (Sun=0 … Sat=6, Python weekday Mon=0 → wd=1)
_DAY_START: List[int] = [0, 3, 6, 2, 5, 1, 4]   # wd → cycle index for day slot 0
_NIGHT_START: List[int] = [5, 1, 4, 0, 3, 6, 2]  # wd → cycle index for night slot 0

# Graha → choghadiya name and rating (drikpanchang convention)
GRAHA_NAME = {
    Graha.SUN:     "Udveg",
    Graha.MOON:    "Amrit",
    Graha.MARS:    "Rog",
    Graha.MERCURY: "Labh",
    Graha.JUPITER: "Shubh",
    Graha.VENUS:   "Char",
    Graha.SATURN:  "Kaal",
}

GRAHA_RATING = {
    Graha.SUN:     "Bad",
    Graha.MOON:    "Good",
    Graha.MARS:    "Bad",
    Graha.MERCURY: "Good",
    Graha.JUPITER: "Good",
    Graha.VENUS:   "Neutral",
    Graha.SATURN:  "Bad",
}

# Canonical good/bad sets (for quick evaluation)
GOOD_RATINGS = {"Good"}
BAD_RATINGS = {"Bad"}
NEUTRAL_RATINGS = {"Neutral"}


# ── Result dataclasses ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ChoghadiyaSlot:
    """A single choghadiya period."""
    name: str
    rating: str       # "Good" | "Neutral" | "Bad"
    lord: Graha
    start: datetime
    end: datetime
    is_night: bool

    @property
    def is_good(self) -> bool:
        return self.rating == "Good"

    @property
    def is_bad(self) -> bool:
        return self.rating == "Bad"

    @property
    def duration_minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60.0


@dataclass(frozen=True)
class ChoghadiyaDay:
    """The full choghadiya day (8 day + 8 night slots)."""
    date: datetime
    day_slots: List[ChoghadiyaSlot]
    night_slots: List[ChoghadiyaSlot]

    @property
    def all_slots(self) -> List[ChoghadiyaSlot]:
        return self.day_slots + self.night_slots

    def _slot_for(self, moment: datetime) -> Optional[ChoghadiyaSlot]:
        for slot in self.all_slots:
            if slot.start <= moment < slot.end:
                return slot
        if moment >= self.day_slots[0].start:
            return self.day_slots[-1]
        return None

    def current_slot(self, moment: datetime) -> Optional[ChoghadiyaSlot]:
        """Return the active slot at the given moment."""
        return self._slot_for(moment)


# ── Internal helpers ────────────────────────────────────────────────────────────

def _sunrise_sunset(date: datetime, lat: float, lon: float, tz_offset: float
                    ) -> Tuple[float, float]:
    """Julian-day sunrise and sunset for *date* at (lat, lon)."""
    from jhora.ephemeris.swe import SweEngine, SE_SUN
    swe = SweEngine()
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


def _jd_to_datetime(jd: float, tz_offset: float) -> datetime:
    """Convert a Julian Day number to a naive datetime in the local timezone."""
    from jhora.ephemeris.swe import SweEngine
    swe = SweEngine()
    year, month, day, hour = swe.revjul(jd)
    total_seconds = int(round(hour * 3600.0))
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    # hour is UTC; shift to local by adding tz_offset
    local_total = total_seconds + int(tz_offset * 3600)
    # Handle day rollover from timezone shift
    local_day_offset = 0
    if local_total < 0:
        local_day_offset = -1
        local_total += 86400
    elif local_total >= 86400:
        local_day_offset = 1
        local_total -= 86400
    lh = local_total // 3600
    lm = (local_total % 3600) // 60
    ls = local_total % 60
    dt = datetime(year, month, day, lh, lm, ls)
    if local_day_offset != 0:
        dt += timedelta(days=local_day_offset)
    return dt


def _weekdays_from_py(py_weekday: int) -> int:
    """Convert Python weekday (Mon=0 … Sun=6) to astro weekday (Sun=0 … Sat=6)."""
    return (py_weekday + 1) % 7


def _make_slots(
    start_jd: float,
    duration_days: float,
    cycle_start: int,
    step: int,
    is_night: bool,
    tz_offset: float,
) -> List[ChoghadiyaSlot]:
    """Build 8 equal choghadiya slots."""
    slot_len = duration_days / 8.0
    slots = []
    for i in range(8):
        cycle_idx = (cycle_start + step * i) % 7
        graha = _CYCLE[cycle_idx]
        slot_start_jd = start_jd + i * slot_len
        slot_end_jd = start_jd + (i + 1) * slot_len
        slots.append(ChoghadiyaSlot(
            name=GRAHA_NAME[graha],
            rating=GRAHA_RATING[graha],
            lord=graha,
            start=_jd_to_datetime(slot_start_jd, tz_offset),
            end=_jd_to_datetime(slot_end_jd, tz_offset),
            is_night=is_night,
        ))
    return slots


# ── Public API ──────────────────────────────────────────────────────────────────

def choghadiya_day(
    date: datetime,
    lat: float,
    lon: float,
    tz_offset: float = 0.0,
) -> ChoghadiyaDay:
    """Compute the 8 day + 8 night Choghadiya slots for *date* at (lat, lon).

    Parameters
    ----------
    date : datetime
        The panchang date (sunrise-date). Any time component is ignored;
        the sunrise of the given date anchors the calculation.
    lat, lon : float
        Geographic coordinates (degrees, north/east positive).
    tz_offset : float
        Hours east of UTC (e.g. IST = +5.5).

    Returns
    -------
    ChoghadiyaDay
        Contains 8 day_slots and 8 night_slots with exact start/end datetimes.
    """
    wd = _weekdays_from_py(date.weekday())

    sunrise_jd, sunset_jd = _sunrise_sunset(date, lat, lon, tz_offset)
    next_date = date + timedelta(days=1)
    next_sunrise_jd, _ = _sunrise_sunset(next_date, lat, lon, tz_offset)

    day_duration = sunset_jd - sunrise_jd
    night_duration = next_sunrise_jd - sunset_jd

    day_slots = _make_slots(
        sunrise_jd, day_duration, _DAY_START[wd], step=1,
        is_night=False, tz_offset=tz_offset,
    )
    night_slots = _make_slots(
        sunset_jd, night_duration, _NIGHT_START[wd], step=5,
        is_night=True, tz_offset=tz_offset,
    )

    return ChoghadiyaDay(date=date, day_slots=day_slots, night_slots=night_slots)


def current_choghadiya(
    moment: datetime,
    lat: float,
    lon: float,
    tz_offset: float = 0.0,
) -> Optional[ChoghadiyaSlot]:
    """Return the active choghadiya slot at *moment*."""
    day = choghadiya_day(moment, lat, lon, tz_offset)
    return day.current_slot(moment)


def evaluate_choghadiya(
    moment: datetime,
    lat: float,
    lon: float,
    tz_offset: float = 0.0,
) -> Optional[ChoghadiyaSlot]:
    """Alias for current_choghadiya (convenience eval endpoint)."""
    return current_choghadiya(moment, lat, lon, tz_offset)


def next_good_slot(
    moment: datetime,
    lat: float,
    lon: float,
    tz_offset: float = 0.0,
) -> Optional[Tuple[ChoghadiyaSlot, float]]:
    """Find the next Good-rated slot after *moment*.

    Returns
    -------
    (slot, minutes_until_start) or None if no Good slot found in the day.
    """
    day = choghadiya_day(moment, lat, lon, tz_offset)
    for slot in day.all_slots:
        if slot.is_good and slot.end > moment:
            minutes_until = max(0.0, (slot.start - moment).total_seconds() / 60.0)
            return slot, minutes_until
    return None


def day_table(wd: int) -> List[Tuple[str, str, Graha]]:
    """Return the 8-element day table for a weekday (Sun=0 … Sat=6).

    Each element is (name, rating, lord).
    """
    start = _DAY_START[wd]
    return [
        (GRAHA_NAME[_CYCLE[(start + i) % 7]],
         GRAHA_RATING[_CYCLE[(start + i) % 7]],
         _CYCLE[(start + i) % 7])
        for i in range(8)
    ]


def night_table(wd: int) -> List[Tuple[str, str, Graha]]:
    """Return the 8-element night table for a weekday (Sun=0 … Sat=6).

    Each element is (name, rating, lord).
    """
    start = _NIGHT_START[wd]
    return [
        (GRAHA_NAME[_CYCLE[(start + 5 * i) % 7]],
         GRAHA_RATING[_CYCLE[(start +5 * i) % 7]],
         _CYCLE[(start + 5 * i) % 7])
        for i in range(8)
    ]
