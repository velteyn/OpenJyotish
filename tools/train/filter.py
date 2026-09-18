"""Verifier filter: keep only zero-flag pairs (spec task 1.4).

A drafted pair enters the dataset only if ``verify_answer`` reports zero
flags against the pair's own chart. Rejections are logged with reasons so
prompt/recipe tuning has signal. Pure offline code; the LLM never runs here.
"""

from typing import Dict, List, Tuple


def filter_pair(pair: Dict, chart) -> Tuple[bool, List[str]]:
    """Check one drafted pair. Returns (keep, rejection_reasons)."""
    from jhora.ai.verify import verify_answer
    text = pair["messages"][-1].get("content", "") if pair.get("messages") else ""
    if not text or not text.strip():
        return False, ["empty answer"]
    passages = pair.get("passages") or []
    v = verify_answer(text, chart, passages)
    if v.flags:
        reasons = [f"{f.kind}: {f.claim} (expected {f.expected})"
                   for f in v.flags]
        return False, reasons
    if v.checked == 0 and pair.get("kind") == "reading":
        return False, ["no checkable claims extracted"]
    return True, []


def filter_pairs(pairs: List[Dict], charts: Dict[str, object],
                 log=None) -> Tuple[List[Dict], List[Dict]]:
    """Split pairs into (kept, rejected). ``charts`` maps pair chart keys
    (birthdata string) to ChartData. Rejected entries carry reasons."""
    kept, rejected = [], []
    for pair in pairs:
        chart = charts.get(pair.get("chart_key", ""))
        if chart is None:
            rejected.append({**pair, "rejection": ["chart not found"]})
            continue
        ok, reasons = filter_pair(pair, chart)
        if ok:
            kept.append(pair)
        else:
            if log is not None:
                log(f"  reject [{pair.get('kind')}]: " + "; ".join(reasons[:4]))
            rejected.append({**pair, "rejection": reasons})
    return kept, rejected
