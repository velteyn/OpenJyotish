"""HTML report generator — produces styled, printable chart reports."""

from datetime import datetime
from typing import Optional

from jhora.charts.chart import ChartData
from jhora.calc.shadbala import ShadbalaComputer
from jhora.calc.bhava_bala import BhavaBalaComputer
from jhora.calc.vimsopaka import VimsopakaComputer, VimsopakaScheme
from jhora.calc.yogas import detect_all
from jhora.calc.gochara import compute_transits
from jhora.dasas.vimsottari import VimsottariDasa
from jhora.dasas.base import DasaOptions
from jhora.types.dasa import PeriodLevel
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra

CSS = """body{font-family:'Segoe UI',sans-serif;background:#0d1b2a;color:#e0e0e0;margin:0;padding:20px}
h1{color:#e0b050;border-bottom:2px solid #2a3f5f;padding-bottom:8px}
h2{color:#c0a040;margin-top:30px}
table{width:100%;border-collapse:collapse;margin:10px 0;font-size:13px}
th{background:#1a2744;color:#e0b050;padding:8px;text-align:left;border:1px solid #2a3f5f}
td{padding:6px 8px;border:1px solid #1a2744}
tr:nth-child(even){background:#111d2e}
.moved{color:#ff6666;font-weight:bold}
.strength{color:#66bb6a;font-weight:bold}
.weak{color:#ff6666}
.footer{color:#666;font-size:11px;text-align:center;margin-top:40px;border-top:1px solid #2a3f5f;padding-top:10px}
.meta{color:#888;font-size:12px}
.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media print{body{background:#fff;color:#000}th{background:#eee;color:#000}tr:nth-child(even){background:#f5f5f5}}"""


def generate_chart_report(cd: ChartData, output_path: str,
                          style: str = "full") -> str:
    """Generate a complete HTML chart report and write to output_path."""
    html = _build_html(cd, style)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


def _meta(cd: ChartData) -> str:
    lagna = Rasi.from_longitude(cd.ascendant)
    lat_hemi = "N" if cd.latitude >= 0 else "S"
    lon_hemi = "E" if cd.longitude >= 0 else "W"
    return f"""
<div class="meta">
  <strong>Birth:</strong> {cd.birth_date.strftime('%Y-%m-%d %H:%M')} |
  <strong>Location:</strong> {lat_hemi}, {lon_hemi} |
  <strong>Lagna:</strong> {lagna.full_name} {cd.ascendant:.1f}° |
  <strong>Ayanamsa:</strong> {cd.ayanamsa_name.title()}
</div>"""


def _planet_table(cd: ChartData) -> str:
    rows = []
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
        p = cd.planet(g)
        r = Rasi.from_longitude(p.longitude)
        n, pada = Nakshatra.from_longitude(p.longitude)
        rows.append(
            f"<tr><td>{g.full_name}</td>"
            f"<td>{p.longitude:.2f}°</td>"
            f"<td>{r.full_name}</td>"
            f"<td>{r.lord}</td>"
            f"<td>{n.name.replace('_',' ').title()} p{pada}</td>"
            f"<td>{'Retrograde' if p.is_retrograde else ''}</td></tr>"
        )
    return f"""<h2>Planetary Positions</h2>
<table><tr><th>Planet</th><th>Longitude</th><th>Sign</th><th>Lord</th>
<th>Nakshatra</th><th>Motion</th></tr>{"".join(rows)}</table>"""


def _house_table(cd: ChartData) -> str:
    rows = []
    for h in range(12):
        cusp = cd.house_cusps[h]
        r = Rasi.from_longitude(cusp)
        rows.append(
            f"<tr><td>{h+1}</td><td>{cusp:.2f}°</td>"
            f"<td>{r.full_name}</td><td>{r.lord}</td></tr>"
        )
    return f"""<h2>House Cusps</h2>
<table><tr><th>House</th><th>Cusp</th><th>Sign</th><th>Lord</th></tr>
{"".join(rows)}</table>"""


def _shadbala_table(cd: ChartData) -> str:
    try:
        sb = ShadbalaComputer(cd)
        rows = []
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                  Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
            r = sb.compute_one(g)
            cls = "strength" if r.total_virupa > 400 else ("weak" if r.total_virupa < 300 else "")
            rows.append(
                f"<tr><td>{r.graha.full_name}</td>"
                f"<td>{r.sthana_total:.1f}</td>"
                f"<td>{r.dig_total:.1f}</td>"
                f"<td>{r.kala_total:.1f}</td>"
                f"<td>{r.chesta_total:.1f}</td>"
                f"<td>{r.naisargika.virupa:.1f}</td>"
                f"<td>{r.drik.virupa:.1f}</td>"
                f"<td class='{cls}'>{r.total_virupa:.0f}</td></tr>"
            )
        return f"""<h2>Shadbala (Planetary Strengths)</h2>
<table><tr><th>Planet</th><th>Sthana</th><th>Dig</th><th>Kala</th>
<th>Chesta</th><th>Naisarg</th><th>Drik</th><th>Total (V)</th></tr>
{"".join(rows)}</table>"""
    except Exception:
        return ""


