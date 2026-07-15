"""Dasa timeline widget — interactive horizontal bar chart for PyQt6."""

from datetime import datetime
from typing import List, Optional

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtWidgets import QWidget

from jhora.charts.chart import ChartData
from jhora.dasas.vimsottari import VimsottariDasa


_PLANET_COLORS = {
    "Ketu": "#8b5cf6",
    "Venus": "#ec4899",
    "Sun": "#f59e0b",
    "Moon": "#e0e0e0",
    "Mars": "#ef4444",
    "Rahu": "#6366f1",
    "Jupiter": "#eab308",
    "Saturn": "#3b82f6",
    "Mercury": "#10b981",
}


class DasaTimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_data: Optional[ChartData] = None
        self._mds: List = []
        self._expanded_md_index: Optional[int] = None
        self._now = datetime.now()
        self.setMinimumHeight(250)
        self.setMouseTracking(True)

    def set_chart(self, cd: ChartData):
        self.chart_data = cd
        try:
            dasa = VimsottariDasa()
            chart_dict = {
                "planets": {g.value: {"longitude": p.longitude}
                            for g, p in cd.planets.items()},
                "lagna_lon": cd.ascendant,
            }
            self._mds = dasa.compute(cd.julian_day, chart_dict)
        except Exception:
            self._mds = []
        self.update()

    def paintEvent(self, event):
        if not self._mds:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width() - 140
        h = self.height() - 40
        y = 10
        bar_h = 22
        gap = 4

        # Calculate time span
        first = self._mds[0].start_date
        last = self._mds[-1].end_date
        total_secs = (last - first).total_seconds()

        # Draw each MD bar
        for i, md in enumerate(self._mds):
            start_secs = (md.start_date - first).total_seconds()
            end_secs = (md.end_date - first).total_seconds()
            x = int((start_secs / total_secs) * w)
            bw = max(2, int(((end_secs - start_secs) / total_secs) * w))

            color = QColor(_PLANET_COLORS.get(md.lord_name, "#666"))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawRoundedRect(QRectF(10 + x, y + i * (bar_h + gap), bw, bar_h), 4, 4)

            # Label
            p.setPen(QColor("#e0e0e0"))
            font = QFont("Segoe UI", 10)
            font.setBold(md.start_date <= self._now <= md.end_date)
            p.setFont(font)
            p.drawText(QRectF(0, y + i * (bar_h + gap), 130, bar_h),
                      Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                      md.lord_name)

            # Current marker
            if md.start_date <= self._now <= md.end_date:
                elapsed = (self._now - md.start_date).total_seconds()
                marker_x = 10 + x + int((elapsed / max(1, (end_secs - start_secs))) * bw)
                p.setPen(QPen(QColor("#ffffff"), 2))
                p.drawLine(marker_x, y + i * (bar_h + gap) - 3,
                          marker_x, y + i * (bar_h + gap) + bar_h + 3)
                p.setPen(QColor("#ffffff"))
                p.setFont(QFont("Segoe UI", 8))
                p.drawText(marker_x - 15, y + i * (bar_h + gap) + bar_h + 14, "NOW")

            # Age labels
            age_start = (md.start_date - self.chart_data.birth_date).total_seconds() / (365.25 * 86400) if self.chart_data else 0
            age_end = (md.end_date - self.chart_data.birth_date).total_seconds() / (365.25 * 86400) if self.chart_data else 0
            if bw > 40:
                p.setPen(QColor("#888"))
                p.setFont(QFont("Segoe UI", 7))
                p.drawText(QRectF(10 + x + 4, y + i * (bar_h + gap), bw - 8, bar_h),
                          Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                          f"age {age_start:.0f}")

            # Expanded AD bars
            if self._expanded_md_index == i:
                ad_y = y + (i + 1) * (bar_h + gap)
                ad_h = 14
                ads = md.sub_periods or []
                for j, ad in enumerate(ads):
                    ad_start = (ad.start_date - first).total_seconds()
                    ad_end = (ad.end_date - first).total_seconds()
                    ax = int((ad_start / total_secs) * w)
                    aw = max(1, int(((ad_end - ad_start) / total_secs) * w))
                    ac = QColor(_PLANET_COLORS.get(ad.lord_name, "#666"))
                    ac.setAlpha(150)
                    p.setBrush(QBrush(ac))
                    p.drawRoundedRect(QRectF(10 + ax, ad_y + j * (ad_h + 2), aw, ad_h), 2, 2)
                    if aw > 30:
                        p.setPen(QColor("#aaa"))
                        p.setFont(QFont("Segoe UI", 6))
                        p.drawText(QRectF(10 + ax + 2, ad_y + j * (ad_h + 2), aw - 4, ad_h),
                                  Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                  ad.lord_name)

        p.end()

    def mousePressEvent(self, event):
        if not self._mds:
            return
        y = event.pos().y()
        bar_h = 22
        gap = 4
        index = (y - 10) // (bar_h + gap)
        if 0 <= index < len(self._mds):
            if self._expanded_md_index == index:
                self._expanded_md_index = None
            else:
                self._expanded_md_index = index
            self.update()
