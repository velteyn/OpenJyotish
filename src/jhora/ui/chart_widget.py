from enum import Enum
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QBrush
from PyQt6.QtWidgets import QWidget

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.charts.chart import ChartData, VargaPosition


class ChartStyle(Enum):
    SOUTH_INDIAN = "south_indian"
    NORTH_INDIAN = "north_indian"
    EAST_INDIAN = "east_indian"


PALETTE = {
    "bg": QColor("#1a1a2e"),
    "cell_bg": QColor("#16213e"),
    "border": QColor("#e94560"),
    "accent": QColor("#00d2ff"),
    "text": QColor("#cccccc"),
    "text_dim": QColor("#888888"),
    "lagna": QColor("#e94560"),
    "navamsa": QColor("#00ff88"),
    "retro": QColor("#e94560"),
}

PLANET_COLORS = {
    Graha.SUN: QColor("#FF6B35"),
    Graha.MOON: QColor("#C0C0C0"),
    Graha.MARS: QColor("#FF4444"),
    Graha.MERCURY: QColor("#44CC44"),
    Graha.JUPITER: QColor("#FFB347"),
    Graha.VENUS: QColor("#FF69B4"),
    Graha.SATURN: QColor("#4488FF"),
    Graha.RAHU: QColor("#8B4513"),
    Graha.KETU: QColor("#FFD700"),
}

_SOUTH_INDIAN_GRID = [
    (3, 0, Rasi.ARIES),     (3, 1, Rasi.PISCES),
    (3, 2, Rasi.AQUARIUS),  (3, 3, Rasi.CAPRICORN),
    (2, 3, Rasi.SAGITTARIUS), (1, 3, Rasi.SCORPIO),
    (0, 3, Rasi.LIBRA),     (0, 2, Rasi.VIRGO),
    (0, 1, Rasi.LEO),       (0, 0, Rasi.CANCER),
    (1, 0, Rasi.GEMINI),    (2, 0, Rasi.TAURUS),
]


