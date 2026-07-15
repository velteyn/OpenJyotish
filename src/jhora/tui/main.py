"""Interactive terminal UI for Jhora — mirrors GUI tabs using Rich."""

import sys
import termios
import tty
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.live import Live
from rich.align import Align
from rich import box

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.charts.varga import VargaChartComputer
from jhora.calc.shadbala import ShadbalaComputer
from jhora.calc.bhava_bala import BhavaBalaComputer
from jhora.calc.vimsopaka import VimsopakaComputer, VimsopakaScheme
from jhora.calc.yogas import detect_all
from jhora.calc.ashtakavarga import sarva_ashtakavarga
from jhora.calc.arudha import all_bhava_arudhas, all_graha_arudhas
from jhora.calc.karaka import compute_chara_karakas
from jhora.calc.gochara import compute_transits
from jhora.calc.tajaka import build_tajaka_chart
from jhora.calc.prasna import PrasnaMode, compute_prasna
from jhora.calc.muhurta import MuhurtaTask, evaluate_time
from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra
from jhora.types.rasi import Rasi
from jhora.types.varga import VargaLevel
from jhora.interpreter.engine import ChartInterpreter
from jhora.interpreter.knowledge_base import KnowledgeBase
from jhora.ai.engine import AiEngine, AiConfig


TAB_NAMES = [
    "Planets", "Houses", "Dasa", "Varga", "Yogas",
    "Shadbala", "Arudha", "Ashtakavarga", "Transit", "Tajaka",
    "Matchmaking", "Prasna", "Muhurta", "Knowledge", "Reading",
    "AI Chat",
]


@contextmanager
def raw_mode():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def getch() -> str:
    with raw_mode():
        ch = sys.stdin.read(1)
        return ch


CHART_ORDER = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
               Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]

VARGA_LEVELS = [VargaLevel.D_1, VargaLevel.D_3, VargaLevel.D_9,
                VargaLevel.D_12, VargaLevel.D_20, VargaLevel.D_30,
                VargaLevel.D_40, VargaLevel.D_60]


