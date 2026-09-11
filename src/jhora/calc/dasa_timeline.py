"""Dasa timeline — text-based visualization of dasa periods."""

from datetime import datetime
from typing import List, Optional

from jhora.charts.chart import ChartData
from jhora.dasas.vimsottari import VimsottariDasa
from jhora.types.dasa import DasaPeriod


def current_period(periods: List[DasaPeriod], now: datetime) -> Optional[DasaPeriod]:
    """Return the period containing `now`, or None if outside the sequence."""
    return next((p for p in periods if p.start_date <= now <= p.end_date), None)


def next_mahadasa(periods: List[DasaPeriod],
                  current_md: DasaPeriod) -> Optional[DasaPeriod]:
    """Return the MD following `current_md`.

    MDs are contiguous: the next starts exactly when the current ends,
    so the comparison must be >= (strict > skips it and lands a full
    cycle ahead).
    """
    for p in periods:
        if p.start_date >= current_md.end_date:
            return p
    return None


def upcoming_sub_periods(md: DasaPeriod, now: datetime,
                         limit: int = 4) -> List[DasaPeriod]:
    """Sub-periods of `md` starting after `now`, soonest first."""
    upcoming = sorted((sp for sp in (md.sub_periods or []) if sp.start_date > now),
                      key=lambda x: x.start_date)
    return upcoming[:limit]


def dasa_timeline_text(cd: ChartData, width: int = 80) -> str:
    """Generate a text-based dasa timeline visualization."""
    try:
        dasa = VimsottariDasa()
        chart_dict = {
            "planets": {g.value: {"longitude": p.longitude}
                        for g, p in cd.planets.items()},
            "lagna_lon": cd.ascendant,
        }
        mds = dasa.compute(cd.julian_day, chart_dict)

        now = datetime.now()
        birth = cd.birth_date
        lines = ["Vimsottari Mahadasha Timeline", "=" * width, ""]

        # Calculate timeline span
        first = mds[0].start_date
        last = mds[-1].end_date
        total_days = (last - first).total_seconds() / 86400

        for md in mds:
            md_days = (md.end_date - md.start_date).total_seconds() / 86400
            bar_len = max(1, int((md_days / total_days) * (width - 10)))
            bar = "█" * bar_len

            # Mark current period
            marker = ""
            if md.start_date <= now <= md.end_date:
                marker = " ◀ CURRENT"
                # Find where "now" is in this bar
                elapsed = (now - md.start_date).total_seconds() / 86400
                pos = int((elapsed / md_days) * bar_len) if md_days > 0 else 0
                bar = bar[:pos] + "●" + bar[pos+1:] if pos < bar_len else bar

            age_start = (md.start_date - birth).total_seconds() / (365.25 * 86400)
            age_end = (md.end_date - birth).total_seconds() / (365.25 * 86400)

            lines.append(
                f"{md.lord_name:<8} {bar} "
                f"age {age_start:.0f}-{age_end:.0f}{marker}"
            )
            # Show antardasas for current MD
            if md.start_date <= now <= md.end_date:
                ad_days = md_days / 9  # approximate
                for i, ad in enumerate(md.sub_periods or []):
                    ad_bar_len = max(1, int(bar_len / len(md.sub_periods or [1])))
                    ad_bar = "─" * ad_bar_len
                    if ad.start_date <= now <= ad.end_date:
                        elapsed = (now - ad.start_date).total_seconds() / 86400
                        dur = (ad.end_date - ad.start_date).total_seconds() / 86400
                        pos = int((elapsed / dur) * ad_bar_len) if dur > 0 else 0
                        ad_bar = ad_bar[:pos] + "○" + ad_bar[pos+1:] if pos < ad_bar_len else ad_bar
                        lines.append(
                            f"  {ad.lord_name:<6} {ad_bar} "
                            f"{ad.start_date.strftime('%Y-%m')} → {ad.end_date.strftime('%Y-%m')} ◀"
                        )

        return "\n".join(lines)
    except Exception as e:
        return f"Dasa timeline error: {e}"
