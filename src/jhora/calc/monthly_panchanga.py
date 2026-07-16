"""Monthly panchanga — calendar-style daily table for a full month.

Shows tithi, nakshatra, yoga, karana, sunrise, sunset, rahu kalam,
gulika kalam, yama gandam, and Moon sign for each day.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

import swisseph as swe

from jhora.ephemeris.swe import SweEngine
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra


@dataclass
class PanchangaDay:
    date: str
    weekday: str
    tithi: str
    nakshatra: str
    yoga: str
    karana: str
    sunrise: str
    sunset: str
    moon_sign: str
    rahu_kalam: str
    gulika_kalam: str
    yama_gandam: str


WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
TITHI_NAMES = [
    "Pratipat", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dasami",
    "Ekadasi", "Dwadasi", "Trayodasi", "Chaturdasi", "Amavasya/Purnima",
]

# Rahu Kalam by weekday (index: 0=Sun, hour block 0=6-7:30, 1=7:30-9, etc.)
# Each block is 1.5 hours. 8 blocks per day (12 hours of daytime)
_RAHU_BLOCK = {"Sun": 7, "Mon": 1, "Tue": 5, "Wed": 2,
               "Thu": 3, "Fri": 4, "Sat": 6}
_GULIKA_BLOCK = {"Sun": 6, "Mon": 5, "Tue": 4, "Wed": 3,
                  "Thu": 2, "Fri": 1, "Sat": 0}
_YAMA_BLOCK = {"Sun": 4, "Mon": 3, "Tue": 2, "Wed": 1,
                "Thu": 0, "Fri": 6, "Sat": 5}


def _block_to_time(block: int, sunrise: float) -> str:
    """Convert a 1.5-hour block index starting from sunrise to HH:MM string."""
    start_h = sunrise + block * 1.5
    end_h = start_h + 1.5
    return f"{int(start_h):02d}:{int((start_h%1)*60):02d}-{int(end_h):02d}:{int((end_h%1)*60):02d}"


def _tithi_at_jd(jd: float) -> tuple:
    """Return tithi index (0-29) and fraction completed at given JD."""
    sun = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]
    moon = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]
    angle = (moon - sun) % 360
    tithi_idx = int(angle / 12) % 30
    fraction = (angle % 12) / 12
    return tithi_idx, fraction


def _nakshatra_at_jd(jd: float) -> tuple:
    """Return nakshatra index (0-26) and fraction completed."""
    moon = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]
    idx = int(moon / (360.0 / 27))
    fraction = (moon % (360.0 / 27)) / (360.0 / 27)
    return idx, fraction


def _sunrise_sunset_jd(jd, lat, lon):
    """Get sunrise JD and sunset JD for a given day at location."""
    try:
        eng = SweEngine()
        y, m, d, h = swe.revjul(jd)
        # Sunrise
        flag = swe.CALC_RISE | swe.BIT_NO_REFRACTION
        res, tret = swe.rise_trans(jd - 1, swe.SUN, 0, 0, flag, (lon, lat, 0))
        sunrise_jd = tret[0] if tret else jd + 0.25
        # Sunset
        res2, tret2 = swe.rise_trans(jd - 1, swe.SUN, 0, 0,
                                     flag | swe.CALC_SET, (lon, lat, 0))
        sunset_jd = tret2[0] if tret2 else jd + 0.75
        return sunrise_jd, sunset_jd
    except Exception:
        return jd + 0.25, jd + 0.75


def monthly_panchanga(year: int, month: int,
                      lat: float = 28.61, lon: float = 77.21) -> List[PanchangaDay]:
    """Compute panchanga for every day of a month."""
    days = []
    # Determine number of days in month
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    num_days = (next_month - datetime(year, month, 1)).days

    for d in range(1, num_days + 1):
        dt = datetime(year, month, d, 12, 0, 0)
        jd = swe.julday(year, month, d, 12.0, swe.GREG_CAL)
        wd = WEEKDAYS[dt.weekday()]

        # Tithi + Nakshatra + Yoga
        ti, tf = _tithi_at_jd(jd)
        tithi_name = TITHI_NAMES[ti % 15] if ti < 30 else "Amavasya"
        ni, _ = _nakshatra_at_jd(jd)
        nak = Nakshatra(ni).name.replace("_", " ").title()

        # Simple yoga: (Sun + Moon) / 13°20'
        sun = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]
        moon = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]
        yoga_idx = int(((sun + moon) % 360) / (360.0 / 27)) % 27

        # Karana: tithi half
        karana_idx = ti * 2 + (0 if tf < 0.5 else 1)

        # Moon sign
        mr = Rasi.from_longitude(moon)

        # Sunrise/sunset
        sr_jd, ss_jd = _sunrise_sunset_jd(jd, lat, lon)
        sr_h = (sr_jd - int(sr_jd)) * 24
        ss_h = (ss_jd - int(ss_jd)) * 24
        sunrise_str = f"{int(sr_h):02d}:{int((sr_h%1)*60):02d}"
        sunset_str = f"{int(ss_h):02d}:{int((ss_h%1)*60):02d}"

        # Inauspicious periods
        rahu = _block_to_time(_RAHU_BLOCK.get(wd, 0), sr_h)
        gulika = _block_to_time(_GULIKA_BLOCK.get(wd, 0), sr_h)
        yama = _block_to_time(_YAMA_BLOCK.get(wd, 0), sr_h)

        days.append(PanchangaDay(
            date=f"{year:04d}-{month:02d}-{d:02d}",
            weekday=wd,
            tithi=tithi_name,
            nakshatra=nak,
            yoga=str(yoga_idx),
            karana=str(karana_idx),
            sunrise=sunrise_str,
            sunset=sunset_str,
            moon_sign=mr.short_name,
            rahu_kalam=rahu,
            gulika_kalam=gulika,
            yama_gandam=yama,
        ))
    return days
