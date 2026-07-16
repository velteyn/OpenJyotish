"""Interactive Terminal UI — prompt_toolkit navigation + Rich rendering.

Uses prompt_toolkit for dialogs/menus/input and Rich for output rendering.
Proper keyboard handling, scrollable lists, input forms.
"""

from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, FormattedTextControl
from prompt_toolkit.widgets import Frame, TextArea, Label, Box
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.application.current import get_app

from rich.console import Console as RichConsole
from rich.table import Table
from rich.panel import Panel
from rich import box as rich_box
from rich.text import Text as RichText

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

rich = RichConsole(color_system="truecolor")

STYLE = Style.from_dict({
    "title": "bold yellow",
    "menu-item": "fg:ansicyan",
    "menu-key": "fg:ansiyellow bold",
    "status": "fg:ansigreen",
    "error": "fg:ansired",
    "dim": "fg:ansibrightblack",
    "content": "fg:ansiwhite",
    "frame.border": "fg:ansiblue",
})


class JhoraTui:
    def __init__(self):
        self.chart: Optional[ChartData] = None
        self.birthdata_str: str = ""
        self._content_lines: List[str] = []
        self._menu_items: List[Tuple[str, str, Callable]] = []
        self._menu_index: int = 0
        self._status: str = "Welcome to Jhora TUI | ↑↓ navigate | Enter select | q quit"

    def run(self):
        self._show_main_menu()

    # ── Rendering ─────────────────────────────────────────────────────────

    def _render_screen(self):
        """Render the current menu + content to the terminal."""
        # Capture Rich output to string
        with rich.capture() as capture:
            rich.print()
            # Menu
            menu_lines = []
            for i, (key, label, _) in enumerate(self._menu_items):
                marker = "▶" if i == self._menu_index else " "
                menu_lines.append(f"  {marker} [{key}] {label}")
            menu_text = "\n".join(menu_lines)
            rich.print(Panel(menu_text, title="[bold yellow]Jhora TUI[/bold yellow]",
                            subtitle=self._status, border_style="blue"))

            # Content
            if self._content_lines:
                for line in self._content_lines:
                    rich.print(line)

        # Build prompt_toolkit layout
        output = capture.get()

        kb = KeyBindings()

        @kb.add("up")
        def _(event):
            if self._menu_items:
                self._menu_index = (self._menu_index - 1) % len(self._menu_items)
                event.app.exit(result="refresh")

        @kb.add("down")
        def _(event):
            if self._menu_items:
                self._menu_index = (self._menu_index + 1) % len(self._menu_items)
                event.app.exit(result="refresh")

        @kb.add("enter")
        def _(event):
            if self._menu_items:
                _, _, action = self._menu_items[self._menu_index]
                event.app.exit(result=action)

        @kb.add("q")
        @kb.add("c-c")
        def _(event):
            event.app.exit(result="quit")

        # Number keys for quick menu selection
        for i, (key, _, action) in enumerate(self._menu_items):
            @kb.add(key.lower())
            def _(event, idx=i, act=action):
                self._menu_index = idx
                event.app.exit(result=act)

        content = FormattedTextControl(text=output, style="class:content")
        root = HSplit([
            Window(content=content, wrap_lines=False),
        ])

        app = Application(
            layout=Layout(root),
            key_bindings=kb,
            style=STYLE,
            full_screen=True,
        )
        return app.run()

    # ── Menu system ───────────────────────────────────────────────────────

    def _menu_loop(self, title: str, items: List[Tuple[str, str, Callable]],
                   status: str = ""):
        """Display a menu and handle navigation. Returns when user quits or drills down."""
        self._menu_items = items
        self._menu_index = 0
        self._status = status or "↑↓ navigate | Enter select | q back/quit"
        self._content_lines = [f"\n  [bold yellow]{title}[/bold yellow]\n"]

        while True:
            try:
                result = self._render_screen()
            except Exception:
                break

            if result == "quit":
                return "quit"
            elif result == "refresh":
                continue
            elif callable(result):
                sub_result = result()
                if sub_result == "quit":
                    return "quit"
                # After sub-action, refresh content
                self._render_screen()
                continue
            else:
                break
        return None

    # ── Actions ───────────────────────────────────────────────────────────

    def _action_back(self):
        return "back"

    def _action_input_birth(self):
        """Birth data input using prompt_toolkit dialogs."""
        from prompt_toolkit.shortcuts import input_dialog, message_dialog

        year = input_dialog("Year", "Enter birth year:", str(datetime.now().year)).run()
        if not year:
            return
        month = input_dialog("Month", "Enter birth month:", str(datetime.now().month)).run()
        if not month:
            return
        day = input_dialog("Day", "Enter birth day:", str(datetime.now().day)).run()
        if not day:
            return
        hour = input_dialog("Hour", "Enter birth hour (24h, e.g. 13.916 for 13:55):", "12.0").run()
        if not hour:
            return
        lat = input_dialog("Latitude", "Latitude (e.g. 45.41):", "28.61").run()
        if not lat:
            return
        lon = input_dialog("Longitude", "Longitude (e.g. 11.88):", "77.21").run()
        if not lon:
            return
        tz = input_dialog("Timezone", "Timezone (e.g. +0100, +0530, -0500):", "+0530").run()
        if not tz:
            return

        try:
            builder = ChartBuilder()
            self.chart = builder.build(
                year=int(year), month=int(month), day=int(day),
                hour=float(hour), lat=float(lat), lon=float(lon), tz=tz,
            )
            self.birthdata_str = f"{year}-{month}-{day} {hour} {tz} {lat} {lon}"
            lagna = Rasi.from_longitude(self.chart.ascendant)
            self._content_lines = [
                f"\n  [green]Chart computed successfully[/green]",
                f"  [green]{self.birthdata_str}[/green]",
                f"  [green]Lagna: {lagna.full_name} ({self.chart.ascendant:.2f}°)[/green]",
            ]
        except Exception as e:
            self._content_lines = [f"\n  [red]Error: {e}[/red]"]

    def _check_chart(self) -> bool:
        if not self.chart:
            self._content_lines = ["\n  [red]No chart loaded. Use 'Birth Data Input' first.[/red]"]
            return False
        return True

    def _action_planets(self):
        if not self._check_chart():
            return
        from jhora.types.nakshatra import Nakshatra
        with rich.capture() as cap:
            t = Table(title="Planetary Positions", box=rich_box.SIMPLE)
            for h in ["Planet", "Longitude", "Sign", "Nakshatra", "Pada", "Motion"]:
                t.add_column(h)
            for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                      Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
                p = self.chart.planet(g)
                r = Rasi.from_longitude(p.longitude)
                n, pada = Nakshatra.from_longitude(p.longitude)
                t.add_row(g.full_name, f"{p.longitude:.2f}°", r.full_name,
                          n.name.replace("_", " ").title(), str(pada),
                          "R" if p.is_retrograde else "")
            lr = Rasi.from_longitude(self.chart.ascendant)
            t.add_row("Lagna", f"{self.chart.ascendant:.2f}°", lr.full_name, "", "", "")
            if self.chart.outer_planets:
                for name, d in self.chart.outer_planets.items():
                    t.add_row(name, f"{d['longitude']:.2f}°", d["sign_full"], "", "",
                              "R" if d["is_retrograde"] else "")
            rich.print(t)
            # Upagrahas
            from jhora.calc.upagraha import compute_solar_upagrahas
            from jhora.calc.special_lagnas import compute_special_lagnas
            sun_lon = self.chart.planet(Graha.SUN).longitude
            ut = Table(title="Upagrahas + Special Lagnas", box=rich_box.SIMPLE)
            ut.add_column("Point")
            ut.add_column("Longitude")
            ut.add_column("Sign")
            for u in compute_solar_upagrahas(sun_lon):
                ut.add_row(u.name, f"{u.longitude:.2f}°", u.rasi)
            for s in compute_special_lagnas(self.chart):
                ut.add_row(s.name, f"{s.longitude:.2f}°", s.sign)
            rich.print(ut)
        self._content_lines = cap.get().split("\n")

    def _action_houses(self):
        if not self._check_chart():
            return
        from jhora.calc.chalit import ChalitComputer
        with rich.capture() as cap:
            cc = ChalitComputer(self.chart)
            cr = cc.compute()
            t = Table(title="House Cusps + Chalit", box=rich_box.SIMPLE)
            for h in ["House", "Cusp", "Sign", "Lord", "Shift"]:
                t.add_column(h)
            for h in range(12):
                cusp = self.chart.house_cusps[h]
                r = Rasi.from_longitude(cusp)
                moved = [e for e in cr.entries if e.cusp_house == h + 1 and e.moved]
                shift = ", ".join(f"{e.graha.short_name} H{e.sign_house}→H{e.cusp_house}"
                                  for e in moved) if moved else ""
                t.add_row(str(h + 1), f"{cusp:.2f}°", r.full_name, r.lord, shift)
            rich.print(t)
        self._content_lines = cap.get().split("\n")

    def _action_yogas(self):
        if not self._check_chart():
            return
        from jhora.calc.yogas import detect_all
        with rich.capture() as cap:
            yogas = detect_all(self.chart)
            t = Table(title=f"Yogas ({len(yogas)} detected)", box=rich_box.SIMPLE)
            t.add_column("Yoga")
            t.add_column("Planets")
            t.add_column("Description")
            for y in yogas:
                planets = ", ".join(p.short_name for p in y.planets) if y.planets else ""
                t.add_row(y.name, planets, y.description[:80])
            rich.print(t)
        self._content_lines = cap.get().split("\n")

    def _action_shadbala(self):
        if not self._check_chart():
            return
        from jhora.calc.shadbala import ShadbalaComputer
        with rich.capture() as cap:
            sb = ShadbalaComputer(self.chart)
            t = Table(title="Shadbala (virupas)", box=rich_box.SIMPLE)
            for h in ["Planet", "Sthana", "Dig", "Kala", "Chesta", "Naisarg", "Drik", "Total"]:
                t.add_column(h)
            for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                      Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
                r = sb.compute_one(g)
                t.add_row(g.full_name, f"{r.sthana_total:.1f}", f"{r.dig_total:.1f}",
                          f"{r.kala_total:.1f}", f"{r.chesta_total:.1f}",
                          f"{r.naisargika.virupa:.1f}", f"{r.drik.virupa:.1f}",
                          f"{r.total_virupa:.0f}")
            rich.print(t)
        self._content_lines = cap.get().split("\n")

    def _action_bhava_bala(self):
        if not self._check_chart():
            return
        from jhora.calc.bhava_bala import BhavaBalaComputer
        with rich.capture() as cap:
            bb = BhavaBalaComputer(self.chart)
            report = bb.compute_all()
            t = Table(title="Bhava Bala", box=rich_box.SIMPLE)
            for h in ["H", "Sign", "Sthana", "Drishti", "Dig", "Adhip", "Drig", "Total"]:
                t.add_column(h)
            for h in range(1, 13):
                r = report.results[h]
                ri = (int(self.chart.ascendant / 30) + h - 1) % 12
                t.add_row(str(h), Rasi(ri).short_name, f"{r.sthana:.0f}",
                          f"{r.drishti:.0f}", f"{r.dig:.0f}",
                          f"{r.adhipati:.0f}", f"{r.drig:+.0f}", f"{r.total:.0f}")
            rich.print(t)
        self._content_lines = cap.get().split("\n")

    def _action_vimsopaka(self):
        if not self._check_chart():
            return
        from jhora.calc.vimsopaka import VimsopakaComputer, VimsopakaScheme
        with rich.capture() as cap:
            vc = VimsopakaComputer(self.chart)
            for scheme in [VimsopakaScheme.SHADVARGA, VimsopakaScheme.SHODASAVARGA]:
                t = Table(title=f"Vimsopaka Bala — {scheme.value}", box=rich_box.SIMPLE)
                t.add_column("Planet")
                t.add_column("Score")
                t.add_column("%")
                for r in sorted(vc.compute_all(scheme), key=lambda x: x.total, reverse=True):
                    t.add_row(r.graha.full_name, f"{r.total:.1f}/20", f"{r.percentage:.0f}%")
                rich.print(t)
                rich.print()
        self._content_lines = cap.get().split("\n")

    def _action_dasa(self):
        if not self._check_chart():
            return
        from jhora.dasas.vimsottari import VimsottariDasa
        with rich.capture() as cap:
            dasa = VimsottariDasa()
            cd = {"planets": {g.value: {"longitude": p.longitude}
                              for g, p in self.chart.planets.items()},
                  "lagna_lon": self.chart.ascendant}
            periods = dasa.compute(self.chart.julian_day, cd)
            now = datetime.now()
            t = Table(title="Vimsottari Mahadasha", box=rich_box.SIMPLE)
            t.add_column("Lord")
            t.add_column("Start")
            t.add_column("End")
            t.add_column("Status")
            for md in periods:
                status = "◀ CURRENT" if md.start_date <= now <= md.end_date else ""
                t.add_row(md.lord_name, md.start_date.strftime("%Y-%m"),
                          md.end_date.strftime("%Y-%m"), status)
                if md.start_date <= now <= md.end_date:
                    for ad in (md.sub_periods or []):
                        if ad.start_date <= now <= ad.end_date:
                            t.add_row(f"  └ {ad.lord_name} (AD)",
                                      ad.start_date.strftime("%Y-%m"),
                                      ad.end_date.strftime("%Y-%m"), "◀ now")
            rich.print(t)
        self._content_lines = cap.get().split("\n")

    def _action_dasa_timeline(self):
        if not self._check_chart():
            return
        from jhora.calc.dasa_timeline import dasa_timeline_text
        text = dasa_timeline_text(self.chart, width=60)
        self._content_lines = text.split("\n")

    def _action_transits(self):
        if not self._check_chart():
            return
        from jhora.calc.gochara import compute_transits
        from jhora.ephemeris.swe import SweEngine
        with rich.capture() as cap:
            eng = SweEngine()
            now = datetime.now()
            jd = eng.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)
            result = compute_transits(self.chart, jd)
            t = Table(title=f"Transits ({now.strftime('%Y-%m-%d')})", box=rich_box.SIMPLE)
            t.add_column("Planet")
            t.add_column("Sign")
            t.add_column("House")
            t.add_column("SAV")
            t.add_column("Fav")
            for e in result.entries:
                t.add_row(e.graha.short_name, e.transit_rasi_name,
                          str(e.house_from_lagna), str(e.sav_score),
                          "✓" if e.is_favorable else "✗")
            rich.print(t)
        self._content_lines = cap.get().split("\n")

    def _action_tajaka(self):
        if not self._check_chart():
            return
        from prompt_toolkit.shortcuts import input_dialog
        y = input_dialog("Tajaka Year", "Target year:", str(datetime.now().year)).run()
        if not y:
            return
        try:
            from jhora.calc.tajaka import build_tajaka_chart
            from jhora.ephemeris.swe import SweEngine
            with rich.capture() as cap:
                eng = SweEngine()
                cbb = ChartBuilder()
                tr = build_tajaka_chart(eng, cbb, self.chart, int(y), tropical=False)
                t = Table(title=f"Tajaka Solar Return {y}", box=rich_box.SIMPLE)
                t.add_column("Planet")
                t.add_column("Sign")
                t.add_column("Deg")
                for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                          Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
                    p = tr.planet(g)
                    r = Rasi.from_longitude(p.longitude)
                    t.add_row(g.short_name, r.short_name, f"{p.longitude:.1f}°")
                rich.print(t)
            self._content_lines = cap.get().split("\n")
        except Exception as e:
            self._content_lines = [f"[red]Error: {e}[/red]"]

    def _action_matchmaking(self):
        if not self._check_chart():
            return
        from prompt_toolkit.shortcuts import input_dialog
        y = input_dialog("Year", "Partner year:").run()
        m = input_dialog("Month", "Partner month:").run()
        d = input_dialog("Day", "Partner day:").run()
        h = input_dialog("Hour", "Partner hour:", "12.0").run()
        la = input_dialog("Latitude", "Partner lat:").run()
        lo = input_dialog("Longitude", "Partner lon:").run()
        tz = input_dialog("Timezone", "Partner TZ:", "+0530").run()
        if not all([y, m, d, h, la, lo, tz]):
            return
        try:
            builder = ChartBuilder()
            c2 = builder.build(year=int(y), month=int(m), day=int(d),
                               hour=float(h), lat=float(la), lon=float(lo), tz=tz)
            from jhora.calc.kuta import compute_kuta
            result = compute_kuta(self.chart, c2)
            lines = [f"\n  [bold green]Total Score: {result.total_score:.1f}[/bold green]"]
            for item in result.items:
                lines.append(f"  {item.name:<20} {item.score:.1f}")
            self._content_lines = lines
        except Exception as e:
            self._content_lines = [f"[red]Error: {e}[/red]"]

    def _action_prasna(self):
        from prompt_toolkit.shortcuts import input_dialog
        n = input_dialog("Prasna", "Number (1-249):", "108").run()
        if not n:
            return
        from jhora.calc.prasna import PrasnaMode, compute_prasna
        lines = []
        for pm in PrasnaMode:
            r = compute_prasna(int(n), pm)
            lines.append(f"  [cyan]{pm.label}[/cyan]: {r.rasi.short_name} "
                        f"({r.prasna_lagna:.1f}°) — {r.nakshatra.name}")
        self._content_lines = lines

    def _action_muhurta(self):
        if not self._check_chart():
            return
        from jhora.calc.muhurta import MuhurtaTask, evaluate_time
        with rich.capture() as cap:
            now = datetime.now()
            t = Table(title=f"Muhurta ({now.strftime('%Y-%m-%d')})", box=rich_box.SIMPLE)
            t.add_column("Task")
            t.add_column("Score")
            t.add_column("Status")
            for mt in MuhurtaTask:
                r = evaluate_time(now, self.chart.latitude, self.chart.longitude,
                                 float(self.chart.timezone.replace("+", "").replace("−", "-") or 0), mt)
                c = "green" if r.is_good else "red"
                t.add_row(mt.label[:35], f"{r.score:.2f}",
                          f"[{c}]{'✓' if r.is_good else '✗'}[/{c}]")
            rich.print(t)
        self._content_lines = cap.get().split("\n")

    def _action_mundane(self):
        from prompt_toolkit.shortcuts import input_dialog
        y = input_dialog("Mundane", "Year:", str(datetime.now().year)).run()
        if not y:
            return
        from jhora.calc.mundane import MundaneCalculator
        mc = MundaneCalculator()
        self._content_lines = mc.analysis_text(int(y)).split("\n")

    def _action_learning(self):
        if not self._check_chart():
            return
        from jhora.calc.learning import marana_karaka_sthana
        from jhora.calc.special_lagnas import kp_sublord_string
        with rich.capture() as cap:
            mk = marana_karaka_sthana(self.chart)
            if mk:
                t = Table(title="Marana Karaka Sthana", box=rich_box.SIMPLE)
                t.add_column("Planet", style="red")
                t.add_column("House")
                t.add_column("Sign")
                for m in mk:
                    t.add_row(m["graha"], str(m["house"]), m["sign"])
                rich.print(t)
            t = Table(title="KP Sub-Lords", box=rich_box.SIMPLE)
            t.add_column("Point")
            t.add_column("Chain")
            for g in Graha:
                if g in self.chart.planets:
                    chain = kp_sublord_string(self.chart.planet(g).longitude, 3)
                    t.add_row(g.full_name, chain)
            rich.print(t)
        self._content_lines = cap.get().split("\n")

    def _action_knowledge(self):
        from prompt_toolkit.shortcuts import input_dialog
        q = input_dialog("Knowledge", "Search textbooks:").run()
        if not q:
            return
        from jhora.interpreter.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        results = kb.search(q, max_results=5)
        lines = []
        for r in results:
            lines.append(f"\n[yellow]{r['source']}[/yellow]")
            lines.append(f"  {r['excerpt'][:300]}")
        self._content_lines = lines

    def _action_export_html(self):
        if not self._check_chart():
            return
        from prompt_toolkit.shortcuts import input_dialog
        path = input_dialog("Export", "Output path:", "chart_report.html").run()
        if not path:
            return
        from jhora.export.report import generate_chart_report
        generate_chart_report(self.chart, path)
        self._content_lines = [f"\n  [green]Saved: {path}[/green]"]

    def _action_varga(self):
        if not self._check_chart():
            return
        from jhora.charts.varga import VargaChartComputer
        from jhora.types.varga import VargaLevel
        with rich.capture() as cap:
            vcc = VargaChartComputer()
            t = Table(title="Divisional Charts (8 Vargas)", box=rich_box.SIMPLE)
            levels = [VargaLevel.D_1, VargaLevel.D_3, VargaLevel.D_9, VargaLevel.D_12,
                      VargaLevel.D_20, VargaLevel.D_30, VargaLevel.D_40, VargaLevel.D_60]
            t.add_column("Planet")
            for vl in levels:
                t.add_column(vl.name)
            for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                      Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
                row = [g.short_name]
                for vl in levels:
                    vcd = vcc.compute(self.chart, vl)
                    lon = vcd.positions[g].longitude
                    row.append(Rasi.from_longitude(lon).short_name)
                t.add_row(*row)
            rich.print(t)
        self._content_lines = cap.get().split("\n")

    def _action_reading(self):
        if not self._check_chart():
            return
        from jhora.interpreter.engine import ChartInterpreter
        interp = ChartInterpreter()
        text = interp.interpret_text(self.chart, style="concise")
        self._content_lines = text.split("\n")

    def _action_ashtakavarga(self):
        if not self._check_chart():
            return
        from jhora.calc.ashtakavarga import sarva_ashtakavarga
        with rich.capture() as cap:
            sav = sarva_ashtakavarga(self.chart)
            t = Table(title="Ashtakavarga SAV", box=rich_box.SIMPLE)
            t.add_column("Rasi")
            t.add_column("SAV")
            for r in range(12):
                t.add_row(Rasi(r).short_name, str(int(sav[r])))
            rich.print(t)
        self._content_lines = cap.get().split("\n")

    def _action_save_db(self):
        if not self._check_chart():
            return
        from jhora.io.jhd_parser import save_chart_to_db
        bd = self.chart.birth_date
        cid = save_chart_to_db(
            name=f"Chart {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            day=bd.day, month=bd.month, year=bd.year,
            time_hours=bd.hour + bd.minute / 60.0,
            tz_offset=float(self.chart.timezone.replace("+", "").replace("−", "-") or 0),
            latitude=self.chart.latitude, longitude=self.chart.longitude,
        )
        self._content_lines = [f"\n  [green]Saved to DB (ID: {cid})[/green]"]

    # ── Main Menu ─────────────────────────────────────────────────────────

    def _show_main_menu(self):
        items = [
            ("1", "Birth Data Input", self._action_input_birth),
            ("2", "Planets + Upagrahas + Lagnas", self._action_planets),
            ("3", "Houses + Chalit Shifts", self._action_houses),
            ("4", "Yogas (Planetary Combinations)", self._action_yogas),
            ("5", "Shadbala (Planetary Strengths)", self._action_shadbala),
            ("6", "Bhava Bala (House Strengths)", self._action_bhava_bala),
            ("7", "Vimsopaka Bala (Varga Strengths)", self._action_vimsopaka),
            ("8", "Dasa Periods (Vimsottari)", self._action_dasa),
            ("9", "Dasa Timeline (Bar Chart)", self._action_dasa_timeline),
            ("a", "Transits (Current vs Natal)", self._action_transits),
            ("b", "Tajaka (Solar Return)", self._action_tajaka),
            ("c", "Varga Charts (D-1 to D-60)", self._action_varga),
            ("d", "Matchmaking (Kuta Porutham)", self._action_matchmaking),
            ("e", "Prasna (Horary)", self._action_prasna),
            ("f", "Muhurta (Electional)", self._action_muhurta),
            ("g", "Mundane (World Events)", self._action_mundane),
            ("h", "Learning Aids (KP, Marana Karaka)", self._action_learning),
            ("i", "AI: Chart Reading (Rule-based)", self._action_reading),
            ("j", "Ashtakavarga (SAV)", self._action_ashtakavarga),
            ("k", "Knowledge Search (Textbooks)", self._action_knowledge),
            ("l", "Export HTML Report", self._action_export_html),
            ("m", "Save Chart to Database", self._action_save_db),
            ("n", "Birth Data (Re-enter)", self._action_input_birth),
        ]
        self._menu_loop("Jhora TUI — Main Menu", items,
                        "↑↓ navigate | letter/Enter select | q quit")
