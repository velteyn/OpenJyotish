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
from rich.prompt import Prompt
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
    nodes: str = typer.Option("mean", "--nodes",
                              help="Lunar nodes: mean (default) or true"),
    chalit: bool = typer.Option(False, "--chalit", help="Show Bhava/Chalit house positions"),
    chalit_varga: Optional[str] = typer.Option(
        None, "--chalit-varga",
        help="Varga level for --chalit (e.g. D-1, D-9, D-60); default D-1 + D-9"),
    bhava_method: str = typer.Option(
        "default", "--bhava-method",
        help="Bhava system for --chalit: default (Placidus D-1, equal vargas) or sripati (D-1)"),
):
    """Compute and display birth chart."""
    if nodes not in ("mean", "true"):
        console.print("[red]Unknown --nodes mode. Use: mean, true.[/red]")
        raise typer.Exit(code=2)
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    chart_data = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa, nodes=nodes,
    )
    _display_chart(chart_data)
    _display_chart_yogas(chart_data)
    if chalit:
        if chalit_varga:
            try:
                levels = [_parse_varga_level(chalit_varga)]
            except ValueError as exc:
                console.print(f"[red]{exc}[/red]")
                raise typer.Exit(code=2)
        else:
            levels = [VargaLevel.D_1, VargaLevel.D_9]
        _display_chalit(chart_data, levels=levels, method=bhava_method)


@app.command("download-ephe")
def download_ephe(
    dest: str = typer.Option("", "--dest",
                             help="Target directory (default: per-user data dir)"),
):
    """Download Swiss precision ephemeris files (~1.8 MB, once)."""
    from jhora.paths import download_ephemeris, ephe_available
    before = ephe_available()
    if before is not None:
        console.print(f"[green]Already present: {before}[/green]")
        return
    console.print("Downloading Swiss ephemeris (sepl_18 + semo_18)...")

    def _prog(name, done, total):
        console.print(f"  {name}: {done}/{total} bytes", end="\r",
                      highlight=False)

    ok, msg = download_ephemeris(dest or None, progress_cb=_prog)
    console.print()
    console.print(f"[green]{msg}[/green]" if ok else f"[red]{msg}[/red]")
    if not ok:
        raise typer.Exit(1)


@app.command("knowledge-import")
def knowledge_import(
    files: list[str] = typer.Argument(..., help=".txt book files to import"),
):
    """Import your own textbook .txt files into the personal library."""
    from jhora.interpreter.knowledge_base import KnowledgeBase
    res = KnowledgeBase().import_files(files)
    for name in res["added"]:
        console.print(f"[green]Added: {name}[/green]")
    for note in res["skipped"]:
        console.print(f"[dim]Skipped: {note}[/dim]")
    if res["added"]:
        console.print("[dim]Rebuild vectors (AI tab) for semantic search.[/dim]")


@app.command()
def analyze(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    jsonld: bool = typer.Option(False, "--jsonld",
                                help="Emit a JSON-LD document instead of plain JSON"),
):
    """AI-friendly JSON dump — all computed data in one structured output."""
    import json
    if jsonld:
        from jhora.ai.jsonld import chart_to_jsonld
        bd = parse_birthdata(birthdata)
        builder = ChartBuilder()
        cd = builder.build(
            year=bd["year"], month=bd["month"], day=bd["day"],
            hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
            tz=bd["tz"], ayanamsa=ayanamsa,
        )
        print(json.dumps(chart_to_jsonld(cd), indent=2, ensure_ascii=False))
        return
    data = full_analysis(birthdata, ayanamsa)
    print(json.dumps(data, indent=2, ensure_ascii=False))


@app.command()
def dasa(
    birthdata: str = typer.Argument(..., help="Birth data"),
    system: str = typer.Argument("vimsottari", help="Dasa system"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    start: str = typer.Option("moon", "--start", help="Nakshatra dasa seed: moon, lagna, sun, kshema, utpanna, adhana, devi, brahma, maandi, trisphuta"),
    ad_method: str = typer.Option("rao_rath", "--ad-method", help="Antardasa method: rao_rath, raman, continuous, raghavacharya"),
    narayana_variant: str = typer.Option("base", "--narayana-variant", help="Narayana variant: base, sama, paka, ayur"),
    narayana_chart: str = typer.Option(None, "--narayana-chart", help="Narayana chart seed (e.g. D-9, D-60, D-144)"),
    sesham: str = typer.Option("moon", "--sesham", help="Sesham handling: moon (reduce first MD), full (no reduction)"),
    year_def: str = typer.Option("solar", "--year-def", help="Year definition: solar, savana, tithi"),
    karaka_role: str = typer.Option("Dara", "--karaka-role", help="Karaka Dasa seed: Putra, Matri, Bhratri, Dara"),
    house: int = typer.Option(1, "--house", help="Shoola Dasa seed house: 1 self, 9 Pitri, 7 Dara, 5 Putra"),
    moola_lagna: bool = typer.Option(True, "--moola-lagna/--no-moola-lagna", help="Moola/Tara: use the Lagna sign as a base candidate"),
    moola_sun: bool = typer.Option(True, "--moola-sun/--no-moola-sun", help="Moola/Tara: use the Sun's sign as a base candidate"),
    moola_moon: bool = typer.Option(True, "--moola-moon/--no-moola-moon", help="Moola/Tara: use the Moon's sign as a base candidate"),
    tara_definition: str = typer.Option("parasara", "--tara-definition", help="Tara dasa definition: parasara, rath"),
    tara_sesham: str = typer.Option("moon", "--tara-sesham", help="Tara sesham: none, moon, moon-rev-apasavya"),
    tara_dir_star: bool = typer.Option(False, "--tara-direction-from-star", help="Tara: reckon direction from the nakshatra instead of the sign"),
    chara_exalt_exc: bool = typer.Option(False, "--chara-exaltation-exception/--no-chara-exaltation-exception", help="Chara dasa: adjust a sign's years when its lord is exalted/debilitated"),
    sudarshana_ad_lord: bool = typer.Option(True, "--sudarshana-ad-from-lord/--no-sudarshana-ad-from-lord", help="Sudarshana Chakra: antardasas run from the MD sign's lord (default) or the MD sign"),
    buddhi_gati_varga: str = typer.Option("D-1", "--buddhi-gati-varga", help="Buddhi Gati dasa base varga (e.g. D-1, D-9, D-60)"),
):
    """Compute dasa periods for a chart.

    system may be: vimsottari, ashtottari, yogini, sudasa, chara, narayana,
    lagnamsaka, padanaathaamsa, rasi-bhukta-vimsottari,
    kalachakra, brahma, karaka, shoola, trikona, varnada,
    sthira, navamsa, yogardha, niryana-shoola, lagna-kendradi,
    kaala, chakra, mandooka, drig, sudarshana, tithi-ashtottari, tithi-yogini,
    karana-chaturaaseeti, yoga-vimsottari, naisargika, moola, tara, buddhi-gati.
    Seed/sesham/year options apply
    to the nakshatra dasas (vimsottari, ashtottari, yogini); --karaka-role
    selects the Karaka Dasa seed; --house selects the Shoola Dasa seed
    house (1, 5, 7, 9).
    """
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    chart_data = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    chart_dict = _chart_to_dict(chart_data)
    from jhora.dasas.base import DasaOptions
    opts = DasaOptions(start_variation=start, sesham_method=sesham, year_definition=year_def,
                       karaka_role=karaka_role, seed_house=house, ad_method=ad_method,
                       narayana_variant=narayana_variant, narayana_chart=narayana_chart,
                       moola_use_lagna=moola_lagna, moola_use_sun=moola_sun,
                       moola_use_moon=moola_moon,
                       tara_definition=tara_definition,
                       tara_use_sesham=(tara_sesham.lower() != "none"),
                       tara_sesham_rev_apasavya=(
                           tara_sesham.lower() == "moon-rev-apasavya"),
                       tara_direction_from_star=tara_dir_star,
                       chara_exaltation_exception=chara_exalt_exc,
                       sudarshana_ad_from_lord=sudarshana_ad_lord)
    if system == "buddhi-gati" and buddhi_gati_varga:
        try:
            vl = _parse_varga_level(buddhi_gati_varga)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=2)
        vcd = VargaChartComputer().compute(chart_data, vl,
                                           VargaVariant.DEFAULT)
        chart_dict["buddhi_gati_varga"] = {
            "planets": {g: {"longitude": p.longitude}
                        for g, p in vcd.positions.items()},
            "lagna_lon": vcd.lagna_position.longitude,
        }
    engine = _get_dasa_engine(system, opts)
    periods = engine.compute(chart_data.julian_day, chart_dict, opts)
    _display_dasa_table(periods, f"{system.title()} Dasa Periods")
    if system.lower() in ("vimsottari", "ashtottari", "yogini"):
        console.print(f"[dim]Seed: {start} · Sesham: {sesham} · Year: {year_def}"
                      f" · AD: {ad_method}[/dim]")


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
    table.add_column("Asta", style="red")

    from jhora.calc.combustion import combust_planets
    _comb = combust_planets(
        {g: p.longitude for g, p in cd.planets.items()},
        cd.planet(Graha.SUN).longitude,
        {g: p.is_retrograde for g, p in cd.planets.items()})
    from jhora.calc.gandanta import gandanta_planets
    _gand = gandanta_planets(
        {g: p.longitude for g, p in cd.planets.items()})
    table.add_column("Gnd", style="red")
    for g in Graha:
        if g in cd.planets:
            p = cd.planets[g]
            table.add_row(
                g.full_name, f"{p.longitude:.2f}",
                p.rasi_name, f"{p.degrees_in_rasi:.2f}",
                p.nakshatra_name, str(p.nakshatra_pada),
                p.dignity, "C" if g in _comb else "",
                "G" if g in _gand else "",
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
    """Convert lord index to full name.

    Graha IDs (0-8) map to planets; rasi-based dasas (Narayana, Sudasa,
    Brahma, etc.) use 100+rasi and map to sign names.
    """
    if idx >= 100:
        from jhora.types.rasi import Rasi
        return Rasi(idx - 100).full_name
    try:
        return Graha(idx).full_name
    except ValueError:
        return str(idx)


def _display_chalit(cd: ChartData, levels=None, method: str = "default"):
    cc = ChalitComputer(cd)
    for vl in (levels if levels is not None
               else [VargaLevel.D_1, VargaLevel.D_9]):
        try:
            r = cc.compute(vl, method=method)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=2)
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
    d = {"planets": planets, "lagna_lon": cd.ascendant}
    # Birth place/time for time-of-day dasas (Kaala, Chakra); other
    # engines ignore these keys.
    d["lat"] = cd.latitude
    d["lon"] = cd.longitude
    d["tz"] = cd.timezone
    if cd.hora_lagna is not None:
        # True Hora Lagna for Varnada dasa; engines fall back to the
        # Sun's sign when the key is absent.
        d["hora_lagna_lon"] = cd.hora_lagna.longitude
    try:
        # Maandi/Gulika longitude for the Maandi and Trisphuta dasa seeds.
        from jhora.calc.upagraha import compute_temporal_upagrahas
        for u in compute_temporal_upagrahas(cd):
            if u.name in ("Gulika", "Maandi", "Mandi"):
                d["gulika_lon"] = u.longitude
                break
    except Exception:
        pass
    return d