class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_data: Optional[ChartData] = None
        self.chart_style = ChartStyle.SOUTH_INDIAN
        self.navamsa_overlay = False
        self.navamsa_data: Optional[Dict[Graha, object]] = None
        self.setMinimumSize(420, 420)
        self.setStyleSheet("background-color: #1a1a2e;")

    def set_chart_data(self, cd: ChartData):
        self.chart_data = cd
        self.navamsa_data = None
        self.update()

    def set_chart_style(self, style: ChartStyle):
        self.chart_style = style
        self.update()

    def set_navamsa_overlay(self, enabled: bool):
        self.navamsa_overlay = enabled
        self.update()

    def set_navamsa_data(self, data: Dict[Graha, object]):
        self.navamsa_data = data
        self.update()

    @staticmethod
    def _navamsa_label(val: object) -> str:
        if isinstance(val, VargaPosition):
            return val.rasi.short_name
        return str(val)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), PALETTE["bg"])

        if self.chart_data is None:
            painter.setPen(PALETTE["text_dim"])
            painter.setFont(QFont("sans-serif", 16))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "Enter birth data\nand click Calculate")
            return

        if self.chart_style == ChartStyle.SOUTH_INDIAN:
            self._draw_south_indian(painter)
        elif self.chart_style == ChartStyle.NORTH_INDIAN:
            self._draw_north_indian(painter)
        elif self.chart_style == ChartStyle.EAST_INDIAN:
            self._draw_east_indian(painter)

    def _cell_grid(self) -> Tuple[float, float, float, float]:
        w, h = self.width(), self.height()
        size = min(w, h) - 8
        ox = (w - size) / 2
        oy = (h - size) / 2
        return ox, oy, size / 4, size / 4

    def _cell_rect(self, row: int, col: int, margin: float = 3) -> QRectF:
        ox, oy, cw, ch = self._cell_grid()
        return QRectF(ox + col * cw + margin, oy + row * ch + margin,
                      cw - 2 * margin, ch - 2 * margin)

    def _center_rect(self, margin: float = 3) -> QRectF:
        ox, oy, cw, ch = self._cell_grid()
        return QRectF(ox + cw + margin, oy + ch + margin,
                      cw * 2 - 2 * margin, ch * 2 - 2 * margin)

    def _planets_by_rasi(self) -> Dict[Rasi, List[Tuple[Graha, float]]]:
        pb = {}
        for g, p in self.chart_data.planets.items():
            pb.setdefault(p.rasi, []).append((g, p.longitude))
        return pb

    def _draw_south_indian(self, painter: QPainter):
        pb = self._planets_by_rasi()
        lagna_rasi = Rasi.from_longitude(self.chart_data.ascendant)
        if lagna_rasi not in pb:
            pb[lagna_rasi] = []

        for row, col, rasi in _SOUTH_INDIAN_GRID:
            rect = self._cell_rect(row, col)
            is_asc = rasi == lagna_rasi
            self._draw_cell(painter, rect, highlight=is_asc)
            self._draw_header(painter, rect, rasi, is_lagna=is_asc)

            planets = pb.get(rasi, [])
            if planets:
                self._draw_planets(painter, rect, planets)

        # Center box
        cr = self._center_rect()
        painter.setPen(QPen(PALETTE["border"], 2))
        painter.setBrush(QBrush(PALETTE["cell_bg"]))
        painter.drawRect(cr.toRect())
        painter.setPen(PALETTE["text_dim"])
        painter.setFont(QFont("sans-serif", 11))
        painter.drawText(cr, Qt.AlignmentFlag.AlignCenter,
                         f"{self.chart_data.ayanamsa_name.title()}\n{self.chart_data.ayanamsa_value:.4f}°")

    def _draw_north_indian(self, painter: QPainter):
        pb = self._planets_by_rasi()
        asc_rasi = Rasi.from_longitude(self.chart_data.ascendant)

        ni_grid = [
            (0, 0, 10), (0, 1, 11), (0, 2, 12), (0, 3, 1),
            (1, 3, 2),  (2, 3, 3),  (3, 3, 4),  (3, 2, 5),
            (3, 1, 6),  (3, 0, 7),  (2, 0, 8),  (1, 0, 9),
        ]

        for row, col, house_num in ni_grid:
            rect = self._cell_rect(row, col)
            ras_idx = (asc_rasi.value + house_num - 1) % 12
            ras = Rasi(ras_idx)
            is_asc = house_num == 1

            self._draw_cell(painter, rect, highlight=is_asc)
            self._draw_house_label(painter, rect, house_num, ras, is_asc)

            planets = pb.get(ras, [])
            if planets:
                self._draw_planets(painter, rect, planets)

        cr = self._center_rect()
        painter.setPen(QPen(PALETTE["border"], 2))
        painter.setBrush(QBrush(PALETTE["cell_bg"]))
        painter.drawRect(cr.toRect())

        painter.setPen(PALETTE["accent"])
        painter.setFont(QFont("sans-serif", 11, QFont.Weight.Bold))
        painter.drawText(cr, Qt.AlignmentFlag.AlignCenter,
                         f"Asc\n{asc_rasi.short_name}")

        _ni_diagonal_lines = [
            (0, 0, 1, 3), (0, 3, 3, 3),
            (3, 3, 3, 0), (3, 0, 0, 0),
        ]
        lw = 1.0
        painter.setPen(QPen(PALETTE["border"], lw))
        for r1, c1, r2, c2 in _ni_diagonal_lines:
            ox, oy, cw, ch = self._cell_grid()
            x1 = ox + c1 * cw + cw / 2
            y1 = oy + r1 * ch + ch / 2
            x2 = ox + c2 * cw + cw / 2
            y2 = oy + r2 * ch + ch / 2
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _draw_east_indian(self, painter: QPainter):
        w, h = self.width(), self.height()
        size = min(w, h) - 24
        cx, cy = w / 2, h / 2
        outer_r, inner_r = size / 2, size * 0.30
        label_r = outer_r - QFontMetrics(QFont("sans-serif", 8, QFont.Weight.Bold)).height() - 4
        offset_r = inner_r + QFontMetrics(QFont("sans-serif", 8, QFont.Weight.Bold)).height()

        import math

        painter.setPen(QPen(PALETTE["border"], 1.5))
        painter.setBrush(QBrush(PALETTE["cell_bg"]))
        painter.drawEllipse(QPointF(cx, cy), outer_r, outer_r)
        painter.setBrush(QBrush())
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        for i in range(12):
            a = math.radians(i * 30 - 90)
            painter.drawLine(QPointF(cx + inner_r * math.cos(a), cy + inner_r * math.sin(a)),
                             QPointF(cx + outer_r * math.cos(a), cy + outer_r * math.sin(a)))

        pb = self._planets_by_rasi()
        lagna_rasi = Rasi.from_longitude(self.chart_data.ascendant)

        for i in range(12):
            rasi = Rasi(i)
            a = math.radians(i * 30 - 90 + 15)
            is_asc = rasi == lagna_rasi

            lx = cx + label_r * math.cos(a)
            ly = cy + label_r * math.sin(a)
            font = QFont("sans-serif", 8, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(PALETTE["lagna"] if is_asc else PALETTE["accent"])
            label = "Asc" if is_asc else rasi.short_name
            tw = QFontMetrics(font).horizontalAdvance(label)
            painter.drawText(int(lx - tw / 2), int(ly + 4), label)

            planets = pb.get(rasi, [])
            if planets:
                planets.sort(key=lambda x: x[1])
                n = len(planets)
                for j, (graha, _) in enumerate(planets):
                    pr = offset_r + j * (label_r - offset_r) / max(n, 1)
                    px = cx + pr * math.cos(a)
                    py = cy + pr * math.sin(a)
                    self._draw_planet_glyph(painter, graha, px, py)

        painter.setPen(PALETTE["text_dim"])
        painter.setFont(QFont("sans-serif", 9))
        painter.drawText(int(cx - 40), int(cy),
                         f"{self.chart_data.ayanamsa_name.title()}\n{self.chart_data.ayanamsa_value:.4f}")

    def _draw_cell(self, painter: QPainter, rect: QRectF, highlight: bool = False):
        bw = 1.5 if not highlight else 2.5
        painter.setPen(QPen(PALETTE["lagna"] if highlight else PALETTE["border"], bw))
        painter.setBrush(QBrush(PALETTE["cell_bg"]))
        painter.drawRect(rect.toRect())

    def _draw_header(self, painter: QPainter, rect: QRectF, rasi: Rasi, is_lagna: bool = False):
        font = QFont("sans-serif", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(PALETTE["lagna"] if is_lagna else PALETTE["accent"])
        label = "Asc" if is_lagna else rasi.short_name
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(label)
        painter.drawText(int(rect.x() + rect.width() / 2 - tw / 2),
                         int(rect.y() + fm.height() + 3), label)

    def _draw_house_label(self, painter: QPainter, rect: QRectF,
                          house_num: int, ras: Rasi, is_asc: bool):
        # House number top-left
        painter.setFont(QFont("sans-serif", 8))
        painter.setPen(PALETTE["accent"])
        painter.drawText(int(rect.x() + 3), int(rect.y() + QFontMetrics(QFont("sans-serif", 8)).height()), str(house_num))

        # Rasi name centered
        font = QFont("sans-serif", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(PALETTE["lagna"] if is_asc else QColor("#ffffff"))
        label = f"Asc ({ras.short_name})" if is_asc else ras.short_name
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(label)
        painter.drawText(int(rect.x() + rect.width() / 2 - tw / 2),
                         int(rect.y() + fm.height() + 4), label)

    def _draw_planets(self, painter: QPainter, rect: QRectF,
                      planets: List[Tuple[Graha, float]]):
        planets.sort(key=lambda x: x[1])
        font = QFont("sans-serif", 8, QFont.Weight.Bold)
        painter.setFont(font)
        fm = QFontMetrics(font)
        nf = QFont("sans-serif", 7)
        has_nav = self.navamsa_overlay and self.navamsa_data is not None

        n = len(planets)
        cols = 2 if n > 2 else 1
        rows = (n + cols - 1) // cols

        cell_w = rect.width()
        cell_h = rect.height()
        header_h = fm.height() + 6

        avail_w = cell_w - 8
        avail_h = cell_h - header_h - 4

        row_h = min(fm.height() + 4, avail_h // max(rows, 1))
        col_w = avail_w // cols

        for i, (graha, _) in enumerate(planets):
            col = i % cols
            row = i // cols

            cx = rect.x() + 4 + col * col_w
            cy = rect.y() + header_h + row * row_h + (row_h - fm.height()) // 2 + fm.ascent()

            self._draw_planet_glyph(painter, graha, cx, cy)

            tx = cx + fm.horizontalAdvance(graha.short_name) + 3

            if self.chart_data and self.chart_data.planets[graha].is_retrograde:
                painter.setPen(PALETTE["retro"])
                painter.drawText(int(tx), int(cy), "R")
                tx += fm.horizontalAdvance("R") + 2

            if has_nav and graha in self.navamsa_data:
                painter.setFont(nf)
                painter.setPen(PALETTE["navamsa"])
                painter.drawText(int(tx), int(cy), self._navamsa_label(self.navamsa_data[graha]))
                painter.setFont(font)

    def _draw_planet_glyph(self, painter: QPainter, graha: Graha, x: float, y: float):
        painter.setPen(PLANET_COLORS.get(graha, QColor("white")))
        painter.drawText(int(x), int(y), graha.short_name)
