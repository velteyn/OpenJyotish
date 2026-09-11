"""Absolute-sky verification (offline replay).

Tropical longitudes vs JPL DE421 (independent Skyfield code path), Lahiri
anchor + rate pins, and mean-node theory check. No network, no extra
dependency at test time — fixtures carry the truth side.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha

FIXTURES = Path(__file__).resolve().parent.parent / "tools" / "xcheck" \
    / "fixtures" / "0.1.0"

GRAHA_BY_BODY = {"Sun": Graha.SUN, "Moon": Graha.MOON, "Mars": Graha.MARS,
                 "Mercury": Graha.MERCURY, "Jupiter": Graha.JUPITER,
                 "Venus": Graha.VENUS, "Saturn": Graha.SATURN}


def _load(cid):
    return json.loads((FIXTURES / f"{cid}.json").read_text())


def _chart_ids():
    return sorted(p.stem for p in FIXTURES.glob("*.json")
                  if p.stem != "index")


def _build(fix):
    b = fix["birth"]
    y, mo, d = (int(x) for x in b["date"].split("-"))
    return ChartBuilder().build(y, mo, d, b["hour"], lat=b["lat"],
                                lon=b["lon"], tz=b["tz_str"])


def _tropical(cd, graha):
    return (cd.planet(graha).longitude + cd.ayanamsa_value) % 360.0


@pytest.mark.parametrize("cid", _chart_ids())
def test_tropical_longitudes_match_jpl(cid):
    """Our tropicals vs JPL apparent place within 0.01° for every body.

    The residual is the explained mean-vs-apparent frame offset (measured
    <= 0.005°); anything larger is a real ephemeris/time-base error.
    """
    fix = _load(cid)
    cd = _build(fix)
    assert fix.get("tropical"), "fixture lacks JPL tropicals"
    for body, trop in fix["tropical"].items():
        ours = _tropical(cd, GRAHA_BY_BODY[body])
        delta = abs((ours - trop + 180.0) % 360.0 - 180.0)
        assert delta < 0.01, f"{body}: {delta:.5f}°"


def test_lahiri_anchor_at_j2000():
    """Lahiri ayanamsa at J2000 within 0.02° of the published 23.853°."""
    swe = SweEngine()
    swe.set_sidereal_mode("lahiri")
    assert abs(swe.get_ayanamsa(2451545.0) - 23.853) < 0.02


def test_lahiri_precession_rate():
    """Ayanamsa grows ~50.3 arcsec/year across 1973–2026 (within 1%)."""
    swe = SweEngine()
    swe.set_sidereal_mode("lahiri")
    a1973 = swe.get_ayanamsa(swe.julday(1973, 3, 13, 12.0))
    a2026 = swe.get_ayanamsa(swe.julday(2026, 7, 7, 12.0))
    rate = (a2026 - a1973) / ((swe.julday(2026, 7, 7, 12.0)
                               - swe.julday(1973, 3, 13, 12.0)) / 365.25)
    assert abs(rate * 3600.0 - 50.3) / 50.3 < 0.01


def _meeus_mean_node(jd):
    """Low-precision lunar ascending node (Meeus): independent theory path."""
    t = (jd - 2451545.0) / 36525.0
    return (125.04452 - 1934.136261 * t + 0.0020708 * t * t
            + t * t * t / 450000.0) % 360.0


@pytest.mark.parametrize("cid", _chart_ids())
def test_mean_node_matches_meeus_theory(cid):
    """Our Rahu is mean-node theory within 0.05° (separates mean from
    true/osculating confusion at degree scale)."""
    import swisseph as swe
    fix = _load(cid)
    swe_eng = SweEngine()
    y, mo, d = (int(x) for x in fix["birth"]["date"].split("-"))
    jd = swe_eng.julday(y, mo, d, 12.0)
    expected = _meeus_mean_node(jd)
    got = (swe_eng.calc_planet(swe.MEAN_NODE, jd).longitude
           + swe_eng.get_ayanamsa(jd)) % 360.0  # wrapper is sidereal
    delta = abs((got - expected + 180.0) % 360.0 - 180.0)
    assert delta < 0.05, f"node theory drift: {delta:.4f}°"
