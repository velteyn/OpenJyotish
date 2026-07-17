"""
jhora CLI — Typer-based command-line interface.

Usage:
    jhora chart "1970-04-04 17:48:20 +0530 13.08 80.27"
    jhora dasa "1970-04-04 17:48:20 +0530 13.08 80.27" vimsottari
    jhora panchanga 2024-06-21 12:00 13.08 80.27
"""

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.charts.varga import VargaChartComputer, VargaChartData, get_variants_for_level
from jhora.calc.shadbala import ShadbalaComputer
from jhora.calc.bhava_bala import BhavaBalaComputer
from jhora.calc.vimsopaka import VimsopakaComputer, VimsopakaScheme
from jhora.ai.engine import AiEngine, AiConfig, PROVIDERS
from jhora.calc.mundane import MundaneCalculator, MUNDANE_HOUSES
from jhora.calc.tithi_pravesha import TithiPraveshaCalculator
from jhora.calc.chalit import ChalitComputer
from jhora.export.report import generate_chart_report
from jhora.calc.ephemeris import generate_ephemeris
from jhora.calc.comparison import compare_natal_transit
from jhora.calc.dasa_timeline import dasa_timeline_text
from jhora.calc.upagraha import compute_solar_upagrahas
from jhora.ai.json_export import full_analysis
from jhora.dasas.vimsottari import VimsottariDasa
from jhora.ephemeris.swe import SweEngine
from jhora.interpreter.engine import ChartInterpreter
from jhora.interpreter.knowledge_base import KnowledgeBase
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.dasa import DasaSystem
from jhora.types.varga import VargaLevel, VargaVariant
from jhora.calc.ashtakavarga import (
    all_bhinna_ashtakavarga, sarva_ashtakavarga, sodhya_pinda,
    kakshya_bindu_table, all_kakshya_tables,
    _OCCUPANT_GRAHAS,
)

app = typer.Typer(name="jhora", help="OpenJyotish — Vedic astrology calculator")
console = Console()

DEFAULT_AYANAMSA = "lahiri"


def parse_birthdata(input_str: str) -> dict:
    """Parse birth data string.
    
    Formats:
        "1970-04-04 17:48:20 +0530 13.08 80.27"
        "1970-04-04 17:48:20 Asia/Kolkata Chennai"
    """
    parts = input_str.strip().split()
    date_str = parts[0]
    time_str = parts[1]
    date = datetime.strptime(date_str, "%Y-%m-%d")
    time_parts = time_str.split(":")
    hour = int(time_parts[0]) + int(time_parts[1]) / 60.0 + (int(time_parts[2]) / 3600.0 if len(time_parts) > 2 else 0)
    tz_str = parts[2]
    lat = float(parts[3])
    lon = float(parts[4])
    return {
        "year": date.year, "month": date.month, "day": date.day,
        "hour": hour, "lat": lat, "lon": lon, "tz": tz_str,
    }


@app.command()
def chart(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    chalit: bool = typer.Option(False, "--chalit", help="Show Bhava/Chalit house positions"),
):
    """Compute and display birth chart."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    chart_data = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    _display_chart(chart_data)
    _display_chart_yogas(chart_data)
    if chalit:
        _display_chalit(chart_data)


@app.command()
def analyze(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """AI-friendly JSON dump — all computed data in one structured output."""
    import json
    data = full_analysis(birthdata, ayanamsa)
    print(json.dumps(data, indent=2, ensure_ascii=False))


@app.command()
def dasa(
    birthdata: str = typer.Argument(..., help="Birth data"),
    system: str = typer.Argument("vimsottari", help="Dasa system"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Compute dasa periods for a chart."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    chart_data = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    chart_dict = _chart_to_dict(chart_data)
    if system == "vimsottari":
        engine = VimsottariDasa()
        periods = engine.compute(chart_data.julian_day, chart_dict)
        _display_dasa_table(periods, "Vimsottari Dasa Periods")
    elif system == "ashtottari":
        from jhora.dasas.ashtottari import AshtottariDasa
        engine = AshtottariDasa()
        periods = engine.compute(chart_data.julian_day, chart_dict)
        _display_dasa_table(periods, "Ashtottari Dasa Periods")


@app.command()
def navamsa(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    variant: str = typer.Option("default", "--variant", "-v", help="Variant: default, k, km, ukm"),
):
    """Display Navamsa (D-9) chart."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    chart_data = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    comp = VargaChartComputer()
    var = _parse_variant(variant)
    vcd = comp.compute(chart_data, VargaLevel.D_9, var)
    _display_varga(vcd, title=f"Navamsa (D-9) — {_variant_label(var)}")


