"""Adapter eval: verifier flag-rate + citation genuineness, held-out charts.

Scores any chat model (base or adapter) by running the SAME reading prompt
the dataset drafter uses (``draft_reading``: engine facts + RESTATE-only
instruction) over the fixed held-out eval charts — never train charts —
and checking every answer with the SAME ``verify_answer`` the dataset
filter and the app use. The dataset gate and the eval judge are one
function: gaming the metric means passing the filter.

Modes (spec tasks 3.1, 3.2):
- ``--mock clean``: no server. Restates the chart's own fact-recall
  answers verbatim plus one genuine ``[Primer NN ...]`` citation.
  Expect ~zero flags. CI-safe.
- ``--mock noisy``: no server. The Qwen failure shape on purpose:
  a systematic house off-by-one plus one fake citation. Expect flags.
- live: ``--lmstudio URL --model KEY`` drafts through the app's AiEngine
  path (thinking caps, reasoning handling; never evicts the user's
  loaded model).

Ship gate (spec task 3.3):
- ``--compare base.json candidate.json`` exits 0 only when the candidate
  flags STRICTLY fewer claims than base at equal-or-better citation
  genuineness. Anything else is rejected regardless of fluency.

Usage:
  PYTHONPATH=. python3 tools/train/eval_adapter.py --mock clean \\
      --n 20 --seed 42 --out /tmp/eval-base.json
  PYTHONPATH=. python3 tools/train/eval_adapter.py --mock noisy \\
      --n 20 --seed 42 --out /tmp/eval-cand.json
  PYTHONPATH=. python3 tools/train/eval_adapter.py \\
      --compare /tmp/eval-base.json /tmp/eval-cand.json
  PYTHONPATH=. python3 tools/train/eval_adapter.py \\
      --lmstudio http://LAN-IP:1234 --model some/adapter \\
      --n 50 --out /tmp/eval-adapter.json
"""

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

MOCK_GENIUINE_SOURCE = "Primer 01 Foundations"
MOCK_FAKE_SOURCE = "Brihat Parashara Hora Shastra"


def clean_answer(facts: Dict) -> str:
    """Mock strong-reader answer: the chart's own fact-recall, verbatim."""
    from tools.train.draft import fact_recall_pairs
    body = " ".join(p["messages"][2]["content"]
                    for p in fact_recall_pairs(facts))
    return f"{body} As taught in [{MOCK_GENIUINE_SOURCE}]."


def noisy_answer(facts: Dict) -> str:
    """Mock weak-reader answer: systematic house off-by-one + fake cite."""
    def _shift(m: "re.Match") -> str:
        return f"H{(int(m.group(1)) % 12) + 1}"
    body = re.sub(r"\bH(\d{1,2})\b", _shift, clean_answer(facts))
    return body.replace(f"[{MOCK_GENIUINE_SOURCE}]",
                        f"[{MOCK_FAKE_SOURCE}]")


def score_answer(answer: str, chart) -> Dict:
    """verify_answer flags + citation genuineness for one reading."""
    from jhora.ai.verify import _library_sources, verify_answer
    from tools.train.filter import _CITATION, _norm
    v = verify_answer(answer, chart)
    cites = _CITATION.findall(answer or "")
    library = _library_sources()
    genuine = sum(1 for c in cites if _norm(c) in library)
    return {
        "flags": len(v.flags),
        "checked": v.checked,
        "flag_kinds": sorted({f.kind for f in v.flags}),
        "citations_total": len(cites),
        "citations_genuine": genuine,
    }


def eval_charts(seed: int, n: int) -> List[Tuple[str, object, Dict]]:
    """First ``n`` held-out eval charts with their engine facts."""
    from jhora.charts.chart import ChartBuilder
    from tools.train.build import heldout_charts
    from tools.train.facts import chart_facts
    out = []
    for bd in heldout_charts(seed)[:n]:
        cd = ChartBuilder().build(**bd)
        key = (f"{bd['year']}-{bd['month']:02d}-{bd['day']:02d} "
               f"{bd['hour']:.4f} {bd['lat']} {bd['lon']}")
        out.append((key, cd, chart_facts(cd)))
    return out


