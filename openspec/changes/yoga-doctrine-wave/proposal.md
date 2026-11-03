# Proposal

## Why

The external collaborator's eight open issues (#284, #288–#293, #298)
document engine-vs-doctrine mismatches in yogas, dignities and Kuja
Dosha, plus one test-only flake. He is out of time; the goal is to fix
them all on majority-use grounds (Tradition Rule) and cut a release
out of the wave.

## What Changes

- Yogas: flanking/Kemadruma exclude luminaries and nodes; Amala needs a
  natural benefic; Raja via conjunction or mutual 7th aspect, graded
  medium; Viparita is placement-based (Harsha/Sarala/Vimala); Kala
  Sarpa reported for both arcs (Sarpa/Amrita names).
- Dignities: natural friend/enemy via sign-lord relationship;
  Vimsopaka inimical scores quarter (primer aligned to code).
- Kuja Dosha: exalted Mars cancels; Jupiter conjunction is whole-sign.
- Test-only: PD-library test uses a fixed book (macOS order flake).
- Primers 1/3/4/6/10, Gandhi retrospective and quote-test updated in
  the same PR (AGENTS.md: verbatim quotes track the detector).

## Capabilities

### New Capabilities
(none — all behavior lands in existing capabilities.)

### Modified Capabilities
- `yogas`: Raja/Viparita/Amala/Kala Sarpa/flanking requirement changes.
- `dignities`: friend/enemy requirement changes.
- `kuja-dosha`: cancellation requirement changes.

## Impact

- `src/jhora/calc/{yogas,dignities,kuja_dosha}.py`, tests, primers,
  `docs/gandhi-retrospective.md`, CHANGELOG, README counts.
- Full suite must stay green (modulo the pre-existing malformed-DB
  GUI errors, identical on clean main); the exact-match primer quote
  test is the reference check for detector output.
