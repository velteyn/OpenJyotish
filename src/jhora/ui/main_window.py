from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QTextEdit, QTabWidget,
    QMessageBox, QGroupBox, QFormLayout,
    QDateEdit, QTimeEdit,
)

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.charts.varga import VargaChartComputer, VargaChartData, get_variants_for_level
from jhora.calc.shadbala import ShadbalaComputer
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.varga import VargaLevel, VargaVariant
from jhora.ui.chart_widget import ChartWidget, ChartStyle
from jhora.calc.ashtakavarga import (
    all_bhinna_ashtakavarga, sarva_ashtakavarga, sodhya_pinda,
    kakshya_bindu_table,
    _OCCUPANT_GRAHAS,
)


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
QTableWidget::item {{ padding: 5px 8px; background-color: {BG2}; }}
QTableWidget::item:alternate {{ background-color: #1a2744; }}
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
QWidget#msgBox {{ background-color: #ffffff; color: #000000;
                 font-size: 14px; }}
QMessageBox {{ background-color: #ffffff; }}
QMessageBox QLabel {{ color: #000000; font-size: 14px; }}
QMessageBox QPushButton {{ background-color: #e94560; color: white;
                          padding: 6px 24px; font-size: 13px; }}
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

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate(1970, 4, 4))
        self.date_input.setToolTip("Click to open calendar")

        self.time_input = QTimeEdit()
        self.time_input.setDisplayFormat("HH:mm:ss")
        self.time_input.setTime(QTime(17, 48, 20))
        self.time_input.setToolTip("Local birth time")

        self.tz_input = QLineEdit()
        self.tz_input.setPlaceholderText("-2.0 or +0530")
        self.tz_input.setToolTip(
            "Offset from UTC: enter signed hours.\n"
            "  Examples:  UTC+2 → -2.0,  UTC+5:30 → +0530,  UTC-5 → +5.0"
        )

        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText("13.08")
        self.lon_input = QLineEdit()
        self.lon_input.setPlaceholderText("80.27")

        # Row with TZ input + detect button + helper label
        tz_row = QHBoxLayout()
        tz_row.setSpacing(6)
        self.tz_detect_btn = QPushButton("🕐 Now")
        self.tz_detect_btn.setFixedWidth(80)
        self.tz_detect_btn.clicked.connect(self._fill_now)
        self.tz_detect_btn.setToolTip("Fill date/time from system clock and detect TZ")
        tz_row.addWidget(self.tz_input, 1)
        tz_row.addWidget(self.tz_detect_btn)
        tz_label = QLabel("UTC = local + offset")
        tz_label.setStyleSheet(f"color: {DIM}; font-size: 11px;")
        tz_label.setToolTip(
            "Enter the signed offset to convert local time to UTC.\n"
            "  Europe summer (UTC+2) → -2.0\n"
            "  Europe winter (UTC+1) → -1.0\n"
            "  India (UTC+5:30) → +0530 or -5.5"
        )
        tz_row.addWidget(tz_label)

        # Lat + detect button
        lat_row = QHBoxLayout()
        lat_row.setSpacing(6)
        self.geo_detect_btn = QPushButton("📍 Detect")
        self.geo_detect_btn.setFixedWidth(90)
        self.geo_detect_btn.clicked.connect(self._detect_location)
        self.geo_detect_btn.setToolTip("Detect location from IP address")
        lat_row.addWidget(self.lat_input, 1)
        lon_row = QHBoxLayout()
        lon_row.setSpacing(6)
        lon_row.addWidget(self.lon_input, 1)
        lon_row.addWidget(self.geo_detect_btn)

        for w in (self.date_input, self.time_input, self.tz_input,
                  self.lat_input, self.lon_input):
            w.setMinimumWidth(180)

        form.addRow("Date:", self.date_input)
        form.addRow("Time:", self.time_input)
        form.addRow("TZ offset:", tz_row)
        form.addRow("Lat:", lat_row)
        form.addRow("Lon:", lon_row)

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
        self.tabs.addTab(self._build_ashtakavarga_tab(), "Ashtakavarga")
        self.tabs.addTab(self._build_transit_tab(), "Transit")

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

    def _detect_location(self):
        """Detect latitude/longitude from IP address via geolocation API."""
        import json
        import urllib.request
        try:
            self.statusBar().showMessage("Detecting location...")
            req = urllib.request.Request(
                "http://ip-api.com/json/",
                headers={"User-Agent": "jhora/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            if data.get("status") != "success":
                QMessageBox.warning(self, "Geo Error", data.get("message", "Unknown error"))
                self.statusBar().showMessage("Location detection failed")
                return
            lat = data["lat"]
            lon = data["lon"]
            self.lat_input.setText(f"{lat:.4f}")
            self.lon_input.setText(f"{lon:.4f}")
            self.statusBar().showMessage(
                f"Detected: {data.get('city', '')}, {data.get('country', '')}  "
                f"({lat:.4f}, {lon:.4f})"
            )
        except Exception as e:
            QMessageBox.warning(self, "Geo Error", f"Could not detect location:\n{e}")
            self.statusBar().showMessage("Location detection failed")

    def _fill_now(self):
        """Fill date/time from system clock, auto-detect timezone offset."""
        now = datetime.now()
        self.date_input.setDate(QDate(now.year, now.month, now.day))
        self.time_input.setTime(QTime(now.hour, now.minute, now.second))
        # Auto-detect UTC offset from system
        import time
        is_dst = time.localtime().tm_isdst
        utc_offset = -time.timezone / 3600  # time.timezone is seconds west of UTC
        if is_dst > 0:
            utc_offset += 1  # DST adds an hour eastward
        # Format as signed decimal: UTC+X → -X.0
        sign = "+" if utc_offset < 0 else "-"
        self.tz_input.setText(f"{sign}{abs(utc_offset):.1f}")
        self.statusBar().showMessage(
            f"Filled: {now.strftime('%Y-%m-%d %H:%M:%S')} local, "
            f"TZ = {sign}{abs(utc_offset):.1f} (UTC{'−' if utc_offset > 0 else '+'}{abs(utc_offset):.1f})"
        )

    def _set_example_data(self):
        self.date_input.setDate(QDate(1970, 4, 4))
        self.time_input.setTime(QTime(17, 48, 20))
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
            qd = self.date_input.date()
            qt = self.time_input.time()
            tz = self.tz_input.text().strip()
            lat_str = self.lat_input.text().strip()
            lon_str = self.lon_input.text().strip()
            ayanamsa = self.ayanamsa_combo.currentText().lower()

            if not tz or not lat_str or not lon_str:
                QMessageBox.warning(self, "Missing Fields", "Please fill in all birth data fields.")
                return

            lat = float(lat_str)
            lon = float(lon_str)
            year, month, day = qd.year(), qd.month(), qd.day()
            hour = qt.hour() + qt.minute() / 60.0 + qt.second() / 3600.0

            self.statusBar().showMessage("Calculating...")
            self.chart_data = self.builder.build(
                year=year, month=month, day=day,
                hour=hour, lat=lat, lon=lon,
                tz=tz, ayanamsa=ayanamsa,
            )
            self.chart_widget.set_chart_data(self.chart_data)
            self._update_planet_table()
            self._update_house_table()
            self._update_dasa_text()
            self._populate_yoga_table(self.chart_data)
            self._populate_shadbala_table(self.chart_data)
            self._populate_ashtakavarga_table(self.chart_data)
            self._populate_transit_table(self.chart_data)

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
        white = QBrush(QColor("#ffffff"))
        bg = QBrush(QColor("#16213e"))
        bg_alt = QBrush(QColor("#1a2744"))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setForeground(white)
                item.setBackground(bg_alt if r % 2 else bg)
                table.setItem(r, c, item)
        table.horizontalHeader().setStretchLastSection(True)
        table.resizeColumnsToContents()
        table.verticalHeader().setVisible(False)

    @staticmethod
    def _dignity_short(d: str) -> str:
        return {"exalted": "Ex", "debilitated": "Db", "moolatrikona": "MT",
                "own": "Own", "neutral": "Neu", "node": "Nd", "lagna": "Lg"}.get(d, d)

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
                             str(p.nakshatra_pada), self._dignity_short(p.dignity)])
        rows.append(["Lagna", f"{self.chart_data.ascendant:.2f}",
                     self.chart_data.lagna.rasi_name,
                     f"{self.chart_data.lagna.degrees_in_rasi:.2f}",
                     self.chart_data.lagna.nakshatra_name,
                     str(self.chart_data.lagna.nakshatra_pada), "Lg"])
        self._fill_table(self.planet_table, headers, rows)
        self.planet_table.setColumnWidth(6, 50)

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
        white = QBrush(QColor("#ffffff"))
        bg = QBrush(QColor("#16213e"))
        bg_alt = QBrush(QColor("#1a2744"))
        for i, y in enumerate(yogas):
            names = ", ".join(p.full_name for p in y.planets) if y.planets else ""
            for col, val in enumerate([y.name, y.category, names, y.strength, y.description]):
                item = QTableWidgetItem(val)
                item.setForeground(white)
                item.setBackground(bg_alt if i % 2 else bg)
                self.yoga_table.setItem(i, col, item)
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

    # --- Ashtakavarga ---

    def _build_ashtakavarga_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        ctrl.addWidget(QLabel("Tradition:"))
        self.ak_tradition_combo = QComboBox()
        self.ak_tradition_combo.addItems(["Parasara", "Varahamihira"])
        self.ak_tradition_combo.currentTextChanged.connect(self._on_ak_tradition_changed)
        ctrl.addWidget(self.ak_tradition_combo)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.ak_bav_table = QTableWidget()
        self.ak_bav_table.setAlternatingRowColors(True)
        layout.addWidget(self.ak_bav_table, stretch=3)

        self.ak_sp_label = QLabel()
        self.ak_sp_label.setStyleSheet(f"color: {ACCENT}; font-weight: bold; padding: 4px;")
        layout.addWidget(self.ak_sp_label)

        self.ak_sp_table = QTableWidget()
        self.ak_sp_table.setAlternatingRowColors(True)
        layout.addWidget(self.ak_sp_table, stretch=1)

        # Kakshya section
        kakshya_ctrl = QHBoxLayout()
        kakshya_ctrl.setSpacing(8)
        kakshya_ctrl.addWidget(QLabel("Kakshya planet:"))
        self.ak_kakshya_combo = QComboBox()
        for g in _OCCUPANT_GRAHAS:
            self.ak_kakshya_combo.addItem(g.full_name, g)
        self.ak_kakshya_combo.currentIndexChanged.connect(self._on_ak_kakshya_changed)
        kakshya_ctrl.addWidget(self.ak_kakshya_combo)
        kakshya_ctrl.addStretch()
        layout.addLayout(kakshya_ctrl)

        self.ak_kakshya_table = QTableWidget()
        self.ak_kakshya_table.setAlternatingRowColors(True)
        layout.addWidget(self.ak_kakshya_table, stretch=2)
        return w

    def _on_ak_kakshya_changed(self, index: int):
        if self.chart_data:
            self._populate_ashtakavarga_table(self.chart_data)

    def _on_ak_tradition_changed(self, text: str):
        if self.chart_data:
            self._populate_ashtakavarga_table(self.chart_data)

    def _populate_ashtakavarga_table(self, cd: ChartData):
        parasara = self.ak_tradition_combo.currentText() == "Parasara"
        bavs = all_bhinna_ashtakavarga(cd, parasara_venus=parasara, parasara_moon=parasara)
        sav = sarva_ashtakavarga(cd, parasara_venus=parasara, parasara_moon=parasara)
        sp = sodhya_pinda(cd, parasara_venus=parasara, parasara_moon=parasara)

        # BAV table
        headers = ["House", "Rasi"] + [g.short_name for g in _OCCUPANT_GRAHAS] + ["SAV"]
        rows = []
        for h in range(12):
            rasi = Rasi(h)
            vals = [str(bavs[g][h]) for g in _OCCUPANT_GRAHAS]
            rows.append([rasi.short_name, rasi.full_name] + vals + [str(sav[h])])
        self._fill_table(self.ak_bav_table, headers, rows)

        # Sodhya Pinda label
        tradition = self.ak_tradition_combo.currentText()
        self.ak_sp_label.setText(f"Sodhya Pinda ({tradition})")

        sp_headers = ["Planet", "Sodhya Pinda"]
        sp_rows = [[g.full_name, str(sp[g])] for g in _OCCUPANT_GRAHAS]
        self._fill_table(self.ak_sp_table, sp_headers, sp_rows)

        # Kakshya table for selected planet
        subject = self.ak_kakshya_combo.currentData()
        kt = kakshya_bindu_table(subject, cd, parasara_venus=parasara, parasara_moon=parasara)
        kt_headers = ["House"] + ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "La"] + ["Total"]
        kt_rows = []
        for h in range(12):
            vals = [str(kt[h][k]) for k in range(8)]
            kt_rows.append([Rasi(h).short_name] + vals + [str(sum(kt[h]))])
        self._fill_table(self.ak_kakshya_table, kt_headers, kt_rows)

    # --- Transit tab ---

    def _build_transit_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        info = QHBoxLayout()
        self.tr_timestamp = QLabel("Transit: —")
        self.tr_timestamp.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        info.addWidget(self.tr_timestamp)
        info.addStretch()
        layout.addLayout(info)

        self.tr_table = QTableWidget()
        self.tr_table.setAlternatingRowColors(True)
        layout.addWidget(self.tr_table, stretch=1)

        sav_label = QLabel("SAV by Rasi")
        sav_label.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        layout.addWidget(sav_label)
        self.tr_sav_table = QTableWidget()
        self.tr_sav_table.setAlternatingRowColors(True)
        self.tr_sav_table.setMaximumHeight(60)
        layout.addWidget(self.tr_sav_table)
        return w

    def _populate_transit_table(self, cd: ChartData):
        from jhora.calc.gochara import compute_transits

        result = compute_transits(cd)

        self.tr_timestamp.setText(f"Transit: {result.timestamp.strftime('%Y-%m-%d %H:%M UTC')}")

        headers = ["Planet", "In", "Deg", "Ret", "H(Lg)", "H(Mo)", "BAV", "SAV", "Fav"]
        rows = []
        for e in result.entries:
            ret = "R" if e.is_retrograde else ""
            fav = "✓" if e.is_favorable else "✗"
            rows.append([
                e.graha.short_name, e.transit_rasi_name,
                f"{e.transit_degrees:.1f}", ret,
                str(e.house_from_lagna), str(e.house_from_moon),
                str(e.bav_score), str(e.sav_score), fav,
            ])
        self._fill_table(self.tr_table, headers, rows)

        sav_headers = [Rasi(r).short_name for r in range(12)]
        sav_row = [str(result.sav[r]) for r in range(12)]
        self._fill_table(self.tr_sav_table, sav_headers, [sav_row])
