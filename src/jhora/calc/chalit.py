"""Bhava/Chalit Chakra — cusp-based house positions for all varga charts.

In standard Vedic, houses are whole-sign (each sign = one house from lagna).
The Chalit (Bhava) chart uses actual house cusps — a planet shifts houses
when its longitude falls past a cusp boundary within a sign.

For each varga level, this module shows:
  - Sign-based house (whole sign)
  - Cusp-based house (chalit/bhava)
  - Whether the planet moved
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from jhora.charts.chart import ChartData
from jhora.charts.varga import VargaChartComputer
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.varga import VargaLevel


@dataclass
class ChalitEntry:
    graha: Graha
    longitude: float
    sign: str
    sign_house: int           # whole-sign house
    cusp_house: int           # cusp-based house (chalit)
    moved: bool               # did the planet change houses?


@dataclass
class ChalitReport:
    varga_level: VargaLevel
    lagna_longitude: float
    house_cusps: List[float]  # 12 cusps
    entries: List[ChalitEntry]
    moved_planets: List[ChalitEntry]


def _compute_cusps(lagna_lon: float) -> List[float]:
    """Compute 12 house cusps from a lagna longitude.

    Uses equal-house system: each house cusp = lagna + house_index * 30°.
    House cusp[0] = lagna, cusp[1] = lagna+30, ..., cusp[11] = lagna+330.
    """
    return [(lagna_lon + h * 30) % 360 for h in range(12)]


def sripati_bhavas(lagna_lon: float, mc_lon: float
                   ) -> List[Tuple[float, float]]:
    """Sripati bhava spans: [(begin, madhya)] for houses 1..12.

    Madhyas: 1st = lagna, 10th = MC, 7th/4th opposite; the rest trisect
    the quadrants. Each bhava runs from its begin (midway between the
    previous madhya and its own) to the next begin. Spans tile 360°.
    """
    lagna_lon %= 360.0
    mc_lon %= 360.0
    mid = [0.0] * 13  # 1-indexed
    mid[1] = lagna_lon
    mid[10] = mc_lon
    mid[7] = (lagna_lon + 180.0) % 360.0
    mid[4] = (mc_lon + 180.0) % 360.0

    def _fill(anchor_from: int, anchor_to: int, targets: Tuple[int, int]):
        arc = (mid[anchor_to] - mid[anchor_from]) % 360.0
        mid[targets[0]] = (mid[anchor_from] + arc / 3.0) % 360.0
        mid[targets[1]] = (mid[anchor_from] + 2.0 * arc / 3.0) % 360.0

    _fill(10, 1, (11, 12))
    _fill(1, 4, (2, 3))
    _fill(4, 7, (5, 6))
    _fill(7, 10, (8, 9))

    result = []
    for h in range(1, 13):
        prev_mid = mid[12] if h == 1 else mid[h - 1]
        arc = (mid[h] - prev_mid) % 360.0
        begin = (prev_mid + arc / 2.0) % 360.0
        result.append((begin, mid[h]))
    return result


def _sripati_house(lon: float, spans: List[Tuple[float, float]]) -> int:
    """Bhava index (1-12) whose [begin, next begin) span holds lon."""
    begins = [b for b, _ in spans]
    for h in range(12):
        start = begins[h]
        end = begins[(h + 1) % 12]
        if start < end:
            if start <= lon < end:
                return h + 1
        elif lon >= start or lon < end:
            return h + 1
    return 1


def _chalit_house(lon: float, cusps: List[float]) -> int:
    """Determine which bhava (1-12) a longitude falls into by cusp boundaries.

    Each house spans from cusps[h-1] to cusps[h] (mod 360).
    """
    for h in range(12):
        start = cusps[h]          # this house cusp
        end = cusps[(h + 1) % 12]  # next house cusp
        if start < end:
            if start <= lon < end:
                return h + 1
        else:  # wraps around 360°
            if lon >= start or lon < end:
                return h + 1
    return 1


def _sign_house(lon: float, lagna_lon: float) -> int:
    """Whole-sign house: which house (1-12) does the sign fall in?"""
    lagna_sign = int(lagna_lon / 30)
    planet_sign = int(lon / 30)
    house = (planet_sign - lagna_sign) % 12 + 1
    return house


class ChalitComputer:
    def __init__(self, chart: ChartData):
        self.chart = chart
        self.vcc = VargaChartComputer()
        self._cache: Dict[VargaLevel, dict] = {}

    def compute(self, varga_level: VargaLevel = VargaLevel.D_1,
                method: str = "default") -> ChalitReport:
        """Compute chalit house positions for a given varga level.

        method "default" keeps historical behavior (D-1 from the Swiss
        Placidus cusps, vargas equal-house from the varga lagna);
        method "sripati" uses Sripati bhava spans (D-1 only — vargas
        have no MC, so they stay equal-house).
        """
        if method not in ("default", "sripati"):
            raise ValueError(
                f"Unknown bhava method {method!r}: use 'default'/'sripati'.")
        if varga_level == VargaLevel.D_1:
            lagna_lon = self.chart.ascendant
            if method == "sripati":
                return self._compute_sripati()
            cusps = list(self.chart.house_cusps)
            entries = []
            for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                      Graha.JUPITER, Graha.VENUS, Graha.SATURN,
                      Graha.RAHU, Graha.KETU]:
                p = self.chart.planet(g)
                sign_h = _sign_house(p.longitude, lagna_lon)
                cusp_h = _chalit_house(p.longitude, cusps)
                entries.append(ChalitEntry(
                    graha=g, longitude=p.longitude,
                    sign=Rasi.from_longitude(p.longitude).short_name,
                    sign_house=sign_h, cusp_house=cusp_h,
                    moved=sign_h != cusp_h,
                ))
        else:
            # Varga chart
            vcd = self.vcc.compute(self.chart, varga_level)
            lagna_lon = vcd.lagna_position.longitude
            cusps = _compute_cusps(lagna_lon)
            entries = []
            for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                      Graha.JUPITER, Graha.VENUS, Graha.SATURN,
                      Graha.RAHU, Graha.KETU]:
                vpos = vcd.positions.get(g)
                if vpos is None:
                    continue
                lon = vpos.longitude
                sign_h = _sign_house(lon, lagna_lon)
                cusp_h = _chalit_house(lon, cusps)
                entries.append(ChalitEntry(
                    graha=g, longitude=lon,
                    sign=Rasi.from_longitude(lon).short_name,
                    sign_house=sign_h, cusp_house=cusp_h,
                    moved=sign_h != cusp_h,
                ))

        moved = [e for e in entries if e.moved]
        return ChalitReport(
            varga_level=varga_level,
            lagna_longitude=lagna_lon,
            house_cusps=cusps,
            entries=entries,
            moved_planets=moved,
        )

    def _compute_sripati(self) -> ChalitReport:
        """D-1 chalit by Sripati bhava spans (madhya 1 = lagna)."""
        lagna_lon = self.chart.ascendant
        spans = sripati_bhavas(lagna_lon, self.chart.mc)
        entries = []
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                  Graha.JUPITER, Graha.VENUS, Graha.SATURN,
                  Graha.RAHU, Graha.KETU]:
            p = self.chart.planet(g)
            sign_h = _sign_house(p.longitude, lagna_lon)
            cusp_h = _sripati_house(p.longitude, spans)
            entries.append(ChalitEntry(
                graha=g, longitude=p.longitude,
                sign=Rasi.from_longitude(p.longitude).short_name,
                sign_house=sign_h, cusp_house=cusp_h,
                moved=sign_h != cusp_h,
            ))
        moved = [e for e in entries if e.moved]
        return ChalitReport(
            varga_level=VargaLevel.D_1,
            lagna_longitude=lagna_lon,
            house_cusps=[b for b, _ in spans],
            entries=entries,
            moved_planets=moved,
        )
