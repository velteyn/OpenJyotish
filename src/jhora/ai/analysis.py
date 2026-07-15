"""Analysis snapshot — combines all computed chart data into LLM-ready text.

Produces structured summaries of dasa periods, transit forecasts, planetary
strengths, detected yogas, and panchanga for injection into AI prompts.
"""

from datetime import datetime
from typing import List

from jhora.charts.chart import ChartData
from jhora.calc.shadbala import ShadbalaComputer
from jhora.calc.bhava_bala import BhavaBalaComputer
from jhora.calc.yogas import detect_all
from jhora.calc.gochara import compute_transits
from jhora.calc.muhurta import compute_panchanga
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


def dasa_snapshot(cd: ChartData) -> str:
    """Current dasa period and upcoming transitions."""
    try:
        from jhora.dasas.vimsottari import VimsottariDasa
        dasa = VimsottariDasa(cd)
        chart_dict = {
            "planets": {g.value: {"longitude": p.longitude}
                        for g, p in cd.planets.items()},
            "lagna_lon": cd.ascendant,
        }
        periods = dasa.compute(cd.julian_day, chart_dict)
        now = cd.birth_date
        # Find current main and sub periods
        current = []
        upcoming = []
        for p in periods:
            if p.start <= now <= p.end:
                current.append(p)
            elif p.start > now:
                upcoming.append(p)
            if len(current) >= 3 and len(upcoming) >= 5:
                break

        lines = ["Current Dasa Periods:"]
        for p in current[:3]:
            lines.append(
                f"  {p.lord.full_name} {p.level.value if hasattr(p.level, 'value') else str(p.level)}: "
                f"{p.start.strftime('%Y-%m-%d')} to {p.end.strftime('%Y-%m-%d')}"
            )
        lines.append("Upcoming Transitions:")
        for p in upcoming[:5]:
            lines.append(
                f"  {p.lord.full_name} {p.level.value if hasattr(p.level, 'value') else str(p.level)} "
                f"begins {p.start.strftime('%Y-%m-%d')}"
            )
        return "\n".join(lines) if len(lines) > 2 else ""
    except Exception:
        return ""


def transit_snapshot(cd: ChartData) -> str:
    """Current planetary transits with Ashtakavarga scores."""
    try:
        eng = SweEngine()
        now = datetime.now()
        jd = eng.julday(now.year, now.month, now.day,
                        now.hour + now.minute / 60.0)
        result = compute_transits(cd, jd)
        lines = [f"Current Transits ({now.strftime('%Y-%m-%d')}):"]
        entries = result.entries if hasattr(result, 'entries') else []
        for e in entries[:9]:
            fav = "favorable" if e.is_favorable else "challenging"
            lines.append(
                f"  {e.graha.full_name if hasattr(e.graha, 'full_name') else e.graha.short_name}: "
                f"{e.transit_rasi_name} (house {e.house_from_lagna} from lagna), "
                f"SAV={e.sav_score}, {fav}"
            )
        return "\n".join(lines) if len(lines) > 1 else ""
    except Exception:
        return ""


def strengths_snapshot(cd: ChartData) -> str:
    """Shadbala + Bhava Bala summary."""
    lines = []
    try:
        sb = ShadbalaComputer(cd)
        gr = []
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                  Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
            r = sb.compute_one(g)
            gr.append((r.graha.full_name, r.total_virupa))
        gr.sort(key=lambda x: x[1], reverse=True)
        lines.append("Planetary Strengths (Shadbala):")
        for name, virupa in gr:
            lines.append(f"  {name}: {virupa:.0f} virupas")
        if gr:
            lines.append(f"  Strongest: {gr[0][0]}, Weakest: {gr[-1][0]}")
    except Exception:
        pass

    try:
        bb = BhavaBalaComputer(cd)
        report = bb.compute_all()
        lines.append("\nHouse Strengths (Bhava Bala):")
        for h in range(1, 13):
            r = report.results[h]
            rasi_idx = (int(cd.ascendant / 30) + h - 1) % 12
            sign = Rasi(rasi_idx).short_name
            lines.append(f"  H{h} ({sign}): {r.total:.0f}")
        s = report.strongest()
        w = report.weakest()
        lines.append(f"  Strongest: H{s.house}, Weakest: H{w.house}")
    except Exception:
        pass

    return "\n".join(lines)


def yogas_snapshot(cd: ChartData) -> str:
    """Detected yogas summary."""
    try:
        yogas = detect_all(cd)
        if not yogas:
            return "No significant yogas detected."
        lines = ["Detected Yogas:"]
        for y in yogas[:10]:
            planets_str = ", ".join(p.short_name for p in y.planets) if y.planets else ""
            lines.append(f"  {y.name}: {y.description[:80]}" +
                        (f" (planets: {planets_str})" if planets_str else ""))
        return "\n".join(lines)
    except Exception:
        return ""


def panchanga_snapshot(cd: ChartData) -> str:
    """Today's panchanga elements."""
    try:
        bd = cd.birth_date
        info = compute_panchanga(
            datetime(bd.year, bd.month, bd.day, 12, 0, 0),
            cd.latitude, cd.longitude,
            tz_offset=0,
        )
        lines = [
            "Panchanga Info:",
            f"  Tithi: {info.tithi_name}",
            f"  Nakshatra: {info.nakshatra_name}",
            f"  Yoga: {info.yoga_name}",
            f"  Karana: {info.karana_name}",
            f"  Weekday: {info.weekday_name}",
        ]
        return "\n".join(lines)
    except Exception:
        return ""


def build_analysis_text(cd: ChartData) -> str:
    """Combine all analysis snapshots into one text block."""
    sections = []
    for title, fn in [
        ("STRENGTHS", lambda: strengths_snapshot(cd)),
        ("YOGAS", lambda: yogas_snapshot(cd)),
        ("DASA PERIODS", lambda: dasa_snapshot(cd)),
        ("TRANSITS", lambda: transit_snapshot(cd)),
    ]:
        try:
            text = fn()
            if text.strip():
                sections.append(f"--- {title} ---\n{text}")
        except Exception:
            pass

    return "\n\n".join(sections) if sections else ""
