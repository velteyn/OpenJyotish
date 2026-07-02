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
from jhora.types.dasa import DasaSystem
from jhora.types.varga import VargaLevel, VargaVariant

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
    window.show()
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


@app.callback()
def cli():
    """Jagannatha Hora — Vedic astrology calculator (Python port)."""


if __name__ == "__main__":
    app()
