"""Verifier filter: keep only clean pairs (spec task 1.4).

Two gates:

- chart pairs (readings, fact-recall) enter only if ``verify_answer``
  reports zero flags against the pair's own chart.
- Primer/PD Q&A pairs carry no chart; they are checked for a real
  ``[Source]`` citation naming a bundled library book and, when the pair
  carries its ``passage``, for verbatim grounding in that source. The
  answer body must be a substring of the book — a pair that cannot
  hallucinate by construction.

Rejections are logged with reasons so prompt/recipe tuning has signal.
Pure offline code; the LLM never runs here.
"""

import re
from typing import Dict, List, Tuple

_CITATION = re.compile(r"\[([A-Z][A-Za-z0-9 .'\-&]{2,60})\]")
_source_cache: Dict[str, str] = {}


def _source_content(source: str):
    if source not in _source_cache:
        from jhora.interpreter.knowledge_base import KnowledgeBase
        _source_cache[source] = KnowledgeBase().get_source(source) or ""
    return _source_cache[source] or None


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def filter_qa_pair(pair: Dict) -> Tuple[bool, List[str]]:
    """Check a chart-less Primer/PD Q&A pair (citation + grounding)."""
    from jhora.ai.verify import _library_sources
    text = pair["messages"][-1].get("content", "") if pair.get("messages") else ""
    if not text.strip():
        return False, ["empty answer"]
    library = _library_sources()
    if not library:
        return False, ["no library sources loaded for citation check"]
    cites = _CITATION.findall(text)
    if not cites:
        return False, ["no [Source] citation"]
    bad = [c for c in cites if _norm(c) not in library]
    if bad:
        return False, [f"citation not in library: [{c}]" for c in bad]

    passage = pair.get("passage")
    source = pair.get("source")
    if passage and source:
        content = _source_content(source)
        if content is None:
            return False, [f"source not loaded: {source}"]
        if _norm(passage) not in _norm(content):
            return False, ["answer not grounded in cited source"]
    return True, []


def filter_pair(pair: Dict, chart, verify_facts: bool = True
                ) -> Tuple[bool, List[str]]:
    """Check one pair. Returns (keep, rejection_reasons).

    ``verify_facts=False`` skips the O(chart) ``verify_answer`` run for
    deterministic fact-recall pairs (engine-generated, clean by
    construction; the full audit lives in ``--verify-facts`` and in
    ``tests/test_train_data.py``). LLM-drafted readings are always
    verified.
    """
    if pair.get("kind") == "qa" and pair.get("provenance") in (
            "primer", "pd-classic"):
        return filter_qa_pair(pair)
    if chart is None:
        return False, ["chart not found"]
    text = pair["messages"][-1].get("content", "") if pair.get("messages") else ""
    if not text or not text.strip():
        return False, ["empty answer"]
    if pair.get("kind") == "fact-recall" and not verify_facts:
        return True, []
    from jhora.ai.verify import verify_answer
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
                 log=None, verify_facts: bool = True
                 ) -> Tuple[List[Dict], List[Dict]]:
    """Split pairs into (kept, rejected). ``charts`` maps pair chart keys
    (birthdata string) to ChartData. Rejected entries carry reasons."""
    kept, rejected = [], []
    for pair in pairs:
        chart = charts.get(pair.get("chart_key", ""))
        ok, reasons = filter_pair(pair, chart, verify_facts=verify_facts)
        if ok:
            kept.append(pair)
        else:
            if log is not None:
                log(f"  reject [{pair.get('kind')}]: " + "; ".join(reasons[:4]))
            rejected.append({**pair, "rejection": reasons})
    return kept, rejected