class TuiApp:
    def __init__(self, chart_data: Optional[ChartData] = None):
        self.tab = 0
        self.chart: Optional[ChartData] = chart_data
        self.kb = KnowledgeBase()
        self.interpreter = ChartInterpreter()

    def _header_text(self) -> str:
        total = len(TAB_NAMES)
        return (f"Jhora TUI  —  {TAB_NAMES[self.tab]}  ({self.tab+1}/{total})  |  "
                f"[1-9,0,a] tabs | ← → nav | r refresh | q quit")

    def _planet_table(self) -> Table:
        t = Table(box=box.SIMPLE)
        t.add_column("Planet", style="yellow")
        t.add_column("Rasi", style="cyan")
        t.add_column("Deg", justify="right")
        t.add_column("Nakshatra", style="magenta")
        t.add_column("Ret", style="red")
        t.add_column("Lord", style="green")
        if not self.chart:
            t.add_row("[dim]No chart[/dim]", "", "", "", "", "")
            return t
        for g in CHART_ORDER:
            p = self.chart.planet(g)
            rasi = Rasi.from_longitude(p.longitude)
            nak, _ = Nakshatra.from_longitude(p.longitude)
            nak_name = nak.name.replace("_", " ").title()
            lord = rasi.lord
            t.add_row(g.short_name, rasi.short_name, f"{p.longitude:.2f}°",
                      nak_name, "R" if p.is_retrograde else "", lord)
        return t

    def _house_table(self) -> Table:
        t = Table(box=box.SIMPLE)
        t.add_column("House", style="yellow")
        t.add_column("Cusp", justify="right", style="cyan")
        t.add_column("Sign", style="green")
        t.add_column("Lord", style="magenta")
        if not self.chart:
            t.add_row("[dim]No chart[/dim]", "", "", "")
            return t
        for h in range(12):
            cusp = self.chart.house_cusps[h]
            rasi = Rasi.from_longitude(cusp)
            t.add_row(str(h+1), f"{cusp:.2f}°", rasi.short_name, rasi.lord)
        return t

    def _dasa_panel(self) -> Panel:
        if not self.chart:
            return Panel("[dim]No chart loaded[/dim]")
        from jhora.dasas.vimsottari import VimsottariDasa
        try:
            dasa = VimsottariDasa(self.chart)
            periods = dasa.compute(max_level=2)[:20]
            t = Table(box=box.SIMPLE)
            t.add_column("Lord", style="yellow")
            t.add_column("Start", style="cyan")
            t.add_column("End", style="cyan")
            for p in periods:
                t.add_row(p.lord.short_name,
                          p.start.strftime("%Y-%m"), p.end.strftime("%Y-%m"))
            return Panel(t, title="Vimsottari Dasa (MD/AD)")
        except Exception as e:
            return Panel(f"[red]Error: {e}[/red]", title="Dasa")

    def _varga_panel(self) -> Panel:
        if not self.chart:
            return Panel("[dim]No chart loaded[/dim]")
        parts = []
        vcc = VargaChartComputer()
        for vl in VARGA_LEVELS:
            try:
                vc_data = vcc.compute(self.chart, vl)
                rows = []
                for g in CHART_ORDER:
                    lon = vc_data.planet_longitudes[g]
                    r = Rasi.from_longitude(lon)
                    rows.append(f"{g.short_name}:{r.short_name}")
                parts.append(Panel("\n".join(rows), title=vl.name.replace("_"," "), width=18))
            except Exception:
                continue
        cols = Columns(parts)
        return Panel(cols, title="Varga Charts")

    def _yoga_panel(self) -> Panel:
        if not self.chart:
            return Panel("[dim]No chart loaded[/dim]")
        yogas = detect_all(self.chart)
        if not yogas:
            return Panel("[dim]No yogas detected[/dim]")
        t = Table(box=box.SIMPLE)
        t.add_column("Yoga", style="yellow")
        t.add_column("Type", style="cyan")
        t.add_column("Desc", style="green")
        for y in yogas[:30]:
            cat = y.category.value if hasattr(y.category, "value") else str(y.category)
            t.add_row(y.name, cat, y.description[:60])
        return Panel(t, title=f"Yogas ({len(yogas)} detected)")

    def _shadbala_panel(self) -> Panel:
        if not self.chart:
            return Panel("[dim]No chart loaded[/dim]")
        comp = ShadbalaComputer(self.chart)
        t_gr = Table(box=box.SIMPLE)
        t_gr.add_column("Planet", style="yellow")
        cols = ["Sthana", "Dig", "Kala", "Chesta", "Naisarg", "Drik", "Total"]
        for c in cols:
            t_gr.add_column(c, justify="right")
        for g in CHART_ORDER:
            try:
                sb = comp.compute_one(g)
                vals = [sb.sthana_total, sb.dig_total, sb.kala_total,
                        sb.chesta_total, sb.naisargika.virupa, sb.drik.virupa]
                total = sb.total_virupa
                t_gr.add_row(g.short_name, *[f"{v:.1f}" for v in vals], f"[bold]{total:.1f}[/bold]")
            except Exception:
                continue

        # Bhava Bala
        bb = BhavaBalaComputer(self.chart)
        report = bb.compute_all()
        t_bh = Table(box=box.SIMPLE)
        t_bh.add_column("H", style="yellow")
        t_bh.add_column("Sthana", justify="right")
        t_bh.add_column("Drishti", justify="right")
        t_bh.add_column("Dig", justify="right")
        t_bh.add_column("Adhip", justify="right")
        t_bh.add_column("Drig", justify="right")
        t_bh.add_column("Total", justify="right", style="bold")
        for h in range(1, 13):
            r = report.results[h]
            t_bh.add_row(str(h), f"{r.sthana:.1f}", f"{r.drishti:.1f}",
                         f"{r.dig:.1f}", f"{r.adhipati:.1f}",
                         f"{r.drig:.1f}", f"[bold]{r.total:.1f}[/bold]")

        cols_layout = Columns([t_gr, t_bh])

        # Vimsopaka Bala
        vc = VimsopakaComputer(self.chart)
        vr = sorted(vc.compute_all(VimsopakaScheme.SHADVARGA), key=lambda r: r.total, reverse=True)
        t_vi = Table(box=box.SIMPLE)
        t_vi.add_column("Planet", style="cyan")
        t_vi.add_column("Vimsopaka", justify="right", style="green")
        t_vi.add_column("%", justify="right", style="yellow")
        for r in vr:
            t_vi.add_row(r.graha.short_name, f"{r.total:.1f}/20", f"{r.percentage:.0f}%")

        cols_layout = Columns([t_gr, t_bh, t_vi])
        return Panel(cols_layout, title="Shadbala + Bhava + Vimsopaka")

    def _arudha_panel(self) -> Panel:
        if not self.chart:
            return Panel("[dim]No chart loaded[/dim]")
        planets_dict = {g: {"longitude": p.longitude} for g, p in self.chart.planets.items()}
        aps = all_bhava_arudhas(self.chart.ascendant, planets_dict)
        t = Table(box=box.SIMPLE)
        t.add_column("House", style="yellow")
        t.add_column("Rasi", style="cyan")
        for h, rasi in sorted(aps.items()):
            t.add_row(str(h), rasi.short_name)
        try:
            cks = compute_chara_karakas(self.chart.planets)
            lines = ["[bold]Chara Karakas:[/bold]"]
            for ck in cks:
                lines.append(f"  {ck.graha.short_name} → {ck.karaka_name}")
            karaka_panel = Panel("\n".join(lines), title="Karaka")
        except Exception:
            karaka_panel = Panel("[dim]No karaka data[/dim]")
        return Panel(Columns([t, karaka_panel]), title="Arudha Padas")

    def _ashtakavarga_panel(self) -> Panel:
        if not self.chart:
            return Panel("[dim]No chart loaded[/dim]")
        sav = sarva_ashtakavarga(self.chart)
        t = Table(box=box.SIMPLE)
        t.add_column("Rasi", style="yellow")
        t.add_column("SAV", justify="right")
        for r in range(12):
            t.add_row(Rasi(r).short_name, str(int(sav[r])))
        return Panel(t, title=f"Ashtakavarga (SAV: {int(sum(sav))} total)")

    def _transit_panel(self) -> Panel:
        if not self.chart:
            return Panel("[dim]No chart loaded[/dim]")
        from jhora.ephemeris.swe import SweEngine
        eng = SweEngine()
        now = datetime.now()
        now_jd = eng.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)
        result = compute_transits(self.chart, now_jd)
        t = Table(box=box.SIMPLE)
        t.add_column("Planet", style="yellow")
        t.add_column("Sign", style="cyan")
        t.add_column("Deg", justify="right")
        t.add_column("H(Lg)", justify="right")
        t.add_column("SAV", justify="right")
        t.add_column("Fav")
        entries = result.entries if hasattr(result, 'entries') else []
        for e in entries[:9]:
            fav = "✓" if e.is_favorable else "✗"
            t.add_row(e.graha.short_name, e.transit_rasi_name, f"{e.transit_degrees:.1f}",
                      str(e.house_from_lagna), str(e.sav_score), fav)
        return Panel(t, title=f"Transit ({datetime.now().strftime('%Y-%m-%d %H:%M')})")

    def _tajaka_panel(self) -> Panel:
        if not self.chart:
            return Panel("[dim]No chart loaded[/dim]")
        try:
            from jhora.ephemeris.swe import SweEngine
            eng = SweEngine()
            cbb = ChartBuilder()
            target = self.chart.birth_date.year + 1
            tr = build_tajaka_chart(eng, cbb, self.chart, target, tropical=False)
            t = Table(box=box.SIMPLE)
            t.add_column("Planet", style="yellow")
            t.add_column("Sign", style="cyan")
            t.add_column("Deg", justify="right")
            for g in CHART_ORDER:
                p = tr.planet(g)
                r = Rasi.from_longitude(p.longitude)
                t.add_row(g.short_name, r.short_name, f"{p.longitude:.2f}°")
            return Panel(t, title=f"Tajaka ({target})")
        except Exception as e:
            return Panel(f"[red]Error: {e}[/red]", title="Tajaka")

    def _kuta_panel(self) -> Panel:
        return Panel(
            "[yellow]Matchmaking:[/yellow]\n"
            "  Use CLI: [bold]jhora kuta[/bold] for full compatibility\n"
            "  (requires two charts — use the GUI for interactive mode)",
            title="Matchmaking",
        )

    def _prasna_panel(self) -> Panel:
        t = Table(box=box.SIMPLE)
        t.add_column("Mode", style="yellow")
        t.add_column("N", style="cyan")
        t.add_column("PL (°)", justify="right")
        t.add_column("Rasi", style="green")
        t.add_column("Nak/Sub", style="magenta")
        for pm in PrasnaMode:
            for n in [1, 50, pm.max_number]:
                r = compute_prasna(n, pm)
                sub = r.sub_lord.short_name if r.sub_lord else ""
                t.add_row(pm.label, str(n), f"{r.prasna_lagna:.2f}",
                          r.rasi.short_name, sub or r.nakshatra.name[:8])
        return Panel(t, title="Prasna Horary (samples: 1, 50, max)")

    def _muhurta_panel(self) -> Panel:
        now = datetime.now().replace(hour=12, minute=0, second=0)
        t = Table(box=box.SIMPLE)
        t.add_column("Task", style="yellow")
        t.add_column("Score", justify="right")
        t.add_column("Status")
        for mt in MuhurtaTask:
            r = evaluate_time(now, 13.08, 80.27, 5.5, mt)
            c = "green" if r.is_good else "red"
            t.add_row(mt.label[:30], f"{r.score:.2f}", f"[{c}]{'✓' if r.is_good else '✗'}[/{c}]")
        return Panel(t, title=f"Muhurta ({now.strftime('%Y-%m-%d')} noon, Chennai)")

    def _knowledge_panel(self) -> Panel:
        t = Table(box=box.SIMPLE)
        t.add_column("Source", style="yellow")
        t.add_column("Chars", justify="right")
        for src in self.kb.list_sources():
            txt = self.kb.docs.get(src, "")
            t.add_row(src, str(len(txt)))
        return Panel(t, title=f"Knowledge Base ({self.kb.loaded} sources)")

    def _reading_panel(self) -> Panel:
        if not self.chart:
            return Panel("[dim]No chart loaded — compute a chart first[/dim]")
        try:
            text = self.interpreter.interpret_text(self.chart, style="concise")
            return Panel(text[:2000], title="Chart Reading (concise)")
        except Exception as e:
            return Panel(f"[red]Error: {e}[/red]", title="Chart Reading")

    def _ai_panel(self) -> Panel:
        if not self.chart:
            return Panel("[dim]No chart loaded[/dim]")
        try:
            engine = AiEngine(AiConfig(provider="ollama"))
            health = engine.health_check()
            if health["ok"]:
                info = f"AI ready ({len(health['models'])} models)"
            else:
                info = f"AI offline: {health['error'][:60]}"
        except Exception as e:
            info = f"AI error: {e}"
        return Panel(
            f"[bold]AI Chart Reading[/bold]\n\n"
            f"Status: {info}\n\n"
            f"Use the CLI for AI interpretation:\n"
            f"  [cyan]jhora ai[/cyan] 'YYYY-MM-DD HH:MM TZ LAT LON'\n"
            f"  [cyan]jhora ai[/cyan] --mode remedies\n"
            f"  [cyan]jhora ai[/cyan] --mode ask --question 'What about my career?'\n\n"
            f"Providers: ollama, lmstudio, unsloth, custom",
            title="AI Chat",
        )

    def _render_tab(self):
        renderers: List = [
            self._planet_table,       # 0
            self._house_table,        # 1
            self._dasa_panel,         # 2
            self._varga_panel,        # 3
            self._yoga_panel,         # 4
            self._shadbala_panel,     # 5
            self._arudha_panel,       # 6
            self._ashtakavarga_panel, # 7
            self._transit_panel,      # 8
            self._tajaka_panel,       # 9
            self._kuta_panel,         # 10
            self._prasna_panel,       # 11
            self._muhurta_panel,      # 12
            self._knowledge_panel,    # 13
            self._reading_panel,      # 14
            self._ai_panel,           # 15
        ]
        if 0 <= self.tab < len(renderers):
            content = renderers[self.tab]()
            return Panel(content)
        return Panel("[red]Unknown tab[/red]")

    def run(self):
        try:
            with Live(RefreshPerSecond=4, screen=True) as live:
                live.console.show_cursor(False)
                live.update(self._render_tab())
                while True:
                    ch = getch()
                    if ch == "q":
                        break
                    elif ch in "123456789":
                        self.tab = int(ch) - 1
                        if self.tab >= len(TAB_NAMES):
                            self.tab = len(TAB_NAMES) - 1
                    elif ch == "0":
                        self.tab = 9
                    elif ch == "a":
                        self.tab = 15
                    elif ch == "\x1b":
                        seq = ""
                        if sys.stdin.read(0):
                            seq = sys.stdin.read(2)
                            if seq == "[C":
                                self.tab = (self.tab + 1) % len(TAB_NAMES)
                            elif seq == "[D":
                                self.tab = (self.tab - 1) % len(TAB_NAMES)
                    elif ch == "r":
                        pass
                    live.update(self._render_tab())
        except Exception:
            self.run_no_live()

    def run_no_live(self):
        from rich.console import Console
        console = Console()
        console.print(Panel(self._header_text()))
        console.print(self._render_tab())
