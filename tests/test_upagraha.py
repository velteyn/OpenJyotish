"""Tests for compute_all_upagrahas wiring (solar + temporal bundle)."""

import datetime

from jhora.calc.muhurta import _sunrise_sunset
from jhora.calc.upagraha import (
    compute_all_upagrahas,
    compute_solar_upagrahas,
    compute_temporal_upagrahas,
)
from jhora.charts.chart import ChartBuilder


def _jalkot():
    return ChartBuilder().build(
        2001, 2, 24, 6 + 11 / 60,
        lat=18 + 38 / 60, lon=77 + 12 / 60, tz="+0530",
    )


class TestComputeAll:
    def test_includes_solar_and_temporal(self):
        names = {r.name for r in compute_all_upagrahas(_jalkot())}
        assert {"Dhuma", "Vyatipata", "Parivesha",
                "Indrachaapa", "Upaketu"} <= names
        assert {"Gulika", "Mandi"} <= names

    def test_temporal_matches_direct_call(self):
        # compute_all_upagrahas must wire sunrise/sunset identically to the
        # direct temporal call used by the sphuta reference tests.
        cd = _jalkot()
        sr, ss = _sunrise_sunset(
            datetime.datetime(2001, 2, 24), 18 + 38 / 60, 77 + 12 / 60, 5.5)
        direct = {r.name: r.longitude
                  for r in compute_temporal_upagrahas(cd, sr, ss)}
        via_all = {r.name: r.longitude for r in compute_all_upagrahas(cd)
                   if r.source == "temporal"}
        assert set(via_all) == set(direct)
        for name, lon in direct.items():
            assert via_all[name] == lon == direct[name]

    def test_solar_unaffected(self):
        cd = _jalkot()
        from jhora.types.graha import Graha
        solar = {r.name: r.longitude
                 for r in compute_solar_upagrahas(
                     cd.planet(Graha.SUN).longitude)}
        via_all = {r.name: r.longitude for r in compute_all_upagrahas(cd)
                   if r.source == "solar"}
        assert via_all == solar
