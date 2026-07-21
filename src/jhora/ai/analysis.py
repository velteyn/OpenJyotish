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
        from datetime import datetime
        from jhora.dasas.vimsottari import VimsottariDasa
        dasa = VimsottariDasa()
        chart_dict = {
            "planets": {g.value: {"longitude": p.longitude}
                        for g, p in cd.planets.items()},
            "lagna_lon": cd.ascendant,
        }
        periods = dasa.compute(cd.julian_day, chart_dict)
        now = datetime.now()

        current_md = None
        for p in periods:
            if p.start_date <= now <= p.end_date:
                current_md = p
                break

        if not current_md:
            return ""

        lines = ["Current Dasa Periods:"]
        lines.append(
            f"  {current_md.lord_name} Mahadasha: "
            f"{current_md.start_date.strftime('%Y-%m-%d')} to "
            f"{current_md.end_date.strftime('%Y-%m-%d')}"
        )

        # Find current sub-period (AD)
        for sp in (current_md.sub_periods or []):
            if sp.start_date <= now <= sp.end_date:
                lines.append(
                    f"    Current {sp.lord_name} Antardasha: "
                    f"{sp.start_date.strftime('%Y-%m-%d')} to "
                    f"{sp.end_date.strftime('%Y-%m-%d')}"
                )

        # Upcoming ADs within current MD
        upcoming = sorted(
            [sp for sp in (current_md.sub_periods or []) if sp.start_date > now],
            key=lambda x: x.start_date,
        )
        if upcoming:
            lines.append("  Upcoming Antardashas:")
            for sp in upcoming[:5]:
                lines.append(
                    f"    {sp.lord_name}: "
                    f"{sp.start_date.strftime('%Y-%m-%d')} to "
                    f"{sp.end_date.strftime('%Y-%m-%d')}"
                )
        return "\n".join(lines) if len(lines) > 2 else ""
    except Exception:
        return ""


def _level_name(level) -> str:
    """Convert PeriodLevel to readable string."""
    v = level.value if hasattr(level, 'value') else level
    names = {0: "MD", 1: "AD", 2: "PD", 3: "SD"}
    return names.get(v, f"Level-{v}")


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
        ("VIMSOPAKA BALA", lambda: _vimsopaka_snapshot(cd)),
        ("KUJA DOSHA", lambda: _kuja_dosha_snapshot(cd)),
        ("YOGAS", lambda: yogas_snapshot(cd)),
        ("DASA PERIODS", lambda: dasa_snapshot(cd)),
        ("TRANSITS", lambda: transit_snapshot(cd)),
        ("ASHTAKAVARGA", lambda: _ashtakavarga_snapshot(cd)),
        ("CHALIT SHIFTS", lambda: _chalit_snapshot(cd)),
        ("SPECIAL POINTS", lambda: _special_points_snapshot(cd)),
        ("LEARNING", lambda: _learning_snapshot(cd)),
    ]:
        try:
            text = fn()
            if text.strip():
                sections.append(f"--- {title} ---\n{text}")
        except Exception:
            pass

    return "\n\n".join(sections) if sections else ""


def _vimsopaka_snapshot(cd: ChartData) -> str:
    from jhora.calc.vimsopaka import VimsopakaComputer, VimsopakaScheme
    vc = VimsopakaComputer(cd)
    lines = ["Vimsopaka Bala (Shadvarga, 20-point scale):"]
    for r in sorted(vc.compute_all(VimsopakaScheme.SHADVARGA), key=lambda x: x.total, reverse=True):
        lines.append(f"  {r.graha.full_name}: {r.total:.1f}/20 ({r.percentage:.0f}%)")
    return "\n".join(lines)


def _ashtakavarga_snapshot(cd: ChartData) -> str:
    from jhora.calc.ashtakavarga import sarva_ashtakavarga
    from jhora.types.rasi import Rasi
    sav = sarva_ashtakavarga(cd)
    lines = ["Ashtakavarga SAV (total bindus in each sign):"]
    for i in range(12):
        lines.append(f"  {Rasi(i).short_name}: {int(sav[i])}")
    lines.append(f"  Total SAV: {int(sum(sav))}")
    return "\n".join(lines)