def _yogas_list(cd: ChartData) -> str:
    try:
        yogas = detect_all(cd)
        if not yogas:
            return ""
        rows = []
        for y in yogas[:20]:
            planets = ", ".join(p.short_name for p in y.planets) if y.planets else ""
            rows.append(
                f"<tr><td>{y.name}</td><td>{y.description[:80]}</td>"
                f"<td>{planets}</td></tr>"
            )
        return f"""<h2>Yogas ({len(yogas)} detected)</h2>
<table><tr><th>Yoga</th><th>Description</th><th>Planets</th></tr>
{"".join(rows)}</table>"""
    except Exception:
        return ""


def _vimsopaka_table(cd: ChartData) -> str:
    try:
        vc = VimsopakaComputer(cd)
        results = sorted(vc.compute_all(VimsopakaScheme.SHADVARGA),
                        key=lambda r: r.total, reverse=True)
        rows = []
        for r in results:
            rows.append(
                f"<tr><td>{r.graha.full_name}</td>"
                f"<td>{r.total:.1f}/20</td>"
                f"<td>{r.percentage:.0f}%</td></tr>"
            )
        return f"""<h2>Vimsopaka Bala (Shadvarga)</h2>
<table><tr><th>Planet</th><th>Score</th><th>%</th></tr>
{"".join(rows)}</table>"""
    except Exception:
        return ""


def _vimsottari_table(cd: ChartData) -> str:
    try:
        from datetime import datetime
        opts = DasaOptions(subdivision_level=PeriodLevel.ANTARDASA)
        chart = {
            "planets": {g.value: {"longitude": cd.planet(g).longitude}
                        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                                 Graha.JUPITER, Graha.VENUS, Graha.SATURN,
                                 Graha.RAHU, Graha.KETU]},
            "lagna_lon": cd.ascendant,
        }
        dasa = VimsottariDasa(opts)
        periods = dasa.compute(cd.julian_day, chart)
        now_jd = SweEngine().julday(datetime.now().year, datetime.now().month,
                                     datetime.now().day, 0)
        rows = []
        for p in periods:
            start = p.start_date.strftime("%Y-%m-%d")
            end = p.end_date.strftime("%Y-%m-%d")
            active = "◀ NOW" if p.start_jd <= now_jd < p.end_jd else ""
            cls = ' style="color:#66bb6a;font-weight:bold"' if active else ""
            rows.append(
                f"<tr{cls}><td>{p.lord_name}</td>"
                f"<td>{p.duration_years:.1f}y</td>"
                f"<td>{start}</td><td>{end}</td><td>{active}</td></tr>"
            )
            for sub in (p.sub_periods or []):
                s_start = sub.start_date.strftime("%Y-%m-%d")
                s_end = sub.end_date.strftime("%Y-%m-%d")
                s_active = "◀ NOW" if sub.start_jd <= now_jd < sub.end_jd else ""
                s_cls = ' style="color:#66bb6a"' if s_active else ""
                rows.append(
                    f"<tr{s_cls}><td>&nbsp;&nbsp;└ {sub.lord_name}</td>"
                    f"<td>{sub.duration_years:.1f}y</td>"
                    f"<td>{s_start}</td><td>{s_end}</td><td>{s_active}</td></tr>"
                )
        return f"""<h2>Vimshottari Dasa</h2>
<table><tr><th>Period</th><th>Duration</th><th>Start</th><th>End</th><th></th></tr>
{"".join(rows)}</table>"""
    except Exception:
        return ""


def _transit_table(cd: ChartData) -> str:
    try:
        eng = SweEngine()
        now = datetime.now()
        jd = eng.julday(now.year, now.month, now.day,
                        now.hour + now.minute / 60.0)
        result = compute_transits(cd, jd)
        entries = result.entries if hasattr(result, 'entries') else []
        rows = []
        for e in entries[:9]:
            fav = "✓" if e.is_favorable else "✗"
            rows.append(
                f"<tr><td>{e.graha.full_name if hasattr(e.graha,'full_name') else e.graha.short_name}</td>"
                f"<td>{e.transit_rasi_name}</td>"
                f"<td>H{e.house_from_lagna}</td>"
                f"<td>{e.sav_score}</td>"
                f"<td>{fav}</td></tr>"
            )
        return f"""<h2>Current Transits ({now.strftime('%Y-%m-%d')})</h2>
<table><tr><th>Planet</th><th>Sign</th><th>House</th><th>SAV</th><th>Fav</th></tr>
{"".join(rows)}</table>"""
    except Exception:
        return ""


def _build_html(cd: ChartData, style: str) -> str:
    title = f"Jhora Chart Report — {cd.birth_date.strftime('%Y-%m-%d %H:%M')}"
    sections = [
        f"<h1>{title}</h1>",
        _meta(cd),
        '<div class="chart-grid">',
        _planet_table(cd),
        _house_table(cd),
        '</div>',
    ]
    if style in ("full", "detailed"):
        sections.extend([
            _shadbala_table(cd),
            _vimsottari_table(cd),
            _yogas_list(cd),
            _vimsopaka_table(cd),
            _transit_table(cd),
        ])

    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
{body}
<div class="footer">
  Generated by Jhora — Vedic Astrology Software |
  {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC
</div>
</body>
</html>"""
