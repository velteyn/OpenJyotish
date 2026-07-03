"""Gochara (Transit) analysis — current planet positions vs natal chart.

Evaluates transiting planets against the natal chart using Ashtakavarga
scores to determine favorability.

References:
  - Brihat Parasara Hora Sastra, Gochara adhyaya
  - "Vedic Astrology: An Integrated Approach" by P.V.R. Narasimha Rao
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.ephemeris.swe import SweEngine
from jhora.calc.ashtakavarga import (
    all_bhinna_ashtakavarga,
    sarva_ashtakavarga,
    _OCCUPANT_GRAHAS,
)
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

# SE planet ID → Graha mapping
_SE_TO_GRAHA = {0: Graha.SUN, 1: Graha.MOON, 2: Graha.MARS,
                3: Graha.MERCURY, 4: Graha.JUPITER, 5: Graha.VENUS,
                6: Graha.SATURN}
_GRAHA_TO_SE = {v: k for k, v in _SE_TO_GRAHA.items()}

SAV_GOOD_THRESHOLD = 30
SAV_BAD_THRESHOLD = 25
BAV_GOOD_THRESHOLD = 4


@dataclass
class TransitEntry:
    graha: Graha
    transit_rasi: int
    transit_rasi_name: str
    transit_degrees: float
    is_retrograde: bool
    house_from_lagna: int
    house_from_moon: int
    sav_score: int
    bav_score: int
    is_favorable: bool
    is_ashtakavarga_good: bool


@dataclass
class TransitResult:
    natal_rasi: int
    moon_rasi: int
    timestamp: datetime
    entries: List[TransitEntry] = field(default_factory=list)
    sav: List[int] = field(default_factory=list)


def compute_transits(
    chart: ChartData,
    transit_jd: Optional[float] = None,
    parasara_moon: bool = True,
    parasara_venus: bool = True,
) -> TransitResult:
    """Compute transit positions for all 7 planets relative to natal chart.

    Args:
        chart: Natal ChartData.
        transit_jd: Julian day for transit (default: now).
        parasara_moon/venus: Ashtakavarga variant.

    Returns:
        TransitResult with per-planet entries.
    """
    se = SweEngine()
    if transit_jd is None:
        now = datetime.now(timezone.utc)
        transit_jd = se.julday(now.year, now.month, now.day,
                                now.hour + now.minute / 60.0 + now.second / 3600.0)

    natal_lagna_rasi = chart.lagna.rasi.value
    natal_moon_rasi = chart.planets[Graha.MOON].rasi.value

    # Compute transit positions for 7 planets
    transit_positions = {}
    for se_id in range(7):
        pd = se.calc_planet(se_id, transit_jd)
        transit_positions[se_id] = pd

    # Natal Ashtakavarga
    bavs = all_bhinna_ashtakavarga(chart, parasara_moon, parasara_venus)
    sav = sarva_ashtakavarga(chart, parasara_moon, parasara_venus)

    entries = []
    for se_id, graha in _SE_TO_GRAHA.items():
        pd = transit_positions[se_id]
        t_rasi = pd.rasi_index
        house_from_lagna = (t_rasi - natal_lagna_rasi) % 12 + 1
        house_from_moon = (t_rasi - natal_moon_rasi) % 12 + 1
        sav_score = sav[t_rasi]
        bav_score = bavs[graha][t_rasi]

        is_av_good = sav_score >= SAV_GOOD_THRESHOLD
        is_bav_good = bav_score >= BAV_GOOD_THRESHOLD
        is_favorable = is_av_good and is_bav_good

        entries.append(TransitEntry(
            graha=graha,
            transit_rasi=t_rasi,
            transit_rasi_name=Rasi(t_rasi).short_name,
            transit_degrees=pd.degrees_in_rasi,
            is_retrograde=pd.is_retrograde,
            house_from_lagna=house_from_lagna,
            house_from_moon=house_from_moon,
            sav_score=sav_score,
            bav_score=bav_score,
            is_favorable=is_favorable,
            is_ashtakavarga_good=is_av_good,
        ))

    ts = datetime.now(timezone.utc)
    if transit_jd:
        y, m, d, h = se.revjul(transit_jd)
        try:
            ts = datetime(int(y), int(m), int(d), 0, tzinfo=timezone.utc)
        except Exception:
            ts = datetime.now(timezone.utc)

    return TransitResult(
        natal_rasi=natal_lagna_rasi,
        moon_rasi=natal_moon_rasi,
        timestamp=ts,
        entries=entries,
        sav=sav,
    )
