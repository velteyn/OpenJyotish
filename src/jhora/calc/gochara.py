"""Gochara (Transit) analysis — current planet positions vs natal chart.

Evaluates transiting planets against the natal chart using Ashtakavarga
scores to determine favorability.

References:
  - Brihat Parasara Hora Sastra, Gochara adhyaya
  - "Vedic Astrology: An Integrated Approach" by P.V.R. Narasimha Rao
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
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


# ── Sade Sati / Kantaka / Ashtama timeline ──
# A working astrologer's daily question is not "is Saturn there now" but
# "when does each phase start and end". Saturn spends ~2.5 years per sign,
# so the three Sade Sati phases span ~7.5 years; retrograde motion can split
# a phase into separate intervals, which are reported as-is (mainstream
# panchangas do the same). Houses are counted whole-sign from natal Moon.

#: (kind, phase label, sign offset from natal Moon) for tracked transits.
_SADE_SATI_PHASES = (
    ("Sade Sati", "12th from Moon", -1),
    ("Sade Sati", "1st from Moon (peak)", 0),
    ("Sade Sati", "2nd from Moon", +1),
)
_SMALL_PANOTI = (
    ("Kantaka Shani", "4th from Moon", +3),
    ("Ashtama Shani", "8th from Moon", +7),
)
_TIMELINE_KINDS = _SADE_SATI_PHASES + _SMALL_PANOTI

#: Grid step for the ingress search. Saturn never exceeds ~0.2°/day, so a
#: 3-day grid cannot skip a 30° sign; boundaries are then refined by bisection.
_TIMELINE_GRID_DAYS = 3


@dataclass
class TransitPhase:
    """One dated interval of a Saturn transit phase from natal Moon."""
    kind: str      # "Sade Sati" | "Kantaka Shani" | "Ashtama Shani"
    phase: str     # e.g. "12th from Moon", "1st from Moon (peak)"
    sign: int      # Saturn's sidereal rasi index during the interval
    start: date
    end: date
    start_exact: bool = True  # False when clipped by the search window
    end_exact: bool = True


def saturn_sidereal_longitude(jd: float,
                              ayanamsa_name: str = "lahiri") -> float:
    """Saturn's sidereal longitude at a Julian Day."""
    se = SweEngine()
    se.set_sidereal_mode(ayanamsa_name)
    return se.calc_planet(6, jd).longitude % 360.0


def saturn_sidereal_rasi(jd: float, ayanamsa_name: str = "lahiri") -> int:
    """Saturn's sidereal rasi index (0 = Aries) at a Julian Day."""
    return int(saturn_sidereal_longitude(jd, ayanamsa_name) // 30) % 12


def _unwrapped_delta(lon: float, ref: float) -> float:
    """Signed angular distance of lon from ref, in (-180, 180]."""
    return (lon - ref + 540.0) % 360.0 - 180.0


def _refine_ingress(se: SweEngine, jd_lo: float, jd_hi: float,
                    boundary_lon: float) -> float:
    """Bisect to the JD of Saturn's crossing of a sign cusp (~1 minute)."""
    lon_lo = se.calc_planet(6, jd_lo).longitude % 360.0
    target = _unwrapped_delta(boundary_lon, lon_lo)
    for _ in range(25):
        mid = (jd_lo + jd_hi) / 2.0
        lon = se.calc_planet(6, mid).longitude % 360.0
        if (_unwrapped_delta(lon, lon_lo) < target) == (target > 0):
            jd_lo = mid
        else:
            jd_hi = mid
    return (jd_lo + jd_hi) / 2.0


def saturn_phase_timeline(natal_moon_rasi: int,
                          ayanamsa_name: str = "lahiri",
                          start: Optional[date] = None,
                          end: Optional[date] = None) -> List[TransitPhase]:
    """Dated Sade Sati / Kantaka / Ashtama intervals in [start, end].

    Scans Saturn's sidereal sign on a coarse grid, groups consecutive days
    by phase, and refines each boundary to the true ingress by bisection.
    Retrograde re-entries surface as separate intervals with the same label.
    """
    today = datetime.now(timezone.utc).date()
    if start is None:
        start = today - timedelta(days=int(365.25 * 8))
    if end is None:
        end = today + timedelta(days=int(365.25 * 8))
    if end <= start:
        return []

    se = SweEngine()
    se.set_sidereal_mode(ayanamsa_name)

    label_of = {(natal_moon_rasi + off) % 12: (kind, phase)
                for kind, phase, off in _TIMELINE_KINDS}

    # Coarse grid: (jd_noon, rasi, label|None).
    grid = []
    day = start
    while day <= end:
        jd = se.julday(day.year, day.month, day.day, 12.0)
        rasi = int(se.calc_planet(6, jd).longitude % 360.0 // 30) % 12
        grid.append((jd, day, rasi, label_of.get(rasi)))
        day += timedelta(days=_TIMELINE_GRID_DAYS)

    def jd_to_date(jd: float) -> date:
        y, m, d, _h = se.revjul(jd)
        return date(int(y), int(m), int(d))

    phases: List[TransitPhase] = []
    i = 0
    while i < len(grid):
        label = grid[i][3]
        if label is None:
            i += 1
            continue
        j = i
        while j + 1 < len(grid) and grid[j + 1][3] == label:
            j += 1
        kind, phase = label
        sign = grid[i][2]
        # Refine the entry boundary (between grid[i-1] and grid[i]) ...
        if i == 0:
            start_d, start_exact = start, False
        else:
            cusp = (sign * 30.0) % 360.0
            jd_in = _refine_ingress(se, grid[i - 1][0], grid[i][0], cusp)
            start_d, start_exact = jd_to_date(jd_in), True
        # ... and the exit boundary (between grid[j] and grid[j+1]).
        if j == len(grid) - 1:
            end_d, end_exact = end, False
        else:
            cusp = ((sign + 1) * 30.0) % 360.0
            jd_out = _refine_ingress(se, grid[j][0], grid[j + 1][0], cusp)
            end_d, end_exact = jd_to_date(jd_out), True
        phases.append(TransitPhase(
            kind=kind, phase=phase, sign=sign,
            start=start_d, end=end_d,
            start_exact=start_exact, end_exact=end_exact,
        ))
        i = j + 1
    return phases


def sade_sati_timeline(natal_moon_rasi: int,
                       ayanamsa_name: str = "lahiri",
                       center: Optional[date] = None,
                       years_before: int = 8,
                       years_after: int = 8) -> List[TransitPhase]:
    """Sade Sati / Kantaka / Ashtama intervals around a central date."""
    if center is None:
        center = datetime.now(timezone.utc).date()
    start = center - timedelta(days=int(365.25 * years_before))
    end = center + timedelta(days=int(365.25 * years_after))
    return saturn_phase_timeline(natal_moon_rasi, ayanamsa_name, start, end)


def current_phase(phases: List[TransitPhase],
                  today: Optional[date] = None) -> Optional[TransitPhase]:
    """The timeline interval containing today, or None."""
    if today is None:
        today = datetime.now(timezone.utc).date()
    for p in phases:
        if p.start <= today <= p.end:
            return p
    return None


def next_sade_sati_start(phases: List[TransitPhase],
                         today: Optional[date] = None) -> Optional[date]:
    """Start date of the next Sade Sati interval after today, or None."""
    if today is None:
        today = datetime.now(timezone.utc).date()
    for p in phases:
        if p.kind == "Sade Sati" and p.start > today:
            return p.start
    return None
