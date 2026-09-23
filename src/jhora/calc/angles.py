"""Longitudinal arithmetic utilities."""

from typing import Tuple


def normalize(lon: float) -> float:
    """Normalize longitude to [0, 360)."""
    return lon % 360.0


def diff(a: float, b: float) -> float:
    """Shortest arc between two longitudes (0-180)."""
    d = abs(normalize(a) - normalize(b))
    return min(d, 360.0 - d)


def signed_diff(a: float, b: float) -> float:
    """Signed difference a - b, normalized to [-180, 180)."""
    d = (normalize(a) - normalize(b)) % 360.0
    if d > 180.0:
        d -= 360.0
    return d


def add(lon: float, delta: float) -> float:
    """Add delta degrees to longitude, normalized."""
    return normalize(lon + delta)


def midpoint(a: float, b: float) -> float:
    """Midpoint (sunya) between two longitudes along the shortest arc."""
    d = signed_diff(b, a)
    return normalize(a + d / 2.0)


def aspect_angle(a: float, b: float) -> float:
    """Return aspect angle class: 0=conjunction, 60=sextile, 90=square, 120=trine, 180=opposition."""
    d = diff(a, b)
    if d < 8:      return 0    # conjunction
    if d < 52:     return 0    # no aspect
    if d < 68:     return 60   # sextile
    if d < 82:     return 0
    if d < 98:     return 90   # square
    if d < 112:    return 0
    if d < 128:    return 120  # trine
    if d < 172:    return 0
    if d < 188:    return 180  # opposition
    return 0


def is_aspected(planet_lon: float, target_lon: float,
                special_only: bool = False) -> bool:
    """Whether a planet aspects a target by the 7th-sign (whole-sign) rule.

    This is the common sign-based aspect; planet-specific special aspects
    (Mars 4/8, Jupiter 5/9, Saturn 3/10) live in :mod:`jhora.calc.drishti`,
    which is graha-aware. ``special_only`` is kept for signature
    compatibility and has no effect here.
    """
    from_sign = int(planet_lon // 30) % 12
    to_sign = int(target_lon // 30) % 12
    return to_sign == (from_sign + 6) % 12