def run_eval(draft_fn, seed: int, n: int, mode: str,
             tag: str, save_answers: bool = False) -> Dict:
    """Draft one reading per held-out chart, score each, aggregate."""
    rows = []
    for key, cd, facts in eval_charts(seed, n):
        try:
            answer = draft_fn(facts)
        except Exception as e:  # a dead model still yields a scored row
            answer = f"[draft failed: {e}]"
        row = {"chart_key": key, **score_answer(answer, cd)}
        if save_answers:
            row["answer"] = answer
        rows.append(row)
    total_flags = sum(r["flags"] for r in rows)
    total_checked = sum(r["checked"] for r in rows)
    cit_total = sum(r["citations_total"] for r in rows)
    cit_genuine = sum(r["citations_genuine"] for r in rows)
    blob = "".join(json.dumps(r, sort_keys=True) for r in rows)
    return {
        "tag": tag, "mode": mode, "seed": seed, "n_charts": n,
        "n_readings": len(rows),
        "total_flags": total_flags, "total_checked": total_checked,
        "flag_rate": (total_flags / total_checked) if total_checked else 0.0,
        "flags_per_reading": (total_flags / len(rows)) if rows else 0.0,
        "citations_total": cit_total, "citations_genuine": cit_genuine,
        "citation_genuineness": (cit_genuine / cit_total) if cit_total else 1.0,
        "eval_charts": len(rows),
        "report_hash": hashlib.sha256(blob.encode()).hexdigest()[:16],
        "rows": rows,
    }


def compare_reports(base: Dict, cand: Dict) -> Tuple[bool, List[str]]:
    """Ship gate: strictly fewer flags AND equal-or-better genuineness."""
    reasons = []
    flags_ok = cand["total_flags"] < base["total_flags"]
    reasons.append(
        f"flags {cand['total_flags']} vs base {base['total_flags']}: "
        f"{'BETTER' if flags_ok else 'NOT strictly fewer — reject'}")
    gen_ok = (cand["citation_genuineness"] >= base["citation_genuineness"])
    reasons.append(
        f"citation genuineness {cand['citation_genuineness']:.3f} vs base "
        f"{base['citation_genuineness']:.3f}: "
        f"{'OK' if gen_ok else 'WORSE — reject'}")
    return (flags_ok and gen_ok), reasons


def main() -> int:
    ap = argparse.ArgumentParser(description="Score a model on held-out "
                                 "charts with the verifier")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--mock", default="", help="clean|noisy (no server)")
    ap.add_argument("--lmstudio", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--save-answers", action="store_true")
    ap.add_argument("--compare", nargs=2, metavar=("BASE", "CAND"),
                    help="ship-gate two eval reports")
    args = ap.parse_args()

    if args.compare:
        base = json.loads(Path(args.compare[0]).read_text())
        cand = json.loads(Path(args.compare[1]).read_text())
        print(f"base [{base.get('tag')}] {base['mode']}: "
              f"flags={base['total_flags']} checked={base['total_checked']} "
              f"genuine={base['citation_genuineness']:.3f}")
        print(f"cand [{cand.get('tag')}] {cand['mode']}: "
              f"flags={cand['total_flags']} checked={cand['total_checked']} "
              f"genuine={cand['citation_genuineness']:.3f}")
        ship, reasons = compare_reports(base, cand)
        for r in reasons:
            print(("SHIP: " if ship else "REJECT: ") + r)
        return 0 if ship else 1

    tag = args.tag or datetime.datetime.now().strftime("%Y%m%d-%H%M")
    if args.mock in ("clean", "noisy"):
        mode = f"mock-{args.mock}"
        draft_fn = (clean_answer if args.mock == "clean" else noisy_answer)
    elif args.lmstudio and args.model:
        from tools.train.draft import draft_reading, engine_call
        call_fn = engine_call(args.lmstudio, args.model)
        mode = f"live:{args.model}"
        draft_fn = lambda facts: draft_reading(facts, call_fn)[  # noqa: E731
            "messages"][2]["content"]
    else:
        ap.error("need --mock clean|noisy or --lmstudio URL --model KEY")
        return 2  # unreachable; keeps linters honest

    report = run_eval(draft_fn, args.seed, args.n, mode, tag,
                      save_answers=args.save_answers)
    print(f"model={mode} charts={report['n_charts']} "
          f"flags={report['total_flags']}/{report['total_checked']} "
          f"rate={report['flag_rate']:.4f} "
          f"genuine={report['citation_genuineness']:.3f}")
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
