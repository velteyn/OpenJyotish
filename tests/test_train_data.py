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


def test_heldout_disjoint_from_train():
    from tools.train.build import heldout_charts
    train = sample_charts(300, seed=42, split="train")
    held = heldout_charts(42)
    t = {(d["year"], d["month"], d["day"], d["hour"]) for d in train}
    e = {(d["year"], d["month"], d["day"], d["hour"]) for d in held}
    assert len(held) == 200 and t.isdisjoint(e)


def test_manifest_gate():
    import pytest
    from tools.train.build import check_manifest
    check_manifest({"provenance": {"primer": 3, "engine-generated": 5}})
    with pytest.raises(ValueError):
        check_manifest({"provenance": {"private-extract": 1}})


def test_deterministic_pairs_verify_clean():
    from tools.train.draft import fact_recall_pairs
    from tools.train.filter import filter_pairs
    cd = _chart0()
    from tools.train.facts import chart_facts
    pairs = fact_recall_pairs(chart_facts(cd))
    for p in pairs:
        p["chart_key"] = "k"
    kept, rejected = filter_pairs(pairs, {"k": cd})
    assert rejected == [] and len(kept) == len(pairs)


def test_lmstudio_call_needs_v1(monkeypatch):
    """LM Studio 200s unknown endpoints — caller must target /v1 and
    surface error bodies instead of returning empty drafts."""
    import requests
    from tools.train.draft import lmstudio_call
    seen = {}

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"error": "Unexpected endpoint or method."}

    def fake_post(url, **kw):
        seen["url"] = url
        return _Resp()

    monkeypatch.setattr(requests, "post", fake_post)
    import pytest
    with pytest.raises(ValueError):
        lmstudio_call("http://x:1234", "m")([{"role": "user",
                                              "content": "hi"}])
    assert seen["url"] == "http://x:1234/v1/chat/completions"


def test_primer_sections_parse():
    from tools.train.draft import primer_sections
    secs = primer_sections()
    assert len(secs) >= 30
    assert all(s["source"].startswith("Primer") for s in secs)
    assert all(s["body"].strip() for s in secs)
    assert any("NINE GRAHAS" in s["title"] for s in secs)


def test_primer_qa_pairs_grounded_and_clean():
    from tools.train.draft import primer_qa_pairs
    from tools.train.filter import filter_pairs
    pairs = primer_qa_pairs()
    assert pairs and all(p["provenance"] == "primer" for p in pairs)
    assert all(p["kind"] == "qa" and p["passage"] for p in pairs)
    for p in pairs:
        answer = p["messages"][-1]["content"]
        assert answer.rstrip().endswith(f"[{p['source']}]")
    kept, rejected = filter_pairs(pairs, {})
    assert rejected == [] and len(kept) == len(pairs)


def test_qa_filter_rejects_bad_citation():
    from copy import deepcopy
    from tools.train.draft import primer_qa_pairs
    from tools.train.filter import filter_pair
    pair = deepcopy(primer_qa_pairs()[0])
    pair["messages"][-1]["content"] = "A confident but uncited claim."
    ok, reasons = filter_pair(pair, None)
    assert not ok and "citation" in reasons[0]


def test_qa_filter_rejects_ungrounded_answer():
    from copy import deepcopy
    from tools.train.draft import primer_qa_pairs
    from tools.train.filter import filter_pair
    pair = deepcopy(primer_qa_pairs()[0])
    pair["passage"] = "This sentence appears in no bundled book at all."
    pair["messages"][-1]["content"] = (
        pair["passage"] + f"\n\n[{pair['source']}]")
    ok, reasons = filter_pair(pair, None)
    assert not ok and "grounded" in reasons[0]


_QUOTE_MARKER = "detector reports, verbatim:"


def _quote_line(y):
    """One detector result as the primers quote it.

    Regenerate a quote with:
    ``for y in detect_all(cd): print(_quote_line(y))``
    """
    return f"{y.name} [{y.strength}] — {y.description}."


def _quote_blocks():
    """Every 'detector reports, verbatim:' block in the primers."""
    from tools.train.draft import PRIMER_DIR
    blocks = []
    for path in sorted(PRIMER_DIR.glob("primer-*.txt")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if _QUOTE_MARKER not in line:
                continue
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            block = []
            while j < len(lines) and lines[j].strip():
                block.append(lines[j])
                j += 1
            blocks.append((path.name, " ".join(" ".join(block).split())))
    return blocks


def test_primer_yoga_quote_matches_detector():
    """Verbatim yoga quotes in the primers must match detect_all (#285)."""
    from jhora.calc.yogas import detect_all
    from jhora.charts.chart import ChartBuilder
    cd = ChartBuilder().build(
        year=1990, month=1, day=15, hour=17.5,
        lat=12.9716, lon=77.5946, tz="+0530")
    expected = " ".join(_quote_line(y) for y in detect_all(cd))
    blocks = _quote_blocks()
    assert blocks, f"no '{_QUOTE_MARKER}' block found in the primers"
    for name, quoted in blocks:
        assert quoted, f"{name}: empty verbatim block"
        assert quoted == expected, f"{name}: stale detector quote"
