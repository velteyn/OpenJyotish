"""Headless wheel math: settings, Lagna-left projection, declutter.

No Qt here — pure geometry the widget paints. Angles in degrees,
longitudes 0-360 sidereal; screen convention handled by the widget.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class WheelSettings:
    """Radii ratios, scale, colors and toggles for the wheel."""

    symbol_scale: float = 1.0
    collision_radius_px: float = 10.0
    natal_ring_ratio: float = 0.78
    transit_ring_ratio: float = 0.94
    sign_ring_ratio: float = 0.62
    hub_ratio: float = 0.45
    show_drishti: bool = True
    show_nodes: bool = True
    show_transits: bool = True
    show_sign_colors: bool = True
    colors: Dict[str, str] = field(default_factory=lambda: {
        "background": "#1a1a2e",
        "ring": "#8a8aa0",
        "benefic": "#ffd700",
        "malefic": "#ff6b6b",
        "transit": "#7a9cc6",
        "retro": "#ff4444",
        "dim": "#555566",
        "drishti_benefic": "#3a7d3a",
        "drishti_malefic": "#7d3a3a",
        "text": "#ffffff",
    })


def screen_angle(lon: float, lagna: float) -> float:
    """Screen degrees for a longitude with lagna at 9 o'clock (180°)."""
    return (180.0 - (lon - lagna)) % 360.0


def project(lon: float, lagna: float, cx: float, cy: float,
            r: float) -> Tuple[float, float]:
    """Screen point for a longitude (Qt y-down convention)."""
    theta = math.radians(screen_angle(lon, lagna))
    return cx + r * math.cos(theta), cy - r * math.sin(theta)


def min_separation_deg(collision_px: float, radius_px: float) -> float:
    """Angular separation keeping two glyph discs apart on a ring."""
    if radius_px <= 0:
        return 360.0
    return math.degrees(2.0 * math.asin(
        min(1.0, collision_px / radius_px)))


def _circular_gap(a: float, b: float) -> float:
    return (b - a) % 360.0


def declutter(items: List[Tuple[str, float]], min_sep_deg: float,
              step: float = 0.5,
              max_passes: int = 720) -> List[Tuple[str, float, float, bool]]:
    """Fan crowded glyphs apart along the ring.

    Returns [(key, display_lon, true_lon, overflow)]; display order
    preserves true-longitude order; leader ticks connect display back
    to true. When the arc cannot fit even after max_passes, every
    entry is flagged overflow (caller falls back to abbreviations).
    """
    if not items:
        return []
    order = sorted(items, key=lambda kv: kv[1])
    display = [lon for _, lon in order]
    n = len(order)
    if n == 1:
        return [(order[0][0], display[0], order[0][1], False)]
    passes = 0
    while passes < max_passes:
        clash = False
        for i in range(n):
            j = (i + 1) % n
            if _circular_gap(display[i], display[j]) < min_sep_deg:
                clash = True
                display[i] = (display[i] - step) % 360.0
                display[j] = (display[j] + step) % 360.0
        if not clash:
            return [(order[i][0], display[i], order[i][1], False)
                    for i in range(n)]
        passes += 1
    return [(order[i][0], display[i], order[i][1], True)
            for i in range(n)]
