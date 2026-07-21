"""Tests for Kuja Dosha calculation."""
import pytest
from jhora.charts.chart import ChartBuilder
from jhora.calc.kuja_dosha import compute_kuja_dosha


def _build(year, month, day, hour, lat, lon, tz="+0530"):
    return ChartBuilder().build(year, month, day, hour, lat, lon, tz)


def test_no_dosha_mars_in_clean_house():
    """Mars in H6 from Lagna — not a dosha house."""
    cd = _build(1973, 3, 14, 14.92, 45.41, 11.88, "+0100")
    r = compute_kuja_dosha(cd)
    assert not r.has_dosha
    assert not r.from_lagna


def test_mars_own_sign_cancels():
    """Mars in own sign (Scorpio) weakens the dosha even if in dosha house."""
    cd = _build(1990, 1, 1, 6, 28.6, 77.2)
    r = compute_kuja_dosha(cd)
    assert r.from_lagna  # Mars in 12th
    assert r.mars_own_sign
    assert not r.has_dosha  # cancelled by own sign


def test_kuja_dosha_present():
    """Chart where Mars afflicts Moon and Venus."""
    cd = _build(2000, 8, 1, 12, 28.6, 77.2)
    r = compute_kuja_dosha(cd)
    assert r.has_dosha
    assert r.from_moon or r.from_venus


def test_dosha_houses_set():
    """Verify the classical dosha houses: 1, 2, 4, 7, 8, 12."""
    from jhora.calc.kuja_dosha import _KUJA_HOUSES
    assert _KUJA_HOUSES == {1, 2, 4, 7, 8, 12}


def test_house_from_mars():
    """Test house calculations."""
    from jhora.calc.kuja_dosha import _house_from
    # Planet at 30 degrees from reference = H2
    assert _house_from(0, 30) == 2
    # Planet at same position = H1
    assert _house_from(0, 5) == 1
    assert _house_from(100, 100.5) == 1
    assert _house_from(0, 350) == 12
