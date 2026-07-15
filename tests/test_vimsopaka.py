"""Tests for Vimsopaka Bala computation."""

import pytest
from jhora.charts.chart import ChartBuilder
from jhora.calc.vimsopaka import (
    VimsopakaComputer, VimsopakaScheme, VimsopakaResult,
    _VIMSOPAKA_PLANETS,
)
from jhora.types.graha import Graha


def _chart():
    b = ChartBuilder()
    return b.build(1973, 3, 13, 13.0 + 55 / 60.0, 45.41, 11.88, tz="+0100")


class TestVimsopaka:
    def test_returns_7_planets(self):
        vc = VimsopakaComputer(_chart())
        results = vc.compute_all(VimsopakaScheme.SHADVARGA)
        assert len(results) == 7

    def test_all_scores_between_0_and_20(self):
        vc = VimsopakaComputer(_chart())
        for scheme in VimsopakaScheme:
            for r in vc.compute_all(scheme):
                assert 0 <= r.total <= 20, f"{r.graha.short_name} {scheme}: {r.total}"
                assert 0 <= r.percentage <= 100

    def test_components_have_correct_vargas(self):
        vc = VimsopakaComputer(_chart())
        r = vc.compute(Graha.SUN, VimsopakaScheme.SHADVARGA)
        vargas = {c.varga for c in r.components}
        expected = {"D_1", "D_2", "D_3", "D_7", "D_9"}
        assert vargas == expected

    def test_sun_scores_differ_by_scheme(self):
        vc = VimsopakaComputer(_chart())
        scores = {}
        for scheme in VimsopakaScheme:
            r = vc.compute(Graha.SUN, scheme)
            scores[scheme] = r.total
        assert len(set(scores.values())) >= 2

    def test_different_chart(self):
        b = ChartBuilder()
        cd = b.build(2026, 7, 7, 10.5, 13.08, 80.27, tz="+0530")
        vc = VimsopakaComputer(cd)
        results = vc.compute_all()
        assert len(results) == 7

    def test_planets_excluded(self):
        vc = VimsopakaComputer(_chart())
        for scheme in VimsopakaScheme:
            results = vc.compute_all(scheme)
            grahas_checked = {r.graha for r in results}
            assert Graha.RAHU not in grahas_checked
            assert Graha.KETU not in grahas_checked
