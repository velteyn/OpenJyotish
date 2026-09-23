"""Tests for the dasa chart (the running period tree at a glance)."""

from datetime import datetime

from jhora.calc.dasa_chart import (
    LEVEL_NAMES,
    dasa_chart,
    dasa_chart_rows,
    format_dasa_chart,
)
from jhora.dasas.vimsottari import VimsottariDasa


def _periods(cd):
    chart = {
        "planets": {g.value: {"longitude": p.longitude}
                    for g, p in cd.planets.items()},
        "lagna_lon": cd.ascendant,
    }
    return VimsottariDasa().compute(cd.julian_day, chart)


class TestDasaChartRows:
    def test_all_mahadasas_listed(self, ref_chart):
        rows = dasa_chart_rows(_periods(ref_chart),
                               ref_chart.julian_day + 100)
        md = [r for r in rows if r.depth == 0]
        assert len(md) == 9

    def test_exactly_one_active_per_level(self, ref_chart):
        rows = dasa_chart_rows(_periods(ref_chart),
                               ref_chart.julian_day + 365 * 30)
        for depth in {r.depth for r in rows}:
            active = [r for r in rows if r.depth == depth and r.active]
            assert len(active) == 1

    def test_running_branch_is_expanded(self, ref_chart):
        rows = dasa_chart_rows(_periods(ref_chart),
                               ref_chart.julian_day + 365 * 30, depth=3)
        assert {r.depth for r in rows} == {0, 1, 2}
        for depth in (1, 2):
            assert len([r for r in rows if r.depth == depth]) == 9

    def test_active_child_nests_in_parent(self, ref_chart):
        rows = dasa_chart_rows(_periods(ref_chart),
                               ref_chart.julian_day + 365 * 30, depth=3)
        active = {r.depth: r for r in rows if r.active}
        for depth in (1, 2):
            child, parent = active[depth], active[depth - 1]
            assert parent.start_jd <= child.start_jd
            assert child.end_jd <= parent.end_jd + 1e-6

    def test_depth_one_is_mahadasas_only(self, ref_chart):
        rows = dasa_chart_rows(_periods(ref_chart),
                               ref_chart.julian_day + 100, depth=1)
        assert {r.depth for r in rows} == {0}

    def test_level_names(self, ref_chart):
        rows = dasa_chart_rows(_periods(ref_chart),
                               ref_chart.julian_day + 365 * 30, depth=3)
        assert {r.level for r in rows} == set(LEVEL_NAMES[:3])


class TestDasaChart:
    def test_deterministic_for_a_date(self, ref_chart):
        when = datetime(2026, 9, 23)
        a = dasa_chart(ref_chart, when=when)
        b = dasa_chart(ref_chart, when=when)
        assert [(r.lord, r.active) for r in a] == [(r.lord, r.active) for r in b]

    def test_format_marks_active(self, ref_chart):
        text = format_dasa_chart(dasa_chart(ref_chart, when=datetime(2026, 9, 23)))
        assert "◀" in text
        assert "[Mahadasa]" in text


class TestDasaChartPaths:
    def test_md_row_path_is_single_lord(self, ref_chart):
        rows = dasa_chart_rows(_periods(ref_chart),
                               ref_chart.julian_day + 365 * 30, depth=3)
        for r in [x for x in rows if x.depth == 0]:
            assert r.path == (r.lord,)

    def test_child_path_extends_active_parent(self, ref_chart):
        rows = dasa_chart_rows(_periods(ref_chart),
                               ref_chart.julian_day + 365 * 30, depth=3)
        active = {r.depth: r for r in rows if r.active}
        for depth in (1, 2):
            child, parent = active[depth], active[depth - 1]
            assert child.path == parent.path + (child.lord,)