def _get_dasa_engine(system: str, options=None):
    """Return a dasa engine for the given system name (vimsottari/ashtottari/
    yogini/sudasa/chara/narayana/lagnamsaka/padanaathaamsa/rasi-bhukta-vimsottari/kalachakra/brahma/karaka/shoola/
    trikona/varnada/sthira/navamsa/yogardha/niryana-shoola/
    lagna-kendradi/kaala/chakra/mandooka/drig/sudarshana/tithi-ashtottari/tithi-yogini/
    karana-chaturaaseeti/yoga-vimsottari/naisargika/moola/tara)."""
    s = system.lower()
    if s == "vimsottari":
        from jhora.dasas.vimsottari import VimsottariDasa
        return VimsottariDasa(options)
    if s == "ashtottari":
        from jhora.dasas.ashtottari import AshtottariDasa
        return AshtottariDasa(options)
    if s == "yogini":
        from jhora.dasas.yogini import YoginiDasa
        return YoginiDasa(options)
    if s == "sudasa":
        from jhora.dasas.sudasa import Sudasa
        return Sudasa()
    if s == "chara":
        from jhora.dasas.chara import CharaDasa
        return CharaDasa()
    if s == "narayana":
        from jhora.dasas.narayana import NarayanaDasa
        return NarayanaDasa()
    if s == "kalachakra":
        from jhora.dasas.kalachakra import KalachakraDasa
        return KalachakraDasa()
    if s == "brahma":
        from jhora.dasas.brahma import BrahmaDasa
        return BrahmaDasa()
    if s == "karaka":
        from jhora.dasas.karaka_dasa import KarakaDasa
        return KarakaDasa(options)
    if s == "shoola":
        from jhora.dasas.shoola import ShoolaDasa
        return ShoolaDasa(options)
    if s == "trikona":
        from jhora.dasas.trikona import TrikonaDasa
        return TrikonaDasa(options)
    if s == "varnada":
        from jhora.dasas.varnada import VarnadaDasa
        return VarnadaDasa(options)
    if s == "sthira":
        from jhora.dasas.sthira import SthiraDasa
        return SthiraDasa(options)
    if s == "navamsa":
        from jhora.dasas.navamsa import NavamsaDasa
        return NavamsaDasa(options)
    if s == "yogardha":
        from jhora.dasas.yogardha import YogardhaDasa
        return YogardhaDasa(options)
    if s == "niryana-shoola":
        from jhora.dasas.niryana_shoola import NiryanaShoolaDasa
        return NiryanaShoolaDasa(options)
    if s == "lagna-kendradi":
        from jhora.dasas.kendradi import LagnaKendradiDasa
        return LagnaKendradiDasa(options)
    if s == "kaala":
        from jhora.dasas.kaala import KaalaDasa
        return KaalaDasa(options)
    if s == "chakra":
        from jhora.dasas.chakra import ChakraDasa
        return ChakraDasa(options)
    if s == "mandooka":
        from jhora.dasas.mandooka import MandookaDasa
        return MandookaDasa(options)
    if s == "buddhi-gati":
        from jhora.dasas.buddhi_gati import BuddhiGatiDasa
        return BuddhiGatiDasa(options)
    if s == "drig":
        from jhora.dasas.drig import DrigDasa
        return DrigDasa(options)
    if s == "sudarshana":
        from jhora.dasas.sudarshana import SudarshanaDasa
        return SudarshanaDasa(options)
    if s == "tithi-ashtottari":
        from jhora.dasas.pravesha import TithiAshtottariDasa
        return TithiAshtottariDasa(options)
    if s == "tithi-yogini":
        from jhora.dasas.pravesha import TithiYoginiDasa
        return TithiYoginiDasa(options)
    if s == "karana-chaturaaseeti":
        from jhora.dasas.pravesha import KaranaChaturaaseetiDasa
        return KaranaChaturaaseetiDasa(options)
    if s == "yoga-vimsottari":
        from jhora.dasas.pravesha import YogaVimsottariDasa
        return YogaVimsottariDasa(options)
    if s == "naisargika":
        from jhora.dasas.naisargika import NaisargikaDasa
        return NaisargikaDasa(options)
    if s == "moola":
        from jhora.dasas.moola import MoolaDasa
        return MoolaDasa(options)
    if s == "tara":
        from jhora.dasas.moola import MoolaDasa
        if options is not None:
            options.tara_variant = True
        return MoolaDasa(options)
    from jhora.dasas.vimsottari import VimsottariDasa
    return VimsottariDasa(options)


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
    planet: str = typer.Option(None, "--planet", "-p",
                               help="USL planet (su/mo/ma/me/ju/ve/sa/ra/ke)"),
    factor: float = typer.Option(None, "--factor", "-f",
                                 help="USL speed factor n (e.g. 9)"),
    reverse: bool = typer.Option(False, "--reverse", "-r",
                                 help="Reverse USL direction (for Rahu/Ketu)"),
):
    """Show all special lagnas (Bhrigu Bindu, Indu, Varnada, etc.).

    Optionally include a User's Special Lagna: pass --planet (and optionally
    --factor / --reverse) to add an e.g. "Ju9" row computed from that planet's
    rising longitude advancing at factor × 15°/hr.
    """
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)

    from jhora.calc.special_lagnas import (
        compute_special_lagnas, SpecialLagna, _PLANET_ABBREV,
        user_special_lagna, user_special_lagna_name, UserSpecialLagnaConfig,
    )
    from jhora.types.graha import Graha
    lagnas = compute_special_lagnas(cd)

    # User's Special Lagna — optional row
    if planet:
        rev_map = {v.lower(): g for g, v in _PLANET_ABBREV.items()}
        graha = rev_map.get(planet.lower())
        if graha is None:
            console.print(f"[red]Unknown planet '{planet}'. "
                          f"Use one of: {', '.join(sorted(rev_map))}[/red]")
            raise typer.Exit(code=2)
        _factor = factor if factor is not None else 1.0
        config = UserSpecialLagnaConfig(graha, _factor, reverse)
        usl_lon = user_special_lagna(cd, graha, _factor, reverse)
        usl_name = user_special_lagna_name(config)
        if usl_lon is not None:
            usl_rasi = Rasi.from_longitude(usl_lon)
            lagnas.append(SpecialLagna(
                usl_name, usl_lon, usl_rasi.short_name,
                f"User's Special Lagna ({graha.full_name} × {_factor})",
            ))
        else:
            lagnas.append(SpecialLagna(usl_name, 0.0, "N/A",
                                       "Could not determine planet rise"))
            console.print("[yellow]Warning: could not compute USL rise "
                          f"for {graha.full_name}[/yellow]")

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
def kp(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    rp: bool = typer.Option(True, "--rp/--no-rp",
                            help="Show the KP Ruling Planets"),
    when: str = typer.Option("", "--when",
                             help="Date for the running dasa chain (YYYY-MM-DD; default now)"),
):
    """Krishnamurti Paddhati — cusps, lord chains and Ruling Planets.

    Uses Placidus cusps (as KP does) and the fourfold Vimsottari chain
    (sign / star / sub / sub-sub lord) for every cusp and planet. KP
    practitioners normally work in the Krishnamurti ayanamsa: pass
    --ayanamsa krishnamurti for that; the ayanamsa used is always shown.
    """
    from jhora.calc.kp import KPComputer

    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)

    kpc = KPComputer(cd).compute()

    cusp_table = Table(title=f"KP Cusps ({kpc.cusp_system}, ayanamsa: {kpc.ayanamsa})")
    cusp_table.add_column("House", style="cyan")
    cusp_table.add_column("Cusp", style="green")
    cusp_table.add_column("Sign", style="yellow")
    cusp_table.add_column("Sign Lord", style="magenta")
    cusp_table.add_column("Star Lord", style="white")
    cusp_table.add_column("Sub Lord", style="white")
    cusp_table.add_column("Sub-Sub", style="dim")
    for c in kpc.cusps:
        cusp_table.add_row(
            str(c.house), f"{c.longitude:.2f}°", c.sign.short_name,
            c.chain.sign_lord.short_name, c.chain.star_lord.short_name,
            c.chain.sub_lord.short_name, c.chain.sub_sub_lord.short_name,
        )
    console.print(cusp_table)

    planet_table = Table(title="KP Planets (Placidus bhava)")
    planet_table.add_column("Planet", style="cyan")
    planet_table.add_column("Longitude", style="green")
    planet_table.add_column("Sign", style="yellow")
    planet_table.add_column("House", style="cyan")
    planet_table.add_column("Sign Lord", style="magenta")
    planet_table.add_column("Star Lord", style="white")
    planet_table.add_column("Sub Lord", style="white")
    planet_table.add_column("Sub-Sub", style="dim")
    for p in kpc.planets:
        planet_table.add_row(
            p.graha.full_name, f"{p.longitude:.2f}°", p.sign.short_name,
            str(p.house), p.chain.sign_lord.short_name,
            p.chain.star_lord.short_name, p.chain.sub_lord.short_name,
            p.chain.sub_sub_lord.short_name,
        )
    console.print(planet_table)

    if rp:
        rp_table = Table(title=f"Ruling Planets (day lord: {kpc.day_lord.full_name})")
        rp_table.add_column("Planet", style="cyan")
        rp_table.add_column("Role", style="white")
        for r in kpc.ruling_planets:
            rp_table.add_row(r.graha.full_name, r.role_string)
        console.print(rp_table)

    _display_kp_significators(cd)
    _display_kp_dasa(cd, when)


