"""Dasa chart — the dasa period tree at a glance.

Where the timeline shows the mahadasas as bars, the *dasa chart* expands the
running branch: all mahadasas, then the antardasas of the running mahadasa,
then the pratyantardasas of the running antardasa (and deeper on request).
The running period at each level is flagged, so a guru sees the full context
of "what period am I in" without scrolling the whole tree.

Tradition: the period lengths and order are whatever the chosen dasa system
produces (standard Vimsottari by default); this module only arranges them.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Sequence

from jhora.charts.chart import ChartData
from jhora.dasas.base import DasaBase
from jhora.types.dasa import DasaPeriod

#: Level labels, in order.
LEVEL_NAMES = (
    "Mahadasa", "Antardasa", "Pratyantardasa", "Sukshma", "Prana", "Deha",
)


@dataclass(frozen=True)
class DasaChartRow:
    """One row of the dasa chart: a period at some level."""

    depth: int
    level: str
    lord: str
    start_jd: float
    end_jd: float
    active: bool


def dasa_chart_rows(periods: Sequence[DasaPeriod], when_jd: float,
                    depth: int = 3) -> List[DasaChartRow]:
    """Flatten the period tree around ``when_jd``.

    Every period at the top level is listed; at each deeper level only the
    children of the running period are listed. Stops early when the running
    period has no sub-periods.
    """
    rows: List[DasaChartRow] = []
    nodes: Sequence[DasaPeriod] = periods
    for level in range(max(1, depth)):
        active: Optional[DasaPeriod] = None
        for p in nodes:
            is_active = p.start_jd <= when_jd < p.end_jd
            rows.append(DasaChartRow(
                depth=level,
                level=LEVEL_NAMES[min(level, len(LEVEL_NAMES) - 1)],
                lord=p.lord_name,
                start_jd=p.start_jd,
                end_jd=p.end_jd,
                active=is_active,
            ))
            if is_active:
                active = p
        if active is None or not active.sub_periods:
            break
        nodes = active.sub_periods
    return rows


def _when_jd(cd: ChartData, when) -> float:
    """Julian day (UT) for a local date/datetime; now when ``when`` is None."""
    import swisseph as swe

    if when is None:
        now = datetime.now()
    elif isinstance(when, datetime):
        now = when
    else:
        now = datetime(when.year, when.month, when.day, 12, 0)
    # Convert local wall time to UT with the chart's own zone offset.
    from jhora.charts.chart import ChartBuilder
    offset = ChartBuilder._parse_tz(cd.timezone, cd.birth_date)
    utc = now + timedelta(hours=offset)
    return swe.julday(
        utc.year, utc.month, utc.day,
        utc.hour + utc.minute / 60.0 + utc.second / 3600.0,
    )


def dasa_chart(cd: ChartData, when=None, depth: int = 3,
               engine: Optional[DasaBase] = None) -> List[DasaChartRow]:
    """The dasa chart for a chart at a date (default: now)."""
    from jhora.dasas.vimsottari import VimsottariDasa

    engine = engine or VimsottariDasa()
    chart = {
        "planets": {g.value: {"longitude": p.longitude}
                    for g, p in cd.planets.items()},
        "lagna_lon": cd.ascendant,
    }
    periods = engine.compute(cd.julian_day, chart)
    return dasa_chart_rows(periods, _when_jd(cd, when), depth=depth)


def format_dasa_chart(rows: Sequence[DasaChartRow],
                      date_fn=None) -> str:
    """Render dasa-chart rows as an indented text tree."""
    if date_fn is None:
        from jhora.ephemeris.swe import SweEngine

        def date_fn(jd):
            y, m, d, _ = SweEngine().revjul(jd)
            return f"{int(y)}/{int(m):02d}/{int(d):02d}"

    lines = []
    for r in rows:
        indent = "  " * r.depth
        marker = " ◀" if r.active else ""
        lines.append(
            f"{indent}{r.lord:<9} {date_fn(r.start_jd)} → {date_fn(r.end_jd)}"
            f"  [{r.level}]{marker}"
        )
    return "\n".join(lines)
