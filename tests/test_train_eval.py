"""Tests for the adapter eval harness + training recipe (no LLM/GPU)."""

import hashlib
import json

from tools.train.eval_adapter import (
    clean_answer,
    compare_reports,
    noisy_answer,
    run_eval,
)


def _eval(mode, n=3, seed=42, tag="t"):
    draft = clean_answer if mode == "clean" else noisy_answer
    return run_eval(draft, seed, n, f"mock-{mode}", tag)


def test_mock_clean_scores_zero_flags():
    r = _eval("clean")
    assert r["n_readings"] == 3
    assert r["total_flags"] == 0
    assert r["total_checked"] > 0
    assert r["citation_genuineness"] == 1.0
    assert all(row["flags"] == 0 for row in r["rows"])


def test_mock_noisy_scores_flags():
    r = _eval("noisy")
    assert r["total_flags"] > 0
    assert r["flag_rate"] > 0
    assert r["citation_genuineness"] < 1.0
    assert any("citation" in row["flag_kinds"] for row in r["rows"])


def test_mock_eval_deterministic():
    assert _eval("clean")["report_hash"] == _eval("clean")["report_hash"]
    a, b = _eval("noisy"), _eval("noisy")
    assert a["total_flags"] == b["total_flags"]


def test_ship_gate():
    base, cand = _eval("noisy"), _eval("clean")
    ship, _ = compare_reports(base, cand)
    assert ship
    for b, c in ((cand, base), (cand, cand), (base, base)):
        ship, reasons = compare_reports(b, c)
        assert not ship, reasons


def test_ship_gate_rejects_worse_citations():
    base = {"total_flags": 10, "citation_genuineness": 1.0}
    cand = {"total_flags": 5, "citation_genuineness": 0.5}
    ship, _ = compare_reports(base, cand)
    assert not ship


def test_recipe_config_validation():
    import argparse
    from tools.train.recipe.train_unsloth import build_train_config
    ns = argparse.Namespace(base="unsloth/qwen3-8b", rank=16, epochs=2,
                            max_seq_len=2048, batch=2, accum=4, lr=2e-4,
                            seed=3407, out="/tmp/x")
    cfg = build_train_config(ns)
    assert cfg["lora_alpha"] == 16 and len(cfg["target_modules"]) == 7
    import pytest
    for bad in (8, 64):
        with pytest.raises(ValueError):
            build_train_config(argparse.Namespace(**{**vars(ns),
                                                     "rank": bad}))


def test_recipe_dataset_hash_gate(tmp_path):
    from tools.train.recipe.train_unsloth import check_dataset
    rows = [{"messages": [{"role": "user", "content": "q"},
                          {"role": "assistant", "content": "a"}],
             "provenance": "primer"}]
    (tmp_path / "pairs.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows))
    blob = "".join(json.dumps(r["messages"], sort_keys=True) for r in rows)
    (tmp_path / "manifest.json").write_text(json.dumps(
        {"dataset_hash": hashlib.sha256(blob.encode()).hexdigest()[:16],
         "provenance": {"primer": 1}}))
    assert check_dataset(tmp_path)["provenance"] == {"primer": 1}
    (tmp_path / "manifest.json").write_text(json.dumps(
        {"dataset_hash": "deadbeefdeadbeef"}))
    import pytest
    with pytest.raises(ValueError):
        check_dataset(tmp_path)
