"""Argala (planetary intervention) — Jaimini Sutras 1-1-5 to 1-1-10.

Primary argala (any planet): 2nd, 4th, 11th from the reference.
Virodha (obstruction), house-for-house: 12th blocks 2nd, 10th blocks
4th, 3rd blocks 11th. An argala holds only when its planets strictly
outnumber the obstructors (1-1-8; a tie goes to the obstruction).
Trikona argala (secondary): 5th, blocked by 9th.
Visesha argala: three or more malefics in the 3rd — always holds,
never obstructed. Ketu reversal (1-1-10): when the reference sign
holds Ketu, argala houses mirror to 10th/12th/3rd with virodha
4th/2nd/11th. Strength grade (Parasara): one planet gives results,
two medium, three or more excellent.

References are the twelve bhavas from lagna. Planet-as-reference and
the Raman benefic-only trikona reading are documented follow-ups.
Malefics for Visesha: Sun, Mars, Saturn, Rahu, Ketu.
"""

from typing import Dict, List

from jhora.types.graha import Graha

#: (argala house, virodha house) pairs, houses from the reference.
_PAIRS = ((2, 12), (4, 10), (11, 3), (5, 9))

#: Mirrored pairs when Ketu sits in the reference sign (the trikona
#: pair has no stated mirror and is skipped there).
_KETU_PAIRS = ((10, 4), (12, 2), (3, 11))

_MALEFICS = frozenset({
    Graha.SUN, Graha.MARS, Graha.SATURN, Graha.RAHU, Graha.KETU})


def _grade(n: int) -> str:
    if n >= 3:
        return "excellent"
    if n == 2:
        return "medium"
    return "results"


def _rel(ref: int, offset_house: int) -> int:
    """House-from-lagna of the Nth house from a reference bhava."""
    return (ref - 1 + offset_house - 1) % 12 + 1


def argala_for_house(ref: int, occupants: Dict[int, List[Graha]],
                     ketu_sign: int = -1) -> List[dict]:
    """Argalas on one bhava (1-12 from lagna).

    ``occupants`` maps house-from-lagna (1-12) to planets. ``ketu_sign``
    is Ketu's house-from-lagna (mirrors the pairs when it equals
    ``ref``). Only occupied causing houses are reported.
    """
    pairs = _KETU_PAIRS if ketu_sign == ref else _PAIRS
    out = []
    for ah, vh in pairs:
        ah_abs, vh_abs = _rel(ref, ah), _rel(ref, vh)
        causers = list(occupants.get(ah_abs, []))
        if not causers:
            continue
        blockers = list(occupants.get(vh_abs, []))
        effective = len(causers) > len(blockers)
        out.append({
            "house": ref,
            "argala_house": ah_abs,
            "planets": causers,
            "virodha_house": vh_abs,
            "obstructors": blockers,
            "effective": effective,
            "grade": _grade(len(causers)) if effective else "blocked",
        })
    # Visesha: 3+ malefics in the 3rd from the reference.
    third_abs = _rel(ref, 3)
    third = [g for g in occupants.get(third_abs, []) if g in _MALEFICS]
    if len(third) >= 3:
        out.append({
            "house": ref,
            "argala_house": third_abs,
            "planets": third,
            "virodha_house": None,
            "obstructors": [],
            "effective": True,
            "grade": "excellent (visesha, unobstructed)",
        })
    return out


def argala_all(planet_houses: Dict[Graha, int]) -> List[dict]:
    """Effective and blocked argalas on all twelve bhavas."""
    occupants: Dict[int, List[Graha]] = {}
    for g, h in planet_houses.items():
        occupants.setdefault(h, []).append(g)
    ketu_sign = planet_houses.get(Graha.KETU, -1)
    out = []
    for ref in range(1, 13):
        out.extend(argala_for_house(ref, occupants, ketu_sign))
    return out
