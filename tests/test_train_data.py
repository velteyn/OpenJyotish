"""Tests for training-data sampler + fact emitter (no LLM needed)."""

import calendar

from tools.train.facts import chart_facts, facts_schema
from tools.train.sample import coverage, sample_charts


def test_sampler_deterministic():
    assert sample_charts(50, seed=7) == sample_charts(50, seed=7)
    assert sample_charts(50, seed=7) != sample_charts(50, seed=8)


def test_sampler_splits_disjoint():
    train = sample_charts(200, seed=42, split="train")
    eval_ = sample_charts(200, seed=42, split="eval")
    t = {(d["year"], d["month"], d["day"], d["hour"]) for d in train}
    e = {(d["year"], d["month"], d["day"], d["hour"]) for d in eval_}
    assert t.isdisjoint(e)


def test_sampler_valid_ranges():
    import re
    for d in sample_charts(200, seed=99):
        assert 1940 <= d["year"] <= 2010
        assert 1 <= d["day"] <= calendar.monthrange(d["year"], d["month"])[1]
        assert 0 <= d["hour"] < 24
        assert -60 <= d["lat"] <= 60 and d["lat"] != 0
        assert -180 <= d["lon"] <= 180
        assert re.fullmatch(r"[+-]\d{4}", d["tz"])


def test_sampler_invalid_split():
    import pytest
    with pytest.raises(ValueError):
        sample_charts(5, split="test")


def test_coverage_full():
    cov = coverage(sample_charts(120, seed=42))
    assert len(cov["lagna"]) == 12
    assert len(cov["moon"]) == 12
    assert len(cov["md_lord"]) == 9


def _chart0():
    from jhora.charts.chart import ChartBuilder
    return ChartBuilder().build(**sample_charts(1, seed=42)[0])


def test_facts_schema():
    f = chart_facts(_chart0())
    assert sorted(f.keys()) == sorted(facts_schema())
    assert len(f["placements"]) == 9
    assert len(f["house_lords"]) == 12
    assert len(f["vimsottari"]) == 9
    assert all(len(m["antardashas"]) == 9 for m in f["vimsottari"])
    assert isinstance(f["yogas"], list)
    p = f["placements"][0]
    assert set(p) == {"planet", "sign", "deg_in_sign", "nakshatra",
                      "pada", "house", "retrograde"}


def test_facts_deterministic():
    cd = _chart0()
    assert chart_facts(cd) == chart_facts(cd)
