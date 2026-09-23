"""Dasa entry chart — the chart of the moment a dasa period begins.

When a mahadasa or antardasa opens, the sky at that moment is read as a
secondary chart (the same idea as a pravesha/return chart): the entry
lagna, the entry Moon, and how the planets have moved since birth.
The period boundaries come from whichever dasa engine is chosen
(Vimsottari by default); this module only locates the period and casts
the sky for its opening moment at the birth place.

The entry moment is the period's start JD (UT) rendered in the chart's
own timezone, so the entry chart carries the same place/zone as natal.
"""

from datetime import timedelta
from typing import List, Optional, Sequence, Tuple

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.dasas.base import DasaBase, DasaOptions
from jhora.types.dasa import DasaPeriod
from jhora.types.graha import Graha


def parse_path(path: str) -> List[str]:
    """Split a period path like ``'Jupiter/Saturn'`` into lord names."""
    return [seg.strip() for seg in path.replace(">", "/").split("/") if seg.strip()]


def _match_lord(periods: Sequence[DasaPeriod], want: str) -> Optional[DasaPeriod]:
    lowered = want.lower()
    exact = [p for p in periods if p.lord_name.lower() == lowered]
    if len(exact) == 1:
        return exact[0]
    if not exact:
        prefix = [p for p in periods if p.lord_name.lower().startswith(lowered)]
        if len(prefix) == 1:
            return prefix[0]
    return None


def find_period(periods: Sequence[DasaPeriod],
                path: Sequence[str]) -> Optional[DasaPeriod]:
    """Walk the period tree following lord names (MD/AD/...)."""
    node: Optional[DasaPeriod] = None
    nodes = periods
    for want in path:
        node = _match_lord(nodes, want)
        if node is None:
            return None
        nodes = node.sub_periods or []
    return node


def _chart_to_dict(cd: ChartData):
    return {
        "planets": {g.value: {"longitude": p.longitude}
                    for g, p in cd.planets.items()},
        "lagna_lon": cd.ascendant,
    }


def dasa_entry(cd: ChartData, path: Sequence[str],
               engine: Optional[DasaBase] = None,
               opts: Optional[DasaOptions] = None,
               ) -> Tuple[DasaPeriod, ChartData]:
    """Locate the period at ``path`` and cast its opening-moment chart.

    Raises ValueError when the path matches nothing (the message lists
    the available lords at the failing level).
    """
    from jhora.dasas.vimsottari import VimsottariDasa

    engine = engine or VimsottariDasa()
    if opts is not None:
        periods = engine.compute(cd.julian_day, _chart_to_dict(cd), opts)
    else:
        periods = engine.compute(cd.julian_day, _chart_to_dict(cd))
    period = find_period(periods, list(path))
    if period is None:
        raise ValueError(_path_error(periods, list(path)))

    import swisseph as swe
    y, m, d, h = swe.revjul(period.start_jd)
    # revjul gives UT; render in the chart's own zone for display fidelity
    # (_parse_tz returns hours added to local to get UTC).
    offset = ChartBuilder._parse_tz(cd.timezone, cd.birth_date)
    local = swe.julday(int(y), int(m), int(d), h) - offset / 24.0
    ly, lm, ld, lh = swe.revjul(local)
    entry = ChartBuilder().build(
        year=int(ly), month=int(lm), day=int(ld), hour=float(lh),
        lat=cd.latitude, lon=cd.longitude,
        tz=cd.timezone, ayanamsa=cd.ayanamsa_name,
    )
    return period, entry


def _path_error(periods: Sequence[DasaPeriod], path: List[str]) -> str:
    nodes = periods
    for depth, want in enumerate(path):
        node = _match_lord(nodes, want)
        if node is None:
            avail = ", ".join(p.lord_name for p in nodes)
            return (f"No {'/'.join(path[:depth + 1])} period: "
                    f"expected one of [{avail}]")
        nodes = node.sub_periods or []
    return f"No {'/'.join(path)} period"


def format_dasa_entry(path: Sequence[str], period: DasaPeriod,
                      natal: ChartData, entry: ChartData) -> str:
    """Render the entry chart as text (moment, lagna, planet motion)."""
    from rich.table import Table

    from jhora.types.rasi import Rasi
    import swisseph as swe

    y, m, d, h = swe.revjul(period.start_jd)
    lines = [
        f"Entry: {'/'.join(path)} opens "
        f"{int(y):04d}-{int(m):02d}-{int(d):02d} {h:05.2f} UT",
        f"Entry lagna: {Rasi.from_longitude(entry.ascendant).short_name} "
        f"{entry.ascendant:.2f}° (natal "
        f"{Rasi.from_longitude(natal.ascendant).short_name} "
        f"{natal.ascendant:.2f}°)",
        f"Entry Moon: {Rasi.from_longitude(entry.planet(Graha.MOON).longitude).short_name} "
        f"(natal "
        f"{Rasi.from_longitude(natal.planet(Graha.MOON).longitude).short_name})",
    ]
    table = Table(title="Planets: natal → entry")
    table.add_column("Planet")
    table.add_column("Natal")
    table.add_column("Entry")
    table.add_column("Moved")
    for g in (Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN):
        nlon = natal.planet(g).longitude
        elon = entry.planet(g).longitude
        moved = (elon - nlon) % 360.0
        table.add_row(
            g.short_name,
            f"{Rasi.from_longitude(nlon).short_name} {nlon % 30:.1f}°",
            f"{Rasi.from_longitude(elon).short_name} {elon % 30:.1f}°",
            f"{moved:.1f}°",
        )
    from rich.console import Console
    import io
    buf = io.StringIO()
    Console(file=buf, width=100).print(table)
    lines.append(buf.getvalue())
    return "\n".join(lines)
