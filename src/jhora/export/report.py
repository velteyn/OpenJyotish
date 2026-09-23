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
h3{color:#c0a040;margin-top:16px;margin-bottom:8px}
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
.chart-img{text-align:center;margin:12px 0}
.chart-img img{border:1px solid #2a3f5f;border-radius:6px}
@media print{body{background:#fff;color:#000}th{background:#eee;color:#000}tr:nth-child(even){background:#f5f5f5}}"""


def generate_chart_report(cd: ChartData, output_path: str,
                          style: str = "full") -> str:
    """Generate a complete HTML chart report and write to output_path."""
    html = _build_html(cd, style)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


def _meta(cd: ChartData) -> str:
    from jhora.export.traditional import (
        _panchanga_fields, _sunrise_sunset, _dasa_balance)
    lagna = Rasi.from_longitude(cd.ascendant)
    lat_hemi = "N" if cd.latitude >= 0 else "S"
    lon_hemi = "E" if cd.longitude >= 0 else "W"
    try:
        pg = _panchanga_fields(cd)
        panch = (f" | <strong>Tithi:</strong> {pg['tithi']} | "
                 f"<strong>Yoga:</strong> {pg['yoga']} | "
                 f"<strong>Karana:</strong> {pg['karana']}")
    except Exception:
        panch = ""
    try:
        sr, ss = _sunrise_sunset(cd)
        sun = f" | <strong>Sunrise:</strong> {sr} | <strong>Sunset:</strong> {ss}"
    except Exception:
        sun = ""
    try:
        lord, bal = _dasa_balance(cd)
        yrs, rem = int(bal), (bal - int(bal)) * 12
        dasa = (f" | <strong>Dasa balance:</strong> {lord.full_name} "
                f"{yrs}y {rem:.0f}m")
    except Exception:
        dasa = ""
    return f"""
<div class="meta">
  <strong>Birth:</strong> {cd.birth_date.strftime('%Y-%m-%d %H:%M')} |
  <strong>Location:</strong> {lat_hemi}, {lon_hemi} |
  <strong>Lagna:</strong> {lagna.full_name} {cd.ascendant:.1f}° |
  <strong>Ayanamsa:</strong> {cd.ayanamsa_name.title()}{panch}{sun}{dasa}
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


def _bhava_bala_table(cd: ChartData) -> str:
    try:
        bc = BhavaBalaComputer(cd)
        rows = []
        for h in range(1, 13):
            r = bc.compute(h)
            rows.append(
                f"<tr><td>{h}</td>"
                f"<td>{r.sthana:.1f}</td>"
                f"<td>{r.drishti:.1f}</td>"
                f"<td>{r.dig:.1f}</td>"
                f"<td>{r.adhipati:.1f}</td>"
                f"<td>{r.drig:.1f}</td>"
                f"<td>{r.total:.1f}</td></tr>"
            )
        return f"""<h2>Bhava Bala (House Strengths)</h2>
<table><tr><th>House</th><th>Sthana</th><th>Drishti</th><th>Dig</th>
<th>Adhipati</th><th>Drig</th><th>Total</th></tr>
{"".join(rows)}</table>"""
    except Exception:
        return ""


def _varga_strength_table(cd: ChartData) -> str:
    """Shadbala and Bhava Bala across every divisional chart."""
    try:
        from jhora.calc.bhava_bala import as_varga_chart
        from jhora.types.varga import VargaLevel

        planets = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                   Graha.JUPITER, Graha.VENUS, Graha.SATURN]
        head = "".join(f"<th>{g.short_name}</th>" for g in planets)
        rows = []
        for level in VargaLevel:
            vc = as_varga_chart(cd, level)
            sb = ShadbalaComputer(vc)
            cells = []
            for g in planets:
                v = sb.compute_one(g).total_virupa
                cls = "strength" if v > 400 else ("weak" if v < 300 else "")
                cells.append(f"<td class='{cls}'>{v:.0f}</td>")
            rows.append(f"<tr><td>{level.short_name}</td>{''.join(cells)}</tr>")
        shadbala = f"""<h3>Shadbala across vargas (total virupa)</h3>
<table><tr><th>Varga</th>{head}</tr>{"".join(rows)}</table>"""

        hh = "".join(f"<th>{h}</th>" for h in range(1, 13))
        rows = []
        for level in VargaLevel:
            bbr = BhavaBalaComputer(as_varga_chart(cd, level)).compute_all()
            cells = "".join(
                f"<td>{bbr.results[h].total:.0f}</td>" for h in range(1, 13))
            rows.append(f"<tr><td>{level.short_name}</td>{cells}</tr>")
        bhava = f"""<h3>Bhava Bala across vargas (total)</h3>
<table><tr><th>Varga</th>{hh}</tr>{"".join(rows)}</table>"""

        return ("<h2>Strength across Divisional Charts</h2>" + shadbala + bhava)
    except Exception:
        return ""


def _ashtakavarga_table(cd: ChartData) -> str:
    try:
        from jhora.export.traditional import _classical_bav
        bavs, sav = _classical_bav(cd)
        head = "".join(f"<th>{i}</th>" for i in range(1, 13))
        rows = []
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                  Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
            cells = "".join(f"<td>{v}</td>" for v in bavs[g])
            rows.append(f"<tr><td>{g.full_name}</td>{cells}</tr>")
        total = "".join(f"<td><strong>{v}</strong></td>" for v in sav)
        rows.append(f"<tr><td><strong>Total</strong></td>{total}</tr>")
        return f"""<h2>Ashtakavarga (SAV total {sum(sav)})</h2>
<table><tr><th>Planet</th>{head}</tr>
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


def _sahamas_table(cd: ChartData) -> str:
    try:
        from jhora.calc.sahama import compute_sahamas, is_day_birth
        from jhora.types.rasi import Rasi
        day = is_day_birth(cd)
        planets = {g: {"longitude": p.longitude}
                   for g, p in cd.planets.items()}
        rows = []
        asc_sign = int(cd.ascendant // 30) % 12
        for s in compute_sahamas(cd.ascendant, planets, day=day):
            sign = int(s.longitude // 30) % 12
            house = (sign - asc_sign) % 12 + 1
            rows.append(
                f"<tr><td>{s.name}</td><td>{s.meaning}</td>"
                f"<td>{s.longitude:.2f}°</td>"
                f"<td>{Rasi(sign).full_name}</td><td>{house}</td></tr>"
            )
        basis = "day" if day else "night"
        return f"""<h2>Sahamas (36, {basis} birth)</h2>
<table><tr><th>Sahama</th><th>Meaning</th><th>Longitude</th>
<th>Sign</th><th>House</th></tr>
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
            vedha = (f"H{e.vedha_house} obstructs" if e.is_vedha
                     else (f"H{e.vedha_house}" if e.vedha_house else "—"))
            rows.append(
                f"<tr><td>{e.graha.full_name if hasattr(e.graha,'full_name') else e.graha.short_name}</td>"
                f"<td>{e.transit_rasi_name}</td>"
                f"<td>H{e.house_from_lagna}</td>"
                f"<td>H{e.house_from_moon}</td>"
                f"<td>{e.sav_score}</td>"
                f"<td>{fav}</td>"
                f"<td>{vedha}</td></tr>"
            )
        return f"""<h2>Current Transits ({now.strftime('%Y-%m-%d')})</h2>
<table><tr><th>Planet</th><th>Sign</th><th>House</th><th>From Moon</th><th>SAV</th><th>Fav</th><th>Vedha</th></tr>
{"".join(rows)}</table>"""
    except Exception:
        return ""


def _sade_sati_table(cd: ChartData) -> str:
    try:
        from datetime import date as _date

        from jhora.calc.gochara import sade_sati_timeline
        moon_rasi = int(cd.planet(Graha.MOON).longitude / 30)
        phases = sade_sati_timeline(
            moon_rasi, getattr(cd, "ayanamsa_name", "lahiri"))
        today = _date.today()
        rows = []
        for p in phases:
            now_mark = "← now" if p.start <= today <= p.end else ""
            start_s = f"~{p.start}" if not p.start_exact else str(p.start)
            end_s = f"~{p.end}" if not p.end_exact else str(p.end)
            rows.append(
                f"<tr><td>{p.kind}</td><td>{p.phase}</td>"
                f"<td>{Rasi(p.sign).short_name}</td>"
                f"<td>{start_s}</td><td>{end_s}</td>"
                f"<td>{now_mark}</td></tr>"
            )
        if not rows:
            return ""
        return f"""<h2>Sade Sati Timeline (dates are UTC)</h2>
<table><tr><th>Kind</th><th>Phase</th><th>Saturn in</th><th>Start</th><th>End</th><th>Now</th></tr>
{"".join(rows)}</table>"""
    except Exception:
        return ""


def _special_lagnas_table(cd: ChartData) -> str:
    try:
        from jhora.calc.special_lagnas import compute_special_lagnas
        rows = []
        for l in compute_special_lagnas(cd):
            rows.append(
                f"<tr><td>{l.name}</td><td>{l.longitude:.2f}&deg;</td>"
                f"<td>{l.sign}</td><td>{l.description}</td></tr>"
            )
        return f"""<h2>Special Lagnas</h2>
<table><tr><th>Lagna</th><th>Longitude</th><th>Sign</th><th>Meaning</th></tr>
{"".join(rows)}</table>"""
    except Exception:
        return ""


def _arudha_pada_table(cd: ChartData) -> str:
    try:
        from jhora.calc.arudha import (
            all_bhava_arudhas, all_graha_arudhas, bhava_pada_name,
            graha_pada_name)
        planets = {g: {"longitude": p.longitude}
                   for g, p in cd.planets.items()}
        bhava = all_bhava_arudhas(cd.ascendant, planets)
        rows = []
        for n in range(1, 13):
            alias = ""
            if n == 7:
                alias = " (Darapada)"
            elif n == 12:
                alias = " (Upapada)"
            elif n == 1:
                alias = " (AL)"
            rows.append(
                f"<tr><td>A{n}</td><td>{bhava_pada_name(n)}{alias}</td>"
                f"<td>{bhava[n].full_name}</td></tr>"
            )
        graha_rows = []
        for g, r in all_graha_arudhas(planets).items():
            graha_rows.append(
                f"<tr><td>{g.full_name if hasattr(g, 'full_name') else g}</td>"
                f"<td>{graha_pada_name(g)}</td><td>{r.full_name}</td></tr>"
            )
        return f"""<h2>Arudha Padas</h2>
<table><tr><th>Pada</th><th>Classical name</th><th>Sign</th></tr>
{"".join(rows)}</table>
<h3>Graha Padas</h3>
<table><tr><th>Planet</th><th>Pada</th><th>Sign</th></tr>
{"".join(graha_rows)}</table>"""
    except Exception:
        return ""


def _karaka_table(cd: ChartData) -> str:
    try:
        from jhora.calc.karaka import compute_chara_karakas
        from jhora.types.rasi import Rasi
        planets = {g: {"longitude": p.longitude, "speed": p.speed}
                   for g, p in cd.planets.items()}
        rows = []
        for k in compute_chara_karakas(planets):
            sign = Rasi.from_longitude(k.longitude).full_name
            rows.append(
                f"<tr><td>{k.short_name}</td><td>{k.full_name}</td>"
                f"<td>{k.graha.full_name}</td><td>{sign}</td>"
                f"<td>{k.meaning}</td></tr>"
            )
        return f"""<h2>Chara Karakas</h2>
<table><tr><th>Karaka</th><th>Name</th><th>Planet</th><th>Sign</th>
<th>Signifies</th></tr>
{"".join(rows)}</table>"""
    except Exception:
        return ""


def _kp_table(cd: ChartData) -> str:
    try:
        from jhora.calc.kp import KPComputer
        kpc = KPComputer(cd).compute()
        cusp_rows = []
        for c in kpc.cusps:
            cusp_rows.append(
                f"<tr><td>{c.house}</td><td>{c.longitude:.2f}&deg;</td>"
                f"<td>{c.sign.short_name}</td>"
                f"<td>{c.chain.sign_lord.short_name}</td>"
                f"<td>{c.chain.star_lord.short_name}</td>"
                f"<td>{c.chain.sub_lord.short_name}</td>"
                f"<td>{c.chain.sub_sub_lord.short_name}</td></tr>"
            )
        planet_rows = []
        for p in kpc.planets:
            planet_rows.append(
                f"<tr><td>{p.graha.full_name}</td><td>{p.house}</td>"
                f"<td>{p.sign.short_name}</td>"
                f"<td>{p.chain.star_lord.short_name}</td>"
                f"<td>{p.chain.sub_lord.short_name}</td>"
                f"<td>{p.chain.sub_sub_lord.short_name}</td></tr>"
            )
        rp = ", ".join(f"{r.graha.full_name} ({r.role_string})"
                       for r in kpc.ruling_planets)
        return f"""<h2>KP ({kpc.cusp_system}, ayanamsa: {kpc.ayanamsa})</h2>
<table><tr><th>House</th><th>Cusp</th><th>Sign</th><th>Sign Lord</th>
<th>Star Lord</th><th>Sub Lord</th><th>Sub-Sub</th></tr>
{"".join(cusp_rows)}</table>
<h3>KP Planets</h3>
<table><tr><th>Planet</th><th>House</th><th>Sign</th><th>Star Lord</th>
<th>Sub Lord</th><th>Sub-Sub</th></tr>
{"".join(planet_rows)}</table>
<p><strong>Ruling Planets:</strong> {rp}</p>"""
    except Exception:
        return ""


def _chalit_table(cd: ChartData) -> str:
    try:
        from jhora.calc.chalit import ChalitComputer
        chalit = ChalitComputer(cd).compute()
        rows = []
        for e in chalit.entries:
            moved = ' class="moved"' if e.moved else ""
            marker = "&#8592; MOVED" if e.moved else ""
            rows.append(
                f"<tr><td>{e.graha.short_name}</td><td>{e.sign}</td>"
                f"<td>{e.sign_house}</td>"
                f"<td{moved}>{e.cusp_house}</td>"
                f"<td{moved}>{marker}</td></tr>"
            )
        return f"""<h2>Chalit (Bhava) Shifts</h2>
<table><tr><th>Planet</th><th>Sign</th><th>Sign H</th><th>Cusp H</th>
<th>Shift</th></tr>
{"".join(rows)}</table>"""
    except Exception:
        return ""


def _dwadasa_vargeeya_table(cd: ChartData) -> str:
    try:
        from jhora.calc.vimsopaka import VimsopakaComputer, VimsopakaScheme
        vc = VimsopakaComputer(cd)
        results = sorted(vc.compute_all(VimsopakaScheme.DWADASAVARGA),
                         key=lambda r: r.total, reverse=True)
        rows = "".join(
            f"<tr><td>{r.graha.full_name}</td><td>{r.total:.1f}/20</td>"
            f"<td>{r.percentage:.0f}%</td></tr>"
            for r in results
        )
        return f"""<h2>Dwadasa Vargeeya Bala (12 vargas)</h2>
<table><tr><th>Planet</th><th>Score</th><th>%</th></tr>{rows}</table>"""
    except Exception:
        return ""


def _remedies_table(cd: ChartData) -> str:
    try:
        from jhora.calc.remedies import compute_remedies
        rep = compute_remedies(cd)
    except Exception:
        return ""
    rows = "".join(
        f"<tr><td>{it.category}</td><td>{it.title}</td>"
        f"<td>{it.detail}</td><td>{it.source}</td></tr>"
        for it in rep.items)
    return (f"""<h2>Remedies</h2>
<p><b>Ishta Devata:</b> {rep.ishta_devata.title} ({rep.ishta_devata.detail})<br>
<b>Palana Devata:</b> {rep.palana_devata.title} ({rep.palana_devata.detail})</p>
<table><tr><th>Category</th><th>Remedy</th><th>Detail</th><th>Source</th></tr>
{rows}</table>""")


def _ishta_kashta_table(cd: ChartData) -> str:
    try:
        from jhora.calc.learning import ishta_kashta_phala
        rows = "".join(
            f"<tr><td>{r['graha']}</td><td>{r['ishta']:.0f}</td>"
            f"<td>{r['kashta']:.0f}</td></tr>"
            for r in ishta_kashta_phala(cd)
        )
        return f"""<h2>Ishta / Kashta Phala</h2>
<table><tr><th>Planet</th><th>Ishta</th><th>Kashta</th></tr>{rows}</table>"""
    except Exception:
        return ""


def _chart_images_html(cd: ChartData) -> str:
    """Render Lagna (D-1) and true Navamsa (D-9) charts and return HTML."""
    import base64
    from PyQt6.QtCore import QBuffer, QIODevice
    from jhora.export.traditional import (
        render_chart_card, _chart_occupants, _navamsa_occupants)
    from jhora.types.rasi import Rasi

    pairs = [
        ("Lagna (D-1)", Rasi.from_longitude(cd.ascendant),
         _chart_occupants(cd)),
        ("Navamsa (D-9)", *_navamsa_occupants(cd)),
    ]

    imgs_html = []
    for label, lagna_rasi, houses in pairs:
        img = render_chart_card(lagna_rasi, houses, size=420, dark=True)
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(buf, "PNG")
        b64 = base64.b64encode(buf.data().data()).decode("ascii")
        buf.close()
        imgs_html.append(
            f'<div class="chart-img">'
            f'<h3>{label}</h3>'
            f'<img src="data:image/png;base64,{b64}" width="420" height="420">'
            f'</div>'
        )

    return (
        '<div class="chart-grid">\n'
        + "\n".join(imgs_html)
        + '\n</div>'
    )


def _build_html(cd: ChartData, style: str) -> str:
    title = f"OpenJyotish Chart Report — {cd.birth_date.strftime('%Y-%m-%d %H:%M')}"
    sections = [
        f"<h1>{title}</h1>",
        _meta(cd),
        _chart_images_html(cd),
        _planet_table(cd),
        _house_table(cd),
        _kp_table(cd),
    ]
    if style in ("full", "detailed"):
        sections.extend([
            _shadbala_table(cd),
            _bhava_bala_table(cd),
            _varga_strength_table(cd),
            _ashtakavarga_table(cd),
            _vimsottari_table(cd),
            _yogas_list(cd),
            _sahamas_table(cd),
            _vimsopaka_table(cd),
            _transit_table(cd),
            _sade_sati_table(cd),
            _special_lagnas_table(cd),
            _arudha_pada_table(cd),
            _karaka_table(cd),
            _chalit_table(cd),
            _dwadasa_vargeeya_table(cd),
            _ishta_kashta_table(cd),
            _remedies_table(cd),
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
  Generated by OpenJyotish — Vedic Astrology Software |
  {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC
</div>
</body>
</html>"""
