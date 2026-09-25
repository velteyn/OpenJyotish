"""Asta-Udaya — combust (asta) and rising (udaya) windows.

Venus and Jupiter combust periods block marriages and other
auspicious works in the most-used tradition, so gurus track these
windows every year. Detection is a daily scan of tropical elongation
(ayanamsa-invariant: Sun and planet shift together) with the
retro-aware combustion orbs. Granularity is ±1 day, documented;
boundaries are muhurta-blocking dates, not eclipse timings.
"""

from datetime import date, timedelta
from typing import Dict, List

from jhora.calc.combustion import elongation, orb
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha

#: Planets tracked (the marriage blockers). Others on request.
TRACKED = (Graha.VENUS, Graha.JUPITER)

#: pyswisseph planet ids: SUN=0 .. SATURN=6.
_PID = {Graha.MERCURY: 2, Graha.VENUS: 3, Graha.MARS: 4,
        Graha.JUPITER: 5, Graha.SATURN: 6}


def spans_from_states(dates: List[date],
                      states: List[bool]) -> List[tuple]:
    """(asta_start, udaya) spans from a daily combust True/False series.

    A span still open at the series end gets udaya None.
    """
    spans = []
    start = None
    for d, s in zip(dates, states):
        if s and start is None:
            start = d
        elif not s and start is not None:
            spans.append((start, d))
            start = None
    if start is not None:
        spans.append((start, None))
    return spans


def asta_periods(year: int,
                 planets: tuple = TRACKED) -> List[Dict]:
    """[{planet, asta (date), udaya (date or None)}] within a year."""
    se = SweEngine()
    days = []
    d = date(year, 1, 1)
    while d.year == year:
        days.append(d)
        d += timedelta(days=1)
    # Extra days to close spans running past Dec 31.
    tail = [days[-1] + timedelta(days=k) for k in range(1, 45)]
    out = []
    for g in planets:
        states = []
        for day in days + tail:
            jd = se.julday(day.year, day.month, day.day, 12.0)
            sun = se.calc_planet(0, jd)
            pl = se.calc_planet(_PID[g], jd)
            o = orb(g, pl.is_retrograde)
            states.append(elongation(pl.longitude, sun.longitude) < o)
        for start, end in spans_from_states(days + tail, states):
            if start.year == year or (end is not None and end.year == year):
                out.append({"planet": g, "asta": start, "udaya": end})
    out.sort(key=lambda r: (r["asta"], r["planet"].value))
    return out
