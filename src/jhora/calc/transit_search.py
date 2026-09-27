"""Transit search — query-driven date search over transit conditions.

Answers "when" questions the single-moment evaluation cannot: on which
dates does a transiting planet occupy a house from the natal Moon, aspect
a natal planet, enter Sade-Sati, or ingress a sign.

Method: daily sweep of the window (one Swiss call per day for the relevant
planet), consecutive matching days grouped into intervals, each boundary
refined by bisection on the sign cusp. Retrograde re-entries surface as
separate labeled intervals (same convention as `saturn_phase_timeline`).

References:
  - Brihat Parasara Hora Sastra, Gochara adhyaya (Moon-based houses)
  - `calc/gochara.py` (single-moment evaluation, ingress bisection)
  - `calc/drishti.py` (Parashara graha-drishti)
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List

from jhora.calc.drishti import aspects_from
from jhora.calc.gochara import (
    _GRAHA_TO_SE,
    _refine_ingress,
    saturn_phase_timeline,
)
from jhora.charts.chart import ChartData
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha

STEP_DAYS = 1
MAX_WINDOW_YEARS = 30

_SATURN_KINDS = ("Sade Sati", "Ashtama", "Ardha-Ashtama", "Kantaka")


@dataclass
class SearchInterval:
    """One matching date span (inclusive), with a human label."""

    start: date
    end: date
    label: str


@dataclass
class SearchResult:
    """Outcome of a transit search, including how it was derived."""

    condition: str
    window_start: date
    window_end: date
    step_days: int = STEP_DAYS
    boundaries_refined: bool = True
    note: str = ""
    intervals: List[SearchInterval] = field(default_factory=list)


@dataclass
class SearchCondition:
    """One searchable condition (v1 set)."""

    kind: str  # "house" | "aspect" | "saturn" | "ingress"
    planet: Graha = Graha.SATURN
    house: int = 1  # 1-12, for kind == "house"
    basis: str = "moon"  # "moon" | "lagna", for kind == "house"
    target: Graha = Graha.MOON  # natal planet, for kind == "aspect"


def _se_id(planet: Graha) -> int:
    """Swiss ephemeris id for a planet.

    Graha enum order is NOT Swiss order (Mars/Jupiter differ) — the
    canonical map lives in gochara; never use int(planet) here.
    """
    if planet.is_node:
        raise ValueError("node searches are not supported in v1")
    return _GRAHA_TO_SE[planet]


def _sign_of(se: SweEngine, se_id: int, jd: float) -> int:
    return int(se.calc_planet(se_id, jd).longitude // 30) % 12


def _jd(d: date) -> float:
    return SweEngine().julday(d.year, d.month, d.day, 0.0)


def _natal_signs(cd: ChartData) -> Dict[Graha, int]:
    return {g: int(p.longitude // 30) % 12 for g, p in cd.planets.items()}


def _house_matches(entry_sign: int, ref_sign: int, house: int) -> bool:
    return ((entry_sign - ref_sign) % 12) + 1 == house


def _refine_day_boundary(se: SweEngine, se_id: int, day_lo: date,
                         day_hi: date, cusp_lon: float) -> date:
    """Refine a day-bracketed cusp crossing back to a calendar date."""
    jd = _refine_ingress(se, _jd(day_lo), _jd(day_hi) + 1.0, cusp_lon,
                         se_id=se_id)
    y, m, d, _ = SweEngine().revjul(jd)
    return date(y, m, d)


def _sweep_sign_days(se: SweEngine, se_id: int, start: date,
                     end: date) -> List[tuple]:
    """Per-day transit signs for one planet: [(date, sign)]."""
    days: List[tuple] = []
    day = start
    while day <= end:
        days.append((day, _sign_of(se, se_id, _jd(day))))
        day += timedelta(days=STEP_DAYS)
    return days


def _group_runs(days: List[tuple],
                matches, label_of) -> List[SearchInterval]:
    """Group consecutive matching days; label each interval."""
    intervals: List[SearchInterval] = []
    run_start = None
    prev = None
    for day, sign in days:
        if matches(sign):
            if run_start is None:
                run_start = day
            prev = day
        else:
            if run_start is not None:
                intervals.append(SearchInterval(run_start, prev,
                                                label_of(run_start, prev)))
                run_start = None
    if run_start is not None:
        intervals.append(SearchInterval(run_start, prev,
                                        label_of(run_start, prev)))
    return intervals


def _search_house(cd: ChartData, cond: SearchCondition, start: date,
                  end: date) -> SearchResult:
    se = SweEngine()
    se_id = _se_id(cond.planet)
    natal = _natal_signs(cd)
    ref = natal[Graha.MOON] if cond.basis == "moon" else int(
        cd.ascendant // 30) % 12
    basis_lbl = "from Moon" if cond.basis == "moon" else "from lagna"
    days = _sweep_sign_days(se, se_id, start, end)
    raw = _group_runs(days, lambda s: _house_matches(s, ref, cond.house),
                      lambda a, b: (f"{cond.planet.name.title()} in house "
                                    f"{cond.house} {basis_lbl}"))
    intervals = []
    for iv in raw:
        lo_cusp = (ref + cond.house - 1) % 12 * 30.0
        hi_cusp = (ref + cond.house) % 12 * 30.0
        lo = _refine_day_boundary(
            se, se_id, max(start, iv.start - timedelta(days=1)),
            iv.start, lo_cusp)
        hi = _refine_day_boundary(
            se, se_id, iv.end, min(end, iv.end + timedelta(days=1)),
            hi_cusp)
        intervals.append(SearchInterval(max(lo, start), min(hi, end),
                                        iv.label))
    return SearchResult(
        condition=(f"{cond.planet.name.title()} in house {cond.house} "
                   f"{basis_lbl}"),
        window_start=start, window_end=end, intervals=intervals,
        note=(f"Daily sweep, boundaries refined to the day; "
              f"retrograde re-entries are separate intervals."))


def _search_aspect(cd: ChartData, cond: SearchCondition, start: date,
                   end: date) -> SearchResult:
    se = SweEngine()
    se_id = _se_id(cond.planet)
    natal = _natal_signs(cd)
    target_sign = natal[cond.target]
    days = _sweep_sign_days(se, se_id, start, end)

    def matches(sign: int) -> bool:
        return any(a.target_sign_index == target_sign
                   for a in aspects_from(cond.planet, sign))

    raw = _group_runs(
        days, matches,
        lambda a, b: (f"{cond.planet.name.title()} aspects natal "
                      f"{cond.target.name.title()}"))
    intervals = []
    for iv in raw:
        entry_sign = next(s for d, s in days if d == iv.start)
        exit_sign = next(s for d, s in days if d == iv.end)
        lo_cusp = float(entry_sign * 30)
        hi_cusp = float((exit_sign + 1) % 12 * 30)
        lo = _refine_day_boundary(
            se, se_id, max(start, iv.start - timedelta(days=1)),
            iv.start, lo_cusp)
        hi = _refine_day_boundary(
            se, se_id, iv.end, min(end, iv.end + timedelta(days=1)),
            hi_cusp)
        intervals.append(SearchInterval(max(lo, start), min(hi, end),
                                        iv.label))
    return SearchResult(
        condition=(f"{cond.planet.name.title()} aspects natal "
                   f"{cond.target.name.title()} (Parashara drishti)"),
        window_start=start, window_end=end, intervals=intervals,
        note=(f"Daily sweep, boundaries refined to the day; "
              f"retrograde re-entries are separate intervals."))


def _search_saturn(cd: ChartData, cond: SearchCondition, start: date,
                   end: date) -> SearchResult:
    natal = _natal_signs(cd)
    phases = saturn_phase_timeline(natal[Graha.MOON], "lahiri", start, end)
    intervals = [SearchInterval(max(p.start, start), min(p.end, end),
                                f"Saturn {p.kind}")
                 for p in phases
                 if p.kind in _SATURN_KINDS and p.end >= start
                 and p.start <= end]
    return SearchResult(
        condition="Saturn Sade-Sati / dhaiya windows",
        window_start=start, window_end=end, intervals=intervals,
        note="Delegated to saturn_phase_timeline (ingress-refined).")


def _search_ingress(cd: ChartData, cond: SearchCondition, start: date,
                    end: date) -> SearchResult:
    del cd
    se = SweEngine()
    se_id = _se_id(cond.planet)
    days = _sweep_sign_days(se, se_id, start, end)
    intervals = []
    for (d0, s0), (d1, s1) in zip(days, days[1:]):
        if s1 != s0:
            cusp = float(s1 * 30)
            refined = _refine_day_boundary(se, se_id, d0, d1, cusp)
            refined = max(start, min(end, refined))
            from jhora.types.rasi import Rasi
            intervals.append(SearchInterval(
                refined, refined,
                f"{cond.planet.name.title()} ingress {Rasi(s1).full_name}"))
    return SearchResult(
        condition=f"{cond.planet.name.title()} sign ingress",
        window_start=start, window_end=end, intervals=intervals,
        note="Daily sweep, crossings refined to the day.")


def search_transits(cd: ChartData, cond: SearchCondition, start: date,
                    end: date) -> SearchResult:
    """Search transit dates matching a condition inside [start, end].

    Raises ValueError when the window exceeds MAX_WINDOW_YEARS.
    """
    if start > end:
        raise ValueError("search window start is after end")
    if (end - start).days > MAX_WINDOW_YEARS * 366:
        raise ValueError(f"search window capped at {MAX_WINDOW_YEARS} years")
    if cond.kind == "house":
        if not 1 <= cond.house <= 12:
            raise ValueError("house must be 1-12")
        if cond.basis not in ("moon", "lagna"):
            raise ValueError("basis must be 'moon' or 'lagna'")
        return _search_house(cd, cond, start, end)
    if cond.kind == "aspect":
        return _search_aspect(cd, cond, start, end)
    if cond.kind == "saturn":
        return _search_saturn(cd, cond, start, end)
    if cond.kind == "ingress":
        return _search_ingress(cd, cond, start, end)
    raise ValueError(f"unknown search kind: {cond.kind}")
