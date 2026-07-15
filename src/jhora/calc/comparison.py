"""Multi-chart comparison — natal vs transit overlay."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from jhora.charts.chart import ChartData
from jhora.calc.gochara import compute_transits
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


@dataclass
class ComparisonEntry:
    graha: Graha
    natal_sign: str
    natal_house: int
    transit_sign: str
    transit_house: int
    is_favorable: bool
    sav_score: int


def compare_natal_transit(natal: ChartData,
                          transit_jd: float = None) -> List[ComparisonEntry]:
    """Compare natal positions with current transit positions."""
    eng = SweEngine()
    if transit_jd is None:
        now = datetime.now()
        transit_jd = eng.julday(now.year, now.month, now.day,
                                now.hour + now.minute / 60.0)

    tr = compute_transits(natal, transit_jd)
    entries = tr.entries if hasattr(tr, 'entries') else []
    results = []
    for e in entries:
        g = e.graha
        if g in natal.planets:
            np = natal.planet(g)
            nr = Rasi.from_longitude(np.longitude)
            nh = _house_from_lagna(np.longitude, natal.ascendant)
        else:
            nr = None
            nh = 0
        results.append(ComparisonEntry(
            graha=g,
            natal_sign=nr.short_name if nr else "",
            natal_house=nh,
            transit_sign=e.transit_rasi_name,
            transit_house=e.house_from_lagna,
            is_favorable=e.is_favorable,
            sav_score=e.sav_score,
        ))
    return results


def _house_from_lagna(lon: float, lagna: float) -> int:
    return (int((lon - lagna) / 30) % 12) + 1


@dataclass
class TwoChartComparison:
    chart1_name: str
    chart2_name: str
    entries: List[dict]


def compare_two_charts(c1: ChartData, c2: ChartData,
                       name1: str = "Chart 1",
                       name2: str = "Chart 2") -> TwoChartComparison:
    """Side-by-side comparison of two arbitrary charts."""
    entries = []
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN,
              Graha.RAHU, Graha.KETU]:
        if g in c1.planets and g in c2.planets:
            p1 = c1.planet(g)
            p2 = c2.planet(g)
            r1 = Rasi.from_longitude(p1.longitude)
            r2 = Rasi.from_longitude(p2.longitude)
            moved = r1 != r2
            entries.append({
                "graha": g.short_name,
                "lon1": p1.longitude,
                "sign1": r1.short_name,
                "lon2": p2.longitude,
                "sign2": r2.short_name,
                "moved": moved,
            })
    return TwoChartComparison(
        chart1_name=name1, chart2_name=name2, entries=entries,
    )
