from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QDate, QTime, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QListWidget, QListWidgetItem, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QTextEdit, QTabWidget,
    QMessageBox, QGroupBox, QFormLayout,
    QDateEdit, QTimeEdit, QFileDialog,
)
from PyQt6.QtGui import QAction

from jhora.io.atlas import AtlasCity, AtlasReader
from jhora.io.jhd_parser import parse_jhd, save_jhd, JhdData, JhdFormat

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
        self.current_file: Optional[str] = None
        self.builder = ChartBuilder()
        self._init_ui()
        self._create_menu_bar()

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

        self._atlas: Optional[AtlasReader] = None
        self._city_search_timer = QTimer()
        self._city_search_timer.setSingleShot(True)
        self._city_search_timer.setInterval(300)
        self._city_search_timer.timeout.connect(self._on_city_search)

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Search city...")
        self.city_input.textChanged.connect(self._on_city_text_changed)

        self.city_search_btn = QPushButton("🔍")
        self.city_search_btn.setFixedWidth(40)
        self.city_search_btn.clicked.connect(self._on_city_search)

        city_row = QHBoxLayout()
        city_row.setSpacing(6)
        city_row.addWidget(self.city_input, 1)
        city_row.addWidget(self.city_search_btn)

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

        for w in (self.date_input, self.time_input, self.city_input, self.tz_input,
                  self.lat_input, self.lon_input):
            w.setMinimumWidth(180)

        form.addRow("Date:", self.date_input)
        form.addRow("Time:", self.time_input)
        form.addRow("City:", city_row)
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

        self.city_results = QListWidget()
        self.city_results.setHidden(True)
        self.city_results.setMaximumHeight(200)
        self.city_results.itemClicked.connect(self._on_city_selected)
        self.city_results.setStyleSheet(f"""
            QListWidget {{ background-color: {BG2}; color: #ffffff;
                          border: 1px solid {BORDER}; border-radius: 4px; }}
            QListWidget::item {{ padding: 6px 8px; }}
            QListWidget::item:selected {{ background-color: {BORDER}; }}
            QListWidget::item:hover {{ background-color: #0f3460; }}
        """)
        left_layout.addWidget(self.city_results)

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
        self.dasa_system_combo.addItems([
            "Vimsottari", "Ashtottari", "Yogini", "Sudasa",
            "Chara", "Narayana", "Kalachakra",
        ])
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
        self.tabs.addTab(self._build_arudha_tab(), "Arudha & Karaka")
        self.tabs.addTab(self._build_ashtakavarga_tab(), "Ashtakavarga")
        self.tabs.addTab(self._build_transit_tab(), "Transit")
        self.tabs.addTab(self._build_tajaka_tab(), "Tajaka")
        self.tabs.addTab(self._build_kuta_tab(), "Matchmaking")
        self.tabs.addTab(self._build_prasna_tab(), "Prasna")
        self.tabs.addTab(self._build_muhurta_tab(), "Muhurta")
        self.tabs.addTab(self._build_knowledge_tab(), "Knowledge")
        self.tabs.addTab(self._build_interpreter_tab(), "Reading")

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

    def _create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        open_act = QAction("&Open...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._on_file_open)
        file_menu.addAction(open_act)

        save_act = QAction("&Save", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self._on_file_save)
        file_menu.addAction(save_act)

        save_as_act = QAction("Save &As...", self)
        save_as_act.setShortcut("Ctrl+Shift+S")
        save_as_act.triggered.connect(self._on_file_save_as)
        file_menu.addAction(save_as_act)

        file_menu.addSeparator()

        exit_act = QAction("E&xit", self)
        exit_act.setShortcut("Ctrl+Q")
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

    def _on_file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open JHora Data", "", "JHora Data (*.jhd);;All Files (*)"
        )
        if not path:
            return
        try:
            data = parse_jhd(path)
            self.date_input.setDate(QDate(data.year, data.month, data.day))
            h = int(data.time_hours)
            m = int((data.time_hours - h) * 60)
            s = int(round(((data.time_hours - h) * 60 - m) * 60))
            self.time_input.setTime(QTime(h, m, s))
            tz_sign = "+" if data.tz_offset >= 0 else "-"
            self.tz_input.setText(f"{tz_sign}{abs(data.tz_offset):.1f}")
            self.lat_input.setText(f"{data.latitude:.4f}")
            self.lon_input.setText(f"{-data.longitude:.4f}")
            if data.city:
                self.city_input.setText(data.city)
            self.current_file = path
            self.setWindowTitle(f"Jagannatha Hora — {data.name}")
            self.statusBar().showMessage(f"Opened: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Open Error", f"Could not open file:\n{e}")

    def _on_file_save(self):
        if self.current_file:
            self._do_save(self.current_file)
        else:
            self._on_file_save_as()

    def _on_file_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save JHora Data", "", "JHora Data (*.jhd);;All Files (*)"
        )
        if path:
            if not path.endswith(".jhd"):
                path += ".jhd"
            self._do_save(path)
            self.current_file = path

    def _do_save(self, path: str):
        try:
            qd = self.date_input.date()
            qt = self.time_input.time()
            tz_str = self.tz_input.text().strip()
            lat = float(self.lat_input.text().strip())
            lon = float(self.lon_input.text().strip())
            city = self.city_input.text().strip()
            hour = qt.hour() + qt.minute() / 60.0 + qt.second() / 3600.0
            tz_offset = ChartBuilder._parse_tz(tz_str)

            data = JhdData(
                filename=path.split("/")[-1],
                format=JhdFormat.BIRTH_CITY,
                day=qd.day(), month=qd.month(), year=qd.year(),
                time_hours=hour,
                tz_offset=tz_offset,
                longitude=-lon,
                latitude=lat,
                ayanamsa_override=0.0,
                city=city, country="",
            )
            save_jhd(path, data)
            self.setWindowTitle(f"Jagannatha Hora — {data.name}")
            self.statusBar().showMessage(f"Saved: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save file:\n{e}")

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

    def _init_atlas(self) -> Optional[AtlasReader]:
        if self._atlas is not None:
            return self._atlas
        try:
            self._atlas = AtlasReader("data/cities.db")
            return self._atlas
        except Exception as e:
            self.statusBar().showMessage(f"Could not load atlas: {e}")
            return None

    def _on_city_text_changed(self, text: str):
        self._city_search_timer.start()

    def _on_city_search(self):
        text = self.city_input.text().strip()
        if len(text) < 2:
            self.city_results.setHidden(True)
            return
        atlas = self._init_atlas()
        if atlas is None:
            return
        results = atlas.search(text, max_results=15)
        self.city_results.clear()
        if results:
            for city in results:
                ns = "N" if city.latitude >= 0 else "S"
                ew = "E" if city.longitude >= 0 else "W"
                item_text = (
                    f"{city.name}  —  "
                    f"{abs(city.latitude):.2f}°{ns}  "
                    f"{abs(city.longitude):.2f}°{ew}  "
                    f"TZ={city.tz_offset:+.1f}h"
                )
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, city)
                self.city_results.addItem(item)
            self.city_results.setHidden(False)
        else:
            self.city_results.setHidden(True)

    def _on_city_selected(self, item: QListWidgetItem):
        city: AtlasCity = item.data(Qt.ItemDataRole.UserRole)
        self.lat_input.setText(f"{city.latitude:.4f}")
        self.lon_input.setText(f"{city.longitude:.4f}")
        jhora_tz = -city.tz_offset
        sign = "+" if jhora_tz >= 0 else "-"
        self.tz_input.setText(f"{sign}{abs(jhora_tz):.1f}")
        self.city_input.blockSignals(True)
        self.city_input.setText(city.name)
        self.city_input.blockSignals(False)
        self.city_results.setHidden(True)
        self.statusBar().showMessage(
            f"Selected: {city.name}  ({abs(city.latitude):.2f}°{'N' if city.latitude >= 0 else 'S'}, "
            f"{abs(city.longitude):.2f}°{'E' if city.longitude >= 0 else 'W'})  "
            f"TZ={city.tz_offset:+.1f}h"
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
            self._populate_arudha_table(self.chart_data)
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

            engine = self._get_dasa_engine(system)

            periods = engine.compute(self.chart_data.julian_day, chart_dict)
            se = SweEngine()
            lines = [f"{system} Dasa Periods", "─" * 48, ""]
            for md in periods:
                lines.extend(self._render_period_tree(md, se, 0))
            self.dasa_text.setText("\n".join(lines))
        except Exception as e:
            self.dasa_text.setText(f"Dasa computation error:\n{e}")

    @staticmethod
    def _render_period_tree(period: "DasaPeriod", se, depth: int) -> list:
        indent = "  " * depth
        y1, m1, d1, _ = se.revjul(period.start_jd)
        y2, m2, d2, _ = se.revjul(period.end_jd)
        level_labels = ["", "MD", "AD", "PD", "SD", "D"]
        label = level_labels[depth] if depth < len(level_labels) else ""
        line = (
            f"{indent}{period.lord_name:16s} {label:3s} "
            f"{int(y1)}/{int(m1):02d}/{int(d1):02d} → "
            f"{int(y2)}/{int(m2):02d}/{int(d2):02d}  "
            f"({period.duration_years:.2f})")
        result = [line]
        if period.sub_periods:
            for sp in period.sub_periods:
                result.extend(MainWindow._render_period_tree(sp, se, depth + 1))
        return result

    def _get_dasa_engine(self, system: str):
        if system == "Vimsottari":
            from jhora.dasas.vimsottari import VimsottariDasa
            return VimsottariDasa()
        elif system == "Ashtottari":
            from jhora.dasas.ashtottari import AshtottariDasa
            return AshtottariDasa()
        elif system == "Yogini":
            from jhora.dasas.yogini import YoginiDasa
            return YoginiDasa()
        elif system == "Sudasa":
            from jhora.dasas.sudasa import Sudasa
            return Sudasa()
        elif system == "Chara":
            from jhora.dasas.chara import CharaDasa
            return CharaDasa()
        elif system == "Narayana":
            from jhora.dasas.narayana import NarayanaDasa
            return NarayanaDasa()
        elif system == "Kalachakra":
            from jhora.dasas.kalachakra import KalachakraDasa
            return KalachakraDasa()
        from jhora.dasas.vimsottari import VimsottariDasa
        return VimsottariDasa()

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

    def _build_arudha_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Bhava Arudhas (Pada of each house):"))
        self.arudha_bhava_table = QTableWidget()
        self.arudha_bhava_table.setAlternatingRowColors(True)
        layout.addWidget(self.arudha_bhava_table, stretch=3)

        layout.addWidget(QLabel("Graha Arudhas (Pada of each planet):"))
        self.arudha_graha_table = QTableWidget()
        self.arudha_graha_table.setAlternatingRowColors(True)
        layout.addWidget(self.arudha_graha_table, stretch=2)

        layout.addWidget(QLabel("Chara Karakas (8 significators by longitude):"))
        self.karaka_table = QTableWidget()
        self.karaka_table.setAlternatingRowColors(True)
        layout.addWidget(self.karaka_table, stretch=2)

        layout.addWidget(QLabel("Sahamas (sensitive points):"))
        self.sahama_table = QTableWidget()
        self.sahama_table.setAlternatingRowColors(True)
        layout.addWidget(self.sahama_table, stretch=3)

        return w

    def _populate_arudha_table(self, cd: ChartData):
        from jhora.calc.arudha import all_bhava_arudhas, all_graha_arudhas
        from jhora.calc.karaka import compute_chara_karakas
        from jhora.calc.sahama import compute_sahamas
        planets = {g: {"longitude": p.longitude, "speed": p.speed}
                   for g, p in cd.planets.items()}

        bhava = all_bhava_arudhas(cd.ascendant, planets)
        headers = ["House", "Pada Name", "Sign"]
        rows = []
        for n in range(1, 13):
            name = {1: "AL (Arudha Lagna)", 2: "A2 (Dhana)", 3: "A3 (Vikrama)",
                    4: "A4 (Sukha)", 5: "A5 (Mantra)", 6: "A6 (Satru)",
                    7: "A7 (Dara)", 8: "A8 (Mrityu)", 9: "A9 (Bhagya)",
                    10: "A10 (Karma)", 11: "A11 (Labha)", 12: "A12 (Upapada)"}.get(n, f"A{n}")
            rows.append([str(n), name, bhava[n].full_name])
        self._fill_table(self.arudha_bhava_table, headers, rows)

        graha_arus = all_graha_arudhas(planets)
        headers = ["Planet", "Pada Name", "Sign"]
        rows = []
        for g in Graha:
            if g in graha_arus:
                rows.append([g.full_name,
                            f"A({g.short_name})",
                            graha_arus[g].full_name])
        self._fill_table(self.arudha_graha_table, headers, rows)

        karakas = compute_chara_karakas(planets)
        headers = ["Rank", "Karaka", "Planet", "Longitude", "Meaning"]
        rows = []
        for k in karakas:
            rows.append([
                str(k.rank), f"{k.short_name} ({k.full_name})",
                k.graha.full_name, f"{k.longitude:.2f}°", k.meaning,
            ])
        self._fill_table(self.karaka_table, headers, rows)

        is_day = 6.0 <= cd.time_of_day_hours < 18.0
        sahamas = compute_sahamas(cd.ascendant, planets, day=is_day)
        headers = ["Sahama", "Meaning", "Longitude", "Sign", "House"]
        rows = []
        for sah in sahamas:
            sign = ZodiacSign(int(sah.longitude / 30))
            house = int(sah.longitude / 30) - int(cd.ascendant / 30) + 1
            if house <= 0:
                house += 12
            rows.append([
                sah.name, sah.meaning,
                f"{sah.longitude:.2f}°",
                sign.full_name,
                str(house),
            ])
        self._fill_table(self.sahama_table, headers, rows)

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

    def _build_tajaka_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        top = QHBoxLayout()
        top.addWidget(QLabel("Year:"))
        self.taj_year_combo = QComboBox()
        self.taj_year_combo.setEditable(True)
        self.taj_year_combo.setCurrentText("2001")
        top.addWidget(self.taj_year_combo)
        self.taj_find_btn = QPushButton("Find Tajaka Chart")
        self.taj_find_btn.clicked.connect(self._on_tajaka_find)
        top.addWidget(self.taj_find_btn)
        top.addStretch()
        layout.addLayout(top)

        self.taj_info = QLabel("")
        self.taj_info.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        layout.addWidget(self.taj_info)

        self.taj_chart_table = QTableWidget()
        self.taj_chart_table.setAlternatingRowColors(True)
        layout.addWidget(self.taj_chart_table, stretch=1)

        self.taj_harsha_table = QTableWidget()
        self.taj_harsha_table.setAlternatingRowColors(True)
        self.taj_harsha_table.setMaximumHeight(140)
        layout.addWidget(self.taj_harsha_table)

        self.taj_patyayini_table = QTableWidget()
        self.taj_patyayini_table.setAlternatingRowColors(True)
        layout.addWidget(self.taj_patyayini_table, stretch=1)

        self.taj_mudda_table = QTableWidget()
        self.taj_mudda_table.setAlternatingRowColors(True)
        layout.addWidget(self.taj_mudda_table, stretch=1)

        return w

    def _on_tajaka_find(self):
        if not self.chart_data:
            return
        from jhora.calc.tajaka import (
            build_tajaka_chart, compute_harsha_bala,
            compute_patyayini_dasa, compute_mudda_dasa,
        )
        try:
            target_year = int(self.taj_year_combo.currentText().strip())
        except ValueError:
            return

        cb = ChartBuilder(self.builder.swe)
        taj = build_tajaka_chart(self.builder.swe, cb, self.chart_data, target_year)
        chart = taj.chart

        y, m, d, h = self.builder.swe.revjul(taj.varsha_pravesh_jd)
        muntha_name = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi",
                        "Li", "Sc", "Sg", "Cp", "Aq", "Pi"][taj.muntha_sign]
        self.taj_info.setText(
            f"Varsha Pravesh: {int(y)}-{int(m):02d}-{int(d):02d} {h:.2f}h UT  |  "
            f"Year {taj.year_index}  |  Muntha: {muntha_name} ({taj.muntha_sign})"
        )

        headers = ["Graha", "Longitude", "Sign", "Nakshatra", "Pada"]
        rows = []
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                   Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
            p = chart.planets[g]
            rows.append([
                g.short_name, f"{p.longitude:.2f}°",
                p.rasi_name, p.nakshatra_name, str(p.nakshatra_pada),
            ])
        self._fill_table(self.taj_chart_table, headers, rows)

        hb = compute_harsha_bala(chart, taj.varsha_pravesh_jd)
        hb_headers = ["Planet", "Score"]
        hb_rows = []
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                   Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
            hb_rows.append([g.short_name, str(hb.get(g, 0))])
        self._fill_table(self.taj_harsha_table, hb_headers, hb_rows)

        periods = compute_patyayini_dasa(chart.planets, chart.ascendant, taj.varsha_pravesh_jd)
        pd_headers = ["Lord", "Days", "Start JD", "End JD"]
        pd_rows = []
        for p in periods:
            pd_rows.append([
                p.lord_name, f"{p.duration_years * 365:.2f}",
                f"{p.start_jd:.4f}", f"{p.end_jd:.4f}",
            ])
        self._fill_table(self.taj_patyayini_table, pd_headers, pd_rows)

        md = compute_mudda_dasa(
            self.chart_data.moon.longitude, taj.year_index - 1, taj.varsha_pravesh_jd,
        )
        md_headers = ["Lord", "Days", "Start JD", "End JD"]
        md_rows = []
        for p in md:
            md_rows.append([
                p.lord_name, f"{p.duration_years * 365:.2f}",
                f"{p.start_jd:.4f}", f"{p.end_jd:.4f}",
            ])
        self._fill_table(self.taj_mudda_table, md_headers, md_rows)

    # --- Kuta / Matchmaking tab ---

    def _build_kuta_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Girl inputs
        girl_group = QGroupBox("Girl (or use current chart)")
        gg = QHBoxLayout(girl_group)
        gg.addWidget(QLabel("Date:"))
        self.kuta_girl_date = QDateEdit()
        self.kuta_girl_date.setCalendarPopup(True)
        self.kuta_girl_date.setDate(QDate(2000, 1, 1))
        gg.addWidget(self.kuta_girl_date)
        gg.addWidget(QLabel("Time:"))
        self.kuta_girl_time = QTimeEdit()
        self.kuta_girl_time.setTime(QTime(12, 0))
        gg.addWidget(self.kuta_girl_time)
        gg.addWidget(QLabel("TZ:"))
        self.kuta_girl_tz = QLineEdit("+0530")
        self.kuta_girl_tz.setMaximumWidth(80)
        gg.addWidget(self.kuta_girl_tz)
        gg.addWidget(QLabel("Lat:"))
        self.kuta_girl_lat = QLineEdit("13.08")
        self.kuta_girl_lat.setMaximumWidth(80)
        gg.addWidget(self.kuta_girl_lat)
        gg.addWidget(QLabel("Lon:"))
        self.kuta_girl_lon = QLineEdit("80.27")
        self.kuta_girl_lon.setMaximumWidth(80)
        gg.addWidget(self.kuta_girl_lon)
        layout.addWidget(girl_group)

        # Boy inputs
        boy_group = QGroupBox("Boy")
        bg = QHBoxLayout(boy_group)
        bg.addWidget(QLabel("Date:"))
        self.kuta_boy_date = QDateEdit()
        self.kuta_boy_date.setCalendarPopup(True)
        self.kuta_boy_date.setDate(QDate(2000, 1, 1))
        bg.addWidget(self.kuta_boy_date)
        bg.addWidget(QLabel("Time:"))
        self.kuta_boy_time = QTimeEdit()
        self.kuta_boy_time.setTime(QTime(12, 0))
        bg.addWidget(self.kuta_boy_time)
        bg.addWidget(QLabel("TZ:"))
        self.kuta_boy_tz = QLineEdit("+0530")
        self.kuta_boy_tz.setMaximumWidth(80)
        bg.addWidget(self.kuta_boy_tz)
        bg.addWidget(QLabel("Lat:"))
        self.kuta_boy_lat = QLineEdit("13.08")
        self.kuta_boy_lat.setMaximumWidth(80)
        bg.addWidget(self.kuta_boy_lat)
        bg.addWidget(QLabel("Lon:"))
        self.kuta_boy_lon = QLineEdit("80.27")
        self.kuta_boy_lon.setMaximumWidth(80)
        bg.addWidget(self.kuta_boy_lon)
        layout.addWidget(boy_group)

        # Scoring system toggle
        system_row = QHBoxLayout()
        system_row.addWidget(QLabel("Scoring system:"))
        self.kuta_system_combo = QComboBox()
        self.kuta_system_combo.addItems(["10 Porutham (19 pts)", "Ashta Koota (36 pts)"])
        system_row.addWidget(self.kuta_system_combo)
        system_row.addStretch()
        layout.addLayout(system_row)

        match_row = QHBoxLayout()
        self.kuta_match_btn = QPushButton("Compute Match")
        self.kuta_match_btn.clicked.connect(self._on_kuta_match)
        match_row.addWidget(self.kuta_match_btn)
        self.kuta_score_label = QLabel("")
        self.kuta_score_label.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 14px;")
        match_row.addWidget(self.kuta_score_label)
        match_row.addStretch()
        layout.addLayout(match_row)

        self.kuta_table = QTableWidget()
        self.kuta_table.setAlternatingRowColors(True)
        layout.addWidget(self.kuta_table, stretch=1)

        self.kuta_detail = QTextEdit()
        self.kuta_detail.setReadOnly(True)
        self.kuta_detail.setMaximumHeight(160)
        layout.addWidget(self.kuta_detail)

        return w

    def _build_prasna_tab(self):
        from jhora.calc.prasna import PrasnaMode

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Mode + number row
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Mode:"))
        self.prasna_mode_combo = QComboBox()
        for pm in PrasnaMode:
            self.prasna_mode_combo.addItem(f"{pm.label} (1-{pm.max_number})", pm)
        self.prasna_mode_combo.currentIndexChanged.connect(self._on_prasna_mode_changed)
        input_row.addWidget(self.prasna_mode_combo)

        input_row.addWidget(QLabel("Number:"))
        self.prasna_number_input = QLineEdit()
        self.prasna_number_input.setPlaceholderText("1-108")
        self.prasna_number_input.setMaximumWidth(100)
        input_row.addWidget(self.prasna_number_input)

        self.prasna_calc_btn = QPushButton("Compute")
        self.prasna_calc_btn.clicked.connect(self._on_prasna_compute)
        input_row.addWidget(self.prasna_calc_btn)

        self.prasna_table_btn = QPushButton("Show All")
        self.prasna_table_btn.clicked.connect(self._on_prasna_show_all)
        input_row.addWidget(self.prasna_table_btn)

        input_row.addStretch()
        layout.addLayout(input_row)

        # Result label
        self.prasna_result_label = QLabel("")
        self.prasna_result_label.setWordWrap(True)
        self.prasna_result_label.setStyleSheet(
            f"color: {ACCENT}; font-weight: bold; font-size: 14px;"
            f" padding: 8px; background-color: {BG2}; border-radius: 4px;"
        )
        layout.addWidget(self.prasna_result_label)

        # Detail text
        self.prasna_detail = QTextEdit()
        self.prasna_detail.setReadOnly(True)
        self.prasna_detail.setMaximumHeight(150)
        layout.addWidget(self.prasna_detail)

        # All positions table
        self.prasna_table = QTableWidget()
        self.prasna_table.setAlternatingRowColors(True)
        layout.addWidget(self.prasna_table, stretch=1)

        return w

    def _on_prasna_mode_changed(self, index: int):
        pm = self.prasna_mode_combo.currentData()
        self.prasna_number_input.setPlaceholderText(f"1-{pm.max_number}")

    def _on_prasna_compute(self):
        from jhora.calc.prasna import PrasnaMode, compute_prasna

        pm = self.prasna_mode_combo.currentData()
        try:
            n = int(self.prasna_number_input.text().strip())
        except (ValueError, AttributeError):
            QMessageBox.warning(self, "Input Error", f"Enter a number between 1 and {pm.max_number}")
            return

        try:
            r = compute_prasna(n, pm)
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
            return

        lines = [
            f"Prasna Lagna: {r.prasna_lagna:.4f}°",
            f"Rasi: {r.rasi.short_name} ({r.rasi.full_name})",
            f"Nakshatra: {r.nakshatra.name.replace('_', ' ').title()} — Pada {r.nakshatra_pada}",
        ]
        if r.navamsa_rasi:
            lines.append(f"Navamsa Rasi: {r.navamsa_rasi.short_name} ({r.navamsa_rasi.full_name})")
        if r.sub_lord:
            lines.append(f"Sub Lord: {r.sub_lord.name.title()}")
        lines.append(f"")
        lines.append(r.description)

        self.prasna_result_label.setText(
            f"Prasna Lagna: {r.prasna_lagna:.4f}° — {r.rasi.short_name} — "
            f"{r.nakshatra.name.replace('_', ' ').title()}"
        )
        self.prasna_detail.setText("\n".join(lines))

        # Clear table
        self.prasna_table.setRowCount(0)

    def _on_prasna_show_all(self):
        from jhora.calc.prasna import PrasnaMode, all_prasna_results

        pm = self.prasna_mode_combo.currentData()
        results = all_prasna_results(pm)

        headers = ["#", "PL (°)", "Rasi", "Deg"]
        if pm == PrasnaMode.MODE_108:
            headers.append("Navamsa")
        elif pm == PrasnaMode.MODE_249:
            headers.append("Nakshatra")
            headers.append("Sub")
        elif pm == PrasnaMode.NADI:
            headers.append("Nadyamsa")

        self.prasna_table.setColumnCount(len(headers))
        self.prasna_table.setHorizontalHeaderLabels(headers)
        self.prasna_table.setRowCount(len(results))

        for i, r in enumerate(results):
            self.prasna_table.setItem(i, 0, QTableWidgetItem(str(r.number)))
            self.prasna_table.setItem(i, 1, QTableWidgetItem(f"{r.prasna_lagna:.4f}"))
            self.prasna_table.setItem(i, 2, QTableWidgetItem(r.rasi.short_name))
            self.prasna_table.setItem(i, 3, QTableWidgetItem(f"{r.degrees_in_rasi:.2f}"))
            col = 4
            if pm == PrasnaMode.MODE_108:
                self.prasna_table.setItem(i, col, QTableWidgetItem(
                    r.navamsa_rasi.short_name if r.navamsa_rasi else ""
                ))
            elif pm == PrasnaMode.MODE_249:
                self.prasna_table.setItem(i, col, QTableWidgetItem(
                    r.nakshatra.name.replace("_", " ").title()
                ))
                self.prasna_table.setItem(i, col + 1, QTableWidgetItem(
                    r.sub_lord.name.title() if r.sub_lord else ""
                ))
            elif pm == PrasnaMode.NADI:
                self.prasna_table.setItem(i, col, QTableWidgetItem(str(i + 1)))

        self.prasna_table.resizeColumnsToContents()
        self.statusBar().showMessage(f"Showing all {len(results)} positions for {pm.label}")

    def _build_muhurta_tab(self):
        from jhora.calc.muhurta import MuhurtaTask

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Input form
        form = QFormLayout()
        form.setSpacing(6)

        self.muhurta_task_combo = QComboBox()
        for t in MuhurtaTask:
            self.muhurta_task_combo.addItem(t.label, t)
        form.addRow("Task:", self.muhurta_task_combo)

        self.muhurta_date = QDateEdit()
        self.muhurta_date.setCalendarPopup(True)
        self.muhurta_date.setDate(self.date_input.date())
        form.addRow("Date:", self.muhurta_date)

        self.muhurta_time = QTimeEdit()
        self.muhurta_time.setDisplayFormat("HH:mm")
        self.muhurta_time.setTime(self.time_input.time())
        form.addRow("Time:", self.muhurta_time)

        self.muhurta_tz = QLineEdit()
        self.muhurta_tz.setPlaceholderText("-2.0 or +0530")
        self.muhurta_tz.setText(self.tz_input.text() or "-2.0")
        form.addRow("TZ:", self.muhurta_tz)

        self.muhurta_lat = QLineEdit()
        self.muhurta_lat.setPlaceholderText("13.08")
        self.muhurta_lat.setText(self.lat_input.text() or "13.08")
        form.addRow("Lat:", self.muhurta_lat)

        self.muhurta_lon = QLineEdit()
        self.muhurta_lon.setPlaceholderText("80.27")
        self.muhurta_lon.setText(self.lon_input.text() or "80.27")
        form.addRow("Lon:", self.muhurta_lon)

        layout.addLayout(form)

        # Buttons row
        btn_row = QHBoxLayout()
        self.muhurta_eval_btn = QPushButton("Evaluate")
        self.muhurta_eval_btn.clicked.connect(self._on_muhurta_evaluate)
        btn_row.addWidget(self.muhurta_eval_btn)

        self.muhurta_find_btn = QPushButton("Find Auspicious Times")
        self.muhurta_find_btn.clicked.connect(self._on_muhurta_find)
        btn_row.addWidget(self.muhurta_find_btn)

        self.muhurta_best_spin = QComboBox()
        self.muhurta_best_spin.addItems(["5", "10", "20", "All"])
        self.muhurta_best_spin.setCurrentIndex(0)
        btn_row.addWidget(QLabel("Show Top:"))
        btn_row.addWidget(self.muhurta_best_spin)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Result label
        self.muhurta_result = QLabel("")
        self.muhurta_result.setWordWrap(True)
        self.muhurta_result.setStyleSheet(
            f"color: {ACCENT}; font-weight: bold; font-size: 14px;"
            f" padding: 8px; background-color: {BG2}; border-radius: 4px;"
        )
        layout.addWidget(self.muhurta_result)

        # Detail text
        self.muhurta_detail = QTextEdit()
        self.muhurta_detail.setReadOnly(True)
        self.muhurta_detail.setMaximumHeight(160)
        layout.addWidget(self.muhurta_detail)

        # Results table
        self.muhurta_table = QTableWidget()
        self.muhurta_table.setAlternatingRowColors(True)
        layout.addWidget(self.muhurta_table, stretch=1)

        return w

    def _get_muhurta_inputs(self):
        from jhora.charts.chart import ChartBuilder
        from datetime import datetime

        qd = self.muhurta_date.date()
        qt = self.muhurta_time.time()
        dt = datetime(qd.year(), qd.month(), qd.day(),
                      qt.hour(), qt.minute(), 0)
        raw_tz = ChartBuilder._parse_tz(self.muhurta_tz.text().strip())
        tz_offset = -raw_tz if raw_tz < 0 else raw_tz
        lat = float(self.muhurta_lat.text().strip())
        lon = float(self.muhurta_lon.text().strip())
        return dt, tz_offset, lat, lon

    def _on_muhurta_evaluate(self):
        from jhora.calc.muhurta import evaluate_time, MuhurtaTask

        try:
            dt, tz_offset, lat, lon = self._get_muhurta_inputs()
        except (ValueError, AttributeError) as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {e}")
            return

        task = self.muhurta_task_combo.currentData()
        r = evaluate_time(dt, lat, lon, tz_offset, task)

        status = "AUSPICIOUS" if r.is_good else "INAUSPICIOUS"
        color = "#00ff88" if r.is_good else "#ff6666"
        self.muhurta_result.setText(
            f'<span style="color:{color}">[{status}]</span> '
            f'Score: <b>{r.score:.2f}</b> / 1.00 — {task.label}'
        )

        self.muhurta_table.setRowCount(0)

        lines = []
        p = r.panchanga
        t_s = "✓" if r.tithi_ok else "✗"
        v_s = "✓" if r.weekday_ok else "✗"
        n_s = "✓" if r.nakshatra_ok else "✗"
        l_s = "✓" if r.lagna_ok else "✗"

        lines.append(f"Tithi: {p.tithi.name} {t_s}  |  Vara: {p.weekday_name} {v_s}")
        lines.append(f"Nakshatra: {p.nakshatra.name.replace('_', ' ').title()} {n_s}")
        lines.append(f"Yoga: index {p.yoga_index}  |  Karana: index {p.karana_index}")
        lines.append(f"Lagna: {r.lagna_rasi.short_name} {l_s}")

        if r.in_abhijit:
            lines.append("★ Abhijit Muhurta! (48-min window around noon)")

        for ip in r.inauspicious_periods:
            s_utc = ((ip.start + 0.5) - int(ip.start + 0.5)) * 24
            e_utc = ((ip.end + 0.5) - int(ip.end + 0.5)) * 24
            s_loc = (s_utc + tz_offset) % 24
            e_loc = (e_utc + tz_offset) % 24
            lines.append(f"{ip.kind}: {s_loc:.1f}h-{e_loc:.1f}h")

        if r.score_detail and r.score_detail != "All good":
            lines.append(f"\nIssues: {r.score_detail}")

        self.muhurta_detail.setText("\n".join(lines))

    def _on_muhurta_find(self):
        from jhora.calc.muhurta import find_muhurta, MuhurtaTask

        try:
            dt, tz_offset, lat, lon = self._get_muhurta_inputs()
        except (ValueError, AttributeError) as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {e}")
            return

        task = self.muhurta_task_combo.currentData()
        results = find_muhurta(dt, lat, lon, tz_offset, task, step_minutes=10)

        top_text = self.muhurta_best_spin.currentText()
        if top_text == "All":
            results = results
        else:
            results = results[:int(top_text)]

        headers = ["Time", "Score", "Tithi", "Vara", "Nakshatra", "Lagna", "Abhijit"]
        self.muhurta_table.setColumnCount(len(headers))
        self.muhurta_table.setHorizontalHeaderLabels(headers)
        self.muhurta_table.setRowCount(len(results))

        for i, r in enumerate(results):
            time_str = r.datetime.strftime("%H:%M")
            score_str = f"{r.score:.2f}"
            ti = f"{'✓' if r.tithi_ok else '✗'} {r.panchanga.tithi.name}"
            vr = f"{'✓' if r.weekday_ok else '✗'} {r.panchanga.weekday_name}"
            nk = f"{'✓' if r.nakshatra_ok else '✗'} {r.panchanga.nakshatra.name.replace('_', ' ').title()}"
            lg = f"{'✓' if r.lagna_ok else '✗'} {r.lagna_rasi.short_name}"
            ab = "★" if r.in_abhijit else ""

            self.muhurta_table.setItem(i, 0, QTableWidgetItem(time_str))
            self.muhurta_table.setItem(i, 1, QTableWidgetItem(score_str))
            self.muhurta_table.setItem(i, 2, QTableWidgetItem(ti))
            self.muhurta_table.setItem(i, 3, QTableWidgetItem(vr))
            self.muhurta_table.setItem(i, 4, QTableWidgetItem(nk))
            self.muhurta_table.setItem(i, 5, QTableWidgetItem(lg))
            self.muhurta_table.setItem(i, 6, QTableWidgetItem(ab))

        self.muhurta_table.resizeColumnsToContents()

        self.muhurta_result.setText(
            f"Found <b>{len(results)}</b> times  |  "
            f"Best score: <b>{results[0].score:.2f}</b> — "
            f"{self.muhurta_date.date().toString('yyyy-MM-dd')}"
        )

    def _build_knowledge_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Search row
        row = QHBoxLayout()
        self.kb_query = QLineEdit()
        self.kb_query.setPlaceholderText("Search Vedic astrology texts...")
        row.addWidget(self.kb_query, 1)

        self.kb_search_btn = QPushButton("Search")
        self.kb_search_btn.clicked.connect(self._on_kb_search)
        row.addWidget(self.kb_search_btn)

        self.kb_max_spin = QComboBox()
        self.kb_max_spin.addItems(["5", "10", "20"])
        self.kb_max_spin.setCurrentIndex(0)
        row.addWidget(QLabel("Results:"))
        row.addWidget(self.kb_max_spin)
        layout.addLayout(row)

        # Sources info
        self.kb_source_label = QLabel("")
        self.kb_source_label.setStyleSheet(f"color: {DIM}; font-size: 11px;")
        layout.addWidget(self.kb_source_label)

        # Results list
        self.kb_results = QTextEdit()
        self.kb_results.setReadOnly(True)
        self.kb_results.setStyleSheet(
            f"background-color: {BG2}; color: #ffffff;"
            f" border: 1px solid #0f3460; border-radius: 4px; padding: 6px;"
        )
        layout.addWidget(self.kb_results, stretch=1)

        return w

    def _on_kb_search(self):
        from jhora.interpreter.knowledge_base import KnowledgeBase

        query = self.kb_query.text().strip()
        if not query:
            return

        kb = KnowledgeBase()
        max_r = int(self.kb_max_spin.currentText())
        results = kb.search(query, max_results=max_r)

        self.kb_source_label.setText(
            f"Loaded {kb.loaded} sources  |  "
            f"Found {len(results)} matches for \"{query}\""
        )

        if not results:
            self.kb_results.setText("No results found.")
            return

        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] {r['source']}  (score: {r['score']:.2f})")
            lines.append(f"    {r['excerpt'][:400]}")
            lines.append("")
        self.kb_results.setText("\n".join(lines))

    def _build_interpreter_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        row = QHBoxLayout()
        self.int_style_combo = QComboBox()
        self.int_style_combo.addItems(["concise", "detailed"])
        row.addWidget(QLabel("Style:"))
        row.addWidget(self.int_style_combo)

        self.int_generate_btn = QPushButton("Generate Reading")
        self.int_generate_btn.clicked.connect(self._on_interpreter_generate)
        row.addWidget(self.int_generate_btn)
        row.addStretch()
        layout.addLayout(row)

        self.int_output = QTextEdit()
        self.int_output.setReadOnly(True)
        self.int_output.setStyleSheet(
            f"background-color: {BG2}; color: #ffffff;"
            f" border: 1px solid #0f3460; border-radius: 4px; padding: 6px;"
            f" font-family: 'DejaVu Sans Mono'; font-size: 12px;"
        )
        layout.addWidget(self.int_output, stretch=1)

        return w

    def _on_interpreter_generate(self):
        from jhora.interpreter.engine import ChartInterpreter

        cd = self._get_chart_data()
        if cd is None:
            return

        style = self.int_style_combo.currentText()
        interpreter = ChartInterpreter()
        text = interpreter.interpret_text(cd, style=style)
        self.int_output.setText(text)

    def _get_chart_data(self) -> Optional[ChartData]:
        try:
            builder = ChartBuilder()
            qd = self.date_input.date()
            qt = self.time_input.time()
            hour = qt.hour() + qt.minute() / 60.0
            ay = self.ayanamsa_combo.currentText().lower()
            tz_raw = self.tz_input.text().strip()
            lat = float(self.lat_input.text().strip())
            lon = float(self.lon_input.text().strip())
            cd = builder.build(
                year=qd.year(), month=qd.month(), day=qd.day(),
                hour=hour, lat=lat, lon=lon, tz=tz_raw, ayanamsa=ay,
            )
            return cd
        except Exception as e:
            QMessageBox.warning(self, "Chart Error", f"Cannot compute chart: {e}")
            return None

    def _on_kuta_match(self):
        from jhora.calc.kuta import compute_kuta, ScoringSystem
        qd_g = self.kuta_girl_date.date()
        qt_g = self.kuta_girl_time.time()
        qd_b = self.kuta_boy_date.date()
        qt_b = self.kuta_boy_time.time()
        tz_g = self.kuta_girl_tz.text().strip()
        tz_b = self.kuta_boy_tz.text().strip()
        lat_g = float(self.kuta_girl_lat.text().strip())
        lon_g = float(self.kuta_girl_lon.text().strip())
        lat_b = float(self.kuta_boy_lat.text().strip())
        lon_b = float(self.kuta_boy_lon.text().strip())
        ayanamsa = self.ayanamsa_combo.currentText().lower()

        is_ashta_koota = self.kuta_system_combo.currentIndex() == 1
        system = ScoringSystem.ASHTA_KOOTA if is_ashta_koota else ScoringSystem.PORUTHAM

        builder = ChartBuilder()
        builder.swe.set_sidereal_mode(ayanamsa)
        g_chart = builder.build(
            year=qd_g.year(), month=qd_g.month(), day=qd_g.day(),
            hour=qt_g.hour() + qt_g.minute() / 60.0 + qt_g.second() / 3600.0,
            lat=lat_g, lon=lon_g, tz=tz_g, ayanamsa=ayanamsa,
        )
        b_chart = builder.build(
            year=qd_b.year(), month=qd_b.month(), day=qd_b.day(),
            hour=qt_b.hour() + qt_b.minute() / 60.0 + qt_b.second() / 3600.0,
            lat=lat_b, lon=lon_b, tz=tz_b, ayanamsa=ayanamsa,
        )

        result = compute_kuta(
            g_chart.planet(Graha.MOON).longitude,
            b_chart.planet(Graha.MOON).longitude,
            system=system,
        )

        score_text = (
            f"Total: {result.total_score:.0f}/{result.max_score:.0f} "
            f"({result.percentage:.0f}%)  |  "
            f"Girl: {result.girl_nakshatra.name} "
            f"({result.girl_rasi.short_name})  →  "
            f"Boy: {result.boy_nakshatra.name} "
            f"({result.boy_rasi.short_name})"
        )
        if is_ashta_koota:
            score_text += f"  |  Level: {result.gunanka_level}"
        self.kuta_score_label.setText(score_text)

        factor_label = "Factor" if is_ashta_koota else "Porutham"
        headers = [factor_label, "Score", "Status"]
        rows = []
        for p in result.poruthams:
            status = "Good" if p.is_good else "Not Good"
            rows.append([p.name, p.fraction, status])
        self._fill_table(self.kuta_table, headers, rows)

        detail_lines = []
        for p in result.poruthams:
            icon = "✓" if p.is_good else "✗"
            detail_lines.append(f"{icon} {p.name} ({p.fraction}): {p.description}")
        self.kuta_detail.setText("\n".join(detail_lines))

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