def _display_kp_significators(cd):
    """The KP significators of each bhava."""
    from jhora.calc.kp import significators

    table = Table(title="KP Significators (strongest role first)")
    table.add_column("Bhava", style="cyan")
    table.add_column("Planets", style="white")
    for h, sigs in significators(cd).items():
        table.add_row(
            str(h),
            ", ".join(f"{s.graha.short_name} ({s.role_string})" for s in sigs)
            or "—",
        )
    console.print(table)


def _display_kp_dasa(cd, when: str = ""):
    """Vimsottari periods read KP-style (sub-lord oriented)."""
    from datetime import datetime

    from jhora.calc.kp import (
        kp_dasa_levels, kp_dasa_lords, significator_houses)
    from jhora.ephemeris.swe import SweEngine

    se = SweEngine()

    def _d(jd):
        y, m, d, _ = se.revjul(jd)
        return f"{int(y)}/{int(m):02d}/{int(d):02d}"

    inv = significator_houses(cd)

    def _sig(graha):
        return ",".join(str(h) for h in inv.get(graha, [])) or "—"

    table = Table(title="Vimsottari Dasa — KP view (sub lord of the dasa lord)")
    table.add_column("Lord", style="cyan")
    table.add_column("Start", style="green")
    table.add_column("End", style="yellow")
    table.add_column("Years", style="white")
    table.add_column("Bhava", style="cyan")
    table.add_column("Sign-Star-Sub-SubSub", style="white")
    table.add_column("Signifies", style="magenta")
    for r in kp_dasa_lords(cd):
        table.add_row(
            r.graha.full_name, _d(r.start_jd), _d(r.end_jd),
            f"{r.duration_years:.2f}", str(r.house), r.chain.string,
            _sig(r.graha),
        )
    console.print(table)

    target = None
    if when:
        target = datetime.strptime(when, "%Y-%m-%d").date()
    chain = kp_dasa_levels(cd, target)
    if chain:
        chain_table = Table(title="Running chain (KP view)")
        chain_table.add_column("Level", style="magenta")
        chain_table.add_column("Lord", style="cyan")
        chain_table.add_column("Bhava", style="cyan")
        chain_table.add_column("Sign-Star-Sub-SubSub", style="white")
        chain_table.add_column("Signifies", style="magenta")
        for r in chain:
            chain_table.add_row(
                r.level, r.graha.full_name, str(r.house), r.chain.string,
                _sig(r.graha),
            )
        console.print(chain_table)


@app.command()
def sahamas(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Show the 36 Tajaka sahamas (sensitive points) for a chart.

    Day/night formulas follow the true sunrise/sunset geometry at the
    birth place (a note names the basis used).
    """
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)
    from jhora.calc.sahama import compute_sahamas, is_day_birth
    day = is_day_birth(cd)
    planets = {g: {"longitude": p.longitude} for g, p in cd.planets.items()}
    rows = compute_sahamas(cd.ascendant, planets, day=day)
    table = Table(title=f"Sahamas (36, {'day' if day else 'night'} birth "
                        f"by sunrise/sunset)")
    table.add_column("Sahama", style="cyan")
    table.add_column("Meaning", style="white")
    table.add_column("Longitude", style="green")
    table.add_column("Sign", style="yellow")
    table.add_column("House", style="magenta")
    asc_sign = int(cd.ascendant // 30) % 12
    for s in rows:
        sign = int(s.longitude // 30) % 12
        house = (sign - asc_sign) % 12 + 1
        table.add_row(s.name, s.meaning, f"{s.longitude:.2f}°",
                      Rasi(sign).full_name, str(house))
    console.print(table)


@app.command()
def vargottama(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Show which planets (and the lagna) are vargottama.

    A body is vargottama in a varga when it occupies the same rasi as in the
    rasi chart (D-1); D-9 is the classical case, where a vargottama planet is
    strengthened. The concept extends to every divisional chart.
    """
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)
    from jhora.calc.vargottama import compute_vargottama
    res = compute_vargottama(cd)
    table = Table(title="Vargottama (same rasi in D-1 and the varga)")
    table.add_column("Body", style="cyan")
    table.add_column("Rasi", style="yellow")
    table.add_column("D-9", style="magenta")
    table.add_column("Vargottama vargas", style="green")
    for g, p in cd.planets.items():
        levels = res.planets.get(g, [])
        table.add_row(
            g.full_name, Rasi.from_longitude(p.longitude).full_name,
            "yes" if VargaLevel.D_9 in levels else "",
            ", ".join(lv.short_name for lv in levels) or "—")
    table.add_row(
        "Lagna", Rasi.from_longitude(cd.ascendant).full_name,
        "yes" if VargaLevel.D_9 in res.lagna else "",
        ", ".join(lv.short_name for lv in res.lagna) or "—")
    console.print(table)


