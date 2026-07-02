from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QTextEdit, QTabWidget,
    QMessageBox, QGroupBox, QFormLayout,
)

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.charts.varga import VargaChartComputer, VargaChartData, get_variants_for_level
from jhora.calc.shadbala import ShadbalaComputer
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.varga import VargaLevel, VargaVariant
from jhora.ui.chart_widget import ChartWidget, ChartStyle


BG = "#1a1a2e"
BG2 = "#16213e"
ACCENT = "#00d2ff"
BORDER = "#e94560"
TEXT = "#cccccc"
DIM = "#888888"

STYLE = f"""
QMainWindow {{ background-color: {BG}; }}
QGroupBox {{ color: {ACCENT}; font-weight: bold; border: 1px solid {BORDER};
            border-radius: 5px; margin-top: 10px; padding-top: 18px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; color: {ACCENT}; }}
QLabel {{ color: {TEXT}; }}
QLineEdit {{ background-color: {BG2}; color: #ffffff; border: 1px solid #0f3460;
            padding: 5px 8px; border-radius: 4px; font-size: 13px; }}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QComboBox {{ background-color: {BG2}; color: #ffffff; border: 1px solid #0f3460;
            padding: 5px 8px; border-radius: 4px; min-width: 110px; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent;
                        border-right: 5px solid transparent;
                        border-top: 6px solid {ACCENT}; margin-right: 6px; }}
QComboBox QAbstractItemView {{ background-color: {BG2}; color: #ffffff;
                               selection-background-color: {BORDER};
                               outline: none; }}
QPushButton {{ background-color: {BORDER}; color: white; border: none;
              padding: 7px 20px; border-radius: 5px; font-weight: bold;
              font-size: 13px; }}
QPushButton:hover {{ background-color: #ff6b6b; }}
QPushButton:pressed {{ background-color: #c23152; }}
QPushButton:checked {{ background-color: #00aa5a; }}
QTableWidget {{ background-color: {BG2}; color: #ffffff; border: 1px solid #0f3460;
               gridline-color: #0f3460; }}
QTableWidget::item {{ padding: 5px 8px; }}
QHeaderView::section {{ background-color: #0f3460; color: {ACCENT}; font-weight: bold;
                       border: 1px solid {BG2}; padding: 5px 8px; }}
QTabWidget::pane {{ background-color: {BG2}; border: 1px solid #0f3460;
                   border-top: none; }}
QTabBar::tab {{ background-color: #0f3460; color: {DIM}; padding: 8px 18px;
               border: none; font-size: 12px; }}
QTabBar::tab:selected {{ background-color: {BG2}; color: {ACCENT};
                         border-bottom: 2px solid {BORDER}; }}
QStatusBar {{ background-color: #0f3460; color: {DIM}; }}
QTextEdit {{ background-color: {BG2}; color: {TEXT}; border: 1px solid #0f3460;
             padding: 8px; font-size: 12px; }}
QSplitter::handle {{ background-color: #0f3460; width: 2px; }}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chart_data: Optional[ChartData] = None
        self.builder = ChartBuilder()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Jagannatha Hora — Vedic Astrology")
        self.setMinimumSize(1100, 760)
        self.setStyleSheet(STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Left panel ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Input group
        input_group = QGroupBox("Birth Data")
        form = QFormLayout(input_group)
        form.setSpacing(6)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("1970-04-04")
        self.date_input.setToolTip("Year-Month-Day")
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("17:48:20")
        self.tz_input = QLineEdit()
        self.tz_input.setPlaceholderText("+0530 or Asia/Kolkata")
        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText("13.08")
        self.lon_input = QLineEdit()
        self.lon_input.setPlaceholderText("80.27")

        for w in (self.date_input, self.time_input, self.tz_input,
                  self.lat_input, self.lon_input):
            w.setMinimumWidth(180)

        form.addRow("Date:", self.date_input)
        form.addRow("Time:", self.time_input)
        form.addRow("TZ:", self.tz_input)
        form.addRow("Lat:", self.lat_input)
        form.addRow("Lon:", self.lon_input)

        # Controls row
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        self.style_combo = QComboBox()
        self.style_combo.addItems(["South Indian", "North Indian", "East Indian"])
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        self.ayanamsa_combo = QComboBox()
        self.ayanamsa_combo.addItems(["lahiri", "raman", "krishnamurti", "sss"])

        self.navamsa_toggle = QPushButton("Navamsa")
        self.navamsa_toggle.setCheckable(True)
        self.navamsa_toggle.toggled.connect(self._on_navamsa_toggle)

        self.calc_btn = QPushButton("Calculate")
        self.calc_btn.setMinimumWidth(120)
        self.calc_btn.clicked.connect(self._on_calculate)

        ctrl.addWidget(self.style_combo)
        ctrl.addWidget(self.ayanamsa_combo)
        ctrl.addWidget(self.navamsa_toggle)
        ctrl.addStretch()
        ctrl.addWidget(self.calc_btn)
        form.addRow(ctrl)

        left_layout.addWidget(input_group)

        # Chart
        self.chart_widget = ChartWidget()
        left_layout.addWidget(self.chart_widget, stretch=1)

        # --- Right panel ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Planet tab
        self.planet_table = QTableWidget()

        # House tab
        self.house_table = QTableWidget()

        # Dasa tab
        self.dasa_widget = QWidget()
        dl = QVBoxLayout(self.dasa_widget)
        dl.setContentsMargins(8, 8, 8, 8)
        dl.setSpacing(8)
        self.dasa_system_combo = QComboBox()
        self.dasa_system_combo.addItems(["Vimsottari", "Ashtottari"])
        self.dasa_system_combo.currentTextChanged.connect(self._update_dasa_text)
        dl.addWidget(self.dasa_system_combo)
        self.dasa_text = QTextEdit()
        self.dasa_text.setReadOnly(True)
        dl.addWidget(self.dasa_text)

        # Varga tab
        self.varga_widget = QWidget()
        vg = QVBoxLayout(self.varga_widget)
        vg.setContentsMargins(8, 8, 8, 8)
        vg.setSpacing(8)

        vc = QHBoxLayout()
        vc.setSpacing(8)
        self.varga_level_combo = QComboBox()
        for vl in VargaLevel:
            self.varga_level_combo.addItem(f"{vl.short_name} — {vl.full_name}", vl)
        self.varga_level_combo.setCurrentIndex(8)
        self.varga_level_combo.currentIndexChanged.connect(self._on_varga_level_changed)
        self.varga_variant_combo = QComboBox()
        self.varga_show_btn = QPushButton("Refresh")
        self.varga_show_btn.clicked.connect(self._on_varga_show)

        vc.addWidget(QLabel("Level:"))
        vc.addWidget(self.varga_level_combo, 1)
        vc.addWidget(QLabel("Variant:"))
        vc.addWidget(self.varga_variant_combo, 1)
        vc.addWidget(self.varga_show_btn)
        vg.addLayout(vc)

        self.varga_table = QTableWidget()
        vg.addWidget(self.varga_table, 1)

        self.tabs.addTab(self.planet_table, "Planets")
        self.tabs.addTab(self.house_table, "Houses")
        self.tabs.addTab(self.dasa_widget, "Dasa Periods")
        self.tabs.addTab(self.varga_widget, "Varga")
        self.tabs.addTab(self._build_yoga_tab(), "Yogas")
        self.tabs.addTab(self._build_shadbala_tab(), "Shadbala")

        right_layout.addWidget(self.tabs)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([580, 520])
        main_layout.addWidget(splitter)

        self.statusBar().showMessage("Ready — enter birth data and press Calculate")

        self._on_varga_level_changed(0)
        self._set_example_data()

    def _set_example_data(self):
        self.date_input.setText("1970-04-04")
        self.time_input.setText("17:48:20")
        self.tz_input.setText("+0530")
        self.lat_input.setText("13.08")
        self.lon_input.setText("80.27")

    # --- Slots ---

    def _on_style_changed(self, text: str):
        m = {"South Indian": ChartStyle.SOUTH_INDIAN,
             "North Indian": ChartStyle.NORTH_INDIAN,
             "East Indian": ChartStyle.EAST_INDIAN}
        self.chart_widget.set_chart_style(m.get(text, ChartStyle.SOUTH_INDIAN))

    def _on_navamsa_toggle(self, checked: bool):
        self.chart_widget.set_navamsa_overlay(checked)
        if checked and self.chart_data and not self.chart_widget.navamsa_data:
            comp = VargaChartComputer()
            vcd = comp.compute(self.chart_data, VargaLevel.D_9, VargaVariant.DEFAULT)
            self.chart_widget.set_navamsa_data(dict(vcd.positions))

    def _on_calculate(self):
        try:
            date_str = self.date_input.text().strip()
            time_str = self.time_input.text().strip()
            tz = self.tz_input.text().strip()
            lat = float(self.lat_input.text().strip())
            lon = float(self.lon_input.text().strip())
            ayanamsa = self.ayanamsa_combo.currentText().lower()

            dt = datetime.strptime(date_str, "%Y-%m-%d")
            parts = time_str.split(":")
            hour = int(parts[0]) + int(parts[1]) / 60.0
            if len(parts) > 2:
                hour += int(parts[2]) / 3600.0

            self.statusBar().showMessage("Calculating...")
            self.chart_data = self.builder.build(
                year=dt.year, month=dt.month, day=dt.day,
                hour=hour, lat=lat, lon=lon,
                tz=tz, ayanamsa=ayanamsa,
            )
            self.chart_widget.set_chart_data(self.chart_data)
            self._update_planet_table()
            self._update_house_table()
            self._update_dasa_text()
            self._populate_yoga_table(self.chart_data)
            self._populate_shadbala_table(self.chart_data)

            if self.navamsa_toggle.isChecked():
                self._on_navamsa_toggle(True)

            self._on_varga_show()
            self.statusBar().showMessage("Done")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Calculation failed:\n{e}")
            self.statusBar().showMessage("Error")

    # --- Table builders ---

    def _fill_table(self, table: QTableWidget, headers: list, rows: list):
        table.setColumnCount(len(headers))
        table.setRowCount(len(rows))
        table.setHorizontalHeaderLabels(headers)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)
        table.horizontalHeader().setStretchLastSection(True)
        table.resizeColumnsToContents()
        table.verticalHeader().setVisible(False)

    def _update_planet_table(self):
        if not self.chart_data:
            return
        headers = ["Planet", "Longitude", "Rasi", "Deg", "Nakshatra", "Pada", "Dignity"]
        rows = []
        for g in Graha:
            if g in self.chart_data.planets:
                p = self.chart_data.planets[g]
                rows.append([g.full_name, f"{p.longitude:.2f}", p.rasi_name,
                             f"{p.degrees_in_rasi:.2f}", p.nakshatra_name,
                             str(p.nakshatra_pada), p.dignity])
        rows.append(["Lagna", f"{self.chart_data.ascendant:.2f}",
                     self.chart_data.lagna.rasi_name,
                     f"{self.chart_data.lagna.degrees_in_rasi:.2f}",
                     self.chart_data.lagna.nakshatra_name,
                     str(self.chart_data.lagna.nakshatra_pada), ""])
        self._fill_table(self.planet_table, headers, rows)

    def _update_house_table(self):
        if not self.chart_data:
            return
        headers = ["House", "Rasi", "Lord", "Cusp Longitude"]
        rows = []
        for i, cusp in enumerate(self.chart_data.house_cusps):
            r = Rasi.from_longitude(cusp)
            rows.append([str(i + 1), r.full_name, r.lord, f"{cusp:.2f}"])
        self._fill_table(self.house_table, headers, rows)

    def _update_dasa_text(self):
        if not self.chart_data:
            return
        try:
            system = self.dasa_system_combo.currentText()
            chart_dict = {
                "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                            for g, p in self.chart_data.planets.items()},
                "lagna_lon": self.chart_data.ascendant,
            }
            if system == "Vimsottari":
                from jhora.dasas.vimsottari import VimsottariDasa
                engine = VimsottariDasa()
            elif system == "Ashtottari":
                from jhora.dasas.ashtottari import AshtottariDasa
                engine = AshtottariDasa()
            else:
                engine = VimsottariDasa()

            periods = engine.compute(self.chart_data.julian_day, chart_dict)
            se = SweEngine()
            lines = [f"{system} Dasa Periods", "─" * 48, ""]
            for md in periods:
                y1, m1, d1, _ = se.revjul(md.start_jd)
                y2, m2, d2, _ = se.revjul(md.end_jd)
                try:
                    lord = Graha(int(md.lord_index)).full_name
                except ValueError:
                    lord = str(md.lord_index)
                lines.append(
                    f"{lord:14s}  {int(y1)}/{int(m1):02d}/{int(d1):02d}"
                    f"  →  {int(y2)}/{int(m2):02d}/{int(d2):02d}"
                    f"  ({md.duration_years:.2f} yrs)")
            self.dasa_text.setText("\n".join(lines))
        except Exception as e:
            self.dasa_text.setText(f"Dasa computation error:\n{e}")

    # --- Varga ---

    def _on_varga_level_changed(self, index: int):
        vl = self.varga_level_combo.currentData()
        variants = get_variants_for_level(vl)
        self.varga_variant_combo.clear()
        for v in variants:
            self.varga_variant_combo.addItem(v.name, v)

    def _on_varga_show(self):
        if not self.chart_data:
            return
        try:
            vl = self.varga_level_combo.currentData()
            var = self.varga_variant_combo.currentData()
            comp = VargaChartComputer()
            vcd = comp.compute(self.chart_data, vl, var)
            self._update_varga_table(vcd)
        except Exception as e:
            QMessageBox.warning(self, "Varga Error", str(e))

    def _update_varga_table(self, vcd: VargaChartData):
        headers = ["Planet", "Rasi", "Degrees", "Lord", "Longitude"]
        rows = []
        for g in Graha:
            if g in vcd.positions:
                p = vcd.positions[g]
                rows.append([g.full_name, p.rasi.full_name,
                             f"{p.degrees_in_rasi:.2f}", p.rasi.lord,
                             f"{p.longitude:.2f}"])
        rows.append(["Lagna", vcd.lagna_position.rasi.full_name,
                     f"{vcd.lagna_position.degrees_in_rasi:.2f}",
                     vcd.lagna_position.rasi.lord,
                     f"{vcd.lagna_position.longitude:.2f}"])
        self._fill_table(self.varga_table, headers, rows)

    # --- Yogas ---

    def _build_yoga_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        self.yoga_table = QTableWidget()
        headers = ["Yoga", "Category", "Planets", "Strength", "Description"]
        self.yoga_table.setColumnCount(len(headers))
        self.yoga_table.setHorizontalHeaderLabels(headers)
        self.yoga_table.horizontalHeader().setStretchLastSection(True)
        self.yoga_table.setAlternatingRowColors(True)
        layout.addWidget(self.yoga_table)
        return w

    def _populate_yoga_table(self, cd: ChartData):
        from jhora.calc.yogas import detect_all
        yogas = detect_all(cd)
        self.yoga_table.setRowCount(len(yogas))
        for i, y in enumerate(yogas):
            names = ", ".join(p.full_name for p in y.planets) if y.planets else ""
            self.yoga_table.setItem(i, 0, QTableWidgetItem(y.name))
            self.yoga_table.setItem(i, 1, QTableWidgetItem(y.category))
            self.yoga_table.setItem(i, 2, QTableWidgetItem(names))
            self.yoga_table.setItem(i, 3, QTableWidgetItem(y.strength))
            self.yoga_table.setItem(i, 4, QTableWidgetItem(y.description))
        self.yoga_table.resizeColumnsToContents()

    # --- Shadbala ---

    def _build_shadbala_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        self.shadbala_table = QTableWidget()
        headers = ["Planet", "Sthana (R)", "Dig (R)", "Kala (R)", "Chesta (R)",
                   "Naisargika (R)", "Drik (R)", "Total (R)", "Total (V)", "Rel Str"]
        self.shadbala_table.setColumnCount(len(headers))
        self.shadbala_table.setHorizontalHeaderLabels(headers)
        self.shadbala_table.horizontalHeader().setStretchLastSection(True)
        self.shadbala_table.setAlternatingRowColors(True)
        layout.addWidget(self.shadbala_table)
        return w

    def _populate_shadbala_table(self, cd: ChartData):
        try:
            comp = ShadbalaComputer(cd)
            results = comp.compute()
        except Exception:
            self.shadbala_table.setRowCount(0)
            return

        planets_order = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                         Graha.JUPITER, Graha.VENUS, Graha.SATURN]
        rows_data = []
        max_total = 0.0
        for g in planets_order:
            if g not in results:
                continue
            r = results[g]
            max_total = max(max_total, r.total_virupa)
            rows_data.append(r)

        self.shadbala_table.setRowCount(len(rows_data))
        for i, r in enumerate(rows_data):
            rel_pct = (r.total_virupa / max_total * 100) if max_total > 0 else 0
            row = [
                r.graha.full_name,
                f"{r.sthana_total / 60:.2f}",
                f"{r.dig_total / 60:.2f}",
                f"{r.kala_total / 60:.2f}",
                f"{r.chesta_total / 60:.2f}",
                f"{r.naisargika.rupa:.2f}",
                f"{r.drik.rupa:.2f}",
                f"{r.total_rupa:.2f}",
                f"{r.total_virupa:.1f}",
                f"{rel_pct:.1f}%",
            ]
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.shadbala_table.setItem(i, c, item)
        self.shadbala_table.resizeColumnsToContents()
