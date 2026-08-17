"""OpenJyotish UI theme — modern dark palette inspired by Vedic gold.

Single source of truth for colors and the global stylesheet.
Import `apply_theme(app)` to set the application-wide look.
"""

# ── Palette ──────────────────────────────────────────────────────────────
BG = "#0e111a"          # window background (deep space navy)
BG_PANEL = "#151a28"    # panels / cards
BG_INPUT = "#1a2135"    # inputs, tables
BG_HOVER = "#1f2740"    # hover state
BORDER = "#2a3350"      # subtle borders
GOLD = "#d4af37"        # primary accent (Vedic gold)
GOLD_DIM = "#8a7434"    # muted gold
TEAL = "#2dd4bf"        # secondary accent
RED = "#e5534b"
GREEN = "#3fb96f"
TEXT = "#e8e9f2"        # primary text
DIM = "#8b90a8"         # secondary text
SIDEBAR_BG = "#0a0d15"  # navigation rail
SIDEBAR_SEL = "#1c2337" # selected nav item


STYLESHEET = f"""
/* ── Base ── */
QMainWindow, QDialog {{ background-color: {BG}; }}
QWidget {{ font-size: 13px; }}
QToolTip {{ background-color: {BG_PANEL}; color: {TEXT};
           border: 1px solid {BORDER}; padding: 4px 8px; }}

/* ── Sidebar navigation rail ── */
QFrame#sidebar {{ background-color: {SIDEBAR_BG};
                 border-right: 1px solid {BORDER}; }}
QLabel#brand {{ color: {GOLD}; font-size: 17px; font-weight: bold;
               padding: 18px 16px 2px 16px; }}
QLabel#brandSub {{ color: {DIM}; font-size: 10px;
                  padding: 0 16px 14px 16px; }}
QLabel#versionLbl {{ color: {DIM}; font-size: 10px; padding: 10px 16px; }}
QListWidget#nav {{ background-color: {SIDEBAR_BG}; border: none;
                  outline: none; padding: 6px 8px; }}
QListWidget#nav::item {{ color: {DIM}; padding: 11px 14px;
                        border-radius: 8px; margin: 2px 0; }}
QListWidget#nav::item:hover {{ background-color: {BG_HOVER}; color: {TEXT}; }}
QListWidget#nav::item:selected {{ background-color: {SIDEBAR_SEL};
                                 color: {GOLD};
                                 border-left: 3px solid {GOLD}; }}

/* ── Group boxes → cards ── */
QGroupBox {{ color: {GOLD}; font-weight: bold; font-size: 13px;
            background-color: {BG_PANEL};
            border: 1px solid {BORDER}; border-radius: 10px;
            margin-top: 14px; padding-top: 20px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 14px; color: {GOLD};
                   padding: 0 4px; }}

/* ── Inputs ── */
QLabel {{ color: {TEXT}; }}
QLineEdit {{ background-color: {BG_INPUT}; color: {TEXT};
            border: 1px solid {BORDER}; padding: 6px 10px;
            border-radius: 6px; selection-background-color: {GOLD_DIM}; }}
QLineEdit:focus {{ border-color: {GOLD}; }}
QComboBox {{ background-color: {BG_INPUT}; color: {TEXT};
            border: 1px solid {BORDER}; padding: 6px 10px;
            border-radius: 6px; min-width: 110px; }}
QComboBox:hover {{ border-color: {GOLD_DIM}; }}
QComboBox:focus {{ border-color: {GOLD}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent;
                        border-right: 5px solid transparent;
                        border-top: 6px solid {GOLD}; margin-right: 8px; }}
QComboBox QAbstractItemView {{ background-color: {BG_PANEL}; color: {TEXT};
                              border: 1px solid {BORDER};
                              selection-background-color: {GOLD_DIM};
                              outline: none; }}
QDateEdit, QTimeEdit {{ background-color: {BG_INPUT}; color: {TEXT};
                       border: 1px solid {BORDER}; padding: 5px 8px;
                       border-radius: 6px; }}
QDateEdit:focus, QTimeEdit:focus {{ border-color: {GOLD}; }}
QDateEdit::up-button, QDateEdit::down-button,
QTimeEdit::up-button, QTimeEdit::down-button {{ width: 16px; border: none; }}
QRadioButton {{ color: {TEXT}; spacing: 6px; }}
QRadioButton::indicator {{ width: 15px; height: 15px; border-radius: 8px;
                          border: 2px solid {DIM}; background: {BG_INPUT}; }}
QRadioButton::indicator:checked {{ border-color: {GOLD};
                                  background: {GOLD}; }}
QCheckBox {{ color: {TEXT}; spacing: 6px; }}

/* ── Buttons ── */
QPushButton {{ background-color: {BG_HOVER}; color: {TEXT};
              border: 1px solid {BORDER}; padding: 7px 18px;
              border-radius: 7px; font-weight: bold; }}
QPushButton:hover {{ background-color: #27304e; border-color: {GOLD_DIM}; }}
QPushButton:pressed {{ background-color: {SIDEBAR_SEL}; }}
QPushButton:checked {{ background-color: {GOLD_DIM}; color: #ffffff;
                      border-color: {GOLD}; }}
QPushButton:disabled {{ background-color: {BG_PANEL}; color: #5a5f74;
                       border-color: {BORDER}; }}
/* Primary action button (Calculate) — gold */
QPushButton#primary {{ background-color: {GOLD}; color: #14100a;
                      border: none; font-size: 14px; padding: 9px 22px; }}
QPushButton#primary:hover {{ background-color: #e6c354; }}
QPushButton#primary:pressed {{ background-color: #b8962e; }}

/* ── Tables ── */
QTableWidget {{ background-color: {BG_PANEL}; color: {TEXT};
               border: 1px solid {BORDER}; border-radius: 8px;
               gridline-color: {BORDER};
               selection-background-color: {GOLD_DIM}; }}
QTableWidget::item {{ padding: 5px 8px; }}
QTableWidget::item:alternate {{ background-color: #181f31; }}
QHeaderView::section {{ background-color: {BG_INPUT}; color: {GOLD};
                       font-weight: bold; border: none;
                       border-bottom: 2px solid {GOLD_DIM};
                       padding: 6px 8px; }}

/* ── Tabs (sub-tabs inside pages) ── */
QTabWidget::pane {{ background-color: {BG_PANEL};
                   border: 1px solid {BORDER}; border-radius: 8px;
                   top: -1px; }}
QTabBar::tab {{ background-color: transparent; color: {DIM};
               padding: 9px 18px; border: none;
               border-bottom: 2px solid transparent; }}
QTabBar::tab:hover {{ color: {TEXT}; }}
QTabBar::tab:selected {{ color: {GOLD};
                        border-bottom: 2px solid {GOLD}; }}

/* ── Text areas ── */
QTextEdit {{ background-color: {BG_PANEL}; color: {TEXT};
            border: 1px solid {BORDER}; border-radius: 8px;
            padding: 8px; selection-background-color: {GOLD_DIM}; }}

/* ── Lists (city results etc.) ── */
QListWidget {{ background-color: {BG_PANEL}; color: {TEXT};
              border: 1px solid {BORDER}; border-radius: 8px; }}
QListWidget::item {{ padding: 6px 8px; }}
QListWidget::item:selected {{ background-color: {GOLD_DIM}; color: #ffffff; }}
QListWidget::item:hover {{ background-color: {BG_HOVER}; }}

/* ── Scrollbars ── */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px;
                              min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {GOLD_DIM}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 5px;
                                min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {GOLD_DIM}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Splitter / status / menu ── */
QSplitter::handle {{ background-color: {BORDER}; width: 1px; }}
QStatusBar {{ background-color: {SIDEBAR_BG}; color: {DIM};
             border-top: 1px solid {BORDER}; }}
QMenuBar {{ background-color: {SIDEBAR_BG}; color: {TEXT};
           border-bottom: 1px solid {BORDER}; padding: 2px; }}
QMenuBar::item {{ padding: 5px 12px; border-radius: 5px; }}
QMenuBar::item:selected {{ background-color: {BG_HOVER}; color: {GOLD}; }}
QMenu {{ background-color: {BG_PANEL}; color: {TEXT};
        border: 1px solid {BORDER}; border-radius: 8px; padding: 4px; }}
QMenu::item {{ padding: 7px 28px 7px 20px; border-radius: 5px; }}
QMenu::item:selected {{ background-color: {GOLD_DIM}; color: #ffffff; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 8px; }}

/* ── Message boxes (light, readable) ── */
QMessageBox {{ background-color: #ffffff; }}
QMessageBox QLabel {{ color: #000000; font-size: 14px; }}
QMessageBox QPushButton {{ background-color: {GOLD}; color: #14100a;
                          padding: 6px 24px; border: none; }}
"""


def apply_theme(app) -> None:
    """Apply the OpenJyotish theme to a QApplication."""
    from PyQt6.QtGui import QFont
    app.setStyleSheet(STYLESHEET)
    app.setFont(QFont("Segoe UI", 10))
