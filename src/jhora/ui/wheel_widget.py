"""Circular bi-wheel chart widget — natal ring + transit ring, Lagna-left.

Paint order (bottom-up): drishti lines, sign ring, natal glyphs,
transit glyphs, ruler ticks, rings. Positions come from ChartData
sidereal longitudes; glyphs from the bundled-font provider; crowding
resolved by the headless declutter with leader ticks to true degrees.
"""

import math
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QToolTip, QWidget

from jhora.calc.avastha import avastha_of
from jhora.calc.combustion import combust_planets
from jhora.calc.drishti import ALL_GRAHAS
from jhora.calc.drishti import drishti as calc_drishti
from jhora.calc.gandanta import gandanta_planets, gandanta_zone
from jhora.charts.chart import ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.ui import glyphs
from jhora.ui.wheel_math import (WheelSettings, declutter,
                                 min_separation_deg, project)

_ELEMENT_TINTS = {
    "fire": "#3a1f1f",
    "earth": "#1f2f1f",
    "air": "#1f2733",
    "water": "#1f1f33",
}


class WheelWidget(QWidget):
    """Natal + transit circular wheel (Lagna at 9 o'clock)."""

    def __init__(self, parent=None, settings: Optional[WheelSettings] = None):
        super().__init__(parent)
        self.settings = settings or WheelSettings()
        self.chart_data: Optional[ChartData] = None
        self.transit_lons: Dict[Graha, float] = {}
        #: Hit records for hover: (graha, x, y, radius, tooltip, natal).
        self._hit: List[Tuple[Graha, float, float, float, str, bool]] = []
        #: Click selection: (graha, natal) or None.
        self.selected: Optional[Tuple[Graha, bool]] = None
        self.setMinimumSize(300, 300)
        self.setMouseTracking(True)
        glyphs.ensure_fonts()

    def set_chart_data(self, cd: ChartData):
        self.chart_data = cd
        self.update()

    def set_transit_data(self, lons: Dict[Graha, float]):
        self.transit_lons = dict(lons)
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position()
        for _g, x, y, r, tip, _natal in self._hit:
            if (pos.x() - x) ** 2 + (pos.y() - y) ** 2 <= r * r:
                QToolTip.showText(
                    event.globalPosition().toPoint(), tip, self)
                return
        QToolTip.hideText()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position()
        self._select_at(pos.x(), pos.y())
        self.update()

    def _select_at(self, x: float, y: float):
        """Select the glyph at a point; None when the sky is clicked."""
        self.selected = None
        for g, hx, hy, r, _tip, natal in self._hit:
            if (x - hx) ** 2 + (y - hy) ** 2 <= r * r:
                self.selected = (g, natal)
                break
        return self.selected

    def _details(self, g: Graha, lon: float, lagna: int,
                 natal: bool) -> Tuple[str, str]:
        rasi = Rasi(int(lon // 30) % 12)
        house = ((int(lon // 30) - lagna) % 12) + 1
        head = f"{g.full_name}{'' if natal else ' (transit)'}"
        if natal and self.chart_data is not None:
            cd = self.chart_data
            p = cd.planet(g)
            flags = []
            av = avastha_of(g, lon)
            if av is not None:
                flags.append(av[0])
            flags.append("retro" if p.is_retrograde else "direct")
            sun = cd.planet(Graha.SUN).longitude
            if g in combust_planets(
                    {g: lon}, sun, {g: p.is_retrograde}):
                flags.append("combust")
            if g in gandanta_planets({g: lon}):
                flags.append("gandanta")
            sub = (f"{rasi.full_name} {lon % 30:.1f}° · H{house} · "
                   f"{p.dignity} · {', '.join(flags)}")
        else:
            sub = f"{rasi.full_name} {lon % 30:.1f}° · H{house}"
        return head, sub

    def _tip_for(self, g: Graha, lon: float, lagna: int,
                 natal: bool) -> str:
        head, sub = self._details(g, lon, lagna, natal)
        return f"{head} — {sub}"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self.settings
        painter.fillRect(self.rect(), QColor(s.colors["background"]))
        if self.chart_data is None:
            painter.setPen(QColor(s.colors["text"]))
            painter.setFont(QFont("sans-serif", 14))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "Calculate a chart to open the wheel")
            return
        cx, cy = self.width() / 2.0, self.height() / 2.0
        radius = min(self.width(), self.height()) / 2.0 - 8.0
        lagna = self.chart_data.ascendant
        self._hit = []
        if s.show_drishti:
            self._paint_drishti(painter, cx, cy, radius, lagna)
        self._paint_signs(painter, cx, cy, radius, lagna)
        self._paint_ring_glyphs(painter, cx, cy, radius, lagna,
                                natal=True)
        if s.show_transits and self.transit_lons:
            self._paint_ring_glyphs(painter, cx, cy, radius, lagna,
                                    natal=False)
        self._paint_ruler(painter, cx, cy, radius, lagna)
        self._paint_circles(painter, cx, cy, radius)
        if self.selected is not None:
            self._paint_selection(painter, cx, cy, lagna)

    def _paint_selection(self, painter: QPainter, cx: float, cy: float,
                         lagna: float):
        s = self.settings
        g, natal = self.selected
        if natal:
            if g not in self.chart_data.planets:
                self.selected = None
                return
            lon = self.chart_data.planet(g).longitude
        else:
            lon = self.transit_lons.get(g)
            if lon is None:
                self.selected = None
                return
        for hg, hx, hy, hr, _tip, hn in self._hit:
            if hg == g and hn == natal:
                painter.setPen(QPen(QColor(s.colors["benefic"]), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(int(hx - hr - 5), int(hy - hr - 5),
                                    int(2 * (hr + 5)), int(2 * (hr + 5)))
                break
        head, sub = self._details(g, lon, int(lagna // 30) % 12, natal)
        painter.setPen(QColor(s.colors["benefic"]))
        painter.setFont(QFont("sans-serif", 13, QFont.Weight.Bold))
        painter.drawText(int(cx) - 200, int(cy) - 34, 400, 24,
                         Qt.AlignmentFlag.AlignCenter, head)
        painter.setPen(QColor(s.colors["text"]))
        painter.setFont(QFont("sans-serif", 10))
        painter.drawText(int(cx) - 200, int(cy) - 8, 400, 22,
                         Qt.AlignmentFlag.AlignCenter, sub)

    def _paint_drishti(self, painter: QPainter, cx: float, cy: float,
                       radius: float, lagna: float):
        s = self.settings
        hub = radius * s.hub_ratio
        for giver, aspects in calc_drishti(self.chart_data).items():
            if giver not in (Graha.SUN, Graha.MOON, Graha.MARS,
                             Graha.MERCURY, Graha.JUPITER, Graha.VENUS,
                             Graha.SATURN) and not s.show_nodes:
                continue
            color = (s.colors["drishti_benefic"] if giver.is_benefic
                     else s.colors["drishti_malefic"])
            painter.setPen(QPen(QColor(color), 1))
            gx, gy = project(
                self.chart_data.planet(giver).longitude, lagna, cx, cy, hub)
            for aspect in aspects:
                tx, ty = project(aspect.target_sign_index * 30.0 + 15.0,
                                 lagna, cx, cy, hub)
                painter.drawLine(int(gx), int(gy), int(tx), int(ty))

    def _paint_signs(self, painter: QPainter, cx: float, cy: float,
                     radius: float, lagna: float):
        s = self.settings
        outer = radius * s.natal_ring_ratio
        inner = radius * s.sign_ring_ratio
        for i in range(12):
            rasi = Rasi((int(lagna // 30) + i) % 12)
            start_lon = (int(lagna // 30) * 30 + i * 30) % 360.0
            tint = (_ELEMENT_TINTS[rasi.element] if s.show_sign_colors
                    else "#22222f")
            self._paint_arc_segment(painter, cx, cy, inner, outer,
                                    start_lon, lagna, tint)
            # Sign boundary divider across the sign band.
            bx, by = project(start_lon, lagna, cx, cy, outer)
            ix, iy = project(start_lon, lagna, cx, cy, inner)
            painter.setPen(QPen(QColor(s.colors["ring"]), 1))
            painter.drawLine(int(bx), int(by), int(ix), int(iy))
            mx, my = project(start_lon + 15.0, lagna, cx, cy,
                             (inner + outer) / 2.0)
            text, family, is_glyph = glyphs.glyph_for_rasi(rasi)
            painter.setPen(QColor(s.colors["text"]))
            font = QFont(family if family else "sans-serif",
                         int(13 * s.symbol_scale))
            painter.setFont(font)
            painter.drawText(int(mx) - 20, int(my) - 20, 40, 40,
                             Qt.AlignmentFlag.AlignCenter, text)
            # Whole-sign house number at the segment's inner edge.
            hx, hy = project(start_lon + 15.0, lagna, cx, cy, inner + 2)
            painter.setFont(QFont("sans-serif", int(9 * s.symbol_scale)))
            painter.setPen(QColor(s.colors["ring"]))
            painter.drawText(int(hx) - 20, int(hy) - 10, 40, 20,
                             Qt.AlignmentFlag.AlignCenter,
                             str(((int(start_lon // 30)
                                   - int(lagna // 30)) % 12) + 1))
        # Lagna marker from the sign ring out to the edge.
        lx0, ly0 = project(lagna, lagna, cx, cy, radius * s.sign_ring_ratio)
        lx, ly = project(lagna, lagna, cx, cy, radius)
        painter.setPen(QPen(QColor(s.colors["benefic"]), 3))
        painter.drawLine(int(lx0), int(ly0), int(lx), int(ly))
        # Ascendant degree beside the line (offset perpendicular).
        import math as _math
        _theta = _math.radians(180.0)
        _nx, _ny = _math.sin(_theta), _math.cos(_theta)
        painter.setPen(QColor(s.colors["benefic"]))
        painter.setFont(QFont("sans-serif", int(9 * s.symbol_scale)))
        painter.drawText(int((lx0 + lx) / 2 + _nx * 16) - 40,
                         int((ly0 + ly) / 2 + _ny * 16) - 10, 80, 20,
                         Qt.AlignmentFlag.AlignCenter,
                         f"Asc {lagna % 30:.1f}°")

    def _paint_arc_segment(self, painter: QPainter, cx: float, cy: float,
                           inner: float, outer: float, start_lon: float,
                           lagna: float, color: str):
        end_deg = 180.0 - (start_lon + 30.0 - lagna)
        start_deg = 180.0 - (start_lon - lagna)
        path = QPainterPath()
        sx = cx + outer * math.cos(math.radians(end_deg))
        sy = cy - outer * math.sin(math.radians(end_deg))
        path.moveTo(sx, sy)
        # NOTE: QPainterPath.arcTo takes plain degrees (unlike
        # QPainter.drawPie which takes sixteenths).
        path.arcTo(cx - outer, cy - outer, 2 * outer, 2 * outer,
                   end_deg, 30)
        ex = cx + inner * math.cos(math.radians(start_deg))
        ey = cy - inner * math.sin(math.radians(start_deg))
        path.lineTo(ex, ey)
        path.arcTo(cx - inner, cy - inner, 2 * inner, 2 * inner,
                   start_deg, -30)
        path.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(color)))
        painter.drawPath(path)

    def _paint_ring_glyphs(self, painter: QPainter, cx: float, cy: float,
                           radius: float, lagna: float, natal: bool):
        s = self.settings
        if natal:
            cd = self.chart_data
            lons = {g: cd.planet(g).longitude for g in ALL_GRAHAS
                    if g in cd.planets}
            ring_r = radius * s.natal_ring_ratio
            dim = False
        else:
            lons = dict(self.transit_lons)
            ring_r = radius * s.transit_ring_ratio
            dim = True
        if not s.show_nodes:
            lons = {g: lon for g, lon in lons.items()
                    if g not in (Graha.RAHU, Graha.KETU)}
        if not lons:
            return
        names = {g: g.short_name for g in lons}
        placed = declutter([(names[g], lon) for g, lon in lons.items()],
                           min_separation_deg(
                               s.collision_radius_px * s.symbol_scale,
                               ring_r))
        by_name = {g.short_name: g for g in lons}
        retro = set()
        comb = set()
        gand = set()
        if natal:
            cd = self.chart_data
            retro = {g for g in lons
                     if cd.planets[g].is_retrograde}
            sun = cd.planet(Graha.SUN).longitude
            comb = set(combust_planets(
                {g: cd.planet(g).longitude for g in lons}, sun,
                {g: cd.planets[g].is_retrograde for g in lons}))
            gand = set(gandanta_planets(
                {g: cd.planet(g).longitude for g in lons}))
        glyph_px = int(16 * s.symbol_scale)
        for key, disp_lon, true_lon, overflow in placed:
            g = by_name[key]
            if overflow:
                text, family = g.short_name, "sans-serif"
            else:
                text, family, _ = glyphs.glyph_for_graha(g)
            if dim:
                color = s.colors["transit"]
            elif g in comb:
                color = s.colors["dim"]
            elif g.is_benefic:
                color = s.colors["benefic"]
            else:
                color = s.colors["malefic"]
            x, y = project(disp_lon, lagna, cx, cy, ring_r)
            painter.setPen(QColor(color))
            painter.setFont(QFont(family, glyph_px))
            painter.drawText(int(x) - 30, int(y) - 30, 60, 60,
                             Qt.AlignmentFlag.AlignCenter, text)
            # Inline annotation: degree + retro mark (LUNA grammar).
            painter.setFont(QFont("sans-serif", int(9 * s.symbol_scale)))
            painter.setPen(QColor(s.colors["retro"]) if g in retro
                           else QColor(s.colors["text"]))
            painter.drawText(int(x) + 10, int(y) - 28, 48, 18,
                             Qt.AlignmentFlag.AlignLeft,
                             f"{true_lon % 30:.0f}°"
                             + (" R" if g in retro else ""))
            self._hit.append(
                (g, x, y, 22.0 * s.symbol_scale,
                 self._tip_for(g, true_lon, int(lagna // 30) % 12,
                               natal),
                 natal))
            if g in gand:
                painter.setPen(QPen(QColor(s.colors["retro"]), 2))
                painter.drawLine(int(x) - 6, int(y) + 16,
                                 int(x) + 6, int(y) + 16)
            if abs(disp_lon - true_lon) > 1e-9:
                tx, ty = project(true_lon, lagna, cx, cy, ring_r)
                painter.setPen(QPen(QColor(s.colors["ring"]), 1))
                painter.drawLine(int(tx), int(ty), int(x), int(y))

    def _paint_ruler(self, painter: QPainter, cx: float, cy: float,
                     radius: float, lagna: float):
        s = self.settings
        painter.setPen(QPen(QColor(s.colors["ring"]), 1))
        base = int(lagna // 30) * 30
        for step in range(0, 360, 5):
            lon = (base + step) % 360.0
            theta = math.radians(180.0 - (lon - lagna))
            wide = step % 30 == 0
            length = 8 if wide else 4
            x0 = cx + radius * math.cos(theta)
            y0 = cy - radius * math.sin(theta)
            x1 = cx + (radius - length) * math.cos(theta)
            y1 = cy - (radius - length) * math.sin(theta)
            painter.drawLine(int(x0), int(y0), int(x1), int(y1))

    def _paint_circles(self, painter: QPainter, cx: float, cy: float,
                       radius: float):
        s = self.settings
        painter.setPen(QPen(QColor(s.colors["ring"]), 1))
        # The sign segments leave a tinted brush behind; outlines only.
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for ratio in (s.hub_ratio, s.sign_ring_ratio, s.natal_ring_ratio,
                      s.transit_ring_ratio, 1.0):
            r = radius * ratio
            painter.drawEllipse(int(cx - r), int(cy - r),
                                int(2 * r), int(2 * r))