def _chalit_snapshot(cd: ChartData) -> str:
    from jhora.calc.chalit import ChalitComputer
    cc = ChalitComputer(cd)
    cr = cc.compute()
    moved = cr.moved_planets
    if not moved:
        return "Chalit: No planets shifted houses."
    lines = ["Chalit (cusp-based) shifts from whole-sign houses:"]
    for e in moved:
        lines.append(f"  {e.graha.full_name}: House {e.sign_house} → {e.cusp_house} (sign: {e.sign})")
    return "\n".join(lines)


def _special_points_snapshot(cd: ChartData) -> str:
    from jhora.calc.upagraha import compute_solar_upagrahas
    from jhora.calc.special_lagnas import compute_special_lagnas
    from jhora.calc.karaka import compute_chara_karakas
    from jhora.types.graha import Graha

    lines = []
    # Upagrahas
    sun_lon = cd.planet(Graha.SUN).longitude
    upas = compute_solar_upagrahas(sun_lon)
    lines.append("Upagrahas (shadow planets):")
    for u in upas:
        lines.append(f"  {u.name}: {u.rasi} {u.longitude:.1f}°")

    # Special lagnas
    sl = compute_special_lagnas(cd)
    lines.append("Special Lagnas:")
    for s in sl:
        lines.append(f"  {s.name}: {s.sign} {s.longitude:.1f}°")

    # Karakas
    planets = {g: {"longitude": p.longitude} for g, p in cd.planets.items()}
    cks = compute_chara_karakas(planets)
    lines.append("Chara Karakas:")
    for ck in cks:
        lines.append(f"  {ck.short_name} ({ck.full_name}): {ck.graha.short_name}")

    return "\n".join(lines)


def _learning_snapshot(cd: ChartData) -> str:
    from jhora.calc.learning import marana_karaka_sthana, vaiseshikamsas, ishta_kashta_phala
    from jhora.calc.special_lagnas import kp_sublord_string
    from jhora.types.graha import Graha

    lines = []
    # Marana karaka
    mk = marana_karaka_sthana(cd)
    if mk:
        lines.append("Marana Karaka (weakened planets):")
        for m in mk:
            lines.append(f"  {m['graha']} in house {m['house']} ({m['sign']}) — weakened")

    # Vaiseshikamsas
    va = vaiseshikamsas(cd)
    if va:
        lines.append("Vaiseshikamsa ranks:")
        for v in va:
            if v["rank"] != "None":
                lines.append(f"  {v['graha']}: {v['rank']} ({v['score']:.1f}/20)")

    # Ishta/Kashta
    ik = ishta_kashta_phala(cd)
    if ik:
        lines.append("Ishta/Kashta Phala (beneficence/difficulty):")
        for r in ik:
            lines.append(f"  {r['graha']}: Ishta={r['ishta']:.0f} Kashta={r['kashta']:.0f}")

    # KP sub-lords
    lines.append("KP Sub-Lords:")
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
        if g in cd.planets:
            chain = kp_sublord_string(cd.planet(g).longitude, 3)
            lines.append(f"  {g.short_name}: {chain}")

    return "\n".join(lines)


def _kuja_dosha_snapshot(cd: ChartData) -> str:
    from jhora.calc.kuja_dosha import compute_kuja_dosha
    r = compute_kuja_dosha(cd)
    lines = ["Kuja Dosha (Mangal Dosha) — Mars Affliction:"]
    if r.has_dosha:
        parts = []
        if r.from_lagna:
            parts.append(f"Lagna(H{r.mars_from_lagna_house})")
        if r.from_moon:
            parts.append(f"Moon(H{r.mars_from_moon_house})")
        if r.from_venus:
            parts.append(f"Venus(H{r.mars_from_venus_house})")
        lines.append(f"  PRESENT from: {', '.join(parts)}")
    else:
        lines.append(f"  Not present")
    lines.append(f"  Mars sign: {r.mars_sign} (own sign: {r.mars_own_sign})")
    lines.append(f"  Jupiter cancellation: {r.jupiter_cancels}")
    lines.append(f"  Lagna ({r.lagna_name}) cancellation: {r.lagna_cancels}")
    return "\n".join(lines)
