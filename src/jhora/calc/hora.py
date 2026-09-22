"""Hora — planetary hours, the everyday muhurta.

The living day (sunrise → next sunrise) is divided into 24 horas: 12 equal
day-horas (sunrise → sunset) and 12 equal night-horas (sunset → next
sunrise). The first hora of the day is ruled by the weekday lord; each next
hora follows the Chaldean order Sun, Venus, Mercury, Moon, Saturn, Jupiter,
Mars (cyclic), so the first hora of the next day is that day's lord.

Mainstream rule (Brihat Parashara Hora Sastra; the drik-panchanga
planetary-hour convention): choose an hora whose lord favours the task.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from jhora.types.graha import Graha

#: Chaldean order followed by the hora cycle.
CHALDEAN: List[Graha] = [
    Graha.SUN, Graha.VENUS, Graha.MERCURY, Graha.MOON,
    Graha.SATURN, Graha.JUPITER, Graha.MARS,
]

#: Weekday lords, Sunday = 0 .. Saturday = 6.
WEEKDAY_LORD: List[Graha] = [
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
    Graha.JUPITER, Graha.VENUS, Graha.SATURN,
]


@dataclass
class HoraSlot:
    index: int          # 0..23 (0..11 day, 12..23 night)
    lord: Graha
    part: str           # "Day" or "Night"
    start: datetime
    end: datetime

    @property
    def lord_name(self) -> str:
        return self.lord.full_name


def _at(date: datetime, hours: float) -> datetime:
    midnight = datetime(date.year, date.month, date.day)
    return midnight + timedelta(hours=hours)


def hora_slots(date: datetime, lat: float, lon: float,
               tz_offset: float = 5.5) -> List[HoraSlot]:
    """The 24 hora slots of the Hindu day beginning at ``date``'s sunrise.

    ``tz_offset`` is signed hours EAST of UTC (e.g. +5.5 for IST).
    """
    from jhora.calc.muhurta import sunrise_sunset_hours
    sr, ss = sunrise_sunset_hours(date, lat, lon, tz_offset)
    next_sr, _ = sunrise_sunset_hours(date + timedelta(days=1), lat, lon,
                                      tz_offset)
    wd = (date.weekday() + 1) % 7  # Sun=0 .. Sat=6
    start_idx = CHALDEAN.index(WEEKDAY_LORD[wd])

    day_len = (ss - sr) / 12.0
    night_len = (next_sr + 24.0 - ss) / 12.0

    slots: List[HoraSlot] = []
    for i in range(12):
        slots.append(HoraSlot(
            index=i, lord=CHALDEAN[(start_idx + i) % 7], part="Day",
            start=_at(date, sr + i * day_len),
            end=_at(date, sr + (i + 1) * day_len)))
    for j in range(12):
        k = 12 + j
        slots.append(HoraSlot(
            index=k, lord=CHALDEAN[(start_idx + k) % 7], part="Night",
            start=_at(date, ss + j * night_len),
            end=_at(date, ss + (j + 1) * night_len)))
    return slots


def current_hora(moment: datetime, lat: float, lon: float,
                 tz_offset: float = 5.5) -> Optional[HoraSlot]:
    """The hora ruling ``moment`` (night horas before sunrise belong to the
    previous Hindu day)."""
    from jhora.calc.muhurta import sunrise_sunset_hours
    day = datetime(moment.year, moment.month, moment.day)
    sr, _ = sunrise_sunset_hours(day, lat, lon, tz_offset)
    base = day if moment >= _at(day, sr) else day - timedelta(days=1)
    for slot in hora_slots(base, lat, lon, tz_offset):
        if slot.start <= moment < slot.end:
            return slot
    return None
