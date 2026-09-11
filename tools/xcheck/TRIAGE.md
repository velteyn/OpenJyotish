# Triage report — jyotishganit cross-check (lib 0.1.0, 8 charts)

## Conventions discovered (run header)

| Parameter | Theirs | Ours | Verdict |
|---|---|---|---|
| Ayanamsa | True Chitra Paksha (~23.842) | Lahiri (~23.808) | Systematic ~0.015–0.034°, normalized per chart |
| Ephemeris | JPL DE421 (Skyfield) | Swiss Ephemeris | Planets agree to the ayanamsa offset; tropical Moon within ~0.01° |
| Nodes | Truncated linear Meeus (proven) | Swiss fitted mean elements | Ours more precise |
| Dasa year | Effectively solar (MD ends ≤ days) | Solar 365.2425 default | Match |
| Houses | Whole-sign Rasi | Whole-sign Rasi (+Placidus Bhava) | Match at Rasi level |
| AD alignment | From MD lord (standard) | Always Ketu-first (see TRIAGE-3) | Our bug |

## Layer results

- **L0 planets**: MATCH after per-chart offset normalization (cluster spread
  < 0.015° incl. lunar arcminute noise; center drifts slowly with epoch =
  ayanamsa proper-motion divergence, documented).
- **L0 nodes**: TRIAGE-1 (open).
- **L1 tithi/nakshatra/yoga/vara**: MATCH exact (cusp charts flip adjacent
  bins as designed — ayanamsa-boundary systematics).
- **L1 karana**: TRIAGE-2 (our bug).
- **L2 MD ends/balance**: MATCH (≤10 d ends, ≤0.3% balance fraction).
- **L2 AD starts**: TRIAGE-3 (our bug).
- **L3 positional (uchcha/dig/kendra/naisargika)**: MATCH (≤0.1/6/exact/0.0).
- **L3 Kala/Cheshta/Saptavargaja/Ojha/Drek/Drik**: TRIAGE-4 (authority
  variants, open research).

## Open findings (mismatches → follow-ups, never absorbed here)

- **TRIAGE-1 — node theory**: ✅ RESOLVED by reading their open source
  (`core/astronomical.py`): their Rahu is the *truncated linear* Meeus mean
  node (`125.04452 − 1934.136261·T`, no higher terms), reproduced to 0.0001°
  on all 8 fixtures. Ours is Swiss fitted mean elements — strictly more
  precise. No action; our mean-node stance stands, documented here.
- **TRIAGE-2 — our `_karana` ignores the half-tithi fraction**
  (`tithi.index * 2 % 11`): wrong karana name for most tithis (e.g. Taitula
  instead of Balava for first-half Krishna Chaturthi). ✅ RESOLVED by
  `fix-karana-mapping` (canonical elongation-based computation shared by
  calculator, panel, and the revived AI panchanga snapshot; proven by a
  60-half-tithi sweep plus the 8 former strict-xfail reference asserts).
- **TRIAGE-3 — our antardashas always start at Ketu** instead of rotating
  from the MD lord (universal Vimsottari rule). ✅ RESOLVED by
  `fix-antardasa-rotation` (opt-in rotation in the shared builder, enabled
  for Vimsottari): full-MD AD order now matches the reference exactly and
  boundaries within days on all 8 charts. Sibling dasas intentionally
  untouched (verify-then-enable follow-ups).
- **TRIAGE-4 — Shadbala model variants**: Paksha graded vs binary, Tribhaga
  lords, Ojha/Drek granularity (15 vs 30 scales), combined VMDH vs split
  Abda/Masa/Vara/Hora, Ayana scale (>60), signed continuous Drik vs our
  0/15 bins, declination-based Cheshta both sides. Needs BPHS-text audit
  before any change; do not "fix" by copying their numbers.

## Process notes (harness lessons)

- A `int()` float truncation in the generator built 9:09 charts instead of
  9:10 (Moon off 0.01°, dashas off ~2 d). Fixed (round + divmod); lesson:
  construct datetimes from total minutes, and the Moon-offset tripwire in
  L0 now guards timestamp fidelity forever.
- Fixture regeneration is deterministic (verified across processes after
  the JPL download completed); fixtures pin lib 0.1.0 in their path.
