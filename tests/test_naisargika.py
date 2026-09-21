"""Tests for Naisargika Dasa (fixed natural ages, Varahamihira).

No balance, no start computation: Moon 0-1, Mars 1-3, Mercury 3-12,
Venus 12-32, Jupiter 32-50, Sun 50-70, Saturn 70-120. The Yavana
Lagna period is excluded per the mainstream objection.
"""

import pytest

from jhora.dasas.base import DasaOptions
from jhora.dasas.naisargika import NaisargikaDasa
from jhora.types.dasa import PeriodLevel


def test_fixed_boundaries():
    mds = NaisargikaDasa().compute(2460000.0, {})
    assert [(m.lord_name, m.duration_years) for m in mds] == [
        ("Moon", 1.0), ("Mars", 2.0), ("Mercury", 9.0), ("Venus", 20.0),
        ("Jupiter", 18.0), ("Sun", 20.0), ("Saturn", 50.0)]
    assert sum(m.duration_years for m in mds) == 120.0
    assert mds[0].start_jd == 2460000.0
    assert all(abs(a.end_jd - b.start_jd) < 1e-9
               for a, b in zip(mds, mds[1:]))


def test_no_lagna_period():
    mds = NaisargikaDasa().compute(2460000.0, {})
    assert all(m.lord_name != "Lagna" for m in mds)


def test_running_period_by_age():
    mds = NaisargikaDasa().compute(2460000.0, {})

    def at(age_years):
        jd = 2460000.0 + age_years * 365.2425
        return next(m.lord_name for m in mds if m.start_jd <= jd < m.end_jd)

    assert at(0.5) == "Moon"
    assert at(40) == "Jupiter"
    assert at(75) == "Saturn"


def test_ads_proportional_from_md_lord():
    mds = NaisargikaDasa().compute(2460000.0, {})
    sun_ads = [m for m in mds if m.lord_name == "Sun"][0].sub_periods
    assert sun_ads[0].lord_name == "Sun"
    assert len(sun_ads) == 7
    assert sum(a.duration_years for a in sun_ads) == pytest.approx(20.0)


def test_year_definition_option():
    mds = NaisargikaDasa(DasaOptions(
        year_definition="savana",
        subdivision_level=PeriodLevel.MAHADASA,
        include_subperiods=False)).compute(2460000.0, {})
    assert mds[0].end_jd - mds[0].start_jd == 360.0


def test_cli_dasa_naisargika_runs():
    from typer.testing import CliRunner
    from jhora.cli.main import app
    out = CliRunner().invoke(
        app, ["dasa", "1990-01-15 17:30:00 +0530 12.9716 77.5946",
              "naisargika"])
    assert out.exit_code == 0, out.output
    assert "Naisargika" in out.stdout
