"""Monthly panchanga — calendar-style daily table for a full month.

Shows tithi (with paksha), nakshatra, yoga, karana, sunrise, sunset,
rahu kalam, gulika kalam, yama gandam and Moon sign for each day.

All five limbs come from the single verified source ``muhurta``
(``compute_panchanga`` / ``sunrise_sunset_hours``); the Rahu/Gulika/Yama
windows divide the actual sunrise->sunset day into eight equal parts.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from jhora.types.rasi import Rasi


@dataclass
class PanchangaDay:
    date: str
    weekday: str
    tithi: str
    paksha: str
    nakshatra: str
    yoga: str
    karana: str
    sunrise: str
    sunset: str
    moon_sign: str
    rahu_kalam: str
    gulika_kalam: str
    yama_gandam: str
    varjya1: str = "—"
    varjya2: str = "—"
    durmuhurta1: str = "—"
    durmuhurta2: str = "—"


WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def _hhmm(hours: float) -> str:
    h = hours % 24.0
    return f"{int(h):02d}:{int((h % 1) * 60):02d}"


def _window(idx: int, sunrise_h: float, seg: float) -> str:
    start = sunrise_h + idx * seg
    return f"{_hhmm(start)}-{_hhmm(start + seg)}"


def monthly_panchanga(year: int, month: int, lat: float = 28.61,
                      lon: float = 77.21, tz_offset: float = 5.5,
                      with_adjuncts: bool = False) -> List[PanchangaDay]:
    """Compute panchanga for every day of a month.

    ``tz_offset`` is signed hours EAST of UTC (e.g. +5.5 for IST).
    ``with_adjuncts`` also fills the Durmuhurta/Varjya windows.
    """
    from jhora.calc.muhurta import (
        compute_panchanga, sunrise_sunset_hours, _get_moon_longitude,
        _YOGA_NAMES, _RAHU_PERIOD_INDEX, _GULIKA_PERIOD_INDEX,
        _YAMAGANDA_PERIOD_INDEX, compute_adjuncts, _datetime_to_jd,
    )

    def _window_jd(jd: float, base_jd: float) -> str:
        h = (jd - base_jd) * 24.0
        return f"{int(h % 24):02d}:{int((h % 1) * 60):02d}"

    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    num_days = (next_month - datetime(year, month, 1)).days

    days: List[PanchangaDay] = []
    for d in range(1, num_days + 1):
        dt = datetime(year, month, d, 12, 0, 0)
        sr_h, ss_h = sunrise_sunset_hours(dt, lat, lon, tz_offset)
        # Panchanga limbs are read at local sunrise (the Hindu day boundary).
        sunrise_dt = (datetime(year, month, d) + timedelta(hours=sr_h))
        p = compute_panchanga(sunrise_dt, lat, lon, tz_offset)
        wd = (dt.weekday() + 1) % 7  # Sun=0 .. Sat=6
        seg = (ss_h - sr_h) / 8.0
        moon = _get_moon_longitude(sunrise_dt, tz_offset)

        base_jd = _datetime_to_jd(datetime(year, month, d), tz_offset)
        vars_ = ["", ""]
        durs = ["", ""]
        if with_adjuncts:
            adj = compute_adjuncts(dt, lat, lon, tz_offset, None)
            vars_ = ["" if i >= len(adj.varjya) else
                     f"{_window_jd(adj.varjya[i].start, base_jd)}-"
                     f"{_window_jd(adj.varjya[i].end, base_jd)}" for i in range(2)]
            durs = ["" if i >= len(adj.durmuhurta) else
                    f"{_window_jd(adj.durmuhurta[i].start, base_jd)}-"
                    f"{_window_jd(adj.durmuhurta[i].end, base_jd)}" for i in range(2)]

        days.append(PanchangaDay(
            date=f"{year:04d}-{month:02d}-{d:02d}",
            weekday=WEEKDAYS[wd],
            tithi=p.tithi.name,
            paksha="Shukla" if p.tithi.is_shukla else "Krishna",
            nakshatra=p.nakshatra.name.replace("_", " ").title(),
            yoga=_YOGA_NAMES[p.yoga_index],
            karana=p.karana_name,
            sunrise=_hhmm(sr_h),
            sunset=_hhmm(ss_h),
            moon_sign=Rasi.from_longitude(moon).short_name,
            rahu_kalam=_window(_RAHU_PERIOD_INDEX[wd], sr_h, seg),
            gulika_kalam=_window(_GULIKA_PERIOD_INDEX[wd], sr_h, seg),
            yama_gandam=_window(_YAMAGANDA_PERIOD_INDEX[wd], sr_h, seg),
            varjya1=vars_[0] or "—", varjya2=vars_[1] or "—",
            durmuhurta1=durs[0] or "—", durmuhurta2=durs[1] or "—",
        ))
    return days
