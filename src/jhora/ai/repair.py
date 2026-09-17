"""Verify-and-repair loop — mechanical enforcement for AI answers.

``verify_answer`` only reports; this module closes the loop: flagged claims
are sent back to the model with engine-supplied corrections, the rewritten
answer is re-verified, and the loop repeats until clean or out of rounds
(then the best version ships with its report — repair must never destroy
an answer). All surfaces (CLI/GUI/TUI, chat/teacher) share this helper so
enforcement is identical everywhere.
"""

from typing import Callable, List, Optional, Tuple

from jhora.charts.chart import ChartData
from jhora.ai.verify import Verification, verify_answer

MAX_ROUNDS = 2


def _repair_messages(answer: str, flags, sources: List[str]) -> List[dict]:
    corrections = "\n".join(
        f"{i}. CLAIM: {f.claim}\n   CORRECTION: {f.expected}"
        for i, f in enumerate(flags, 1))
    allowed = ""
    if sources:
        allowed = ("\nOnly cite these books (verbatim [Name] form): "
                   + "; ".join(f"[{s}]" for s in sources[:40])
                   + ". Drop any other [Source] citation.")
    return [
        {"role": "system",
         "content": ("You are a careful editor of Vedic astrology readings. "
                     "Fix ONLY what is listed below. Do not add new claims, "
                     "new yogas, new dates, or new citations.")},
        {"role": "user",
         "content": (f"Revise this reading so every listed claim matches its "
                     f"correction. Keep all correct passages word-for-word. "
                     f"If a flagged claim cannot be corrected with certainty, "
                     f"delete its sentence instead of rewording it. "
                     f"Return ONLY the revised reading, no preamble.\n\n"
                     f"FLAGED CLAIMS AND THEIR CORRECTIONS:\n{corrections}"
                     f"{allowed}\n\nREADING:\n{answer}")},
    ]


def repair_answer(
    answer: str,
    cd: ChartData,
    passages: Optional[List[str]] = None,
    call_fn: Optional[Callable[[List[dict]], str]] = None,
    notify_fn: Optional[Callable[[str], None]] = None,
    max_rounds: int = MAX_ROUNDS,
) -> Tuple[str, Verification]:
    """Verify, repair flagged claims via the model, re-verify.

    Without ``call_fn`` this is verify-only (report, no rewrite), so unit
    tests and offline paths stay network-free. Returns (best_text, report).
    """
    from jhora.interpreter.knowledge_base import KnowledgeBase
    try:
        sources = KnowledgeBase().list_sources()
    except Exception:
        sources = []
    v = verify_answer(answer, cd, passages)
    if not v.flags or call_fn is None:
        return answer, v
    best, best_v = answer, v
    for _ in range(max(0, max_rounds)):
        if notify_fn is not None:
            try:
                notify_fn(
                    f"\n\n⏳ {len(best_v.flags)} claims differ from your "
                    f"chart — repairing (extra delay)…\n\n")
            except Exception:
                pass
        try:
            revised = call_fn(_repair_messages(
                best, best_v.flags, sources)) or ""
        except Exception:
            break
        if not revised.strip() or revised.strip().startswith("---\n"):
            break  # engine offline/timeout notice, not a revision
        v2 = verify_answer(revised, cd, passages)
        if len(v2.flags) < len(best_v.flags):
            best, best_v = revised, v2
        if not v2.flags:
            break
    return best, best_v
