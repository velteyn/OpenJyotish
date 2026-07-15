"""Medini Jyotisha (mundane astrology) — world events, national futures, wars.

Computes special-event charts:
  - Solar ingress (Sankranti) — Sun enters each sign
  - Lunation charts — New Moon and Full Moon
  - Eclipse charts — upcoming solar/lunar eclipses
  - Major conjunctions — Jupiter-Saturn, Mars-Saturn, etc.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import swisseph as swe

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

_EPHE_PATH = Path(__file__).resolve().parents[3] / "jhcore" / "ephe"
if _EPHE_PATH.exists():
    swe.set_ephe_path(str(_EPHE_PATH.resolve()))

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

DEFAULT_LAT = 28.6139
DEFAULT_LON = 77.2090
DEFAULT_TZ = "+0530"

MAJOR_CONJUNCTIONS = [
    (swe.JUPITER, swe.SATURN, 3.0, "Jupiter-Saturn (social/economy shift)"),
    (swe.MARS, swe.SATURN, 2.0, "Mars-Saturn (conflict/military)"),
    (swe.JUPITER, swe.MEAN_NODE, 2.0, "Jupiter-Rahu (upheaval)"),
    (swe.SATURN, swe.MEAN_NODE, 2.0, "Saturn-Rahu (crisis/fear)"),
]

MUNDANE_HOUSES = {
    1: "People, national character, public health",
    2: "Treasury, banking, currency, national wealth",
    3: "Communications, media, neighbors, trade",
    4: "Land, agriculture, opposition, housing",
    5: "Education, children, speculation, stock market",
    6: "Military, police, labor, civil service, disease",
    7: "Foreign relations, war/peace, treaties, trade",
    8: "Debt, disasters, death rate, secrets, espionage",
    9: "Religion, judiciary, higher education, foreign travel",
    10: "Government, head of state, administration, honor",
    11: "Parliament, allies, national income, reforms",
    12: "Prisons, hospitals, hidden enemies, exile",
}


@dataclass
class MundaneEvent:
    name: str
    event_type: str
    julian_day: float
    datetime_utc: str
    sign: str
    chart: Optional[ChartData] = None


def _jd_str(jd: float) -> str:
    y, m, d, h = swe.revjul(jd)
    mi = int((h - int(h)) * 60)
    return f"{int(y)}-{m:02d}-{int(d):02d} {int(h):02d}:{mi:02d} UT"


def _from_jd(jd: float) -> tuple:
    y, m, d, h = swe.revjul(jd)
    return int(y), m, int(d), h


class MundaneCalculator:
    def __init__(self, lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON,
                 tz: str = DEFAULT_TZ):
        self.lat = lat
        self.lon = lon
        self.tz = tz
        self.builder = ChartBuilder()

    def _chart(self, jd: float) -> Optional[ChartData]:
        try:
            y, m, d, h = _from_jd(jd)
            return self.builder.build(
                year=y, month=m, day=d, hour=h,
                lat=self.lat, lon=self.lon, tz=self.tz,
            )
        except Exception:
            return None

    def solar_ingresses(self, year: int) -> List[MundaneEvent]:
        events = []
        jd_start = swe.julday(year, 1, 1, 0.0, swe.GREG_CAL)
        for deg in range(0, 360, 30):
            try:
                jd = swe.solcross_ut(float(deg), jd_start)
            except Exception:
                continue
            sign = SIGN_NAMES[deg // 30]
            events.append(MundaneEvent(
                name=f"Sun enters {sign}",
                event_type="solar_ingress",
                julian_day=jd,
                datetime_utc=_jd_str(jd),
                sign=sign,
            ))
        return events

    def aries_ingress(self, year: int) -> Optional[MundaneEvent]:
        try:
            jd_start = swe.julday(year, 1, 1, 0.0, swe.GREG_CAL)
            jd = swe.solcross_ut(0.0, jd_start)
        except Exception:
            return None
        return MundaneEvent(
            name=f"Mesha Sankranti {year}",
            event_type="solar_ingress",
            julian_day=jd,
            datetime_utc=_jd_str(jd),
            sign="Aries",
            chart=self._chart(jd),
        )

    def eclipses(self) -> List[MundaneEvent]:
        now = datetime.now()
        jd = swe.julday(now.year, now.month, now.day, 0.0)
        end = swe.julday(now.year + 3, 1, 1, 0.0)
        events = []
        while jd < end:
            try:
                r = swe.lun_eclipse_when(jd, swe.ECL_ALLTYPES_LUNAR, False)
                if r and r[0] > 0 and r[0] > jd:
                    events.append(MundaneEvent(
                        name="Lunar Eclipse", event_type="lunar_eclipse",
                        julian_day=r[0], datetime_utc=_jd_str(r[0]), sign="",
                        chart=self._chart(r[0]),
                    ))
                    jd = r[0]
                else:
                    break
            except Exception:
                break
            jd += 15
        jd = swe.julday(now.year, now.month, now.day, 0.0)
        while jd < end:
            try:
                r = swe.sol_eclipse_when_glob(jd, swe.ECL_ALLTYPES_LUNAR, False)
                if r and r[0] > 0 and r[0] > jd:
                    events.append(MundaneEvent(
                        name="Solar Eclipse", event_type="solar_eclipse",
                        julian_day=r[0], datetime_utc=_jd_str(r[0]), sign="",
                        chart=self._chart(r[0]),
                    ))
                    jd = r[0]
                else:
                    break
            except Exception:
                break
            jd += 15
        events.sort(key=lambda e: e.julian_day)
        return events

    def conjunctions(self, year: int) -> List[MundaneEvent]:
        jd_start = swe.julday(year, 1, 1, 0.0)
        jd_end = swe.julday(year + 1, 1, 1, 0.0)
        events = []
        for p1, p2, orb, desc in MAJOR_CONJUNCTIONS:
            jd = jd_start
            while jd < jd_end:
                lon1 = swe.calc_ut(jd, p1, swe.FLG_SWIEPH)[0][0]
                lon2 = swe.calc_ut(jd, p2, swe.FLG_SWIEPH)[0][0]
                diff = abs(((lon1 - lon2 + 180) % 360) - 180)
                if diff <= orb:
                    events.append(MundaneEvent(
                        name=desc, event_type="conjunction",
                        julian_day=jd, datetime_utc=_jd_str(jd),
                        sign=Rasi(int(lon1 / 30)).full_name,
                        chart=self._chart(jd),
                    ))
                    jd += 30
                jd += 0.5
        return events

    def analysis_text(self, year: int) -> str:
        lines = [f"Mundane Astrology Analysis for {year}"]
        ingress = self.aries_ingress(year)
        if ingress:
            lines.append(f"\nMesha Sankranti: {ingress.datetime_utc}")
            if ingress.chart:
                lagna = Rasi.from_longitude(ingress.chart.ascendant)
                lines.append(f"  Lagna: {lagna.full_name} {ingress.chart.ascendant:.1f}°")
                for g in [Graha.SUN, Graha.MOON, Graha.MARS,
                          Graha.JUPITER, Graha.SATURN, Graha.RAHU]:
                    p = ingress.chart.planet(g)
                    r = Rasi.from_longitude(p.longitude)
                    lines.append(f"  {g.short_name}: {r.short_name} {p.longitude:.1f}°"
                                f"{' R' if p.is_retrograde else ''}")
        eclipses = self.eclipses()
        if eclipses:
            lines.append(f"\nEclipses: {len(eclipses)} upcoming")
            for e in eclipses[:4]:
                lines.append(f"  {e.name}: {e.datetime_utc}")
        conj = self.conjunctions(year)
        if conj:
            lines.append(f"\nMajor Conjunctions: {len(conj)}")
            for c in conj[:8]:
                lines.append(f"  {c.name}: {c.datetime_utc} in {c.sign}")
        return "\n".join(lines)
