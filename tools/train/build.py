"""Dataset builder: sample -> facts -> draft -> filter -> manifest.

Orchestrates the public-tier pipeline (spec tasks 1.5, 1.6):

- train charts come ONLY from the train split; the fixed held-out eval set
  (eval split, separate seed stream) is never drafted into training output.
- every pair carries provenance in {primer, pd-classic, engine-generated};
  the manifest records counts + dataset hash, and ``check_manifest`` rejects
  anything else (CI gate).
- without ``--lmstudio``, only deterministic fact-recall pairs are emitted
  (no LLM needed); with it, readings are drafted live and filtered.

Usage:
  PYTHONPATH=. python3 tools/train/build.py --n 50 --seed 42 --out /tmp/ds
  PYTHONPATH=. python3 tools/train/build.py --n 50 --lmstudio \\
      http://100.106.227.22:1234 --model mistralai/ministral-3-14b-reasoning
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

ALLOWLIST = ("primer", "pd-classic", "engine-generated")
EVAL_N = 200


def heldout_charts(seed: int = 42, n: int = EVAL_N):
    """Fixed eval chart set (disjoint from train by construction)."""
    from tools.train.sample import sample_charts
    return sample_charts(n, seed=seed, split="eval")


def check_manifest(manifest: dict) -> None:
    """CI gate: public-tier provenance only (spec task 1.5)."""
    bad = [p for p in manifest.get("provenance", {})
           if p not in ALLOWLIST]
    if bad:
        raise ValueError(f"non-public-tier provenance: {bad}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the training dataset")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lmstudio", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--max-readings", type=int, default=0,
                    help="LLM-drafted readings (0 = deterministic only)")
    ap.add_argument("--repair", action="store_true",
                    help="repair flagged drafts via the model before filtering")
    ap.add_argument("--rounds", type=int, default=2,
                    help="repair rounds per draft (offline: time is cheap)")
    args = ap.parse_args()

    from jhora.charts.chart import ChartBuilder
    from tools.train.draft import (fact_recall_pairs, draft_reading,
                                   engine_call)
    from tools.train.facts import chart_facts
    from tools.train.filter import filter_pairs
    from tools.train.sample import sample_charts

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    eval_keys = {
        (d["year"], d["month"], d["day"], d["hour"])
        for d in heldout_charts(args.seed)
    }
    call_fn = (engine_call(args.lmstudio, args.model)
               if args.lmstudio and args.model else None)

    charts, raw = {}, []
    drafted = 0
    for bd in sample_charts(args.n, seed=args.seed, split="train"):
        key = (bd["year"], bd["month"], bd["day"], bd["hour"])
        assert key not in eval_keys, "eval chart leaked into train output"
        cd = ChartBuilder().build(**bd)
        ckey = f"{bd['year']}-{bd['month']:02d}-{bd['day']:02d} " \
               f"{bd['hour']:.4f} {bd['lat']} {bd['lon']}"
        charts[ckey] = cd
        facts = chart_facts(cd)
        for pair in fact_recall_pairs(facts):
            pair["chart_key"] = ckey
            raw.append(pair)
        if call_fn is not None and drafted < args.max_readings:
            try:
                pair = draft_reading(facts, call_fn)
                pair["chart_key"] = ckey
                if args.repair:
                    from jhora.ai.repair import repair_answer
                    best, _v = repair_answer(
                        pair["messages"][2]["content"], cd, None,
                        call_fn=lambda msgs: call_fn(msgs),
                        max_rounds=args.rounds,
                        notify_fn=lambda m: print("   ",
                                                  m.strip()[:80]))
                    pair["messages"][2]["content"] = best
                raw.append(pair)
                drafted += 1
            except Exception as e:
                print(f"  draft failed for {ckey}: {e}")
    kept, rejected = filter_pairs(raw, charts, log=print)

    prov: dict = {}
    for p in kept:
        prov[p["provenance"]] = prov.get(p["provenance"], 0) + 1
    blob = "".join(json.dumps(p["messages"], sort_keys=True) for p in kept)
    manifest = {
        "n_charts": args.n, "seed": args.seed,
        "n_raw": len(raw), "n_kept": len(kept),
        "n_rejected": len(rejected),
        "provenance": prov,
        "eval_charts": EVAL_N, "eval_seed": args.seed,
        "dataset_hash": hashlib.sha256(blob.encode()).hexdigest()[:16],
    }
    check_manifest(manifest)
    (out / "pairs.jsonl").write_text(
        "\n".join(json.dumps(p) for p in kept), encoding="utf-8")
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"charts={args.n} raw={len(raw)} kept={len(kept)} "
          f"rejected={len(rejected)} hash={manifest['dataset_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
