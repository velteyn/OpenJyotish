from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QDate, QTime, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QDialog, QListWidget, QListWidgetItem, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QTextEdit, QTabWidget,
    QMessageBox, QGroupBox, QFormLayout,
    QDateEdit, QTimeEdit, QFileDialog, QScrollArea,
)
from PyQt6.QtGui import QAction

from jhora.io.atlas import AtlasCity, AtlasReader, StaticAtlasReader, open_default_atlas
from jhora.io.jhd_parser import (
    parse_jhd, save_jhd, JhdData, JhdFormat,
    save_chart_to_db, load_chart_from_db, list_charts, delete_chart,
    import_jhd_to_db, export_chart_to_jhd,
)
from jhora.core.database import get_db, set_db_path
from jhora.ai.engine import AiEngine, AiConfig, PROVIDERS

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.charts.varga import VargaChartComputer, VargaChartData, get_variants_for_level
from jhora.calc.shadbala import ShadbalaComputer
from jhora.calc.bhava_bala import BhavaBalaComputer
from jhora.calc.vimsopaka import VimsopakaComputer, VimsopakaScheme
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.varga import VargaLevel, VargaVariant
from jhora.ui.dasa_timeline_widget import DasaTimelineWidget
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

        self._atlas: Optional[AtlasReader | StaticAtlasReader] = None
        self._city_search_timer = QTimer()
        self._city_search_timer.setSingleShot(True)
        self._city_search_timer.setInterval(300)
        self._city_search_timer.timeout.connect(self._on_city_search)

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Search city...")
        self.city_input.textChanged.connect(self._on_city_text_changed)
        self.city_input.returnPressed.connect(self._on_city_search)

        self.city_search_btn = QPushButton("Search")
        self.city_search_btn.setFixedWidth(80)
        self.city_search_btn.setToolTip("Search city in bundled atlas data")
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

        # House tab — includes chalit
        self.house_widget = QWidget()
        hl = QVBoxLayout(self.house_widget)
        hl.setContentsMargins(4, 4, 4, 4)
        hl.setSpacing(6)
        self.house_table = QTableWidget()
        hl.addWidget(self.house_table)

        self.chalit_label = QLabel("Chalit (Bhava) Shifts — cusp-based house positions")
        self.chalit_label.setStyleSheet("font-weight: bold; color: #e0b050;")
        hl.addWidget(self.chalit_label)
        self.chalit_table = QTableWidget()
        self.chalit_table.setMaximumHeight(260)
        hl.addWidget(self.chalit_table)

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

        self.dasa_timeline = DasaTimelineWidget()
        dl.addWidget(self.dasa_timeline)

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

        # 1. Dashboard
        self.tabs.addTab(self._build_dashboard_tab(), "Dashboard")

        # 2. Chart & Varga
        chart_sub = QTabWidget()
        chart_sub.addTab(self._build_consolidated_tab(), "Chart View")
        chart_sub.addTab(self.planet_table, "Planets")
        chart_sub.addTab(self.house_widget, "Houses & Chalit")
        chart_sub.addTab(self.varga_widget, "Varga Charts")
        chart_sub.addTab(self._build_yoga_tab(), "Yogas")
        self.tabs.addTab(chart_sub, "Chart & Varga")

        # 3. Strengths
        str_sub = QTabWidget()
        str_sub.addTab(self._build_shadbala_tab(), "Shadbala")
        str_sub.addTab(self._build_arudha_tab(), "Arudha & Karaka")
        str_sub.addTab(self._build_ashtakavarga_tab(), "Ashtakavarga")
        self.tabs.addTab(str_sub, "Strengths")

        # 4. Dasas
        dasa_sub = QTabWidget()
        dasa_sub.addTab(self.dasa_widget, "Dasa Periods")
        self.tabs.addTab(dasa_sub, "Dasas")

        # 5. Transits & Tajaka
        trans_sub = QTabWidget()
        trans_sub.addTab(self._build_transit_tab(), "Transits")
        trans_sub.addTab(self._build_tajaka_tab(), "Tajaka & TP")
        trans_sub.addTab(self._build_mundane_tab(), "Mundane")
        self.tabs.addTab(trans_sub, "Transits & Tajaka")

        # 6. Special Topics
        spec_sub = QTabWidget()
        spec_sub.addTab(self._build_kuta_tab(), "Matchmaking")
        spec_sub.addTab(self._build_prasna_tab(), "Prasna")
        spec_sub.addTab(self._build_muhurta_tab(), "Muhurta")
        self.tabs.addTab(spec_sub, "Special")

        # 7. AI & Knowledge
        ai_sub = QTabWidget()
        ai_sub.addTab(self._build_ai_chat_tab(), "AI Chat")
        ai_sub.addTab(self._build_ai_teacher_tab(), "AI Teacher")
        ai_sub.addTab(self._build_knowledge_tab(), "Knowledge")
        ai_sub.addTab(self._build_interpreter_tab(), "Reading")
        self.tabs.addTab(ai_sub, "AI & Learn")

        # 8. Tools
        tool_sub = QTabWidget()
        tool_sub.addTab(self._build_ephemeris_tab(), "Ephemeris")
        self.tabs.addTab(tool_sub, "Tools")

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

        open_act = QAction("&Import .jhd...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._on_file_open)
        file_menu.addAction(open_act)

        save_act = QAction("&Save to Database", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self._on_file_save)
        file_menu.addAction(save_act)

        export_act = QAction("&Export .jhd...", self)
        export_act.setShortcut("Ctrl+Shift+S")
        export_act.triggered.connect(self._on_file_export)
        file_menu.addAction(export_act)

        file_menu.addSeparator()

        browse_act = QAction("&Browse Charts...", self)
        browse_act.setShortcut("Ctrl+B")
        browse_act.triggered.connect(self._on_chart_browse)
        file_menu.addAction(browse_act)

        file_menu.addSeparator()

        export_report_act = QAction("&Export Report (HTML)...", self)
        export_report_act.triggered.connect(self._on_export_report)
        file_menu.addAction(export_report_act)

        file_menu.addSeparator()

        exit_act = QAction("E&xit", self)
        exit_act.setShortcut("Ctrl+Q")
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

    def _on_file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import JHora Chart", "", "JHora Data (*.jhd);;All Files (*)"
        )
        if not path:
            return
        try:
            data = parse_jhd(path)
            self._fill_form_from_jhd(data, path)
        except Exception as e:
            QMessageBox.warning(self, "Open Error", f"Could not open file:\n{e}")

    def _fill_form_from_jhd(self, data: JhdData, filepath: str = ""):
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
        self.current_file = filepath
        self.setWindowTitle(f"Jagannatha Hora — {data.name}")
        if filepath:
            self.statusBar().showMessage(f"Opened: {filepath}")

    def _on_file_save(self):
        """Save chart to database."""
        try:
            qd = self.date_input.date()
            qt = self.time_input.time()
            tz_str = self.tz_input.text().strip()
            lat = float(self.lat_input.text().strip())
            lon = float(self.lon_input.text().strip())
            city = self.city_input.text().strip()
            hour = qt.hour() + qt.minute() / 60.0 + qt.second() / 3600.0
            tz_offset = ChartBuilder._parse_tz(tz_str)
            name = f"{city or 'Unknown'} {qd.day():02d}/{qd.month():02d}/{qd.year()}"
            chart_id = save_chart_to_db(
                name=name, day=qd.day(), month=qd.month(), year=qd.year(),
                time_hours=hour, tz_offset=tz_offset,
                latitude=lat, longitude=-lon,
                city=city,
            )
            self.setWindowTitle(f"Jagannatha Hora — {name}")
            self.statusBar().showMessage(f"Saved to database (ID: {chart_id})")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save:\n{e}")

    def _on_export_report(self):
        if not self.chart_data:
            QMessageBox.warning(self, "Export", "Compute a chart first using the main form.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Chart Report", "chart_report.html",
            "HTML Files (*.html);;All Files (*)",
        )
        if not path:
            return
        try:
            from jhora.export.report import generate_chart_report
            generate_chart_report(self.chart_data, path)
            self.statusBar().showMessage(f"Report saved: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", str(e))

    def _on_file_export(self):
        """Export current chart data to .jhd file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Chart", "", "JHora Data (*.jhd);;All Files (*)"
        )
        if not path:
            return
        if not path.endswith(".jhd"):
            path += ".jhd"
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
                time_hours=hour, tz_offset=tz_offset,
                longitude=-lon, latitude=lat,
                city=city, country="",
            )
            save_jhd(path, data)
            self.statusBar().showMessage(f"Exported: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Could not export:\n{e}")

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

    def _init_atlas(self) -> Optional[AtlasReader | StaticAtlasReader]:
        if self._atlas is not None:
            return self._atlas
        try:
            self._atlas = open_default_atlas()
            if isinstance(self._atlas, StaticAtlasReader):
                self.statusBar().showMessage(
                    "City atlas not found; using sample data fallback."
                )
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
            self.statusBar().showMessage("Enter at least 2 letters to search for a city.")
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
            self.statusBar().showMessage(f"Found {len(results)} city match(es) for '{text}'.")
        else:
            self.city_results.setHidden(True)
            self.statusBar().showMessage(f"No city matches found for '{text}'.")

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
            self._populate_tithi_pravesha(self.chart_data)
            self._populate_progressions(self.chart_data)
            self.dasa_timeline.set_chart(self.chart_data)
            self._populate_consolidated(self.chart_data)
            self._update_cons_navamsa(self.chart_data)
            self._populate_dashboard(self.chart_data)

            if self.navamsa_toggle.isChecked():
                self._on_navamsa_toggle(True)

            self._on_varga_show()
            self.statusBar().showMessage("Done")
        except Exception as e:
            import traceback
            detail = traceback.format_exc()
            QMessageBox.warning(self, "Error", f"Calculation failed:\n{e}\n\nLocation:\n{detail[-300:]}")
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

        # Chalit / Bhava table
        from jhora.calc.chalit import ChalitComputer
        cc = ChalitComputer(self.chart_data)
        chalit = cc.compute()
        ch_headers = ["Planet", "Sign", "Sign H", "Cusp H", "Shift"]
        self.chalit_table.setColumnCount(len(ch_headers))
        self.chalit_table.setHorizontalHeaderLabels(ch_headers)
        self.chalit_table.setRowCount(len(chalit.entries))
        for i, e in enumerate(chalit.entries):
            for j, val in enumerate([e.graha.full_name, e.sign,
                                     str(e.sign_house), str(e.cusp_house),
                                     "← MOVED" if e.moved else ""]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if e.moved:
                    item.setForeground(QColor("#ff6666"))
                self.chalit_table.setItem(i, j, item)
        self.chalit_table.resizeColumnsToContents()
        moved = len(chalit.moved_planets)
        self.chalit_label.setText(
            f"Chalit (Bhava) — {moved} planet(s) shifted houses vs whole-sign")

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

        lbl_gr = QLabel("Shadbala — Planetary Strengths (rupa / virupa)")
        lbl_gr.setStyleSheet("font-weight: bold; color: #e0b050;")
        layout.addWidget(lbl_gr)

        self.shadbala_table = QTableWidget()
        headers = ["Planet", "Sthana (R)", "Dig (R)", "Kala (R)", "Chesta (R)",
                   "Naisargika (R)", "Drik (R)", "Total (R)", "Total (V)", "Rel Str"]
        self.shadbala_table.setColumnCount(len(headers))
        self.shadbala_table.setHorizontalHeaderLabels(headers)
        self.shadbala_table.horizontalHeader().setStretchLastSection(True)
        self.shadbala_table.setAlternatingRowColors(True)
        layout.addWidget(self.shadbala_table)

        lbl_bh = QLabel("Bhava Bala — House Strengths (virupas)")
        lbl_bh.setStyleSheet("font-weight: bold; color: #e0b050; margin-top: 8px;")
        layout.addWidget(lbl_bh)

        self.bhava_bala_table = QTableWidget()
        bh_headers = ["House", "Sign", "Lord", "Sthana", "Drishti", "Dig",
                      "Adhipati", "Drig", "Total"]
        self.bhava_bala_table.setColumnCount(len(bh_headers))
        self.bhava_bala_table.setHorizontalHeaderLabels(bh_headers)
        self.bhava_bala_table.horizontalHeader().setStretchLastSection(True)
        self.bhava_bala_table.setAlternatingRowColors(True)
        layout.addWidget(self.bhava_bala_table)

        lbl_vi = QLabel("Vimsopaka Bala — Varga-weighted Strength (Shadvarga)")
        lbl_vi.setStyleSheet("font-weight: bold; color: #e0b050; margin-top: 8px;")
        layout.addWidget(lbl_vi)

        self.vimsopaka_table = QTableWidget()
        vi_headers = ["Planet", "Total (/20)", "%", "D1", "D2", "D3", "D7", "D9"]
        self.vimsopaka_table.setColumnCount(len(vi_headers))
        self.vimsopaka_table.setHorizontalHeaderLabels(vi_headers)
        self.vimsopaka_table.horizontalHeader().setStretchLastSection(True)
        self.vimsopaka_table.setAlternatingRowColors(True)
        layout.addWidget(self.vimsopaka_table)
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

        # Bhava Bala
        from jhora.calc.bhava_bala import BhavaBalaComputer
        from jhora.types.rasi import Rasi
        bb = BhavaBalaComputer(cd)
        report = bb.compute_all()
        self.bhava_bala_table.setRowCount(12)
        for h in range(1, 13):
            r = report.results[h]
            rasi_idx = (int(cd.ascendant / 30) + h - 1) % 12
            lord_str = Rasi(rasi_idx).lord
            row = [str(h), Rasi(rasi_idx).short_name, lord_str,
                   f"{r.sthana:.1f}", f"{r.drishti:.1f}", f"{r.dig:.1f}",
                   f"{r.adhipati:.1f}", f"{r.drig:+.1f}", f"{r.total:.1f}"]
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.bhava_bala_table.setItem(h - 1, c, item)
        self.bhava_bala_table.resizeColumnsToContents()

        # Vimsopaka Bala
        from jhora.calc.vimsopaka import VimsopakaComputer, VimsopakaScheme
        vc = VimsopakaComputer(cd)
        import_r = sorted(vc.compute_all(VimsopakaScheme.SHADVARGA), key=lambda r: r.total, reverse=True)
        self.vimsopaka_table.setRowCount(len(import_r))
        varga_order = [VimsopakaScheme.SHADVARGA]
        for i, r in enumerate(import_r):
            row = [r.graha.full_name, f"{r.total:.1f}/20", f"{r.percentage:.0f}%"]
            for c in r.components:
                row.append(f"{c.score:.1f}")
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.vimsopaka_table.setItem(i, j, item)
        self.vimsopaka_table.resizeColumnsToContents()

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

        is_day = 6.0 <= cd.birth_date.hour < 18.0
        sahamas = compute_sahamas(cd.ascendant, planets, day=is_day)
        headers = ["Sahama", "Meaning", "Longitude", "Sign", "House"]
        rows = []
        for sah in sahamas:
            sign = Rasi(int(sah.longitude / 30))
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

        # Tithi Pravesha section
        self.tp_label = QLabel("Tithi Pravesha — Annual Tithi-Solar Return")
        self.tp_label.setStyleSheet(f"color: {ACCENT}; font-weight: bold; margin-top: 8px;")
        layout.addWidget(self.tp_label)

        self.tp_table = QTableWidget()
        self.tp_table.setAlternatingRowColors(True)
        self.tp_table.setMaximumHeight(100)
        layout.addWidget(self.tp_table)

        # Progressions section
        self.prog_label = QLabel("Secondary Progressions (1 day = 1 year)")
        self.prog_label.setStyleSheet(f"color: {ACCENT}; font-weight: bold; margin-top: 8px;")
        layout.addWidget(self.prog_label)

        self.prog_table = QTableWidget()
        self.prog_table.setAlternatingRowColors(True)
        self.prog_table.setMaximumHeight(200)
        layout.addWidget(self.prog_table)

        return w

    def _populate_tithi_pravesha(self, cd: ChartData):
        from jhora.calc.tithi_pravesha import TithiPraveshaCalculator
        from jhora.types.rasi import Rasi
        tp = TithiPraveshaCalculator(cd)
        now_year = datetime.now().year
        entries = tp.compute_range(now_year - 1, now_year + 1)

        headers = ["Year", "Date (UT)", "Lagna", "Sun", "Moon", "Tithi Angle"]
        self.tp_table.setColumnCount(len(headers))
        self.tp_table.setHorizontalHeaderLabels(headers)
        self.tp_table.setRowCount(len(entries))
        self.tp_table.horizontalHeader().setStretchLastSection(True)
        for i, e in enumerate(entries):
            if e.chart is None:
                continue
            lagna = Rasi.from_longitude(e.chart.ascendant).short_name
            sun_r = Rasi.from_longitude(e.chart.planet(Graha.SUN).longitude).short_name
            moon_r = Rasi.from_longitude(e.chart.planet(Graha.MOON).longitude).short_name
            m = e.chart.planet(Graha.MOON).longitude
            s = e.chart.planet(Graha.SUN).longitude
            a = (m - s) % 360
            row = [str(e.year), e.event_date, lagna, sun_r, moon_r, f"{a:.2f}°"]
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tp_table.setItem(i, j, item)
        self.tp_table.resizeColumnsToContents()

    def _populate_progressions(self, cd: ChartData):
        from jhora.calc.progressions import ProgressionCalculator
        from jhora.types.rasi import Rasi
        pc = ProgressionCalculator(cd)
        age = (datetime.now() - cd.birth_date).total_seconds() / (365.25 * 86400)
        sec = pc.secondary(target_age=age)

        headers = ["Planet", "Natal Sign", "Progressed Sign", "Change"]
        self.prog_table.setColumnCount(len(headers))
        self.prog_table.setHorizontalHeaderLabels(headers)
        self.prog_table.setRowCount(9)
        self.prog_table.horizontalHeader().setStretchLastSection(True)
        for i, g in enumerate([Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                               Graha.JUPITER, Graha.VENUS, Graha.SATURN,
                               Graha.RAHU, Graha.KETU]):
            np = cd.planet(g)
            nr = Rasi.from_longitude(np.longitude).short_name
            if sec.chart:
                pp = sec.chart.planet(g)
                pr = Rasi.from_longitude(pp.longitude).short_name
                moved = "✓" if nr != pr else ""
            else:
                pr, moved = "?", ""
            for j, val in enumerate([g.full_name, f"{nr} {np.longitude:.1f}°",
                                     f"{pr} {pp.longitude:.1f}°" if sec.chart else "",
                                     moved]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.prog_table.setItem(i, j, item)
        self.prog_table.resizeColumnsToContents()

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

    # --- AI Chat ---

    def _build_ai_chat_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Provider config row
        cfg = QHBoxLayout()
        cfg.addWidget(QLabel("Provider:"))
        self.ai_provider = QComboBox()
        self.ai_provider.addItems(list(PROVIDERS.keys()))
        self.ai_provider.setCurrentText("ollama")
        self.ai_provider.currentTextChanged.connect(self._on_ai_provider_changed)
        cfg.addWidget(self.ai_provider)

        cfg.addWidget(QLabel("Model:"))
        self.ai_model = QLineEdit("llama3.2")
        self.ai_model.setFixedWidth(140)
        cfg.addWidget(self.ai_model)

        self.ai_check_btn = QPushButton("Check")
        self.ai_check_btn.setFixedWidth(60)
        self.ai_check_btn.clicked.connect(self._on_ai_health_check)
        cfg.addWidget(self.ai_check_btn)

        self.ai_status = QLabel("")
        self.ai_status.setStyleSheet("color: #888888;")
        cfg.addWidget(self.ai_status)
        cfg.addStretch()
        layout.addLayout(cfg)

        # Action buttons
        btn_row = QHBoxLayout()
        self.ai_interpret_btn = QPushButton("Interpret Chart")
        self.ai_interpret_btn.clicked.connect(lambda: self._on_ai_action("interpret"))
        btn_row.addWidget(self.ai_interpret_btn)

        self.ai_remedy_btn = QPushButton("Suggest Remedies")
        self.ai_remedy_btn.clicked.connect(lambda: self._on_ai_action("remedies"))
        btn_row.addWidget(self.ai_remedy_btn)

        self.ai_style = QComboBox()
        self.ai_style.addItems(["concise", "detailed", "professional"])
        self.ai_style.setCurrentText("detailed")
        self.ai_style.setFixedWidth(120)
        btn_row.addWidget(QLabel("Style:"))
        btn_row.addWidget(self.ai_style)

        self.ai_topic = QComboBox()
        self.ai_topic.addItems(["general", "relationship", "career", "health",
                                "spirituality", "children", "finance"])
        self.ai_topic.setCurrentText("general")
        btn_row.addWidget(QLabel("Topic:"))
        btn_row.addWidget(self.ai_topic)

        self.ai_ask_input = QLineEdit()
        self.ai_ask_input.setPlaceholderText("Or ask a specific question...")
        self.ai_ask_input.returnPressed.connect(self._on_ai_ask)
        btn_row.addWidget(self.ai_ask_input)

        self.ai_ask_btn = QPushButton("Ask")
        self.ai_ask_btn.clicked.connect(self._on_ai_ask)
        btn_row.addWidget(self.ai_ask_btn)
        layout.addLayout(btn_row)

        # Output area
        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.setStyleSheet(
            "QTextEdit { background-color: #0d1b2a; color: #e0e0e0; "
            "font-family: 'Segoe UI', sans-serif; font-size: 13px; "
            "border: 1px solid #2a3f5f; border-radius: 4px; padding: 8px; }"
        )
        layout.addWidget(self.ai_output)

        self._ai_worker: Optional[_AiWorker] = None
        self._ai_engine: Optional[AiEngine] = None
        return w

    def _get_ai_engine(self) -> AiEngine:
        config = AiConfig(
            provider=self.ai_provider.currentText(),
            model=self.ai_model.text().strip(),
            base_url=PROVIDERS.get(self.ai_provider.currentText(), {}).get("base_url", ""),
        )
        return AiEngine(config)

    def _on_ai_provider_changed(self, provider: str):
        preset = PROVIDERS.get(provider, {})
        self.ai_model.setText(preset.get("default_model", ""))

    def _on_ai_health_check(self):
        self.ai_check_btn.setEnabled(False)
        self.ai_status.setText("Checking...")
        engine = self._get_ai_engine()
        result = engine.health_check()
        if result["ok"]:
            self.ai_status.setText(f"OK — {len(result['models'])} models")
        else:
            self.ai_status.setText(f"Error: {result['error'][:60]}")
        self.ai_check_btn.setEnabled(True)

    def _on_ai_action(self, mode: str):
        cd = self.chart_data
        if cd is None:
            self.ai_output.setText("[Compute a chart first using the main form]")
            return
        style = self.ai_style.currentText()
        topic = self.ai_topic.currentText()
        self.ai_output.clear()
        self.ai_output.append(f"[Generating {mode} with {self.ai_provider.currentText()}/{self.ai_model.text()}...]\n")
        self._set_ai_buttons_enabled(False)

        engine = self._get_ai_engine()
        if mode == "interpret":
            self._ai_worker = _AiWorker(engine, "interpret", cd, style=style, topic=topic)
        elif mode == "remedies":
            self._ai_worker = _AiWorker(engine, "remedies", cd)

        self._ai_worker.token.connect(self._on_ai_token)
        self._ai_worker.done.connect(self._on_ai_done)
        self._ai_worker.error.connect(self._on_ai_error)
        self._ai_worker.start()

    def _on_ai_ask(self):
        q = self.ai_ask_input.text().strip()
        if not q:
            return
        cd = self.chart_data
        if cd is None:
            self.ai_output.setText("[Compute a chart first using the main form]")
            return
        self.ai_output.clear()
        self.ai_output.append(f"[Asking: {q}]\n")
        self._set_ai_buttons_enabled(False)

        engine = self._get_ai_engine()
        self._ai_worker = _AiWorker(engine, "ask", cd, question=q)
        self._ai_worker.token.connect(self._on_ai_token)
        self._ai_worker.done.connect(self._on_ai_done)
        self._ai_worker.error.connect(self._on_ai_error)
        self._ai_worker.start()

    def _on_ai_token(self, text: str):
        cursor = self.ai_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.ai_output.ensureCursorVisible()

    def _on_ai_done(self):
        self.ai_output.append("\n\n[done]")
        self._set_ai_buttons_enabled(True)

    def _on_ai_error(self, msg: str):
        self.ai_output.append(f"\n\n[Error: {msg}]")
        self._set_ai_buttons_enabled(True)

    def _set_ai_buttons_enabled(self, enabled: bool):
        for btn in [self.ai_interpret_btn, self.ai_remedy_btn, self.ai_ask_btn]:
            btn.setEnabled(enabled)

    # --- AI Teacher Tab ---

    def _build_ai_teacher_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        cfg = QHBoxLayout()
        cfg.addWidget(QLabel("Provider:"))
        self.teach_provider = QComboBox()
        self.teach_provider.addItems(["ollama", "lmstudio", "unsloth", "custom"])
        cfg.addWidget(self.teach_provider)
        cfg.addWidget(QLabel("Model:"))
        self.teach_model = QLineEdit("llama3.2")
        self.teach_model.setFixedWidth(140)
        cfg.addWidget(self.teach_model)
        cfg.addStretch()
        layout.addLayout(cfg)

        self.teach_input = QLineEdit()
        self.teach_input.setPlaceholderText("Ask the Guru — learn Vedic astrology step by step...")
        self.teach_input.returnPressed.connect(self._on_teach_ask)
        layout.addWidget(self.teach_input)

        btn_row = QHBoxLayout()
        self.teach_btn = QPushButton("Ask Guru")
        self.teach_btn.clicked.connect(self._on_teach_ask)
        btn_row.addWidget(self.teach_btn)
        self.teach_topic = QComboBox()
        self.teach_topic.addItems([
            "Ask anything...", "Explain my lagna", "What is the 7th house?",
            "How do I read dasa periods?", "What are yogas?",
            "How does transit work?", "What is Shadbala?",
            "Explain Vimsopaka Bala", "How to predict career?",
            "How to predict relationships?", "What is Tithi Pravesha?",
            "How to use the Chalit chart?", "What is mundane astrology?",
        ])
        self.teach_topic.currentTextChanged.connect(self._on_teach_topic)
        btn_row.addWidget(self.teach_topic)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.teach_output = QTextEdit()
        self.teach_output.setReadOnly(True)
        self.teach_output.setStyleSheet(
            "QTextEdit { background-color: #0d1b2a; color: #e0e0e0; "
            "font-family: 'Segoe UI', sans-serif; font-size: 13px; "
            "border: 1px solid #2a3f5f; border-radius: 4px; padding: 8px; }"
        )
        layout.addWidget(self.teach_output)

        self._build_teacher_btn = QPushButton("Build Textbook Index")
        self._build_teacher_btn.clicked.connect(self._on_build_teacher_index)
        self._build_teacher_btn.setToolTip(
            "Chunk all textbooks and generate embedding vectors (requires Ollama + nomic-embed-text)"
        )
        layout.addWidget(self._build_teacher_btn)
        return w

    def _on_build_teacher_index(self):
        from jhora.ai.embeddings import EmbeddingStore
        self.teach_output.append("[Building textbook index...]\n")
        self._build_teacher_btn.setEnabled(False)
        try:
            store = EmbeddingStore()
            count = store.build()
            self.teach_output.append(f"[✓ Index built: {count} chunks]\n")
        except Exception as e:
            self.teach_output.append(f"[✗ Error: {e}]\n")
        self._build_teacher_btn.setEnabled(True)

    def _on_teach_topic(self, text: str):
        if text != "Ask anything...":
            self.teach_input.setText(text)

    def _on_teach_ask(self):
        question = self.teach_input.text().strip()
        if not question:
            return
        self.teach_output.clear()
        self.teach_output.append(f"[Guru, {question}]\n")
        self.teach_btn.setEnabled(False)

        provider = self.teach_provider.currentText()
        model = self.teach_model.text().strip()
        base_url = {"ollama": "http://localhost:11434/v1",
                     "lmstudio": "http://localhost:1234/v1",
                     "unsloth": "http://localhost:8000/v1"}.get(provider,
                                                               "http://localhost:11434/v1")
        chart = self.chart_data if hasattr(self, "chart_data") else None

        self._teacher_worker = _TeacherWorker(question, chart, provider, base_url, model)
        self._teacher_worker.token.connect(self._on_teach_token)
        self._teacher_worker.done.connect(lambda: self.teach_btn.setEnabled(True))
        self._teacher_worker.start()

    def _on_teach_token(self, text: str):
        cursor = self.teach_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.teach_output.ensureCursorVisible()

    # --- Chart Browser ---

    def _on_chart_browse(self):
        charts = list_charts()
        if not charts:
            QMessageBox.information(self, "Browse Charts", "No saved charts found.\n\nUse File → Save to Database to save charts.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Browse Saved Charts")
        dialog.resize(700, 400)
        dialog.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout(dialog)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Name", "Date", "City", "Country", "ID"])
        table.setRowCount(len(charts))
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        for i, ch in enumerate(charts):
            dt = f"{ch.get('day','')}/{ch.get('month','')}/{ch.get('year','')}"
            for j, val in enumerate([ch.get("name", ""), dt,
                                     ch.get("city", ""), ch.get("country", ""),
                                     str(ch.get("id", ""))]):
                table.setItem(i, j, QTableWidgetItem(str(val)))
        layout.addWidget(table)

        btn_row = QHBoxLayout()
        load_btn = QPushButton("Load")
        delete_btn = QPushButton("Delete")
        close_btn = QPushButton("Close")
        btn_row.addWidget(load_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        def _load():
            row = table.currentRow()
            if row < 0:
                return
            chart_id = int(table.item(row, 4).text())
            data = load_chart_from_db(chart_id)
            if data:
                self.date_input.setDate(QDate(data["year"], data["month"], data["day"]))
                th = data["time_hours"]
                self.time_input.setTime(QTime(int(th), int((th % 1) * 60), 0))
                tz_sign = "+" if data["tz_offset"] >= 0 else "-"
                self.tz_input.setText(f"{tz_sign}{abs(data['tz_offset']):.1f}")
                self.lat_input.setText(f"{data['latitude']:.4f}")
                self.lon_input.setText(f"{-data['longitude']:.4f}")
                if data.get("city"):
                    self.city_input.setText(data["city"])
                self.setWindowTitle(f"Jagannatha Hora — {data['name']}")
                dialog.accept()

        def _delete():
            row = table.currentRow()
            if row < 0:
                return
            chart_id = int(table.item(row, 4).text())
            name = table.item(row, 0).text()
            reply = QMessageBox.question(dialog, "Delete Chart",
                                        f"Delete '{name}'?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                delete_chart(chart_id)
                table.removeRow(row)

        load_btn.clicked.connect(_load)
        delete_btn.clicked.connect(_delete)
        close_btn.clicked.connect(dialog.reject)
        table.doubleClicked.connect(lambda *_: _load())
        dialog.exec()

    # --- Mundane Tab ---

    def _build_mundane_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Year:"))
        self.mun_year = QLineEdit(str(datetime.now().year))
        self.mun_year.setFixedWidth(60)
        ctrl.addWidget(self.mun_year)
        ctrl.addWidget(QLabel("Lat:"))
        self.mun_lat = QLineEdit("28.61")
        self.mun_lat.setFixedWidth(70)
        ctrl.addWidget(self.mun_lat)
        ctrl.addWidget(QLabel("Lon:"))
        self.mun_lon = QLineEdit("77.21")
        self.mun_lon.setFixedWidth(70)
        ctrl.addWidget(QLabel("TZ:"))
        self.mun_tz = QLineEdit("+0530")
        self.mun_tz.setFixedWidth(60)

        self.mun_compute_btn = QPushButton("Compute")
        self.mun_compute_btn.clicked.connect(self._on_mundane_compute)
        ctrl.addWidget(self.mun_compute_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Ingress table
        self.mun_ingress_label = QLabel("")
        self.mun_ingress_label.setStyleSheet("font-weight: bold; color: #e0b050;")
        layout.addWidget(self.mun_ingress_label)

        self.mun_ingress_table = QTableWidget()
        self.mun_ingress_table.setColumnCount(4)
        self.mun_ingress_table.setHorizontalHeaderLabels(["Sign", "Date/Time (UT)", "Lagna", "Planets"])
        self.mun_ingress_table.horizontalHeader().setStretchLastSection(True)
        self.mun_ingress_table.setAlternatingRowColors(True)
        layout.addWidget(self.mun_ingress_table)

        # Eclipses
        self.mun_eclipse_label = QLabel("")
        self.mun_eclipse_label.setStyleSheet("font-weight: bold; color: #e0b050; margin-top: 8px;")
        layout.addWidget(self.mun_eclipse_label)
        self.mun_eclipse_table = QTableWidget()
        self.mun_eclipse_table.setColumnCount(2)
        self.mun_eclipse_table.setHorizontalHeaderLabels(["Event", "Date/Time (UT)"])
        self.mun_eclipse_table.horizontalHeader().setStretchLastSection(True)
        self.mun_eclipse_table.setAlternatingRowColors(True)
        layout.addWidget(self.mun_eclipse_table)

        return w

    def _on_mundane_compute(self):
        from jhora.calc.mundane import MundaneCalculator
        from jhora.types.rasi import Rasi
        from jhora.types.graha import Graha

        try:
            year = int(self.mun_year.text())
            lat = float(self.mun_lat.text())
            lon = float(self.mun_lon.text())
            tz = self.mun_tz.text()
        except ValueError:
            return

        mc = MundaneCalculator(lat=lat, lon=lon, tz=tz)

        # Ingress table
        self.mun_ingress_label.setText(f"Solar Ingresses {year}")
        ingresses = mc.solar_ingresses(year)
        self.mun_ingress_table.setRowCount(len(ingresses))
        for i, e in enumerate(ingresses):
            row = [e.sign, e.datetime_utc, "", ""]
            if e.chart is None:
                e.chart = mc._chart(e.julian_day)
            ch = e.chart
            if ch:
                lagna = Rasi.from_longitude(ch.ascendant).short_name
                planets = ", ".join(
                    f"{Rasi.from_longitude(ch.planet(g).longitude).short_name}"
                    for g in [Graha.SUN, Graha.MOON, Graha.MARS]
                )
                row[2] = lagna
                row[3] = planets
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mun_ingress_table.setItem(i, j, item)
        self.mun_ingress_table.resizeColumnsToContents()

        # Eclipse table
        eclipses = mc.eclipses()
        self.mun_eclipse_label.setText(f"Upcoming Eclipses ({len(eclipses)})")
        self.mun_eclipse_table.setRowCount(len(eclipses))
        for i, e in enumerate(eclipses):
            for j, val in enumerate([e.name, e.datetime_utc]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mun_eclipse_table.setItem(i, j, item)
        self.mun_eclipse_table.resizeColumnsToContents()

    # --- Ephemeris Tab ---

    def _build_ephemeris_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Start:"))
        self.eph_start = QDateEdit(QDate.currentDate().addDays(-15))
        self.eph_start.setCalendarPopup(True)
        ctrl.addWidget(self.eph_start)
        ctrl.addWidget(QLabel("End:"))
        self.eph_end = QDateEdit(QDate.currentDate().addDays(15))
        self.eph_end.setCalendarPopup(True)
        ctrl.addWidget(self.eph_end)
        ctrl.addWidget(QLabel("Step:"))
        self.eph_step = QComboBox()
        self.eph_step.addItems(["1", "7", "14", "30"])
        self.eph_step.setCurrentText("7")
        ctrl.addWidget(self.eph_step)

        self.eph_go = QPushButton("Generate")
        self.eph_go.clicked.connect(self._on_ephemeris_generate)
        ctrl.addWidget(self.eph_go)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.eph_table = QTableWidget()
        self.eph_table.setAlternatingRowColors(True)
        layout.addWidget(self.eph_table)
        return w

    def _on_ephemeris_generate(self):
        from jhora.calc.ephemeris import generate_ephemeris
        from jhora.types.graha import Graha
        start = self.eph_start.date().toPyDate()
        end = self.eph_end.date().toPyDate()
        step = int(self.eph_step.currentText())
        entries = generate_ephemeris(
            datetime(start.year, start.month, start.day),
            datetime(end.year, end.month, end.day), step,
        )

        grahas = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                  Graha.JUPITER, Graha.VENUS, Graha.SATURN,
                  Graha.RAHU, Graha.KETU]
        headers = ["Date"] + [g.short_name for g in grahas]
        self.eph_table.setColumnCount(len(headers))
        self.eph_table.setHorizontalHeaderLabels(headers)
        self.eph_table.setRowCount(len(entries))
        for i, e in enumerate(entries):
            self.eph_table.setItem(i, 0, QTableWidgetItem(e.date.strftime("%Y-%m-%d")))
            for j, g in enumerate(grahas):
                p = e.planets.get(g, {})
                item = QTableWidgetItem(f"{p.get('sign', '?')} {p.get('longitude', 0):.0f}°")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if p.get("retrograde"):
                    item.setForeground(QColor("#ff6666"))
                self.eph_table.setItem(i, j + 1, item)
        self.eph_table.resizeColumnsToContents()

    # --- Smart Dashboard — everything at a glance ---

    def _build_dashboard_tab(self):
        w = QWidget()
        grid = QHBoxLayout(w)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(8)

        # Left column: Now + Strengths
        left = QVBoxLayout()
        left.setSpacing(6)

        self.dash_now = QTextEdit()
        self.dash_now.setReadOnly(True)
        self.dash_now.setMaximumHeight(220)
        self.dash_now.setStyleSheet("QTextEdit{background:#0d1b2a;color:#e0e0e0;font-size:12px;border:1px solid #2a3f5f;border-radius:4px;padding:8px;}")
        left.addWidget(QLabel("RIGHT NOW"))
        left.addWidget(self.dash_now)

        self.dash_strengths = QTextEdit()
        self.dash_strengths.setReadOnly(True)
        self.dash_strengths.setStyleSheet("QTextEdit{background:#0d1b2a;color:#e0e0e0;font-size:12px;border:1px solid #2a3f5f;border-radius:4px;padding:8px;}")
        left.addWidget(QLabel("STRENGTHS"))
        left.addWidget(self.dash_strengths)

        grid.addLayout(left, stretch=2)

        # Right column: Upcoming + Key Dates
        right = QVBoxLayout()
        right.setSpacing(6)

        self.dash_upcoming = QTextEdit()
        self.dash_upcoming.setReadOnly(True)
        self.dash_upcoming.setMaximumHeight(220)
        self.dash_upcoming.setStyleSheet("QTextEdit{background:#0d1b2a;color:#e0e0e0;font-size:12px;border:1px solid #2a3f5f;border-radius:4px;padding:8px;}")
        right.addWidget(QLabel("UPCOMING"))
        right.addWidget(self.dash_upcoming)

        self.dash_keydates = QTextEdit()
        self.dash_keydates.setReadOnly(True)
        self.dash_keydates.setStyleSheet("QTextEdit{background:#0d1b2a;color:#e0e0e0;font-size:12px;border:1px solid #2a3f5f;border-radius:4px;padding:8px;}")
        right.addWidget(QLabel("KEY DATES"))
        right.addWidget(self.dash_keydates)

        grid.addLayout(right, stretch=2)
        return w

    def _populate_dashboard(self, cd: ChartData):
        from jhora.dasas.vimsottari import VimsottariDasa
        from jhora.calc.shadbala import ShadbalaComputer
        from jhora.calc.bhava_bala import BhavaBalaComputer
        from jhora.calc.gochara import compute_transits
        from jhora.ephemeris.swe import SweEngine
        from jhora.types.nakshatra import Nakshatra
        from datetime import datetime, timedelta

        now = datetime.now()
        # ── RIGHT NOW ──
        moon = cd.planet(Graha.MOON).longitude
        sun = cd.planet(Graha.SUN).longitude
        tithi_angle = (moon - sun) % 360
        tithi_idx = int(tithi_angle / 12)
        nak, pada = Nakshatra.from_longitude(moon)
        rahu_block = [7,1,5,2,3,4,6][now.weekday()]
        rahu_start = 6 + rahu_block * 1.5
        rahu_end = rahu_start + 1.5

        # Dasa
        try:
            dasa = VimsottariDasa()
            cd_dict = {"planets": {g.value: {"longitude": p.longitude}
                                   for g, p in cd.planets.items()},
                      "lagna_lon": cd.ascendant}
            periods = dasa.compute(cd.julian_day, cd_dict)
            current_md = next((p for p in periods if p.start_date <= now <= p.end_date), None)
            current_ad = None
            if current_md:
                for ad in (current_md.sub_periods or []):
                    if ad.start_date <= now <= ad.end_date:
                        current_ad = ad
                        break
        except Exception:
            current_md = current_ad = None

        now_lines = [
            f"[bold yellow]Today: {now.strftime('%B %d, %Y')} | {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][now.weekday()]}[/bold yellow]",
            f"Tithi: {tithi_idx} | Nakshatra: {nak.name.replace('_',' ').title()} | Moon: {Rasi.from_longitude(moon).short_name}",
            f"Rahu Kalam: {int(rahu_start):02d}:{int((rahu_start%1)*60):02d} – {int(rahu_end):02d}:{int((rahu_end%1)*60):02d}",
            "",
        ]
        if current_md:
            time_left = current_md.end_date - now
            months_left = time_left.days / 30
            now_lines.append(f"[bold]Current Dasa: {current_md.lord_name} Mahadasha[/bold] — {months_left:.0f} months remaining")
            if current_ad:
                ad_left = current_ad.end_date - now
                now_lines.append(f"  └ {current_ad.lord_name} Antardasha — {ad_left.days} days remaining")
        self.dash_now.setText("\n".join(now_lines))

        # ── STRENGTHS ──
        try:
            sb = ShadbalaComputer(cd)
            gr = [(g.full_name, sb.compute_one(g).total_virupa) for g in
                  [Graha.SUN,Graha.MOON,Graha.MARS,Graha.MERCURY,
                   Graha.JUPITER,Graha.VENUS,Graha.SATURN]]
            gr.sort(key=lambda x:x[1], reverse=True)
            bb = BhavaBalaComputer(cd)
            bb_r = bb.compute_all()
            bh = [(h, bb_r.results[h].total) for h in range(1,13)]
            bh.sort(key=lambda x:x[1], reverse=True)

            str_lines = ["[bold]Planet Strengths:[/bold]"]
            for name, val in gr:
                bar = "█" * int(val / 30) + "░" * (18 - int(val / 30))
                str_lines.append(f"  {name:<8} {bar} {val:.0f}")
            str_lines.append("")
            str_lines.append("[bold]House Strengths:[/bold]")
            for h, val in bh[:5]:
                ri = (int(cd.ascendant/30) + h - 1) % 12
                bar = "█" * int(val / 12) + "░" * (18 - int(val / 12))
                str_lines.append(f"  H{h} {Rasi(ri).short_name} {bar} {val:.0f}")
            self.dash_strengths.setText("\n".join(str_lines))
        except Exception:
            self.dash_strengths.setText("")

        # ── UPCOMING ──
        up_lines = []
        if current_md:
            up_lines.append("[bold]Upcoming Antardasas:[/bold]")
            upcoming = sorted([sp for sp in (current_md.sub_periods or [])
                              if sp.start_date > now], key=lambda x: x.start_date)
            for sp in upcoming[:4]:
                days_to = (sp.start_date - now).days
                up_lines.append(f"  {sp.lord_name}: {sp.start_date.strftime('%b %d, %Y')} ({days_to}d)")
            up_lines.append("")
            next_md = None
            for p in periods:
                if p.start_date > current_md.end_date:
                    next_md = p
                    break
            if next_md:
                up_lines.append(f"[bold]Next Mahadasha: {next_md.lord_name}[/bold] — {next_md.start_date.strftime('%b %Y')}")
        up_lines.append("")
        up_lines.append("[bold]Major Transits (next 6 months):[/bold]")
        try:
            eng = SweEngine()
            for m in range(1, 7):
                jd = eng.julday(now.year, now.month + m if now.month + m <= 12 else now.month + m - 12,
                              1 if now.month + m <= 12 else now.year + 1,
                              now.day, 12.0)
                try:
                    tr = compute_transits(cd, jd)
                    notable = []
                    for e in tr.entries:
                        if hasattr(e, 'is_favorable') and e.is_favorable and e.sav_score >= 30:
                            notable.append(e.graha.short_name)
                    if notable:
                        up_lines.append(f"  {now.year}-{((now.month+m-1)%12)+1:02d}: {', '.join(notable)} favorable")
                except Exception:
                    pass
        except Exception:
            pass
        self.dash_upcoming.setText("\n".join(up_lines) if up_lines else "Dasa data unavailable")

        # ── KEY DATES ──
        kd_lines = ["[bold]Sade Sati Check:[/bold]"]
        saturn = cd.planet(Graha.SATURN).longitude
        moon_rasi = int(cd.planet(Graha.MOON).longitude / 30)
        sat_rasi = int(saturn / 30)
        # Sade Sati: Saturn transiting 12th, 1st, 2nd from Moon
        ss_signs = [(moon_rasi - 1) % 12, moon_rasi, (moon_rasi + 1) % 12]
        if sat_rasi in ss_signs:
            pos = ["12th from Moon", "1st from Moon (peak)", "2nd from Moon"][ss_signs.index(sat_rasi)]
            kd_lines.append(f"  🟡 IN Sade Sati ({pos})")
        else:
            dist = min((sat_rasi - moon_rasi) % 12, (moon_rasi - sat_rasi) % 12)
            kd_lines.append(f"  Sade Sati in ~{dist * 2.5:.0f} years (Saturn at {dist} signs away)")

        kd_lines.append("")
        kd_lines.append("[bold]Retrograde Watch:[/bold]")
        for g in [Graha.MERCURY, Graha.VENUS, Graha.MARS, Graha.JUPITER, Graha.SATURN]:
            p = cd.planet(g)
            if p.is_retrograde:
                kd_lines.append(f"  {g.short_name} is currently RETROGRADE")
        kd_lines.append("")
        kd_lines.append("[bold]Auspicious Days (this month):[/bold]")
        kd_lines.append("  Every Monday, Thursday, Friday")
        kd_lines.append("  Ekadasi tithi days (check panchanga)")

        self.dash_keydates.setText("\n".join(kd_lines))

    # --- Consolidated View (JHora-style three-column layout) ---

    def _build_consolidated_tab(self):
        w = QWidget()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_consolidated_charts())
        splitter.addWidget(self._build_consolidated_center())
        splitter.addWidget(self._build_consolidated_ashtakavarga())
        splitter.setSizes([380, 420, 300])
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        return w

    def _build_consolidated_charts(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.cons_chart = ChartWidget()
        self.cons_chart.setMinimumSize(350, 350)
        layout.addWidget(self.cons_chart, stretch=1)

        self.cons_navamsa = ChartWidget()
        self.cons_navamsa.setMinimumSize(350, 350)
        layout.addWidget(self.cons_navamsa, stretch=1)
        return w

    def _build_consolidated_center(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Planet table — DMS format with all bodies
        self.cons_planet_table = QTableWidget()
        self.cons_planet_table.setAlternatingRowColors(True)
        self.cons_planet_table.setMinimumWidth(380)
        layout.addWidget(self.cons_planet_table, stretch=2)

        # Natal data panel
        self.cons_natal_panel = QTextEdit()
        self.cons_natal_panel.setReadOnly(True)
        self.cons_natal_panel.setMaximumHeight(300)
        self.cons_natal_panel.setStyleSheet(
            "QTextEdit { background-color: #0d1b2a; color: #e0e0e0; "
            "font-family: monospace; font-size: 12px; "
            "border: 1px solid #2a3f5f; border-radius: 4px; padding: 8px; }"
        )
        layout.addWidget(self.cons_natal_panel, stretch=1)
        return w

    def _build_consolidated_ashtakavarga(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.cons_sav_label = QLabel("SAV (Samudaya Ashtakavarga)")
        self.cons_sav_label.setStyleSheet("font-weight: bold; color: #e0b050;")
        layout.addWidget(self.cons_sav_label)

        self.cons_sav = QTableWidget()
        self.cons_sav.setMaximumHeight(180)
        layout.addWidget(self.cons_sav)

        # BAV grids — all 8 planets in a scrollable area
        bav_scroll = QScrollArea()
        bav_scroll.setWidgetResizable(True)
        bav_inner = QWidget()
        self.cons_bav_layout = QVBoxLayout(bav_inner)
        self.cons_bav_layout.setContentsMargins(0, 0, 0, 0)
        self.cons_bav_layout.setSpacing(4)
        bav_scroll.setWidget(bav_inner)
        layout.addWidget(bav_scroll)
        return w

    def _populate_consolidated(self, cd: ChartData):
        self.cons_chart.set_chart_data(cd)
        self._populate_cons_planet_table(cd)
        self._populate_cons_natal_panel(cd)
        self._populate_cons_ashtakavarga(cd)

    def _populate_cons_planet_table(self, cd: ChartData):
        from jhora.types.nakshatra import Nakshatra
        from jhora.calc.karaka import compute_chara_karakas
        from jhora.charts.varga import VargaChartComputer
        from jhora.types.varga import VargaLevel

        # Chara karakas for suffixes
        planets_dict = {g: {"longitude": p.longitude} for g, p in cd.planets.items()}
        cks = compute_chara_karakas(planets_dict)
        karaka_map = {}
        for ck in cks:
            karaka_map[ck.graha] = ck.short_name

        # Navamsa positions
        try:
            vcc = VargaChartComputer()
            d9 = vcc.compute(cd, VargaLevel.D_9)
            navamsa_map = {g: Rasi.from_longitude(d9.positions[g].longitude).short_name
                          for g in d9.positions}
        except Exception:
            navamsa_map = {}

        bodies = []
        # Lagna
        lr = Rasi.from_longitude(cd.ascendant)
        n_l, p_l = Nakshatra.from_longitude(cd.ascendant)
        deg = int(cd.ascendant)
        min_p = (cd.ascendant - deg) * 60
        min_v = int(min_p)
        sec = int((min_p - min_v) * 60)
        dms = f"{deg}°{min_v:02d}'{sec:02d}\""
        nav_lagna = navamsa_map.get(0, Rasi.from_longitude(cd.ascendant % 30 * 9 % 360).short_name)
        bodies.append(("Lagna", dms, n_l.name.replace("_"," ").title(), p_l,
                       lr.short_name, nav_lagna, "", ""))

        planets_order = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                        Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]
        for g in planets_order:
            p = cd.planet(g)
            r = Rasi.from_longitude(p.longitude)
            n, pada = Nakshatra.from_longitude(p.longitude)
            deg = int(p.longitude)
            min_p = (p.longitude - deg) * 60
            min_v = int(min_p)
            sec = int((min_p - min_v) * 60)
            dms = f"{deg}°{min_v:02d}'{sec:02d}\""
            suffix = f" - {karaka_map.get(g, '')}" if g in karaka_map else ""
            name = f"{g.full_name} (R)" if p.is_retrograde else g.full_name
            nav = navamsa_map.get(g, "?")
            bodies.append((name + suffix, dms, n.name.replace("_"," ").title(),
                           pada, r.short_name, nav, "", p.is_retrograde))

        # Built-in lagnas (Bhava, Hora, Ghati, etc.)
        for lagna_name, lagna_data in [
            ("Bhava Lagna", cd.bhava_lagna),
            ("Hora Lagna", cd.hora_lagna),
            ("Ghati Lagna", cd.ghati_lagna),
        ]:
            if lagna_data:
                lr = Rasi.from_longitude(lagna_data.longitude)
                n, pada = Nakshatra.from_longitude(lagna_data.longitude)
                deg = int(lagna_data.longitude)
                min_p = (lagna_data.longitude - deg) * 60
                min_v = int(min_p)
                sec = int((min_p - min_v) * 60)
                dms_f = f"{deg}°{min_v:02d}'{sec:02d}\""
                bodies.append((lagna_name, dms_f, n.name.replace("_"," ").title(),
                               pada, lr.short_name, "", "", ""))

        # Maandi + Gulika
        from jhora.calc.upagraha import compute_solar_upagrahas
        sun_lon = cd.planet(Graha.SUN).longitude

        headers = ["Body", "DMS", "Nakshatra", "Pada", "Rasi", "Nav", "Ld", "M"]
        self.cons_planet_table.setColumnCount(len(headers))
        self.cons_planet_table.setHorizontalHeaderLabels(headers)
        self.cons_planet_table.setRowCount(len(bodies))
        for i, (name, dms_val, nak, pada, rasi, nav, lord, retro) in enumerate(bodies):
            row_data = [name, dms_val, nak, str(pada) if pada else "",
                       rasi, nav, lord, "R" if retro else ""]
            for j, val in enumerate(row_data):
                item = QTableWidgetItem(str(val) if val else "")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if "Lagna" in name and not any(x in name for x in ["Hora","Ghati","Bhava"]):
                    item.setForeground(QColor("#e94560"))
                if isinstance(retro, bool) and retro:
                    item.setForeground(QColor("#e94560"))
                self.cons_planet_table.setItem(i, j, item)
        self.cons_planet_table.resizeColumnsToContents()

    def _populate_cons_natal_panel(self, cd: ChartData):
        from jhora.types.nakshatra import Nakshatra
        import swisseph as swe

        moon = cd.planet(Graha.MOON).longitude
        sun = cd.planet(Graha.SUN).longitude
        tithi_angle = (moon - sun) % 360
        tithi_idx = int(tithi_angle / 12)
        tithi_pct = (1 - (tithi_angle % 12) / 12) * 100
        tithi_names = ["Pratipat","Dwitiya","Tritiya","Chaturthi","Panchami",
                       "Shashthi","Saptami","Ashtami","Navami","Dasami",
                       "Ekadasi","Dwadasi","Trayodasi","Chaturdasi",
                       "Amavasya/Purnima"]
        phase = "Sukla" if tithi_idx < 15 else "Krishna"
        tithi_name = tithi_names[tithi_idx % 15]
        if tithi_idx == 14:
            tithi_name = "Amavasya"
        elif tithi_idx == 29:
            tithi_name = "Purnima"

        # Tithi lord (weekday mapping: Sun=Pratipat...)
        tithi_lords = ["Su","Mo","Ma","Me","Ju","Ve","Sa"]
        tithi_lord = tithi_lords[tithi_idx % 7]

        nak, pada = Nakshatra.from_longitude(moon)
        nak_name = nak.name.replace("_", " ").title()
        nak_pct = (1 - (moon % (360.0/27)) / (360.0/27)) * 100
        # Nakshatra lord from Vimsottari mapping
        nak_lords = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
        nak_lord = nak_lords[nak.value % 9]

        # Yoga: (Sun+Moon)/13°20' → 27 yogas
        yoga_idx = int(((sun + moon) % 360) / (360.0 / 27)) % 27
        yoga_names = ["Vishkambha","Preeti","Aayushman","Saubhagya","Shobhana",
                      "Atiganda","Sukarma","Dhriti","Shoola","Ganda","Vriddhi",
                      "Dhruva","Vyaghaata","Harshana","Vajra","Siddhi",
                      "Vyatipaata","Variyaana","Parigha","Shiva","Siddha",
                      "Saadhya","Shubha","Shukla","Brahma","Indra","Vaidhriti"]
        yoga_name = yoga_names[yoga_idx]
        yoga_lords = ["Su","Mo","Ma","Me","Ju","Ve","Sa"]
        yoga_lord = yoga_lords[yoga_idx % 7]

        # Karana: tithi_index * 2 + (0 if first half, 1 if second)
        karana_idx = (tithi_idx * 2 + (0 if tithi_pct > 50 else 1)) % 11
        karana_names = ["Bava","Balava","Kaulava","Taitula","Garaja","Vanija",
                        "Vishti","Shakuni","Chatushpada","Naaga","Kimstughna"]
        karana_name = karana_names[karana_idx % 11]
        karana_lords = ["Su","Mo","Ma","Me","Ju","Ve","Sa"]
        karana_lord = karana_lords[karana_idx % 7]

        # Sunrise/sunset
        try:
            jd = cd.julian_day
            flag = swe.CALC_RISE | swe.BIT_NO_REFRACTION
            res, tret = swe.rise_trans(jd - 1, swe.SUN, 0, 0, flag,
                                       (cd.longitude, cd.latitude, 0))
            sr_jd = tret[0] if tret else jd + 0.25
            sr_h = (sr_jd - int(sr_jd)) * 24
            res2, tret2 = swe.rise_trans(jd - 1, swe.SUN, 0, 0,
                                         flag | swe.CALC_SET,
                                         (cd.longitude, cd.latitude, 0))
            ss_jd = tret2[0] if tret2 else jd + 0.75
            ss_h = (ss_jd - int(ss_jd)) * 24
            sunrise = f"{int(sr_h):02d}:{int((sr_h%1)*60):02d}:{int(((sr_h%1)*60%1)*60):02d}"
            sunset = f"{int(ss_h):02d}:{int((ss_h%1)*60):02d}:{int(((ss_h%1)*60%1)*60):02d}"
        except Exception:
            sunrise = "N/A"
            sunset = "N/A"

        # Janma ghatis (1 ghati = 24 min from sunrise)
        birth_h = cd.birth_date.hour + cd.birth_date.minute / 60.0 + cd.birth_date.second / 3600.0
        try:
            jg = (birth_h - sr_h + 24) % 24 / 0.4
        except Exception:
            jg = 0

        # Ayanamsa
        aya_deg = int(cd.ayanamsa_value)
        aya_min = int((cd.ayanamsa_value - aya_deg) * 60)
        aya_sec = int(((cd.ayanamsa_value - aya_deg) * 60 - aya_min) * 60)

        wdays = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
        wd = wdays[cd.birth_date.weekday()]

        lines = [
            f"Date:         {cd.birth_date.strftime('%B %d, %Y')}",
            f"Time:         {cd.birth_date.strftime('%H:%M:%S')}",
            f"Time Zone:    {cd.timezone} (West of GMT)" if cd.timezone.startswith("-") else f"Time Zone:    {cd.timezone} (East of GMT)",
            f"Place:        {cd.latitude:.4f}°, {cd.longitude:.4f}°",
            f"",
            f"Tithi:        {phase} {tithi_name} ({tithi_lord}) ({tithi_pct:.1f}% left)",
            f"Vedic Day:    {wd}",
            f"Nakshatra:    {nak_name} ({nak_lord}) ({nak_pct:.1f}% left)",
            f"Yoga:         {yoga_name} ({yoga_lord})",
            f"Karana:       {karana_name} ({karana_lord})",
            f"",
            f"Sunrise:      {sunrise}",
            f"Sunset:       {sunset}",
            f"Janma Ghatis: {jg:.3f}",
            f"Ayanamsa:     {aya_deg}-{aya_min:02d}-{aya_sec:02d} ({cd.ayanamsa_name})",
        ]
        self.cons_natal_panel.setText("\n".join(lines))

    def _populate_cons_ashtakavarga(self, cd: ChartData):
        from jhora.calc.ashtakavarga import sarva_ashtakavarga, all_bhinna_ashtakavarga
        sav = sarva_ashtakavarga(cd)

        # SAV grid: 4 rows × 3 cols
        self.cons_sav.setColumnCount(3)
        self.cons_sav.setRowCount(4)
        cell_h = ["", "", ""]
        self.cons_sav.setHorizontalHeaderLabels(cell_h)
        self.cons_sav.horizontalHeader().setDefaultSectionSize(50)
        for h in range(12):
            r, c = h // 3, h % 3
            item = QTableWidgetItem(f"{Rasi(h).short_name}\n{sav[h]}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.cons_sav.setItem(r, c, item)
        self.cons_sav.setMaximumHeight(160)

        # BAV — all 8 planets
        # Clear old BAV widgets from the layout
        while self.cons_bav_layout.count():
            child = self.cons_bav_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        from jhora.types.graha import Graha
        bavs = all_bhinna_ashtakavarga(cd)
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                  Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
            if g not in bavs:
                continue
            bav = bavs[g]
            label = QLabel(g.short_name)
            label.setStyleSheet("font-weight: bold; color: #e0b050;")
            self.cons_bav_layout.addWidget(label)
            table = QTableWidget()
            table.setColumnCount(3)
            table.setRowCount(4)
            table.setMaximumHeight(110)
            table.horizontalHeader().setDefaultSectionSize(35)
            table.verticalHeader().setDefaultSectionSize(22)
            for h in range(12):
                r, c = h // 3, h % 3
                item = QTableWidgetItem(str(bav[h]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)
            self.cons_bav_layout.addWidget(table)

    # ── Navamsa overlay for consolidated charts ──

    def _update_cons_navamsa(self, cd: ChartData):
        from jhora.charts.varga import VargaChartComputer
        from jhora.types.varga import VargaLevel
        comp = VargaChartComputer()
        vcd = comp.compute(cd, VargaLevel.D_9)
        self.cons_navamsa.set_chart_data(cd)
        self.cons_navamsa.set_navamsa_data(vcd.positions)
        self.cons_navamsa.set_navamsa_overlay(True)


class _TeacherWorker(QThread):
    token = pyqtSignal(str)
    done = pyqtSignal()

    def __init__(self, question, chart, provider, base_url, model):
        super().__init__()
        self.question = question
        self.chart = chart
        self.provider = provider
        self.base_url = base_url
        self.model = model

    def run(self):
        try:
            from jhora.ai.teacher import AiTeacher
            teacher = AiTeacher(self.provider, self.base_url, self.model)
            teacher.ask(self.question, chart=self.chart, on_token=self.token.emit)
            self.done.emit()
        except Exception as e:
            self.token.emit(str(e))
            self.done.emit()


class _AiWorker(QThread):
    token = pyqtSignal(str)
    done = pyqtSignal()
    error = pyqtSignal(str)
    def __init__(self, engine: AiEngine, mode: str, chart: ChartData,
                 style: str = "", question: str = "", topic: str = "general"):
        super().__init__()
        self.engine = engine
        self.mode = mode
        self.chart = chart
        self.style = style
        self.question = question
        self.topic = topic

    def run(self):
        try:
            if self.mode == "interpret":
                self.engine.interpret(self.chart, self.style, self.topic,
                                      on_token=self.token.emit)
            elif self.mode == "remedies":
                self.engine.remedies(self.chart, on_token=self.token.emit)
            elif self.mode == "ask":
                self.engine.ask(self.chart, self.question, on_token=self.token.emit)
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))
