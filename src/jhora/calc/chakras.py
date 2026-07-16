"""Chakras — Vedic astrological diagrams for transit and prasna analysis.

Sarvatobhadra Chakra: 9×9 grid of nakshatras used for transit impact,
vedha (obstruction) analysis, and prasna. Each of the 27 nakshatras
appears once, arranged in a specific order from NE to SW.

The grid is:
  4  5  6  7  8  9  1  2  3 (top row = beginning of nakshatra cycle)
  3  4  5  6  7  8  9  1  2
  2  3  4  5  6  7  8  9  1
  1  2  3  4  5  6  7  8  9
  9  1  2  3  4  5  6  7  8
  8  9  1  2  3  4  5  6  7
  7  8  9  1  2  3  4  5  6
  6  7  8  9  1  2  3  4  5
  5  6  7  8  9  1  2  3  4

Vedha lines: N-S, E-W, NE-SW, NW-SE from each cell show
which nakshatras obstruct (vedha) the target nakshatra.
"""

from dataclasses import dataclass
from typing import List, Optional, Set, Tuple


# Sarvatobhadra: 9×9 encoded as rows of nakshatra indices (0-26)
# Reading order: top-left is NE, each row goes E→W, rows go S
# The grid maps nakshatras cyclically from NE corner
_SARVATOBHADRA = [
    [26, 0, 1, 2, 3, 4, 5, 6, 7],
    [25, 26, 0, 1, 2, 3, 4, 5, 6],
    [24, 25, 26, 0, 1, 2, 3, 4, 5],
    [23, 24, 25, 26, 0, 1, 2, 3, 4],
    [22, 23, 24, 25, 26, 0, 1, 2, 3],
    [21, 22, 23, 24, 25, 26, 0, 1, 2],
    [20, 21, 22, 23, 24, 25, 26, 0, 1],
    [19, 20, 21, 22, 23, 24, 25, 26, 0],
    [18, 19, 20, 21, 22, 23, 24, 25, 26],
]

# Vedha directions: (dr, dc) offsets for each target cell
_VEDHA_DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),  # N, NE, NW
    (0, -1), (0, 1),              # E, W
    (1, -1), (1, 0), (1, 1),      # S, SE, SW
]

_NAK_NAMES = [
    "Asvini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]


def _find_nakshatra_pos(nak_idx: int) -> Optional[Tuple[int, int]]:
    """Find the (row, col) of a nakshatra in the Sarvatobhadra grid."""
    for r in range(9):
        for c in range(9):
            if _SARVATOBHADRA[r][c] == nak_idx:
                return (r, c)
    return None


def sarvatobhadra_grid() -> List[List[str]]:
    """Return 9×9 grid as nakshatra short names."""
    return [[_NAK_NAMES[idx][:4] for idx in row] for row in _SARVATOBHADRA]


def sarvatobhadra_vedha(target_nak: int) -> List[dict]:
    """Find which nakshatras obstruct (vedha) the target nakshatra.

    Vedha = any nakshatra in the same row, column, or diagonal.
    """
    pos = _find_nakshatra_pos(target_nak)
    if pos is None:
        return []
    r, c = pos
    vedha = []
    for dr, dc in _VEDHA_DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 9 and 0 <= nc < 9:
            v_idx = _SARVATOBHADRA[nr][nc]
            direction = {
                (-1, -1): "NW", (-1, 0): "N", (-1, 1): "NE",
                (0, -1): "W", (0, 1): "E",
                (1, -1): "SW", (1, 0): "S", (1, 1): "SE",
            }[(dr, dc)]
            vedha.append({
                "nakshatra": v_idx,
                "name": _NAK_NAMES[v_idx],
                "direction": direction,
            })
    return vedha


def sarvatobhadra_text() -> str:
    """Render the Sarvatobhadra chakra as a text table."""
    lines = ["Sarvatobhadra Chakra (9×9 nakshatra grid)", "─" * 45]
    for row in _SARVATOBHADRA:
        cells = [f"{_NAK_NAMES[idx][:4]:>5}" for idx in row]
        lines.append("".join(cells))
    lines.append("")
    lines.append("Vedha: any nakshatra in same row/col/diagonal obstructs the target.")
    return "\n".join(lines)


# ── Kota Chakra ──────────────────────────────────────────────────────────────

def kota_chakra(target_nak: int = 0) -> str:
    """Kota Chakra (Fort chart) — 4 concentric squares centered on target nakshatra.

    Inner = target, then 8 surrounding, then 16, then 24.
    """
    pos = _find_nakshatra_pos(target_nak)
    if pos is None:
        return "Nakshatra not in grid"
    r, c = pos
    lines = [f"Kota Chakra — centered on {_NAK_NAMES[target_nak]} ({target_nak})", "─" * 40]
    # Ring 1: inner circle = center only
    center = f"[{_NAK_NAMES[target_nak][:4]}]"
    lines.append(f"      {center}")
    # Ring 2: 8 surrounding (vedha positions)
    ring2 = []
    for dr in range(-1, 2):
        for dc in range(-1, 2):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < 9 and 0 <= nc < 9:
                ring2.append(_NAK_NAMES[_SARVATOBHADRA[nr][nc]][:4])
    lines.append("  " + "  ".join(ring2[:4]))
    lines.append("  " + "  ".join(ring2[4:]))
    return "\n".join(lines)
