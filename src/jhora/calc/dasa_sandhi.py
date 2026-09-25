"""Dasa Sandhi — gear-shift junctions between mahadasas.

The most-used rule: sandhi opens in the last 10% of the outgoing
mahadasa and closes in the first 10% of the incoming one (so a
Ketu→Venus changeover spans 0.7 + 2.0 years). Applies to any
mahadasa sequence; computed here on whatever MD list the caller
passes (Vimshottari by convention). Other schools use fixed months; they do as they do — this module
ships the 10% reading as is. Chidra-dasha (final bhukti closure)
rides along: the last antardasa of each mahadasa.
"""

from typing import Dict, List

#: Fraction of each adjoining MD inside the junction.
SANDHI_FRACTION = 0.10


def sandhi_periods(mds: List, y_per_d: float = 365.2425) -> List[Dict]:
    """[{outgoing, incoming, start_jd, junction_jd, end_jd,
    duration_years}] for each MD junction.

    Each element needs ``lord_name``, ``start_jd``, ``end_jd`` and
    ``duration_years`` (DasaPeriod shape); sub-periods are ignored.
    The opening is clamped to the outgoing MD's own start (a
    sesham-shortened first MD cannot open its sandhi before birth).
    """
    out = []
    for prev, nxt in zip(mds, mds[1:]):
        start = prev.end_jd - SANDHI_FRACTION * prev.duration_years * y_per_d
        start = max(start, prev.start_jd)
        end = nxt.start_jd + SANDHI_FRACTION * nxt.duration_years * y_per_d
        out.append({
            "outgoing": prev.lord_name,
            "incoming": nxt.lord_name,
            "start_jd": start,
            "junction_jd": nxt.start_jd,
            "end_jd": end,
            "duration_years": (end - start) / y_per_d,
        })
    return out


def chidra_periods(mds: List) -> List[Dict]:
    """[{md_lord, chidra_lord, start_jd, end_jd, duration_years}].

    The chidra is the last antardasa of each mahadasa (closure and
    release). MDs computed without sub-periods are skipped; each
    sub-period needs ``lord_name``, ``start_jd``, ``end_jd`` and
    ``duration_years``.
    """
    out = []
    for md in mds:
        subs = list(getattr(md, "sub_periods", None) or [])
        if not subs:
            continue
        last = subs[-1]
        out.append({
            "md_lord": md.lord_name,
            "chidra_lord": last.lord_name,
            "start_jd": last.start_jd,
            "end_jd": last.end_jd,
            "duration_years": last.duration_years,
        })
    return out