@app.command()
def arudhas(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    varga: str = typer.Option("D-1", "--varga", "-v",
                              help="Divisional chart: D-1, D-9, D-10, ..."),
):
    """Show arudha padas (bhava + graha) with classical names.

    Arudhas are defined for every divisional chart; pass --varga to read
    them from that varga (default D-1). A7 Dara pada and A12 Upapada are
    shown explicitly.
    """
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)
    from jhora.calc.arudha import (
        bhava_pada_name, graha_pada_name, varga_arudhas)
    level = _parse_varga_level(varga)
    bhava, graha_arus = varga_arudhas(cd, level)

    bt = Table(title=f"Bhava Arudhas — {level.full_name}")
    bt.add_column("Pada", style="cyan")
    bt.add_column("Name", style="white")
    bt.add_column("Sign", style="yellow")
    for n in range(1, 13):
        bt.add_row(f"A{n}", bhava_pada_name(n), bhava[n].short_name)
    console.print(bt)

    gt = Table(title=f"Graha Arudhas — {level.full_name}")
    gt.add_column("Planet", style="cyan")
    gt.add_column("Pada", style="white")
    gt.add_column("Sign", style="yellow")
    for g in Graha:
        if g in graha_arus:
            gt.add_row(g.full_name, graha_pada_name(g),
                       graha_arus[g].short_name)
    console.print(gt)


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
def kuja_dosha(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Check Kuja Dosha (Mangal Dosha) — Mars affliction analysis."""
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)

    from jhora.calc.kuja_dosha import compute_kuja_dosha
    r = compute_kuja_dosha(cd)

    if r.has_dosha:
        console.print(f"[red bold]Kuja Dosha PRESENT[/red bold]")
    else:
        console.print(f"[green bold]No Kuja Dosha[/green bold]")

    table = Table(title="Kuja Dosha Analysis (Mars Affliction)")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="white")
    table.add_column("Detail", style="yellow")

    for label, has, house in [
        ("From Lagna", r.from_lagna, r.mars_from_lagna_house),
        ("From Moon", r.from_moon, r.mars_from_moon_house),
        ("From Venus", r.from_venus, r.mars_from_venus_house),
    ]:
        if has:
            table.add_row(label, "[red]✓ Afflicted[/red]", f"Mars in H{house}")
        else:
            table.add_row(label, "[dim]— Clean[/dim]", f"Mars in H{house}")

    table.add_row("Mars Sign", r.mars_sign, "Own sign — weakened" if r.mars_own_sign else "")
    table.add_row("Jupiter", "[green]Cancels[/green]" if r.jupiter_cancels else "[dim]No aspect[/dim]", "")
    table.add_row("Lagna", "[green]Weakens[/green]" if r.lagna_cancels else "", r.lagna_name)
    console.print(table)

    for m in r.messages:
        if m != "No Kuja Dosha":
            console.print(f"  {m}")


@app.command()
def panchanga(
    year: int = typer.Argument(None, help="Year (default: current)"),
    month: int = typer.Argument(None, help="Month (default: current)"),
    lat: float = typer.Option(28.61, "--lat", help="Latitude"),
    lon: float = typer.Option(77.21, "--lon", help="Longitude"),
    tz: str = typer.Option("+0530", "--tz", "-z", help="Timezone offset"),
    adjuncts: bool = typer.Option(False, "--adjuncts", help="Add Durmuhurta/Varjya windows"),
):
    """Monthly panchanga calendar — tithi, nakshatra, yoga, karana per day."""
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month

    from jhora.calc.monthly_panchanga import monthly_panchanga
    from jhora.charts.chart import ChartBuilder
    tz_offset = -ChartBuilder._parse_tz(tz, datetime(year, month, 1))
    days = monthly_panchanga(year, month, lat, lon, tz_offset,
                             with_adjuncts=adjuncts)
    table = Table(title=f"Panchanga — {year}-{month:02d}")
    table.add_column("Date", style="cyan")
    table.add_column("Day", style="white")
    table.add_column("Paksha", style="blue")
    table.add_column("Tithi", style="yellow")
    table.add_column("Nakshatra", style="magenta")
    table.add_column("Yoga", style="green")
    table.add_column("Karana", style="green")
    table.add_column("Sunrise", style="white")
    table.add_column("Sunset", style="white")
    table.add_column("Rahu Kalam", style="red")
    for d in days:
        table.add_row(d.date, d.weekday, d.paksha, d.tithi, d.nakshatra,
                      d.yoga, d.karana, d.sunrise, d.sunset, d.rahu_kalam)
    console.print(table)
    if adjuncts:
        win = Table(title=f"Daily Windows — {year}-{month:02d}")
        win.add_column("Date", style="cyan")
        win.add_column("DurMuhurta1", style="red")
        win.add_column("DurMuhurta2", style="red")
        win.add_column("Varjya1", style="red")
        win.add_column("Varjya2", style="red")
        for d in days:
            win.add_row(d.date, d.durmuhurta1, d.durmuhurta2,
                        d.varjya1, d.varjya2)
        console.print(win)


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
        console.print(f"    [dim]gate: {d['condition']}[/dim]")


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


@app.command("dasa-chart")
def dasa_chart_cmd(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    at: str = typer.Option("", "--at",
                           help="Date (YYYY-MM-DD) whose branch to expand; default now"),
    depth: int = typer.Option(3, "--depth", "-d",
                              help="Levels to expand (1=MD, 2=+AD, 3=+PD)"),
):
    """Dasa chart — the period tree around the running period.

    Lists all mahadasas, then expands the running mahadasa into its
    antardasas, the running antardasa into its pratyantardasas, and so on,
    flagging the period running at the given date (default: now).
    """
    from datetime import datetime

    from jhora.calc.dasa_chart import dasa_chart, format_dasa_chart

    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)
    when = datetime.strptime(at, "%Y-%m-%d").date() if at else None
    rows = dasa_chart(cd, when=when, depth=depth)
    console.print(format_dasa_chart(rows))


@app.command()
def dasa_entry(
    birthdata: str = typer.Argument(..., help="Birth data"),
    path: str = typer.Argument(..., help="Period path like 'Jupiter/Saturn' (MD/AD/...)"),
    system: str = typer.Option("vimsottari", "--system", "-s",
                               help="Dasa system (same names as the dasa command)"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Dasa entry chart — the sky at the moment a period opens.

    Casts the chart for the start of the given period at the birth
    place: entry lagna/Moon plus natal vs entry planet motion.
    """
    from jhora.calc.dasa_entry import dasa_entry as entry_for, format_dasa_entry, parse_path
    from jhora.dasas.base import DasaOptions

    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(year=bd["year"], month=bd["month"], day=bd["day"],
                       hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
                       tz=bd["tz"], ayanamsa=ayanamsa)
    segs = parse_path(path)
    if not segs:
        console.print("[red]Empty period path — e.g. 'Jupiter/Saturn'.[/red]")
        raise typer.Exit(1)
    engine = _get_dasa_engine(system, DasaOptions())
    try:
        period, entry = entry_for(cd, segs, engine=engine,
                                  opts=DasaOptions())
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    console.print(format_dasa_entry(segs, period, cd, entry))


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
def traditional_report(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    output: str = typer.Option("traditional_report.png", "--output", "-o",
                               help="Output image path (.png or .jpg)"),
    name: str = typer.Option("", "--name", "-n", help="Native's name"),
    sex: str = typer.Option("", "--sex", "-s", help="Native's sex (M/F)"),
    place: str = typer.Option("", "--place", "-p", help="Birth place name"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Generate a traditional one-page report as PNG/JPG."""
    from jhora.export.traditional import generate_traditional_report
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    path = generate_traditional_report(cd, output, name, sex, place)
    console.print(f"[green]Traditional report saved: {path}[/green]")


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
                               help="Vimsopaka scheme: shadvarga, saptavarga, dashavarga, shodasavarga, dwadasavarga"),
    bhava_varga: str = typer.Option(None, "--bhava-varga",
                                    help="Varga for Bhava Bala (e.g. D-9, D-10); default rasi"),
    ishta_kashta: bool = typer.Option(False, "--ishta-kashta",
                                      help="Show Ishta/Kashta Phala (beneficence vs difficulty)"),
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
        _print_bhava_bala(cd, bhava_varga)

    if vimsopaka:
        console.print()
        _print_vimsopaka(cd, scheme)

    if ishta_kashta:
        console.print()
        from jhora.calc.learning import ishta_kashta_phala
        ik = ishta_kashta_phala(cd)
        t = Table(title="Ishta/Kashta Phala (Beneficence vs Difficulty)")
        t.add_column("Planet", style="cyan")
        t.add_column("Ishta", style="green")
        t.add_column("Kashta", style="red")
        for r in ik:
            t.add_row(r["graha"], f"{r['ishta']:.0f}", f"{r['kashta']:.0f}")
        console.print(t)


def _print_bhava_bala(cd, varga: str = None):
    from jhora.types.rasi import Rasi
    from jhora.types.varga import VargaLevel
    if varga:
        try:
            lvl = _parse_varga_level(varga)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            return
        bb = BhavaBalaComputer.for_varga(cd, lvl)
        asc_lon = bb.chart.ascendant
        title = f"Bhava Bala — {lvl.name.replace('D_', 'D-')} House Strengths"
    else:
        bb = BhavaBalaComputer(cd)
        asc_lon = cd.ascendant
        title = "Bhava Bala — House Strengths"
    report = bb.compute_all()
    table = Table(title=title)
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
        rasi_idx = (int(asc_lon / 30) + h - 1) % 12
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
    parasara: bool = typer.Option(True, "--parasara/--varahamihira", help="Ashtakavarga tradition (Varahamihira matrix not yet validated — Parasara only)"),
    kakshya: Optional[str] = typer.Option(None, "--kakshya", "-k", help="Show Kakshya table for a planet: sun, moon, mars, mercury, jupiter, venus, saturn"),
    bala: bool = typer.Option(False, "--bala", "-b", help="Show the Bala view: strength at each reduction stage"),
):
    """Compute Ashtakavarga — planetary strengths by house."""
    if not parasara:
        console.print("[red]The Varahamihira Ashtakavarga matrix is not validated yet — Parasara only.[/red]")
        raise typer.Exit(1)
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

    # Bala view: strength at each reduction stage
    if bala:
        from jhora.calc.ashtakavarga import ashtakavarga_bala
        rows = ashtakavarga_bala(cd, parasara_moon=parasara,
                                 parasara_venus=parasara)
        bala_table = Table(title="Ashtakavarga Bala (reduction stages)")
        bala_table.add_column("Planet", style="cyan")
        bala_table.add_column("BAV", style="white")
        bala_table.add_column("Trikona", style="green")
        bala_table.add_column("Ekadhipatya", style="green")
        bala_table.add_column("Rasi Pinda", style="green")
        bala_table.add_column("Graha Pinda", style="green")
        bala_table.add_column("Sodhya Pinda", style="yellow bold")
        for b in rows:
            bala_table.add_row(b.graha.full_name, str(b.bav_total),
                               str(b.trikona_total),
                               str(b.ekadhipatya_total),
                               str(b.rasi_pinda), str(b.graha_pinda),
                               str(b.sodhya_pinda))
        console.print(bala_table)

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
    level: str = typer.Option("annual", "--level", "-l",
                              help="annual | monthly | 2.5-day | 5-hr | 25-min | 2-min"),
    index: int = typer.Option(1, "--index", "-i",
                              help="One-based sub-period index (1 = period start)"),
    sunrise: bool = typer.Option(False, "--sunrise",
                                 help="Cast at sunrise of the computed day"),
    vimshottari: str = typer.Option("none", "--vimshottari",
                                    help="Vimsottari from the return Moon: none, sesham, full"),
):
    """Compute a Tajaka return chart for a given year.

    The Tajaka year begins at the varsha pravesh (solar return); every level is
    a duodecimal division of that year, so --level monthly --index 3 gives the
    third monthly chart of the year.
    """
    from jhora.calc.tajaka import (
        TajakaLevel, build_tajaka_level_chart, compute_harsha_bala,
        compute_patyayini_dasa, compute_mudda_dasa,
    )
    level_map = {
        "annual": TajakaLevel.ANNUAL,
        "monthly": TajakaLevel.MONTHLY,
        "2.5-day": TajakaLevel.TWO_AND_HALF_DAY,
        "5-hr": TajakaLevel.FIVE_HOUR,
        "25-min": TajakaLevel.TWENTY_FIVE_MIN,
        "2-min": TajakaLevel.TWO_MIN,
    }
    lvl = level_map.get(level.lower())
    if lvl is None:
        console.print(f"[red]Unknown level '{level}'. Use one of: "
                      f"{', '.join(level_map)}[/red]")
        raise typer.Exit(code=2)

    bd = parse_birthdata(birthdata)
    cb = ChartBuilder()
    cb.swe.set_sidereal_mode(ayanamsa)
    natal = cb.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    try:
        taj = build_tajaka_level_chart(
            cb.swe, cb, natal, target_year, lvl, index, sunrise,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2)
    chart = taj.chart

    ay, am, ad, ah = cb.swe.revjul(taj.anchor_jd)
    my, mm, md_, mh = cb.swe.revjul(taj.moment_jd)
    console.print(f"\n[bold]Tajaka anchor (varsha pravesh)[/bold]: "
                  f"{int(ay)}-{int(am):02d}-{int(ad):02d} {ah:.2f}h UT")
    console.print(f"[bold]{lvl.label} chart[/bold] index {taj.index}"
                  f"{' (sunrise)' if taj.sunrise else ''}: "
                  f"{int(my)}-{int(mm):02d}-{int(md_):02d} {mh:.2f}h UT")
    console.print(f"Natal lagna: {natal.ascendant:.2f}° ({int(natal.ascendant//30)%12})")
    console.print(f"Year index: {taj.year_index}, Muntha sign: {taj.muntha_sign}")

    table = Table(title=f"Solar Return Chart ({lvl.label} #{taj.index}, {target_year})")
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

    if vimshottari.lower() not in ("none", "sesham", "full"):
        console.print("[red]Unknown --vimshottari mode. Use: none, sesham, full.[/red]")
        raise typer.Exit(code=2)
    if vimshottari.lower() != "none":
        from jhora.calc.tajaka import annual_vimsottari
        av = annual_vimsottari(
            chart, taj.moment_jd or taj.varsha_pravesh_jd,
            sesham=(vimshottari.lower() == "sesham"))
        _display_dasa_table(av, f"Annual Vimsottari ({vimshottari.lower()})")

    from jhora.calc.tajaka_yoga import tajaka_yogas
    yogas = tajaka_yogas(chart)
    yg_table = Table(title="Tajaka Yogas")
    yg_table.add_column("Yoga", style="cyan")
    yg_table.add_column("Planets", style="yellow")
    yg_table.add_column("Detail", style="white")
    for r in yogas.ithasalas:
        flags = []
        if r.manahoo_by:
            flags.append(f"Manahoo by {r.manahoo_by.full_name}")
        if r.radda:
            flags.append("Radda")
        if r.kamboola:
            flags.append("Kamboola")
        yg_table.add_row(f"Ithasala ({r.itype})",
                         f"{r.g1.short_name}–{r.g2.short_name}",
                         "; ".join(flags))
    for a, b in yogas.eesarphas:
        yg_table.add_row("Eesarpha", f"{a.short_name}–{b.short_name}", "")
    for a, b, m in yogas.naktas:
        yg_table.add_row("Nakta",
                         f"{a.short_name}–{b.short_name} via {m.short_name}",
                         "")
    for a, b, m in yogas.yamayas:
        yg_table.add_row("Yamaya",
                         f"{a.short_name}–{b.short_name} via {m.short_name}",
                         "")
    if yogas.ishkavala:
        yg_table.add_row("Ishkavala", "all", "kendras + panapharas only")
    if yogas.induvara:
        yg_table.add_row("Induvara", "all", "apoklimas only")
    for ll, x in yogas.khallasaras:
        yg_table.add_row("Khallasara",
                         f"{ll.short_name} blocks {x.short_name}", "")
    console.print(yg_table)


@app.command()
def progression(
    birthdata: str = typer.Argument(..., help="Birth data"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    age: float = typer.Option(None, "--age", help="Age in years (default: current age)"),
):
    """Compute secondary progressions (1 day = 1 year) and aspects to natal."""
    from jhora.calc.progressions import ProgressionCalculator
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
def yoga_pravesha(
    birthdata: str = typer.Argument(..., help="Birth data"),
    year: int = typer.Option(None, "--year", "-y", help="Target year (default: current year)"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Compute Yoga Pravesha chart — annual (Sun+Moon) return for year-ahead prediction."""
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

    from jhora.calc.pravesha import YogaPraveshaCalculator
    yp = YogaPraveshaCalculator(cd)
    console.print(f"Natal yoga point: {yp.natal_yoga:.2f}°")

    entries = yp.compute_range(year - 1, year + 1)
    table = Table(title=f"Yoga Pravesha Charts ({year-1}-{year+1})")
    table.add_column("Year", style="cyan")
    table.add_column("Date/Time (UT)", style="white")
    table.add_column("Lagna", style="yellow")
    table.add_column("Yoga Angle", style="white")

    from jhora.calc.pravesha import yoga_angle
    for e in entries:
        if e.chart is None:
            continue
        lagna = Rasi.from_longitude(e.chart.ascendant).short_name
        m = e.chart.planet(Graha.MOON).longitude
        s = e.chart.planet(Graha.SUN).longitude
        marker = " ◀" if e.year == year else ""
        table.add_row(
            f"{e.year}{marker}", e.event_date, lagna,
            f"{yoga_angle(s, m):.2f}°",
        )
    console.print(table)


@app.command()
def nakshatra_pravesha(
    birthdata: str = typer.Argument(..., help="Birth data"),
    year: int = typer.Option(None, "--year", "-y", help="Target year (default: current year)"),
    month: int = typer.Option(None, "--month", "-m", help="Target month 1-12 (default: current month)"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Compute Nakshatra Pravesha chart — monthly lunar return to natal Moon."""
    from datetime import datetime
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )

    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    from jhora.calc.pravesha import NakshatraPraveshaCalculator
    np = NakshatraPraveshaCalculator(cd)
    e = np.compute(year, month)
    if e.chart is None:
        console.print("[red]Could not compute Nakshatra Pravesha chart.[/red]")
        return
    lagna = Rasi.from_longitude(e.chart.ascendant).short_name
    moon = Rasi.from_longitude(e.chart.planet(Graha.MOON).longitude).short_name
    console.print(f"Nakshatra Pravesha {year}-{month:02d}: {e.event_date} "
                  f"(lagna {lagna}, Moon {moon})")


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
    parasara: bool = typer.Option(True, "--parasara/--varahamihira", help="Ashtakavarga tradition (Varahamihira matrix not yet validated — Parasara only)"),
):
    """Current transit positions vs natal chart with Ashtakavarga scores."""
    from jhora.calc.gochara import compute_transits

    if not parasara:
        console.print("[red]The Varahamihira Ashtakavarga matrix is not validated yet — Parasara only.[/red]")
        raise typer.Exit(1)
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
    table.add_column("Vedha", style="red")

    for e in result.entries:
        ret = "R" if e.is_retrograde else ""
        fav_s = "[green]✓[/green]" if e.is_favorable else "[red]✗[/red]"
        if e.is_vedha:
            vedha_s = f"[red]H{e.vedha_house} obstructs[/red]"
        elif e.vedha_house:
            vedha_s = f"[dim]H{e.vedha_house}[/dim]"
        else:
            vedha_s = ""
        table.add_row(
            e.graha.short_name, e.transit_rasi_name,
            f"{e.transit_degrees:.1f}", ret,
            str(e.house_from_lagna), str(e.house_from_moon),
            str(e.bav_score), str(e.sav_score), fav_s, vedha_s,
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
def upagrahas(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Upagrahas — solar points plus time-based Gulika/Mandi."""
    import datetime as _dt

    from jhora.calc.upagraha import (compute_solar_upagrahas,
                                     compute_temporal_upagrahas)

    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    table = Table(title="Solar Upagrahas (from Sun)")
    table.add_column("Upagraha", style="cyan")
    table.add_column("Longitude", style="yellow")
    table.add_column("Rasi", style="green")
    for u in compute_solar_upagrahas(cd.planet(Graha.SUN).longitude):
        table.add_row(u.name, f"{u.longitude:.2f}°", u.rasi)
    console.print(table)

    try:
        from jhora.calc.muhurta import _sunrise_sunset
        day = _dt.datetime(bd["year"], bd["month"], bd["day"])
        tz_offset = -ChartBuilder._parse_tz(cd.timezone, cd.birth_date)
        sr, ss = _sunrise_sunset(day, cd.latitude, cd.longitude,
                                 tz_offset)
        temporal = compute_temporal_upagrahas(cd, sr, ss)
    except Exception:
        temporal = []
    if temporal:
        ttable = Table(title="Temporal Upagrahas (weekday portions)")
        ttable.add_column("Upagraha", style="cyan")
        ttable.add_column("Longitude", style="yellow")
        ttable.add_column("Rasi", style="green")
        for u in temporal:
            ttable.add_row(u.name, f"{u.longitude:.2f}°", u.rasi)
        console.print(ttable)
    else:
        console.print("[dim]Temporal upagrahas unavailable for this chart.[/dim]")


@app.command()
def maitri(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Graha Maitri — natural, temporal and compound (Panchadha) friendships."""
    from jhora.calc.maitri import GRAHAS, maitri_table, naisargika, tatkalika

    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    rasis = {g: cd.planet(g).rasi.value for g in GRAHAS}
    table = Table(title="Panchadha Maitri (row → column)")
    table.add_column("", style="cyan")
    for g in GRAHAS:
        table.add_column(g.short_name, style="yellow")
    names = maitri_table(rasis)
    for a in GRAHAS:
        table.add_row(a.short_name,
                      *[names[(a, b)] for b in GRAHAS])
    console.print(table)
    nat = Table(title="Naisargika (natural)")
    nat.add_column("", style="cyan")
    for g in GRAHAS:
        nat.add_column(g.short_name, style="green")
    for a in GRAHAS:
        nat.add_row(a.short_name,
                    *[naisargika(a, b) if a != b else "—" for b in GRAHAS])
    console.print(nat)
    tmp = Table(title="Tatkalika (temporal)")
    tmp.add_column("", style="cyan")
    for g in GRAHAS:
        tmp.add_column(g.short_name, style="magenta")
    for a in GRAHAS:
        tmp.add_row(a.short_name,
                    *["—" if a == b else tatkalika(rasis[a], rasis[b])
                      for b in GRAHAS])
    console.print(tmp)


@app.command()
def special_points(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Special sensitive points — Baadhaka, Pushkara, Khara navamsa, 22nd drekkana."""
    from jhora.calc.special_points import (
        baadhaka_lord, baadhaka_sthana, drekkana_22, khara_navamsa_64,
        planets_in_mrityu_bhaga, planets_in_pushkara_bhaga,
        planets_in_pushkara_navamsa,
    )

    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    lagna_rasi = int(cd.ascendant // 30) % 12
    badha = baadhaka_sthana(lagna_rasi)
    lons = {g: p.longitude for g, p in cd.planets.items()}
    moon_lon = cd.planet(Graha.MOON).longitude
    table = Table(title="Special Points")
    table.add_column("Point", style="cyan")
    table.add_column("Sign", style="yellow")
    table.add_column("Detail", style="white")
    table.add_row("Baadhaka sthana",
                  Rasi(badha).short_name,
                  f"lord {baadhaka_lord(lagna_rasi).full_name}")
    table.add_row("Pushkara navamsa", "—",
                  ", ".join(g.full_name
                            for g in planets_in_pushkara_navamsa(lons))
                  or "none")
    table.add_row("Pushkara bhaga", "—",
                  ", ".join(g.full_name
                            for g in planets_in_pushkara_bhaga(lons))
                  or "none")
    table.add_row("64th navamsa (Khara)",
                  Rasi(khara_navamsa_64(moon_lon)).short_name, "from Moon")
    table.add_row("22nd drekkana",
                  Rasi(drekkana_22(moon_lon)).short_name, "from Moon")
    try:
        import datetime as _dt
        import math as _math

        from jhora.calc.muhurta import _sunrise_sunset
        from jhora.calc.upagraha import compute_temporal_upagrahas
        day = _dt.datetime(bd["year"], bd["month"], bd["day"])
        tz_offset = -ChartBuilder._parse_tz(cd.timezone, cd.birth_date)
        sr, ss = _sunrise_sunset(day, cd.latitude, cd.longitude,
                                 tz_offset)
        temporal = {r.name: r.longitude
                    for r in compute_temporal_upagrahas(cd, sr, ss)}
        mandi_lon = temporal.get("Mandi", _math.nan)
    except Exception:
        mandi_lon = _math.nan
    bodies = [cd.planet(g).longitude for g in
              (Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
               Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU,
               Graha.KETU)]
    bodies += [mandi_lon, cd.ascendant]
    names = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
             "Saturn", "Rahu", "Ketu", "Mandi", "Lagna"]
    table.add_row("Mrityu bhaga", "—",
                  ", ".join(names[i]
                            for i in planets_in_mrityu_bhaga(bodies))
                  or "none")
    console.print(table)


@app.command()
def sade_sati(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Sade Sati timeline — Saturn phase dates + Kantaka/Ashtama Shani."""
    from datetime import date
    from jhora.calc.gochara import sade_sati_timeline

    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    moon_rasi = cd.planets[Graha.MOON].rasi.value
    phases = sade_sati_timeline(moon_rasi, ayanamsa)
    today = date.today()

    console.print(f"[dim]Natal Moon: {Rasi(moon_rasi).short_name}  "
                  f"(dates are UTC)[/dim]")
    table = Table(title="Sade Sati & Saturn Transits Timeline")
    table.add_column("Kind", style="cyan")
    table.add_column("Phase", style="yellow")
    table.add_column("Saturn in", style="green")
    table.add_column("Start", style="white")
    table.add_column("End", style="white")
    table.add_column("Now", style="bold")
    for p in phases:
        now = "[bold green]← now[/bold green]" \
            if p.start <= today <= p.end else ""
        start_s = f"~{p.start}" if not p.start_exact else str(p.start)
        end_s = f"~{p.end}" if not p.end_exact else str(p.end)
        table.add_row(p.kind, p.phase, Rasi(p.sign).short_name,
                      start_s, end_s, now)
    console.print(table)


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
    adjuncts: bool = typer.Option(False, "--adjuncts", help="Show daily Durmuhurta/Varjya/Panchaka windows and Bala grades"),
    janma_nakshatra: Optional[str] = typer.Option(None, "--janma-nakshatra", help="Janma nakshatra for Chandra/Tara Bala (used only with --adjuncts)"),
):
    """Muhurta (Electional Astrology) — evaluate or find auspicious times."""
    from jhora.calc.muhurta import (
        MuhurtaTask, Tara, compute_adjuncts, evaluate_time, find_muhurta,
        _datetime_to_jd, _sunrise_sunset,
    )
    from jhora.types.nakshatra import Nakshatra
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

    try:
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        console.print("[red]Invalid date/time format. Use YYYY-MM-DD HH:MM[/red]")
        raise typer.Exit(1)

    # _parse_tz returns negative for positive timezones; muhurta module expects positive.
    # The event date resolves historical DST for IANA zone names.
    raw_tz = ChartBuilder._parse_tz(tz, dt)
    tz_offset = -raw_tz if raw_tz < 0 else raw_tz

    def _parse_janma(value: Optional[str]):
        # --janma-nakshatra is honored only with --adjuncts so it never changes
        # the default output by itself.
        if value is None:
            return None
        key = value.strip().upper().replace(" ", "_").replace("-", "_")
        key = {"ASHVINI": "ASVINI", "ASHWINI": "ASVINI", "ASWINI": "ASVINI"}.get(key, key)
        try:
            return Nakshatra[key]
        except KeyError:
            console.print(f"[red]Unknown Janma nakshatra: {value}[/red]")
            raise typer.Exit(2)

    def _hhmm(jd_value: float, base_jd: float) -> str:
        total = int(round((((jd_value - base_jd) * 24.0) % 24.0) * 60.0)) % (24 * 60)
        return f"{total // 60:02d}:{total % 60:02d}"

    def _print_adjuncts(day: datetime, janma) -> None:
        info = compute_adjuncts(day, lat, lon, tz_offset, janma)
        base_jd = _datetime_to_jd(day.replace(hour=0, minute=0, second=0, microsecond=0), tz_offset)
        sunrise, sunset = _sunrise_sunset(day, lat, lon, tz_offset)

        windows = Table(title=f"Daily Muhurta Adjuncts — {day.strftime('%Y-%m-%d')}")
        windows.add_column("Item", style="cyan")
        windows.add_column("Start", style="yellow")
        windows.add_column("End", style="yellow")
        windows.add_row("Sunrise", _hhmm(sunrise, base_jd), "")
        windows.add_row("Sunset", _hhmm(sunset, base_jd), "")
        for index, label in enumerate(("DurMuhurta1", "DurMuhurta2")):
            if index < len(info.durmuhurta):
                win = info.durmuhurta[index]
                windows.add_row(label, _hhmm(win.start, base_jd), _hhmm(win.end, base_jd))
            else:
                windows.add_row(label, "—", "—")
        for index, label in enumerate(("Varjya1", "Varjya2")):
            if index < len(info.varjya):
                win = info.varjya[index]
                windows.add_row(label, _hhmm(win.start, base_jd), _hhmm(win.end, base_jd))
            else:
                windows.add_row(label, "—", "—")
        console.print(windows)

        segments = Table(title="Panchaka Segments")
        segments.add_column("#", style="cyan")
        segments.add_column("Start", style="yellow")
        segments.add_column("End", style="yellow")
        segments.add_column("Category", style="green")
        for number, seg in enumerate(info.panchaka, start=1):
            segments.add_row(str(number), _hhmm(seg.start, base_jd),
                             _hhmm(seg.end, base_jd), seg.kind)
        console.print(segments)

        console.print(f"Chandra Bala: {info.chandra_bala.value}")
        if info.tara_bala is None:
            console.print("Tara Bala: unavailable (no Janma nakshatra)")
        else:
            if info.tara_bala is Tara.JANMA:
                tara_class = "neutral"
            elif info.tara_auspicious:
                tara_class = "auspicious"
            else:
                tara_class = "inauspicious"
            console.print(f"Tara Bala: {info.tara_bala.value} ({tara_class})")

    janma = _parse_janma(janma_nakshatra) if adjuncts else None

    if find:
        results = find_muhurta(dt, lat, lon, tz_offset, t, jnama_nakshatra=janma, step_minutes=10)
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
        if adjuncts:
            _print_adjuncts(dt, janma)
        return

    r = evaluate_time(dt, lat, lon, tz_offset, t, jnama_nakshatra=janma)
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

    if adjuncts:
        _print_adjuncts(dt, janma)


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


def _verify_and_print(answer: str, cd, passages=None, disable=False):
    """Mechanical fact-check of an answer against computed chart data.

    Prints a ✓/⚠ verification report. Never alters the answer; failures
    are silent so verification can never break a reading.
    """
    if disable or not answer or cd is None:
        return
    try:
        from jhora.ai.verify import verify_answer, format_report
        report = format_report(verify_answer(answer, cd, passages or []))
        if report:
            console.print(f"[dim]{report}[/dim]")
    except Exception:
        pass


def _repair_tracker():
    """Notify callback that records whether a repair round ran.

    The streamed draft can differ from the repaired return text — callers
    re-print the repaired text when ``state["repaired"]`` is set, then
    reset it for the next turn.
    """
    state = {"repaired": False}

    def _notify(msg: str):
        state["repaired"] = True
        console.print(f"[dim]{msg.strip()}[/dim]", highlight=False)

    return state, _notify


def _print_repaired(state, text: str):
    if state["repaired"]:
        console.print("\n[bold]Repaired reading:[/bold]\n")
        console.print(text, highlight=False)
        state["repaired"] = False


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
    chat: bool = typer.Option(False, "--chat",
                              help="Interactive conversation mode (ask only)"),
    preferred_model: str = typer.Option("", "--preferred-model",
                                        help="LM Studio model key to auto-load when missing"),
    ensure_context: int = typer.Option(8192, "--ensure-context",
                                       help="Context requested when auto-loading (halved on refusal)"),
    temperature: float = typer.Option(0.2, "--temperature",
                                      help="Sampling temperature (0.2 factual)"),
    no_verify: bool = typer.Option(False, "--no-verify",
                                   help="Skip mechanical answer verification"),
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

    config = AiConfig(provider=provider, base_url=base_url, max_context_tokens=context,
                      preferred_model=preferred_model, ensure_context=ensure_context,
                      temperature=temperature)
    if model:
        config.model = model
    engine = AiEngine(config)

    health = engine.health_check()
    if not health["ok"]:
        console.print(f"[red]AI server unreachable: {health['error']}[/red]")
        console.print("[yellow]Make sure your LLM server is running.[/yellow]")
        raise typer.Exit(1)

    if not model and health.get("status") == "no_model":
        console.print(f"[red]{health['message']}[/red]")
        console.print("[yellow]Install a chat model (≤9GB) or load one, then retry.[/yellow]")
        raise typer.Exit(1)

    used = health.get("model") or engine.config.model or model
    console.print(f"[dim]Using {provider} / {used}...[/dim]\n")

    def _on_token(tok: str):
        console.print(tok, end="", highlight=False)

    tracker, _notify = _repair_tracker()

    if chat:
        if not question:
            console.print("[red]--question required as initial question in --chat mode[/red]")
            raise typer.Exit(1)
        history: list = []
        console.print(f"[bold yellow]AI Chat ({provider}/{used})[/bold yellow]  "
                      "Type 'quit' or Ctrl-C to exit.\n")
        try:
            while True:
                answer, history, reset = engine.chat(
                    cd, question, history=history, on_token=_on_token,
                    notify=_notify)
                console.print()
                _print_repaired(tracker, answer)
                _verify_and_print(answer, cd, disable=no_verify)
                if reset:
                    console.print("[dim][context compacted][/dim]")
                question = Prompt.ask("[bold green]You[/bold green]")
                if question.lower() in ("quit", "exit", "q", ""):
                    break
                console.print()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Chat ended.[/dim]")
        return

    if mode == "ask" and not question:
        console.print("[red]--question required for ask mode[/red]")
        raise typer.Exit(1)

    if mode == "interpret":
        text = engine.interpret(cd, style, topic, on_token=_on_token,
                                notify=_notify)
    elif mode == "ask":
        text = engine.ask(cd, question, on_token=_on_token, notify=_notify)
    elif mode == "remedies":
        text = engine.remedies(cd, on_token=_on_token, notify=_notify)
    else:
        console.print(f"[red]Unknown mode: {mode}[/red]")
    console.print()
    if mode in ("interpret", "ask", "remedies"):
        _print_repaired(tracker, text)
        _verify_and_print(text, cd, disable=no_verify)
    console.print()


@app.command()
def teach(
    question: str = typer.Argument(..., help="What do you want to learn about Vedic astrology?"),
    birthdata: str = typer.Option(None, "--chart", "-c", help="Optional: your birth data for chart-based teaching"),
    provider: str = typer.Option("ollama", "--provider", "-p"),
    model: str = typer.Option("", "--model", "-m"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
    chat: bool = typer.Option(False, "--chat",
                              help="Interactive conversation mode"),
    preferred_model: str = typer.Option("", "--preferred-model",
                                        help="LM Studio model key to auto-load when missing"),
    ensure_context: int = typer.Option(8192, "--ensure-context",
                                       help="Context requested when auto-loading (halved on refusal)"),
    temperature: float = typer.Option(0.2, "--temperature",
                                      help="Sampling temperature (0.2 factual)"),
    no_verify: bool = typer.Option(False, "--no-verify",
                                   help="Skip mechanical answer verification"),
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

    teacher = AiTeacher(provider=provider, base_url=base_url, model=model or "",
                        temperature=temperature)

    from jhora.ai.engine import AiEngine, AiConfig
    resolver = AiEngine(AiConfig(provider=provider, base_url=base_url, model=model,
                                 preferred_model=preferred_model,
                                 ensure_context=ensure_context,
                                 temperature=temperature))
    health = resolver.health_check()
    if not health["ok"]:
        console.print(f"[red]AI server unreachable: {health['error']}[/red]")
        raise typer.Exit(1)
    if not model and health.get("status") == "no_model":
        console.print(f"[red]{health['message']}[/red]")
        raise typer.Exit(1)
    if health.get("status") == "ok" and health.get("model"):
        teacher.model = health["model"]

    def _print(tok):
        console.print(tok, end="", highlight=False)

    tracker, _notify = _repair_tracker()

    console.print(f"[dim]Teacher ({provider} / {teacher.model}):[/dim]\n")

    if chat:
        history: list = []
        console.print(f"[bold yellow]AI Teacher ({provider}/{teacher.model})[/bold yellow]  "
                      "Type 'quit' or Ctrl-C to exit.\n")
        try:
            while True:
                answer, history, reset = teacher.chat(
                    question, chart=chart, history=history, on_token=_print,
                    notify=_notify)
                console.print()
                _print_repaired(tracker, answer)
                _verify_and_print(
                    answer, chart,
                    [s.get("excerpt", "") for s in teacher.last_sources
                     if isinstance(s, dict)], disable=no_verify)
                if reset:
                    console.print("[dim][context compacted — fresh conversation][/dim]")
                question = Prompt.ask("[bold green]You[/bold green]")
                if question.lower() in ("quit", "exit", "q", ""):
                    break
                console.print()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Chat ended.[/dim]")
        return

    text = teacher.ask(question, chart=chart, on_token=_print,
                       notify=_notify)
    console.print()
    _print_repaired(tracker, text)
    _verify_and_print(
        text, chart,
        [s.get("excerpt", "") for s in teacher.last_sources
         if isinstance(s, dict)], disable=no_verify)
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


@app.command()
def choghadiya(
    date_str: Optional[str] = typer.Argument(None, help="Date YYYY-MM-DD (default: today)"),
    lat: float = typer.Option(28.61, "--lat", help="Latitude"),
    lon: float = typer.Option(77.21, "--lon", help="Longitude"),
    tz: float = typer.Option(5.5, "--tz", help="Timezone offset hours east of UTC"),
    now: bool = typer.Option(False, "--now", help="Highlight the current slot"),
):
    """Choghadiya — 8 day + 8 night auspicious/inauspicious time slots."""
    from jhora.calc.choghadiya import choghadiya_day, GRAHA_NAME
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cd = choghadiya_day(dt, lat, lon, tz)
    current = None
    if now:
        current = cd.current_slot(datetime.now())

    table = Table(title=f"Choghadiya — {dt.strftime('%A %d %B %Y')}  ({lat:.2f}°, {lon:.2f}°)")
    table.add_column("#", style="dim", width=3)
    table.add_column("Slot", style="cyan", width=8)
    table.add_column("Rating", width=8)
    table.add_column("Lord", style="magenta", width=8)
    table.add_column("Start", style="white")
    table.add_column("End", style="white")
    table.add_column("Duration", style="dim")

    rating_style = {"Good": "green", "Bad": "red", "Neutral": "yellow"}

    for i, slot in enumerate(cd.day_slots, 1):
        rs = rating_style.get(slot.rating, "white")
        is_current = current is not None and slot is current
        label = f"[bold]{slot.name}[/bold]" if is_current else slot.name
        rating_label = f"[{rs}]{slot.rating}[/{rs}]"
        dur = f"{slot.duration_minutes:.0f}m"
        table.add_row(str(i), label, rating_label, slot.lord.name,
                      slot.start.strftime("%H:%M"), slot.end.strftime("%H:%M"), dur)

    for i, slot in enumerate(cd.night_slots, 9):
        rs = rating_style.get(slot.rating, "white")
        is_current = current is not None and slot is current
        label = f"[bold]{slot.name}[/bold]" if is_current else slot.name
        rating_label = f"[{rs}]{slot.rating}[/{rs}]"
        dur = f"{slot.duration_minutes:.0f}m"
        table.add_row(str(i), label, rating_label, slot.lord.name,
                      slot.start.strftime("%H:%M"), slot.end.strftime("%H:%M"), dur)

    console.print(table)
    if current:
        remaining = (current.end - datetime.now()).total_seconds() / 60.0
        console.print(f"\n[bold]Current: {current.name} ({current.rating}) "
                      f"— {remaining:.0f} min remaining[/bold]")


@app.command()
def hora(
    date_str: Optional[str] = typer.Argument(None, help="Date YYYY-MM-DD (default: today)"),
    lat: float = typer.Option(28.61, "--lat", help="Latitude"),
    lon: float = typer.Option(77.21, "--lon", help="Longitude"),
    tz: float = typer.Option(5.5, "--tz", help="Timezone offset hours east of UTC"),
    now: bool = typer.Option(False, "--now", help="Highlight the current hora"),
):
    """Planetary hours (Hora) — the 24-hora cycle for a day."""
    from jhora.calc.hora import hora_slots, current_hora, WEEKDAY_LORD
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    slots = hora_slots(dt, lat, lon, tz)
    current = current_hora(datetime.now(), lat, lon, tz) if now else None

    wd = (dt.weekday() + 1) % 7
    table = Table(title=f"Hora — {dt.strftime('%A %d %B %Y')}  "
                        f"(day lord {WEEKDAY_LORD[wd].full_name})")
    table.add_column("#", style="dim", width=3)
    table.add_column("Part", style="blue", width=5)
    table.add_column("Lord", style="magenta", width=8)
    table.add_column("Start", style="white")
    table.add_column("End", style="white")
    table.add_column("Duration", style="dim")
    for slot in slots:
        label = f"[bold]{slot.lord_name}[/bold]" if slot is current else slot.lord_name
        dur = (slot.end - slot.start).total_seconds() / 60.0
        table.add_row(str(slot.index + 1), slot.part, label,
                      slot.start.strftime("%H:%M"), slot.end.strftime("%H:%M"),
                      f"{dur:.0f}m")
    console.print(table)
    if current:
        remaining = (current.end - datetime.now()).total_seconds() / 60.0
        console.print(f"\n[bold]Current: {current.lord_name} hora — "
                      f"{remaining:.0f} min remaining[/bold]")


@app.command()
def sphutas(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Sphutas — Prasna Marga auspicious-point longitudes."""
    from jhora.calc.sphuta import compute_sphutas
    from jhora.calc.upagraha import compute_temporal_upagrahas
    from jhora.calc.muhurta import _sunrise_sunset
    from jhora.types.graha import Graha
    from jhora.types.rasi import Rasi
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    day_start = datetime(bd["year"], bd["month"], bd["day"])
    tz_east = -ChartBuilder._parse_tz(bd["tz"], day_start)
    # Sunrise/sunset JDs on the civil-day scale, as upagraha expects.
    sunrise, sunset = _sunrise_sunset(day_start, bd["lat"], bd["lon"], tz_east)
    temporal = compute_temporal_upagrahas(cd, sunrise, sunset)
    gulika = next((r.longitude for r in temporal if r.name == "Gulika"), None)
    if gulika is None:
        console.print("[red]Could not determine Gulika for this date[/red]")
        raise typer.Exit(1)
    pl = cd.planet
    sph = compute_sphutas(
        lagna=cd.ascendant, sun=pl(Graha.SUN).longitude,
        moon=pl(Graha.MOON).longitude, mars=pl(Graha.MARS).longitude,
        jupiter=pl(Graha.JUPITER).longitude,
        venus=pl(Graha.VENUS).longitude, rahu=pl(Graha.RAHU).longitude,
        gulika=gulika)
    table = Table(title=f"Sphutas — {birthdata}")
    table.add_column("Sphuta", style="cyan")
    table.add_column("Longitude", style="yellow")
    table.add_column("Rasi", style="green")
    for name, val in sph.items():
        r = Rasi.from_longitude(val)
        table.add_row(name, f"{val:.2f}°", r.short_name)
    console.print(table)
    from jhora.calc.sphuta import compute_yogi
    yg = compute_yogi(pl(Graha.MOON).longitude, pl(Graha.SUN).longitude)
    console.print(f"\n[bold]Yogi:[/bold] {yg['Yogi']}   "
                  f"[bold]Avayogi:[/bold] {yg['Avayogi']}   "
                  f"[bold]Sahayogi:[/bold] {yg['Sahayogi']}")


@app.command()
def remedies(
    birthdata: str = typer.Argument(..., help="Birth data: 'YYYY-MM-DD HH:MM:SS TZ LAT LON'"),
    when: Optional[str] = typer.Option(None, "--when", help="Date YYYY-MM-DD for Sade Sati"),
    partner: Optional[str] = typer.Option(None, "--partner", help="Partner birth data for marriage remedies"),
    ayanamsa: str = typer.Option(DEFAULT_AYANAMSA, "--ayanamsa", "-a"),
):
    """Rule-based remedies — Ishta devata, gemstone, mantra, charity, doshas."""
    from jhora.calc.remedies import compute_marriage_remedies, compute_remedies
    bd = parse_birthdata(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    w = datetime.strptime(when, "%Y-%m-%d") if when else None
    report = compute_remedies(cd, when=w)
    if partner:
        bd2 = parse_birthdata(partner)
        partner_cd = builder.build(
            year=bd2["year"], month=bd2["month"], day=bd2["day"],
            hour=bd2["hour"], lat=bd2["lat"], lon=bd2["lon"],
            tz=bd2["tz"], ayanamsa=ayanamsa,
        )
        report.items.extend(compute_marriage_remedies(cd, partner_cd))
    console.print(f"[bold]Ishta Devata:[/bold] {report.ishta_devata.title}  "
                  f"[dim]({report.ishta_devata.detail})[/dim]")
    console.print(f"[bold]Palana Devata:[/bold] {report.palana_devata.title}  "
                  f"[dim]({report.palana_devata.detail})[/dim]\n")
    table = Table(title="Remedies")
    table.add_column("Category", style="cyan")
    table.add_column("Remedy", style="yellow")
    table.add_column("Detail")
    table.add_column("Source", style="dim")
    for it in report.items:
        table.add_row(it.category, it.title, it.detail, it.source)
    console.print(table)


def _version_callback(value: bool) -> None:
    if value:
        from jhora import __version__
        console.print(f"OpenJyotish {__version__}")
        raise typer.Exit()


@app.callback()
def cli(
    version: bool = typer.Option(
        False, "--version", "-V",
        help="Show the version and exit.",
        callback=_version_callback, is_eager=True),
):
    """OpenJyotish — Vedic astrology calculator (implementation)."""


if __name__ == "__main__":
    app()
