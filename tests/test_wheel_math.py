"""Tests for headless wheel math — projection, separation, declutter."""

import math

from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha
from jhora.ui.wheel_math import (WheelSettings, declutter,
                                 min_separation_deg, project, screen_angle)


class TestSettings:
    def test_defaults(self):
        s = WheelSettings()
        assert s.symbol_scale == 1.0
        assert s.show_drishti and s.show_nodes and s.show_transits
        assert s.colors["benefic"]


class TestProjection:
    def test_lagna_at_nine_oclock(self):
        assert screen_angle(311.0, 311.0) == 180.0

    def test_counterclockwise(self):
        # Higher longitude reads counterclockwise from lagna.
        a = screen_angle(320.0, 311.0)
        assert a == 171.0

    def test_jalkot_project(self):
        cd = ChartBuilder().build(2001, 2, 24, 6 + 11 / 60,
                                  lat=18 + 38 / 60, lon=77 + 12 / 60,
                                  tz="+0530", ayanamsa="lahiri")
        x, y = project(cd.ascendant, cd.ascendant, 200.0, 200.0, 100.0)
        assert abs(x - 100.0) < 1e-9 and abs(y - 200.0) < 1e-9


class TestSeparation:
    def test_geometry(self):
        # 20px discs on a 200px ring need ~11.5 degrees.
        assert abs(min_separation_deg(20.0, 200.0) - 11.48) < 0.05


class TestDeclutter:
    def test_no_clash_untouched(self):
        items = [(Graha.SUN, 10.0), (Graha.MOON, 100.0),
                 (Graha.MARS, 200.0)]
        out = declutter([(g.short_name, lon) for g, lon in items], 5.0)
        assert [(k, d, t, o) for k, d, t, o in out] == [
            ("Su", 10.0, 10.0, False), ("Mo", 100.0, 100.0, False),
            ("Ma", 200.0, 200.0, False)]

    def test_close_pair_fans_out(self):
        out = declutter([("Ju", 31.0), ("Sa", 31.06)], 4.0)
        by_key = {k: (d, t, o) for k, d, t, o in out}
        assert by_key["Ju"][2] is False
        gap = (by_key["Sa"][0] - by_key["Ju"][0]) % 360.0
        assert gap >= 4.0
        # True longitudes preserved for leader ticks.
        assert by_key["Ju"][1] == 31.0 and by_key["Sa"][1] == 31.06

    def test_order_preserved(self):
        out = declutter([("A", 10.0), ("B", 10.5), ("C", 11.0)], 4.0)
        assert [k for k, _, _, _ in out] == ["A", "B", "C"]

    def test_overflow_flags(self):
        items = [(f"P{i}", 10.0 + i * 0.1) for i in range(30)]
        out = declutter(items, 10.0, max_passes=10)
        assert all(o for _, _, _, o in out)

    def test_wraparound(self):
        out = declutter([("A", 359.0), ("B", 0.5)], 4.0)
        assert all(o is False for _, _, _, o in out)
