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

# Swiss Ephemeris planet ID → Graha. SE order is Sun, Moon, Mercury,
# Venus, Mars, Jupiter, Saturn (NOT the Vedic weekday order).
_SE_TO_GRAHA = {0: Graha.SUN, 1: Graha.MOON, 2: Graha.MERCURY,
                3: Graha.VENUS, 4: Graha.MARS, 5: Graha.JUPITER,
                6: Graha.SATURN}
_GRAHA_TO_SE = {v: k for k, v in _SE_TO_GRAHA.items()}

SAV_GOOD_THRESHOLD = 30
SAV_BAD_THRESHOLD = 25
BAV_GOOD_THRESHOLD = 4

#: Gochara favourable transit houses counted from the natal Moon
#: (Phaladeepika ch. 26; the classical "good positions" table).
GOCHARA_GOOD: Dict[Graha, Tuple[int, ...]] = {
    Graha.SUN: (3, 6, 10, 11),
    Graha.MOON: (1, 3, 6, 7, 10, 11),
    Graha.MARS: (3, 6, 11),
    Graha.MERCURY: (2, 4, 6, 8, 10, 11),
    Graha.JUPITER: (2, 5, 7, 9, 11),
    Graha.VENUS: (1, 2, 3, 4, 5, 8, 9, 11, 12),
    Graha.SATURN: (3, 6, 11),
}

#: Vedha (obstruction): the house from the Moon whose occupation by any other
#: transiting planet cancels the benefit of a favourable house. The pairs are
#: mutual (Phaladeepika ch. 26); Rahu/Ketu have no vedha.
GOCHARA_VEDHA: Dict[Graha, Dict[int, int]] = {
    Graha.SUN: {3: 9, 6: 12, 10: 4, 11: 5},
    Graha.MOON: {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    Graha.MARS: {3: 12, 6: 9, 11: 5},
    Graha.MERCURY: {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
    Graha.JUPITER: {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    Graha.VENUS: {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 3, 12: 6},
    Graha.SATURN: {3: 12, 6: 9, 11: 5},
}


def vedha_house(graha: Graha, house_from_moon: int) -> int:
    """The vedha (obstructing) house for a planet's transit house, or 0."""
    return GOCHARA_VEDHA.get(graha, {}).get(house_from_moon, 0)


def sade_sati_status(natal_moon_rasi: int, transit_saturn_rasi: int) -> str:
    """Sade Sati phase of transit Saturn against the natal Moon.

    Returns '12th from Moon', '1st from Moon (peak)' or '2nd from Moon'
    when transit Saturn occupies those signs from natal Moon, else ''.
    Rasi indices are 0-based (0 = Aries).
    """
    ss = [(natal_moon_rasi - 1) % 12, natal_moon_rasi, (natal_moon_rasi + 1) % 12]
    if transit_saturn_rasi in ss:
        return ["12th from Moon", "1st from Moon (peak)",
                "2nd from Moon"][ss.index(transit_saturn_rasi)]
    return ""


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
    is_good_transit: bool = False
    vedha_house: int = 0
    is_vedha: bool = False


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

    # Gochara vedha: a favourable house is obstructed when another transiting
    # planet — or a node — occupies its paired vedha house. The Sun and
    # Saturn, and the Moon and Mercury, are exempt from obstructing each
    # other (Raman, Hindu Predictive Astrology ch. 34).
    occupants: Dict[int, set] = {}
    for e in entries:
        occupants.setdefault(e.house_from_moon, set()).add(e.graha)
    rahu = se.calc_planet(10, transit_jd)  # mean node (Rahu); Ketu = +180
    for node, rasi in ((Graha.RAHU, rahu.rasi_index),
                       (Graha.KETU, (rahu.rasi_index + 6) % 12)):
        occupants.setdefault(
            (rasi - natal_moon_rasi) % 12 + 1, set()).add(node)

    _EXEMPT = (frozenset((Graha.SUN, Graha.SATURN)),
               frozenset((Graha.MOON, Graha.MERCURY)))
    for e in entries:
        e.is_good_transit = e.house_from_moon in GOCHARA_GOOD.get(e.graha, ())
        vedha = vedha_house(e.graha, e.house_from_moon)
        e.vedha_house = vedha
        blockers = occupants.get(vedha, set()) - {e.graha}
        blockers = {b for b in blockers
                    if frozenset((b, e.graha)) not in _EXEMPT}
        e.is_vedha = bool(e.is_good_transit and vedha and blockers)

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
