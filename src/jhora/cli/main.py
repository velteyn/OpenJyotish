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

app = typer.Typer(name="jhora", help="Jagannatha Hora — Vedic astrology calculator")
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


def _lord_name(idx: int) -> str:
    """Convert Graha ID to full name."""
    try:
        return Graha(idx).full_name
    except ValueError:
        return str(idx)


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
def gui():
    """Launch the graphical user interface."""
    from PyQt6.QtWidgets import QApplication
    from jhora.ui.main_window import MainWindow

    import sys
    qapp = QApplication(sys.argv)
    qapp.setApplicationName("Jagannatha Hora")
    qapp.setStyle("Fusion")
    window = MainWindow()
    window.showMaximized()
    qapp.exec()


@app.command()
def shadbala(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Compute Shadbala (six-fold planetary strength)."""
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
def kuta(
    girl: str = typer.Argument(..., help="Girl birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    boy: str = typer.Argument(..., help="Boy birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    ashta_koota: bool = typer.Option(False, "--ashta-koota", "-k",
                                     help="Use Ashta Koota (36pt, 8 factors) instead of 10 Porutham (19pt)"),
):
    """Compute marriage compatibility between two charts.

    10 Porutham (19pt) is the default. Use --ashta-koota for the Ashta Koota
    36-point system used by the original JHora binary.
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
    birthdata: str = typer.Argument(None, help="Birth data (optional; uses sample if omitted)"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Launch interactive terminal UI (Rich-based, keyboard-navigable tabs)."""
    from jhora.tui.main import TuiApp

    if birthdata:
        bd = parse_birthdata(birthdata)
        builder = ChartBuilder()
        builder.swe.set_sidereal_mode(ayanamsa)
        cd = builder.build(
            year=bd["year"], month=bd["month"], day=bd["day"],
            hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
            tz=bd["tz"], ayanamsa=ayanamsa,
        )
    else:
        cd = None

    app_tui = TuiApp(chart_data=cd)
    try:
        app_tui.run()
    except Exception as e:
        console.print(f"[yellow]TUI fallback: printing static view[/yellow]")
        app_tui.run_no_live()


@app.callback()
def cli():
    """Jagannatha Hora — Vedic astrology calculator (Python port)."""


if __name__ == "__main__":
    app()