@app.command()
def varga(
    birthdata: str = typer.Argument(None, help="Birth data (not needed with --list)"),
    level: str = typer.Argument("D-9", help="Varga level: D-1..D-150 or name (navamsa, dasamsa, etc.)"),
    variant: str = typer.Option("default", "--variant", "-v", help="Variant name (default, rev, trd, pv, k, etc.)"),
    list_levels: bool = typer.Option(False, "--list", "-l", help="List all available varga levels and variants"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Compute any divisional chart (varga)."""
    if list_levels:
        _list_varga_levels()
        return

    if not birthdata:
        console.print("[red]BIRTHDATA is required without --list[/red]")
        raise typer.Exit(1)
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    chart_data = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )

    vl = _parse_varga_level(level)
    var = _parse_variant(variant)

    comp = VargaChartComputer()
    vcd = comp.compute(chart_data, vl, var)
    _display_varga(vcd, title=f"{vl.full_name} ({vl.short_name}) — {_variant_label(var)}")


def _display_chart(cd: ChartData):
    """Display chart in terminal."""
    table = Table(title="Rasi Chart (D-1)")
    table.add_column("Planet", style="cyan")
    table.add_column("Longitude", style="green")
    table.add_column("Rasi", style="yellow")
    table.add_column("Degrees", style="white")
    table.add_column("Nakshatra", style="magenta")
    table.add_column("Pada", style="white")
    table.add_column("Dignity", style="blue")

    for g in Graha:
        if g in cd.planets:
            p = cd.planets[g]
            table.add_row(
                g.full_name, f"{p.longitude:.2f}",
                p.rasi_name, f"{p.degrees_in_rasi:.2f}",
                p.nakshatra_name, str(p.nakshatra_pada),
                p.dignity,
            )
    table.add_row(
        "Lagna", f"{cd.ascendant:.2f}",
        cd.lagna.rasi_name, f"{cd.lagna.degrees_in_rasi:.2f}",
        cd.lagna.nakshatra_name, str(cd.lagna.nakshatra_pada),
        "",
    )
    console.print(table)

    # Upagrahas
    sun_lon = cd.planet(Graha.SUN).longitude
    upas = compute_solar_upagrahas(sun_lon)
    if upas:
        ut = Table(title="Solar Upagrahas")
        ut.add_column("Name", style="yellow")
        ut.add_column("Longitude", style="cyan")
        ut.add_column("Sign", style="green")
        for u in upas:
            ut.add_row(u.name, f"{u.longitude:.2f}°", u.rasi)
        console.print(ut)

    # Outer planets
    if cd.outer_planets:
        ot = Table(title="Outer Planets")
        ot.add_column("Planet", style="yellow")
        ot.add_column("Longitude", style="cyan")
        ot.add_column("Sign", style="green")
        ot.add_column("Motion", style="white")
        for name, data in cd.outer_planets.items():
            ot.add_row(name, f"{data['longitude']:.2f}°", data["sign"],
                      "Retrograde" if data["is_retrograde"] else "")
        console.print(ot)


def _lord_name(idx: int) -> str:
    """Convert Graha ID to full name."""
    try:
        return Graha(idx).full_name
    except ValueError:
        return str(idx)


def _display_chalit(cd: ChartData):
    cc = ChalitComputer(cd)
    for vl in [VargaLevel.D_1, VargaLevel.D_9]:
        r = cc.compute(vl)
        table = Table(title=f"{vl.name} Chalit Chakra — Bhava (cusp) vs Rasi (sign)")
        table.add_column("Planet", style="cyan")
        table.add_column("Sign", style="yellow")
        table.add_column("Sign H", justify="right")
        table.add_column("Cusp H", justify="right", style="green")
        table.add_column("Shift", style="red")
        for e in r.entries:
            marker = "← MOVED" if e.moved else ""
            table.add_row(e.graha.short_name, e.sign,
                         str(e.sign_house), str(e.cusp_house), marker)
        if r.moved_planets:
            moved = ", ".join(f"{e.graha.short_name}(H{e.sign_house}→H{e.cusp_house})"
                             for e in r.moved_planets)
            table.caption = f"Planets that shifted houses: {moved}"
        console.print(table)
        console.print()


def _display_dasa_table(periods, title: str = "Dasa Periods"):
    """Display dasa periods in a table."""
    table = Table(title=title)
    table.add_column("Lord", style="cyan")
    table.add_column("Start", style="green")
    table.add_column("End", style="yellow")
    table.add_column("Years", style="white")

    for md in periods:
        from jhora.ephemeris.swe import SweEngine
        se = SweEngine()
        y1, m1, d1, _ = se.revjul(md.start_jd)
        y2, m2, d2, _ = se.revjul(md.end_jd)
        table.add_row(
            _lord_name(int(md.lord_index)),
            f"{int(y1)}/{int(m1):02d}/{int(d1):02d}",
            f"{int(y2)}/{int(m2):02d}/{int(d2):02d}",
            f"{md.duration_years:.2f}",
        )
    console.print(table)


def _chart_to_dict(cd: ChartData) -> dict:
    """Convert ChartData to dict for dasa computation."""
    planets = {}
    for g, p in cd.planets.items():
        planets[g] = {"longitude": p.longitude, "speed": p.speed}
    return {"planets": planets, "lagna_lon": cd.ascendant}


@app.command()
def interpret(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search book knowledge base"),
):
    """Generate chart interpretation / reading."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    interpreter = ChartInterpreter()

    if search:
        results = interpreter.search_knowledge(search)
        console.print(f"[bold cyan]Knowledge Base: {search}[/bold cyan]")
        if not results:
            console.print("  No matches found.")
        for r in results:
            console.print(f"  [yellow]{r['source']}[/yellow]")
            console.print(f"  [dim]{r['excerpt'][:200]}...[/dim]")
            console.print()
        return

    reading = interpreter.interpret_text(cd)
    console.print("[bold cyan]Chart Reading[/bold cyan]")
    console.print(reading)


@app.command()
def knowledge(
    query: str = typer.Argument(..., help="Search query"),
    max_results: int = typer.Option(5, "--max", "-n"),
):
    """Search the Vedic astrology book/PDF knowledge base."""
    kb = KnowledgeBase()
    console.print(f"[bold cyan]Knowledge Base — {kb.loaded} sources[/bold cyan]")
    results = kb.search(query, max_results=max_results)
    if not results:
        console.print("  No matches found.")
        return
    for i, r in enumerate(results, 1):
        console.print(f"\n[bold yellow]{i}. {r['source']}[/bold yellow]")
        console.print(f"  {r['excerpt'][:300]}...")


@app.command()
def yogas(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Detect planetary yogas (combinations) in a chart."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    from jhora.calc.yogas import detect_all
    results = detect_all(cd)
    if not results:
        console.print("[yellow]No major yogas detected.[/yellow]")
        return
    table = Table(title=f"Yogas Detected ({len(results)})")
    table.add_column("Yoga", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Planets", style="yellow")
    table.add_column("Strength", style="white")
    table.add_column("Description", style="dim")
    for y in results:
        names = ", ".join(p.full_name for p in y.planets) if y.planets else ""
        table.add_row(y.name, y.category, names, y.strength, y.description)
    console.print(table)


@app.command()
def lagnas(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Show all special lagnas (Bhrigu Bindu, Indu, Varnada, etc.)."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)

    from jhora.calc.special_lagnas import compute_special_lagnas, SpecialLagna
    lagnas = compute_special_lagnas(cd)

    # Also add built-in lagnas
    if cd.hora_lagna:
        lr = Rasi.from_longitude(cd.hora_lagna.longitude)
        lagnas.insert(0, SpecialLagna("Hora Lagna", cd.hora_lagna.longitude, lr.short_name, "Wealth/time"))
    if cd.ghati_lagna:
        lr = Rasi.from_longitude(cd.ghati_lagna.longitude)
        lagnas.insert(0, SpecialLagna("Ghati Lagna", cd.ghati_lagna.longitude, lr.short_name, "Power"))
    if cd.bhava_lagna:
        lr = Rasi.from_longitude(cd.bhava_lagna.longitude)
        lagnas.insert(0, SpecialLagna("Bhava Lagna", cd.bhava_lagna.longitude, lr.short_name, "House-based"))
    if cd.sree_lagna:
        lr = Rasi.from_longitude(cd.sree_lagna.longitude)
        lagnas.insert(0, SpecialLagna("Sree Lagna", cd.sree_lagna.longitude, lr.short_name, "Prosperity"))
    lr = Rasi.from_longitude(cd.ascendant)
    lagnas.insert(0, SpecialLagna("Udaya Lagna", cd.ascendant, lr.short_name, "Ascendant"))

    table = Table(title="Special Lagnas")
    table.add_column("Lagna", style="cyan")
    table.add_column("Longitude", style="green")
    table.add_column("Sign", style="yellow")
    table.add_column("Meaning", style="white")
    for s in lagnas:
        table.add_row(s.name, f"{s.longitude:.2f}°", s.sign, s.description)
    console.print(table)


@app.command()
def learning(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Show learning aids: marana karaka, vaiseshikamsas, relationships."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)

    # Marana Karaka
    from jhora.calc.learning import marana_karaka_sthana as _mk
    mk = _mk(cd)
    if mk:
        table = Table(title="Marana Karaka Sthana (death-inflicting positions)")
        table.add_column("Planet", style="red")
        table.add_column("House", style="white")
        table.add_column("Sign", style="yellow")
        for m in mk:
            table.add_row(m["graha"], str(m["house"]), m["sign"])
        console.print(table)

    # Vaiseshikamsas
    from jhora.calc.learning import vaiseshikamsas as _va
    va = _va(cd)
    table = Table(title="Vaiseshikamsas (Dignity Ranks from Vimsopaka)")
    table.add_column("Planet", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Rank", style="yellow bold")
    for v in va:
        table.add_row(v["graha"], f"{v['score']:.1f}/20", v["rank"])
    console.print(table)

    # Ishta/Kashta
    from jhora.calc.learning import ishta_kashta_phala as _ik
    ik = _ik(cd)
    table = Table(title="Ishta/Kashta Phala (Beneficence vs Difficulty)")
    table.add_column("Planet", style="cyan")
    table.add_column("Ishta", style="green")
    table.add_column("Kashta", style="red")
    for r in ik:
        table.add_row(r["graha"], f"{r['ishta']:.0f}", f"{r['kashta']:.0f}")
    console.print(table)

    # KP sub-lords
    from jhora.calc.special_lagnas import kp_sublord_string as _kp
    table = Table(title="KP Sub-Lords (Krishnamoorthy Paddhati)")
    table.add_column("Point", style="cyan")
    table.add_column("Longitude", style="green")
    table.add_column("Sub-Lord Chain", style="yellow")
    for g in Graha:
        if g in cd.planets:
            p = cd.planets[g]
            chain = _kp(p.longitude, 3)
            table.add_row(g.full_name, f"{p.longitude:.2f}°", chain)
    lagna_c = _kp(cd.ascendant, 3)
    table.add_row("Lagna", f"{cd.ascendant:.2f}°", lagna_c)
    console.print(table)


@app.command()
def panchanga(
    year: int = typer.Argument(None, help="Year (default: current)"),
    month: int = typer.Argument(None, help="Month (default: current)"),
    lat: float = typer.Option(28.61, "--lat", help="Latitude"),
    lon: float = typer.Option(77.21, "--lon", help="Longitude"),
):
    """Monthly panchanga calendar — tithi, nakshatra, yoga, karana per day."""
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month

    from jhora.calc.monthly_panchanga import monthly_panchanga
    days = monthly_panchanga(year, month, lat, lon)
    table = Table(title=f"Panchanga — {year}-{month:02d}")
    table.add_column("Date", style="cyan")
    table.add_column("Day", style="white")
    table.add_column("Tithi", style="yellow")
    table.add_column("Nakshatra", style="magenta")
    table.add_column("Moon", style="green")
    table.add_column("Sunrise", style="white")
    table.add_column("Rahu Kalam", style="red")
    for d in days:
        table.add_row(d.date, d.weekday, d.tithi, d.nakshatra,
                     d.moon_sign, d.sunrise, d.rahu_kalam)
    console.print(table)


@app.command()
def chakras(
    nak: int = typer.Option(None, "--nakshatra", "-n", help="Target nakshatra (0-26)"),
):
    """Display Sarvatobhadra and Kota chakras."""
    from jhora.calc.chakras import sarvatobhadra_text, kota_chakra, sarvatobhadra_vedha
    console.print(sarvatobhadra_text())
    if nak is not None:
        console.print()
        console.print(kota_chakra(nak))
        console.print()
        vedha = sarvatobhadra_vedha(nak)
        t = Table(title=f"Vedha for nak {nak}")
        t.add_column("Direction")
        t.add_column("Nakshatra")
        for v in vedha:
            t.add_row(v["direction"], v["name"])
        console.print(t)


@app.command()
def conditional_dasas(
    birthdata: str = typer.Argument(None, help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """List which conditional dasas apply to a chart."""
    if not birthdata:
        console.print("[yellow]List of conditional dasa systems:[/yellow]")
        from jhora.dasas.conditional import ALL_CONDITIONAL
        for key, d in ALL_CONDITIONAL.items():
            console.print(f"  [cyan]{key}[/cyan]: {d.name} ({d.total_years} years)")
        console.print("\n[yellow]Pass birth data to check applicability:[/yellow]")
        return
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)
    from jhora.dasas.conditional import list_applicable
    applicable = list_applicable(cd)
    console.print(f"[green]{len(applicable)} conditional dasas apply:[/green]")
    for d in applicable:
        console.print(f"  [cyan]{d['name']}[/cyan]: {d['full_name']} ({d['total_years']} years)")


@app.command()
def ephemeris(
    start: str = typer.Argument(..., help="Start date: YYYY-MM-DD"),
    end: str = typer.Argument(None, help="End date (default: +30 days)"),
    step: int = typer.Option(7, "--step", "-s", help="Days between entries"),
):
    """Generate daily planet positions for a date range."""
    from datetime import datetime as dt
    start_dt = dt.strptime(start, "%Y-%m-%d")
    if end:
        end_dt = dt.strptime(end, "%Y-%m-%d")
    else:
        from datetime import timedelta
        end_dt = start_dt + timedelta(days=30)

    entries = generate_ephemeris(start_dt, end_dt, step)
    table = Table(title=f"Ephemeris: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')} (every {step}d)")
    table.add_column("Date", style="cyan")
    for g in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]:
        table.add_column(g, style="yellow")
    for e in entries:
        row = [e.date.strftime("%Y-%m-%d")]
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                  Graha.JUPITER, Graha.VENUS, Graha.SATURN,
                  Graha.RAHU, Graha.KETU]:
            p = e.planets.get(g, {})
            row.append(f"{p.get('sign', '?')} {p.get('longitude', 0):.0f}°")
        table.add_row(*row)
    console.print(table)


@app.command()
def compare(
    chart1: str = typer.Argument(..., help="First chart data"),
    chart2: str = typer.Argument(None, help="Second chart (or 'transit' for current transit)"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Compare two charts or natal vs transit."""
    from jhora.calc.comparison import compare_two_charts, compare_natal_transit
    bd1 = parse_birthdata(chart1)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd1 = builder.build(year=bd1["year"], month=bd1["month"], day=bd1["day"],
                        hour=bd1["hour"], lat=bd1["lat"], lon=bd1["lon"],
                        tz=bd1["tz"], ayanamsa=ayanamsa)

    if chart2 is None or chart2 == "transit":
        entries = compare_natal_transit(cd1)
        table = Table(title="Natal vs Current Transit Comparison")
        table.add_column("Planet", style="cyan")
        table.add_column("Natal", style="yellow")
        table.add_column("Transit", style="green")
        table.add_column("SAV", style="white")
        table.add_column("Fav")
        for e in entries:
            fav = "✓" if e.is_favorable else "✗"
            table.add_row(e.graha.short_name,
                         f"{e.natal_sign} H{e.natal_house}",
                         f"{e.transit_sign} H{e.transit_house}",
                         str(e.sav_score), fav)
        console.print(table)
    else:
        bd2 = parse_birthdata(chart2)
        cd2 = builder.build(year=bd2["year"], month=bd2["month"], day=bd2["day"],
                            hour=bd2["hour"], lat=bd2["lat"], lon=bd2["lon"],
                            tz=bd2["tz"], ayanamsa=ayanamsa)
        comp = compare_two_charts(cd1, cd2, "Chart 1", "Chart 2")
        table = Table(title=f"{comp.chart1_name} vs {comp.chart2_name}")
        table.add_column("Planet", style="cyan")
        table.add_column("Chart 1", style="yellow")
        table.add_column("Chart 2", style="green")
        table.add_column("Δ")
        for e in comp.entries:
            m = "→" if e["moved"] else ""
            table.add_row(e["graha"], f"{e['sign1']} {e['lon1']:.0f}°",
                         f"{e['sign2']} {e['lon2']:.0f}°", m)
        console.print(table)


@app.command()
def dasa_timeline(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Display Vimsottari dasa timeline as text visualization."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)
    text = dasa_timeline_text(cd)
    console.print(text)


@app.command()
def export(
    birthdata: str = typer.Argument(..., help="Birth data"),
    output: str = typer.Option("chart_report.html", "--output", "-o", help="Output file path"),
    style: str = typer.Option("full", "--style", "-s", help="full or compact"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Export chart as styled HTML report."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    path = generate_chart_report(cd, output, style)
    console.print(f"[green]Report saved: {path}[/green]")


@app.command()
def gui():
    """Launch the graphical user interface."""
    from PyQt6.QtWidgets import QApplication
    from jhora.ui.main_window import MainWindow

    import sys
    qapp = QApplication(sys.argv)
    qapp.setApplicationName("OpenJyotish")
    qapp.setStyle("Fusion")
    window = MainWindow()
    window.showMaximized()
    qapp.exec()


@app.command()
def shadbala(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    bhava: bool = typer.Option(False, "--bhava", "-b", help="Show Bhava Bala (house strengths)"),
    vimsopaka: bool = typer.Option(False, "--vimsopaka", "-v",
                                   help="Show Vimsopaka Bala (varga-weighted strength)"),
    scheme: str = typer.Option("shadvarga", "--scheme",
                               help="Vimsopaka scheme: shadvarga, saptavarga, dashavarga, shodasavarga"),
):
    """Compute Shadbala (six-fold planetary strength) or Bhava Bala (house strength)."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    comp = ShadbalaComputer(cd)
    results = comp.compute()

    table = Table(title="Shadbala — Planetary Strengths")
    table.add_column("Planet", style="cyan")
    table.add_column("Sthana", style="yellow")
    table.add_column("Dig", style="yellow")
    table.add_column("Kala", style="yellow")
    table.add_column("Chesta", style="yellow")
    table.add_column("Naisarg", style="yellow")
    table.add_column("Drik", style="yellow")
    table.add_column("Total (R)", style="green bold")
    table.add_column("Total (V)", style="white")

    planets_order = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                     Graha.JUPITER, Graha.VENUS, Graha.SATURN]
    for g in planets_order:
        if g not in results:
            continue
        r = results[g]
        table.add_row(
            r.graha.full_name,
            f"{r.sthana_total/60:.2f}",
            f"{r.dig_total/60:.2f}",
            f"{r.kala_total/60:.2f}",
            f"{r.chesta_total/60:.2f}",
            f"{r.naisargika.rupa:.2f}",
            f"{r.drik.rupa:.2f}",
            f"{r.total_rupa:.2f}",
            f"{r.total_virupa:.0f}",
        )
    console.print(table)

    if bhava:
        console.print()
        _print_bhava_bala(cd)

    if vimsopaka:
        console.print()
        _print_vimsopaka(cd, scheme)


def _print_bhava_bala(cd):
    from jhora.types.rasi import Rasi
    bb = BhavaBalaComputer(cd)
    report = bb.compute_all()
    table = Table(title="Bhava Bala — House Strengths")
    table.add_column("H", style="cyan")
    table.add_column("Sign", style="yellow")
    table.add_column("Lord", style="yellow")
    table.add_column("Sthana", style="green")
    table.add_column("Drishti", style="green")
    table.add_column("Dig", style="green")
    table.add_column("Adhip", style="green")
    table.add_column("Drig", style="green")
    table.add_column("Total", style="white bold")
    for h in range(1, 13):
        r = report.results[h]
        rasi_idx = (int(cd.ascendant / 30) + h - 1) % 12
        table.add_row(
            str(h), Rasi(rasi_idx).short_name, Rasi(rasi_idx).lord,
            f"{r.sthana:.1f}", f"{r.drishti:.1f}", f"{r.dig:.1f}",
            f"{r.adhipati:.1f}", f"{r.drig:+.1f}", f"{r.total:.1f}",
        )
    console.print(table)


def _print_vimsopaka(cd, scheme_name: str = "shadvarga"):
    scheme_map = {s.value: s for s in VimsopakaScheme}
    scheme = scheme_map.get(scheme_name, VimsopakaScheme.SHADVARGA)
    vc = VimsopakaComputer(cd)
    results = sorted(vc.compute_all(scheme), key=lambda r: r.total, reverse=True)

    table = Table(title=f"Vimsopaka Bala — {scheme.value.upper()} (20-point scale)")
    table.add_column("Planet", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("%", style="yellow")
    table.add_column("Breakdown", style="white")
    for r in results:
        breakdown = ", ".join(
            f"{c.varga}={c.dignity[:3]}" for c in r.components
        )
        table.add_row(r.graha.full_name, f"{r.total:.1f}/20",
                     f"{r.percentage:.0f}%", breakdown)
    console.print(table)


@app.command()
def ashtakavarga(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    parasara: bool = typer.Option(True, "--parasara/--varahamihira", help="Use Parasara (moon=1, venus=11) or Varahamihira (moon=12, venus=12)"),
    kakshya: Optional[str] = typer.Option(None, "--kakshya", "-k", help="Show Kakshya table for a planet: sun, moon, mars, mercury, jupiter, venus, saturn"),
):
    """Compute Ashtakavarga — planetary strengths by house."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )

    bavs = all_bhinna_ashtakavarga(cd, parasara_venus=parasara, parasara_moon=parasara)
    sav = sarva_ashtakavarga(cd, parasara_venus=parasara, parasara_moon=parasara)
    sp = sodhya_pinda(cd, parasara_venus=parasara, parasara_moon=parasara)

    # BAV table
    header_label = "Parasara" if parasara else "Varahamihira"
    table = Table(title=f"Bhinna Ashtakavarga ({header_label})")
    table.add_column("House", style="cyan")
    for g in _OCCUPANT_GRAHAS:
        table.add_column(g.short_name, style="green")
    table.add_column("SAV", style="yellow bold")
    table.add_column("Rasi", style="white")

    for h in range(12):
        rasi = Rasi(h)
        vals = [str(bavs[g][h]) for g in _OCCUPANT_GRAHAS]
        table.add_row(rasi.short_name, *vals, str(sav[h]), rasi.full_name)
    console.print(table)

    # Sodhya Pinda
    sp_table = Table(title="Sodhya Pinda (after Trikona & Ekadhipatya Shodhana)")
    sp_table.add_column("Planet", style="cyan")
    sp_table.add_column("Sodhya Pinda", style="green bold")
    for g in _OCCUPANT_GRAHAS:
        sp_table.add_row(g.full_name, str(sp[g]))
    console.print(sp_table)

    # Kakshya table (optional)
    if kakshya:
        try:
            graha = Graha[kakshya.upper()]
        except KeyError:
            console.print(f"[red]Unknown planet: {kakshya}[/red]")
            raise typer.Exit(1)
        kt = kakshya_bindu_table(graha, cd, parasara_venus=parasara, parasara_moon=parasara)
        kt_table = Table(title=f"Kakshya Bindus — {graha.full_name}")
        kt_table.add_column("House", style="cyan")
        ref_labels = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "La"]
        for rl in ref_labels:
            kt_table.add_column(rl, style="green")
        kt_table.add_column("Total", style="yellow bold")
        for h in range(12):
            vals = [str(kt[h][k]) for k in range(8)]
            kt_table.add_row(Rasi(h).short_name, *vals, str(sum(kt[h])))
        console.print(kt_table)


def _parse_varga_level(name: str) -> VargaLevel:
    """Parse varga level from string like 'D-9', 'navamsa', 'd9'."""
    clean = name.lower().replace("-", "").replace(" ", "")
    for vl in VargaLevel:
        if f"d{vl.divisions}" == clean:
            return vl
        if vl.full_name.lower().replace(" ", "").replace("-", "") == clean:
            return vl
    mapping = {
        "navamsa": VargaLevel.D_9, "navamsha": VargaLevel.D_9,
        "dasamsa": VargaLevel.D_10, "drekkana": VargaLevel.D_3,
        "hora": VargaLevel.D_2, "rasi": VargaLevel.D_1,
        "dwadasamsa": VargaLevel.D_12, "shodasamsa": VargaLevel.D_16,
        "siddhamsa": VargaLevel.D_24, "trimsamsa": VargaLevel.D_30,
        "shashtyamsa": VargaLevel.D_60, "vimsamsa": VargaLevel.D_20,
        "nakshatramsa": VargaLevel.D_27, "saptamsa": VargaLevel.D_7,
        "panchamsa": VargaLevel.D_5, "chaturthamsa": VargaLevel.D_4,
    }
    result = mapping.get(clean)
    if result is None:
        console.print(f"[red]Unknown varga level: {name}[/red]")
        raise typer.Exit(1)
    return result


def _parse_variant(name: str) -> VargaVariant:
    """Parse variant name to VargaVariant enum."""
    mapping = {
        "default": VargaVariant.DEFAULT,
        "rev": VargaVariant.REV,
        "rev2": VargaVariant.REV2,
        "trd": VargaVariant.TRD,
        "pv": VargaVariant.PV,
        "b": VargaVariant.B,
        "bhava": VargaVariant.B,
        "k": VargaVariant.K,
        "km": VargaVariant.KM,
        "ukm": VargaVariant.UKM,
        "jn": VargaVariant.JN,
        "sn": VargaVariant.SN,
        "us": VargaVariant.US,
        "ra": VargaVariant.RA,
        "rm": VargaVariant.RM,
        "rmm": VargaVariant.RMM,
        "ni": VargaVariant.NI,
        "nim": VargaVariant.NIM,
        "md": VargaVariant.MD,
        "lm": VargaVariant.LM,
        "cnl": VargaVariant.CNL,
        "sn2": VargaVariant.SN2,
        "kn": VargaVariant.KN,
        "ar": VargaVariant.AR,
        "rvar": VargaVariant.RVAR,
        "sh": VargaVariant.SH,
        "1_7": VargaVariant.V1_7,
        "7_1": VargaVariant.V7_1,
        "5_8": VargaVariant.V5_8,
        "6_9": VargaVariant.V6_9,
        "9_12": VargaVariant.V9_12,
        "knrao": VargaVariant.K_N_RAO,
    }
    result = mapping.get(name.lower().replace("-", "_"))
    if result is None:
        console.print(f"[red]Unknown variant: {name}[/red]")
        raise typer.Exit(1)
    return result


def _variant_label(var: VargaVariant) -> str:
    if var == VargaVariant.DEFAULT:
        return "Default"
    return var.name


def _list_varga_levels():
    table = Table(title="Available Varga Levels")
    table.add_column("Level", style="cyan")
    table.add_column("Divisions", style="green")
    table.add_column("Sanskrit Name", style="yellow")
    table.add_column("Variants", style="white")
    for vl in VargaLevel:
        variants = get_variants_for_level(vl)
        variant_names = ", ".join(v.name for v in variants)
        table.add_row(vl.short_name, str(vl.divisions), vl.full_name, variant_names)
    console.print(table)


def _display_chart_yogas(cd: ChartData):
    from jhora.calc.yogas import detect_all
    results = detect_all(cd)
    if not results:
        return
    table = Table(title=f"Yogas ({len(results)})")
    table.add_column("Yoga", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Strength", style="white")
    for y in results:
        table.add_row(y.name, y.category, y.strength)
    console.print(table)


def _display_varga(vcd: VargaChartData, title: str = ""):
    table = Table(title=title or f"Varga Chart ({vcd.varga_level.short_name})")
    table.add_column("Planet", style="cyan")
    table.add_column("Rasi", style="yellow")
    table.add_column("Degrees", style="white")
    table.add_column("Sign", style="green")

    for g in Graha:
        if g in vcd.positions:
            p = vcd.positions[g]
            table.add_row(
                g.full_name,
                p.rasi.short_name,
                f"{p.degrees_in_rasi:.2f}",
                p.rasi.full_name,
            )
    table.add_row(
        "Lagna",
        vcd.lagna_position.rasi.short_name,
        f"{vcd.lagna_position.degrees_in_rasi:.2f}",
        vcd.lagna_position.rasi.full_name,
    )
    console.print(table)


@app.command()
def tajaka(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    target_year: int = typer.Argument(..., help="Target year for yearly chart"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Compute Tajaka solar return chart for a given year."""
    from jhora.calc.tajaka import build_tajaka_chart, compute_harsha_bala, compute_patyayini_dasa, compute_mudda_dasa
    bd = parse_birthdata(birthdata)
    cb = ChartBuilder()
    cb.swe.set_sidereal_mode(ayanamsa)
    natal = cb.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    taj = build_tajaka_chart(cb.swe, cb, natal, target_year)
    chart = taj.chart

    y, m, d, h = cb.swe.revjul(taj.varsha_pravesh_jd)
    console.print(f"\n[bold]Tajaka Varsha Pravesh[/bold]: {int(y)}-{int(m):02d}-{int(d):02d} {h:.2f}h UT")
    console.print(f"Natal lagna: {natal.ascendant:.2f}° ({int(natal.ascendant//30)%12})")
    console.print(f"Year index: {taj.year_index}, Muntha sign: {taj.muntha_sign}")

    table = Table(title=f"Solar Return Chart (Year {target_year})")
    table.add_column("Graha", style="yellow")
    table.add_column("Longitude", style="cyan")
    table.add_column("Sign", style="green")
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
               Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
        p = chart.planets[g]
        table.add_row(g.short_name, f"{p.longitude:.2f}°", p.rasi_name)
    console.print(table)

    hb = compute_harsha_bala(chart, taj.varsha_pravesh_jd)
    hb_table = Table(title="Harsha Bala")
    hb_table.add_column("Planet", style="yellow")
    hb_table.add_column("Score", style="cyan")
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
               Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
        hb_table.add_row(g.short_name, str(hb.get(g, 0)))
    console.print(hb_table)

    periods = compute_patyayini_dasa(chart.planets, chart.ascendant, taj.varsha_pravesh_jd)
    pd_table = Table(title="Patyayini Dasa")
    pd_table.add_column("Lord", style="yellow")
    pd_table.add_column("Days", style="cyan")
    for p in periods:
        pd_table.add_row(p.lord_name, f"{p.duration_years*365:.2f}")
    console.print(pd_table)

    md = compute_mudda_dasa(natal.moon.longitude, taj.year_index - 1, taj.varsha_pravesh_jd)
    md_table = Table(title="Mudda Dasa (Varsha Vimsottari)")
    md_table.add_column("Lord", style="yellow")
    md_table.add_column("Days", style="cyan")
    for p in md:
        md_table.add_row(p.lord_name, f"{p.duration_years*365:.2f}")
    console.print(md_table)


@app.command()
def progression(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    age: float = typer.Option(None, "--age", help="Age in years (default: current age)"),
):
    """Compute secondary progressions (1 day = 1 year) and aspects to natal."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )

    if age is None:
        from datetime import datetime
        age = (datetime.now() - cd.birth_date).total_seconds() / (365.25 * 86400)

    pc = ProgressionCalculator(cd)
    sec = pc.secondary(target_age=age)

    from jhora.types.rasi import Rasi
    table = Table(title=f"Secondary Progression (age {age:.1f})")
    table.add_column("Planet", style="cyan")
    table.add_column("Natal", style="yellow")
    table.add_column("Progressed", style="green")
    table.add_column("Δ", style="white")
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
        np = cd.planet(g)
        pp = sec.chart.planet(g) if sec.chart else None
        nr = Rasi.from_longitude(np.longitude).short_name
        pr = Rasi.from_longitude(pp.longitude).short_name if pp else "?"
        moved = "→" if nr != pr else ""
        table.add_row(g.full_name, f"{nr} {np.longitude:.1f}°",
                     f"{pr} {pp.longitude:.1f}°" if pp else "",
                     moved)
    console.print(table)

    aspects = pc.aspects_to_natal(sec, max_orb=3.0)
    if aspects:
        console.print()
        at = Table(title=f"Progressed to Natal Aspects (orb < 3°)")
        at.add_column("Progressed", style="cyan")
        at.add_column("Aspect", style="yellow")
        at.add_column("Natal", style="green")
        at.add_column("Orb", style="white")
        for a in aspects:
            at.add_row(a.progressed_graha.full_name, a.aspect_type,
                      a.natal_graha.full_name, f"{a.orb:.1f}°")
        console.print(at)


@app.command()
def tithi_pravesha(
    birthdata: str = typer.Argument(..., help="Birth data"),
    year: int = typer.Option(None, "--year", "-y", help="Target year (default: current year)"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Compute Tithi Pravesha chart — annual solar-tithi return for year-ahead prediction."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )

    if year is None:
        from datetime import datetime
        year = datetime.now().year

    tp = TithiPraveshaCalculator(cd)

    natal_t = tp.natal_tithi
    tithi_idx = int(natal_t / 12)
    tithi_phase = "Shukla" if tithi_idx < 15 else "Krishna"
    tithi_num = tithi_idx % 15 + 1 if tithi_idx < 30 else 1
    console.print(f"Natal tithi angle: {natal_t:.2f}° ({tithi_phase} {tithi_num})")

    entries = tp.compute_range(year - 1, year + 1)
    table = Table(title=f"Tithi Pravesha Charts ({year-1}-{year+1})")
    table.add_column("Year", style="cyan")
    table.add_column("Date/Time (UT)", style="white")
    table.add_column("Lagna", style="yellow")
    table.add_column("Sun", style="green")
    table.add_column("Moon", style="green")
    table.add_column("Tithi Angle", style="white")

    from jhora.types.rasi import Rasi
    for e in entries:
        if e.chart is None:
            continue
        lagna = Rasi.from_longitude(e.chart.ascendant).short_name
        sun_r = Rasi.from_longitude(e.chart.planet(Graha.SUN).longitude).short_name
        moon_r = Rasi.from_longitude(e.chart.planet(Graha.MOON).longitude).short_name
        m = e.chart.planet(Graha.MOON).longitude
        s = e.chart.planet(Graha.SUN).longitude
        a = (m - s) % 360
        marker = " ◀" if e.year == year else ""
        table.add_row(
            f"{e.year}{marker}", e.event_date, lagna, sun_r, moon_r,
            f"{a:.2f}°",
        )
    console.print(table)


@app.command()
def kuta(
    girl: str = typer.Argument(..., help="Girl birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    boy: str = typer.Argument(..., help="Boy birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    ashta_koota: bool = typer.Option(False, "--ashta-koota", "-k",
                                     help="Use Ashta Koota (36pt, 8 factors) instead of 10 Porutham (19pt)"),
):
    """Compute marriage compatibility between two charts.

    10 Porutham (19pt) is the default. Use --ashta-koota for the Ashta Koota
    36-point system used by the classical Vedic binary.
    """
    from jhora.calc.kuta import compute_kuta, ScoringSystem, gunanka_level
    system = ScoringSystem.ASHTA_KOOTA if ashta_koota else ScoringSystem.PORUTHAM
    bd_g = parse_birthdata(girl)
    bd_b = parse_birthdata(boy)
    cb = ChartBuilder()
    cb.swe.set_sidereal_mode(ayanamsa)
    g_chart = cb.build(
        year=bd_g["year"], month=bd_g["month"], day=bd_g["day"],
        hour=bd_g["hour"], lat=bd_g["lat"], lon=bd_g["lon"],
        tz=bd_g["tz"], ayanamsa=ayanamsa,
    )
    b_chart = cb.build(
        year=bd_b["year"], month=bd_b["month"], day=bd_b["day"],
        hour=bd_b["hour"], lat=bd_b["lat"], lon=bd_b["lon"],
        tz=bd_b["tz"], ayanamsa=ayanamsa,
    )

    result = compute_kuta(
        g_chart.planet(Graha.MOON).longitude,
        b_chart.planet(Graha.MOON).longitude,
        system=system,
    )

    system_label = result.system_name
    console.print(f"\n[bold]{system_label} — Matchmaking[/bold]")
    console.print(f"  Girl: [yellow]{result.girl_nakshatra.name}[/yellow] / "
                  f"[cyan]{result.girl_rasi.full_name}[/cyan]")
    console.print(f"  Boy:  [yellow]{result.boy_nakshatra.name}[/yellow] / "
                  f"[cyan]{result.boy_rasi.full_name}[/cyan]")
    console.print()

    title = f"{system_label} — {result.total_score:.0f}/{result.max_score:.0f} ({result.percentage:.0f}%)"
    if result.system == ScoringSystem.ASHTA_KOOTA:
        title += f" — [bold]{result.gunanka_level}[/bold]"
    table = Table(title=title)
    table.add_column("Factor" if ashta_koota else "Porutham", style="yellow")
    table.add_column("Score", style="cyan")
    table.add_column("Result", style="white")
    for p in result.poruthams:
        status = "[green]Good[/green]" if p.is_good else "[red]Not Good[/red]"
        table.add_row(p.name, f"{p.score:.0f}/{p.max_score:.0f}", status)
    console.print(table)

    # Detail descriptions
    console.print("\n[bold]Details:[/bold]")
    for p in result.poruthams:
        status = "✓" if p.is_good else "✗"
        console.print(f"  {status} [yellow]{p.name}[/yellow]: {p.description}")


@app.command()
def transit(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    parasara: bool = typer.Option(True, "--parasara/--varahamihira", help="Ashtakavarga tradition"),
):
    """Current transit positions vs natal chart with Ashtakavarga scores."""
    from jhora.calc.gochara import compute_transits

    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )

    result = compute_transits(cd, parasara_moon=parasara, parasara_venus=parasara)

    console.print(f"[dim]Transit: {result.timestamp.strftime('%Y-%m-%d %H:%M UTC')}[/dim]")
    console.print(f"[dim]Natal Lagna: {Rasi(result.natal_rasi).short_name}  "
                  f"Moon: {Rasi(result.moon_rasi).short_name}[/dim]")

    table = Table(title="Gochara — Transit Positions")
    table.add_column("P", style="cyan")
    table.add_column("In", style="yellow")
    table.add_column("Deg", style="white")
    table.add_column("Ret", style="dim")
    table.add_column("H(Lg)", style="green")
    table.add_column("H(Mo)", style="green")
    table.add_column("BAV", style="magenta")
    table.add_column("SAV", style="magenta")
    table.add_column("Fav", style="bold")

    for e in result.entries:
        ret = "R" if e.is_retrograde else ""
        fav = "✓" if e.is_favorable else "✗"
        fav_s = "[green]✓[/green]" if e.is_favorable else "[red]✗[/red]"
        table.add_row(
            e.graha.short_name, e.transit_rasi_name,
            f"{e.transit_degrees:.1f}", ret,
            str(e.house_from_lagna), str(e.house_from_moon),
            str(e.bav_score), str(e.sav_score), fav_s,
        )
    console.print(table)

    # Summary: SAV map
    sav_table = Table(title="SAV by Rasi")
    for r in range(12):
        sav_table.add_column(Rasi(r).short_name, style="yellow")
    row = [str(result.sav[r]) for r in range(12)]
    sav_table.add_row(*row)
    console.print(sav_table)


@app.command()
def prasna(
    number: int = typer.Argument(..., help="Query number (1-108, 1-249, or 1-1800)"),
    mode: str = typer.Option("108", "--mode", "-m", help="Prasna mode: 108, 249, or nadi"),
    table_: bool = typer.Option(False, "--table", "-t", help="Show all positions for the mode"),
):
    """Prasna (Horary) — compute Prasna Lagna from a query number."""
    from jhora.calc.prasna import (
        PrasnaMode, compute_prasna, all_prasna_results,
    )

    mode_map = {
        "108": PrasnaMode.MODE_108,
        "249": PrasnaMode.MODE_249,
        "nadi": PrasnaMode.NADI,
    }
    if mode.lower() not in mode_map:
        console.print(f"[red]Unknown mode: {mode}. Use 108, 249, or nadi.[/red]")
        raise typer.Exit(1)

    pm = mode_map[mode.lower()]

    if table_:
        results = all_prasna_results(pm)
        table = Table(title=f"{pm.label} — All {pm.max_number} Positions")
        table.add_column("#", style="cyan")
        table.add_column("PL (°)", style="yellow")
        table.add_column("Rasi", style="green")
        table.add_column("Deg", style="white")
        if pm == PrasnaMode.MODE_108:
            table.add_column("Navamsa", style="magenta")
        elif pm == PrasnaMode.MODE_249:
            table.add_column("Nakshatra", style="magenta")
            table.add_column("Sub", style="cyan")
        for r in results:
            row = [
                str(r.number),
                f"{r.prasna_lagna:.4f}",
                r.rasi.short_name,
                f"{r.degrees_in_rasi:.2f}",
            ]
            if pm == PrasnaMode.MODE_108:
                row.append(r.navamsa_rasi.short_name if r.navamsa_rasi else "")
            elif pm == PrasnaMode.MODE_249:
                row.append(r.nakshatra.name.replace("_", " ").title())
                row.append(r.sub_lord.name.title() if r.sub_lord else "")
            table.add_row(*row)
        console.print(table)
        return

    r = compute_prasna(number, pm)
    console.print(f"[bold]{pm.label}[/bold] — Number [cyan]#{number}[/cyan]")
    console.print(f"  Prasna Lagna: [yellow]{r.prasna_lagna:.4f}°[/yellow]")
    console.print(f"  Rasi: {r.rasi.short_name} ({r.rasi.full_name})")
    console.print(f"  Degrees in Rasi: {r.degrees_in_rasi:.2f}°")
    console.print(f"  Nakshatra: {r.nakshatra.name.replace('_', ' ').title()}")
    console.print(f"  Pada: {r.nakshatra_pada}")
    if r.navamsa_rasi:
        console.print(f"  Navamsa: {r.navamsa_rasi.short_name} ({r.navamsa_rasi.full_name})")
    if r.sub_lord:
        console.print(f"  Sub Lord: {r.sub_lord.name.title()}")
    console.print(f"  [dim]{r.description}[/dim]")


@app.command()
def muhurta(
    date: str = typer.Argument(..., help="Date: YYYY-MM-DD"),
    time: str = typer.Argument("12:00", help="Time: HH:MM (24h)"),
    lat: float = typer.Argument(13.08, help="Latitude"),
    lon: float = typer.Argument(80.27, help="Longitude"),
    tz: str = typer.Option("+0530", "--tz", "-z", help="Timezone offset"),
    task: str = typer.Option("general", "--task", "-t",
                             help="Task: general, wedding, new_job, housewarming, "
                                  "naming_child, first_rice, teaching_alphabet, "
                                  "sacred_thread, new_vehicle, placing_idols, "
                                  "house_construction"),
    find: bool = typer.Option(False, "--find", "-f", help="Scan entire day for best times (10-min steps)"),
    best: int = typer.Option(5, "--best", "-b", help="Number of best times to show (with --find)"),
):
    """Muhurta (Electional Astrology) — evaluate or find auspicious times."""
    from jhora.calc.muhurta import (
        MuhurtaTask, evaluate_time, find_muhurta,
    )
    from datetime import datetime

    task_map = {
        "general": MuhurtaTask.GENERAL,
        "wedding": MuhurtaTask.WEDDING,
        "new_job": MuhurtaTask.NEW_JOB,
        "housewarming": MuhurtaTask.HOUSEWARMING,
        "naming_child": MuhurtaTask.NAMING_CHILD,
        "first_rice": MuhurtaTask.FIRST_RICE,
        "teaching_alphabet": MuhurtaTask.TEACHING_ALPHABET,
        "sacred_thread": MuhurtaTask.SACRED_THREAD,
        "new_vehicle": MuhurtaTask.NEW_VEHICLE,
        "placing_idols": MuhurtaTask.PLACING_IDOLS,
        "house_construction": MuhurtaTask.HOUSE_CONSTRUCTION,
    }
    t = task_map.get(task.lower().replace(" ", "_"))
    if t is None:
        console.print(f"[red]Unknown task: {task}[/red]")
        raise typer.Exit(1)

    # _parse_tz returns negative for positive timezones; muhurta module expects positive
    raw_tz = ChartBuilder._parse_tz(tz)
    tz_offset = -raw_tz if raw_tz < 0 else raw_tz

    try:
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        console.print("[red]Invalid date/time format. Use YYYY-MM-DD HH:MM[/red]")
        raise typer.Exit(1)

    if find:
        results = find_muhurta(dt, lat, lon, tz_offset, t, step_minutes=10)
        top = results[:best]
        table = Table(title=f"Top {best} Muhurta Times — {t.label}")
        table.add_column("Time", style="cyan")
        table.add_column("Score", style="yellow")
        table.add_column("Tithi", style="green")
        table.add_column("Vara", style="green")
        table.add_column("Nakshatra", style="green")
        table.add_column("Abhijit", style="magenta")
        table.add_column("Issues", style="red")
        for r in top:
            tithi = f"{r.panchanga.tithi.name}"
            if r.tithi_ok:
                tithi = f"[green]{tithi}[/green]"
            else:
                tithi = f"[red]{tithi}[/red]"
            vara = r.panchanga.weekday_name
            if r.weekday_ok:
                vara = f"[green]{vara}[/green]"
            else:
                vara = f"[red]{vara}[/red]"
            nak = r.panchanga.nakshatra.name.replace("_", " ").title()
            if r.nakshatra_ok:
                nak = f"[green]{nak}[/green]"
            else:
                nak = f"[red]{nak}[/red]"
            abh = "✓" if r.in_abhijit else ""
            issues = r.score_detail if not r.is_good else ""
            table.add_row(
                r.datetime.strftime("%H:%M"),
                f"{r.score:.2f}", tithi, vara, nak, abh, issues,
            )
        console.print(table)
        return

    r = evaluate_time(dt, lat, lon, tz_offset, t)
    status = "[green]AUSPICIOUS[/green]" if r.is_good else "[red]INAUSPICIOUS[/red]"
    console.print(f"[bold]{t.label}[/bold] — {dt.strftime('%Y-%m-%d %H:%M')} — {status}")
    console.print(f"  Score: [yellow]{r.score:.2f}[/yellow] / 1.00")

    p = r.panchanga
    tithi_s = "✓" if r.tithi_ok else "✗"
    vara_s = "✓" if r.weekday_ok else "✗"
    nak_s = "✓" if r.nakshatra_ok else "✗"
    lagna_s = "✓" if r.lagna_ok else "✗"
    console.print(f"  Panchanga: Tithi={p.tithi.name} {tithi_s}  "
                  f"Vara={p.weekday_name} {vara_s}  "
                  f"Nak={p.nakshatra.name.replace('_', ' ').title()} {nak_s}")
    console.print(f"  Lagna: {r.lagna_rasi.short_name} {lagna_s}")

    if r.in_abhijit:
        console.print(f"  [bold magenta]✓ Abhijit Muhurta![/bold magenta]")

    for ip in r.inauspicious_periods:
        start_h = (((ip.start + 0.5) - int(ip.start + 0.5)) * 24 + tz_offset) % 24
        end_h = (((ip.end + 0.5) - int(ip.end + 0.5)) * 24 + tz_offset) % 24
        console.print(f"  [dim]{ip.kind}: {start_h:.1f}h-{end_h:.1f}h[/dim]")

    if r.score_detail and r.score_detail != "All good":
        console.print(f"  [red]{r.score_detail}[/red]")


@app.command()
def tui(
    birthdata: str = typer.Argument(None, help="Birth data (optional; interactive input if omitted)"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Launch interactive terminal UI (prompt_toolkit menus + Rich rendering)."""
    from jhora.tui.main import JhoraTui
    app = JhoraTui()
    if birthdata:
        bd = parse_birthdata(birthdata)
        builder = ChartBuilder()
        builder.swe.set_sidereal_mode(ayanamsa)
        app.chart = builder.build(
            year=bd["year"], month=bd["month"], day=bd["day"],
            hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
            tz=bd["tz"], ayanamsa=ayanamsa,
        )
        app.birthdata_str = birthdata
        lagna = Rasi.from_longitude(app.chart.ascendant)
        console.print(f"[green]Chart loaded: Lagna {lagna.full_name} "
                      f"({app.chart.ascendant:.2f}°)[/green]")
    app.run()


@app.command()
def ai(
    birthdata: str = typer.Argument(None, help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    provider: str = typer.Option("ollama", "--provider", "-p",
                                 help="AI provider: ollama, lmstudio, unsloth, custom"),
    model: str = typer.Option("", "--model", "-m", help="Model name"),
    base_url: str = typer.Option("", "--url", help="Custom API base URL"),
    mode: str = typer.Option("interpret", "--mode",
                             help="interpret, ask, or remedies"),
    style: str = typer.Option("detailed", "--style", "-s",
                              help="concise, detailed, or professional"),
    question: str = typer.Option("", "--question", "-q",
                                 help="Question for ask mode"),
    topic: str = typer.Option("general", "--topic", "-t",
                              help="general, relationship, career, health, spirituality, children, finance"),
    context: int = typer.Option(4096, "--context", "-c",
                                help="Max prompt tokens (2048-16384)"),
):
    """AI-powered chart interpretation via local LLM (Ollama/LM Studio/Unsloth)."""
    if not birthdata:
        console.print("[red]Birth data required[/red]")
        raise typer.Exit(1)

    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )

    config = AiConfig(provider=provider, base_url=base_url, max_context_tokens=context)
    if model:
        config.model = model
    engine = AiEngine(config)

    health = engine.health_check()
    if not health["ok"]:
        console.print(f"[red]AI server unreachable: {health['error']}[/red]")
        console.print("[yellow]Make sure your LLM server is running.[/yellow]")
        raise typer.Exit(1)

    console.print(f"[dim]Using {config.provider} / {config.model}...[/dim]\n")

    def _on_token(token: str):
        console.print(token, end="", highlight=False)

    if mode == "ask" and not question:
        console.print("[red]--question required for ask mode[/red]")
        raise typer.Exit(1)

    if mode == "interpret":
        engine.interpret(cd, style, topic, on_token=_on_token)
    elif mode == "ask":
        engine.ask(cd, question, on_token=_on_token)
    elif mode == "remedies":
        engine.remedies(cd, on_token=_on_token)
    else:
        console.print(f"[red]Unknown mode: {mode}[/red]")
    console.print()


@app.command()
def teach(
    question: str = typer.Argument(..., help="What do you want to learn about Vedic astrology?"),
    birthdata: str = typer.Option(None, "--chart", "-c", help="Optional: your birth data for chart-based teaching"),
    provider: str = typer.Option("ollama", "--provider", "-p"),
    model: str = typer.Option("", "--model", "-m"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """AI Teacher — learn Vedic astrology from the textbook corpus."""
    chart = None
    if birthdata:
        bd = parse_birthdata(birthdata)
        builder = ChartBuilder()
        builder.swe.set_sidereal_mode(ayanamsa)
        chart = builder.build(
            year=bd["year"], month=bd["month"], day=bd["day"],
            hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
            tz=bd["tz"], ayanamsa=ayanamsa,
        )

    from jhora.ai.teacher import AiTeacher
    base_url = {
        "ollama": "http://localhost:11434/v1",
        "lmstudio": "http://localhost:1234/v1",
        "unsloth": "http://localhost:8000/v1",
    }.get(provider, "http://localhost:11434/v1")

    teacher = AiTeacher(provider=provider, base_url=base_url, model=model or "")

    def _print(token):
        console.print(token, end="", highlight=False)

    console.print(f"[dim]Teacher ({provider}):[/dim]\n")
    teacher.ask(question, chart=chart, on_token=_print)
    console.print()


@app.command()
def mundane(
    year: int = typer.Argument(None, help="Year to analyze (default: current year)"),
    lat: float = typer.Option(28.61, "--lat", help="Latitude of location (default: Delhi)"),
    lon: float = typer.Option(77.21, "--lon", help="Longitude (default: Delhi)"),
    tz: str = typer.Option("+0530", "--tz", help="Timezone (default: +0530)"),
    ai: bool = typer.Option(False, "--ai", help="Use AI to interpret the ingress chart"),
    provider: str = typer.Option("ollama", "--provider", "-p"),
    model: str = typer.Option("", "--model", "-m"),
):
    """Mundane astrology — solar ingresses, eclipses, world event indicators."""
    if year is None:
        from datetime import datetime
        year = datetime.now().year

    mc = MundaneCalculator(lat=lat, lon=lon, tz=tz)

    # Aries ingress (most important)
    aries = mc.aries_ingress(year)
    if aries and aries.chart:
        from jhora.types.rasi import Rasi
        l = Rasi.from_longitude(aries.chart.ascendant)
        table = Table(title=f"Mesha Sankranti (Aries Ingress) {year} — Annual World Chart")
        table.add_column("", style="cyan")
        table.add_column("Lagna", style="yellow")
        table.add_column("", style="green")
        table.add_row("Date", aries.datetime_utc, "")
        table.add_row("Lagna", l.full_name, f"{aries.chart.ascendant:.1f}°")
        from jhora.types.graha import Graha
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                  Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
            p = aries.chart.planet(g)
            r = Rasi.from_longitude(p.longitude)
            table.add_row(g.full_name, r.full_name,
                         f"{p.longitude:.1f}°" + (" R" if p.is_retrograde else ""))
        console.print(table)

    # All ingresses
    console.print()
    ing_table = Table(title=f"2026 Solar Ingresses (Sankrantis)")
    ing_table.add_column("Sign", style="cyan")
    ing_table.add_column("Date/Time (UT)", style="white")
    for e in mc.solar_ingresses(year):
        ing_table.add_row(e.sign, e.datetime_utc)
    console.print(ing_table)

    # Eclipses
    eclipses = mc.eclipses()
    if eclipses:
        console.print()
        ec_table = Table(title="Upcoming Eclipses")
        ec_table.add_column("Type", style="red")
        ec_table.add_column("Date/Time (UT)", style="white")
        for e in eclipses:
            ec_table.add_row(e.name, e.datetime_utc)
        console.print(ec_table)

    # Major conjunctions
    conj = mc.conjunctions(year)
    if conj:
        console.print()
        cj_table = Table(title=f"Major Conjunctions {year}")
        cj_table.add_column("Event", style="yellow")
        cj_table.add_column("Date (UT)", style="white")
        cj_table.add_column("Sign", style="cyan")
        for c in conj:
            cj_table.add_row(c.name, c.datetime_utc, c.sign)
        console.print(cj_table)

    # AI interpretation if requested
    if ai and aries and aries.chart:
        console.print("\n[bold]AI Mundane Interpretation:[/bold]\n")
        config = AiConfig(provider=provider)
        if model:
            config.model = model
        engine = AiEngine(config)
        health = engine.health_check()
        if not health["ok"]:
            console.print(f"[red]AI offline: {health['error']}[/red]")
        else:
            engine.interpret(aries.chart, style="detailed", topic="mundane",
                            on_token=lambda t: console.print(t, end="", highlight=False))
            console.print()


@app.callback()
def cli():
    """OpenJyotish — Vedic astrology calculator (Python port)."""


if __name__ == "__main__":
    app()
