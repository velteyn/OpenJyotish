# Design

## Context

Eight open issues from the external collaborator (#284, #288–#293,
#298), who is out of time. All fixes already implemented on
`fix/yoga-doctrine-wave`: yogas.py, dignities.py, kuja_dosha.py, tests,
primers 1/3/4/6/10, Gandhi retrospective. Verified: 1922 passed, 0
failed, 75 pre-existing malformed-DB GUI errors identical on clean
main; primer quote test exact-matches detector output.

## Goals / Non-Goals

**Goals:**
- Codify each majority-use decision where a reader can find it.
- Keep every spec statement covered by a test in the branch.

**Non-Goals:**
- New capabilities; engine changes beyond the eight issues.

## Decisions

- Mutual 7th aspect only for Raja sambandha (aspects_planet sep==6,
  symmetric): the narrowest majority reading of aspect-sambandha;
  special aspects stay out until sourced.
- Conjunction and mutual aspect share medium grade (primer rule);
  exchange remains Parivartana-only (strong) to avoid double
  reporting the same pair.
- Viparita: own-sign case kept, placement adds Harsha/Sarala/Vimala,
  conjunction-anywhere dropped; same planet never reported twice
  (found-planets guard).
- Natural (naisargika) — not panchadha — relationships for dignity;
  Vimsopaka ladder keeps code fractions, primer aligned to code.
- Kala Sarpa/Amrita named halves; primer 6 rewritten from
  "not auto-detected" to documented detection.
- Kuja: exalted Mars cancels (primer already stated); Jupiter
  conjunction whole-sign (matches whole-sign aspects).
- #298: fixed PD book (brihat-jataka) instead of sorted-glob, so the
  test asserts the PD-only property, not just determinism.

## Risks / Trade-offs

- [Risk] Raja medium grade changes existing user-visible output →
  Mitigation: primer-led (book is the contract), quote test locks it.
- [Risk] Vimsopaka totals shift for every chart → Mitigation: quotes
  regenerated from the engine, quote test enforces.
- [Risk] Gandhi retrospective loses Amala → Mitigation: factual
  correction per the new rule, minimal diff.
