# Dasas Trikona Specification

## Purpose

Trikona rasi dasa times life through the strongest lagna trine with
Chara-rule durations, for charts where purushartha (dharma/artha/kama/moksha)
themes dominate the reading.

## Requirements

### Requirement: Trikona sequence starts at the strongest trine
The system SHALL start the 12-Mahadasha sequence at the stronger of
the lagna, 5th and 9th houses (same BPHS stronger-sign determination
as Brahma — cross-verified replacement for the previously specced
Atmakaraka start), running forward when the seed index is even and
backward otherwise.

#### Scenario: Fixture start sign
- **WHEN** computed for the 1990 Bangalore fixture (Gemini trine
  alone occupied)
- **THEN** the first Mahadasha lord is Gemini, running forward:
  Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn,
  Aquarius, Pisces, Aries, Taurus.

### Requirement: Chara durations with the Rao dual-lord exception
The system SHALL use Chara lord-distance durations (inclusive
sign-to-lord count minus one, footed directions, own sign 12, full
circle 11) with the mainstream Rao exception for Scorpio/Aquarius,
identical to the Chara cycle on the same chart — cross-verified
replacement for the previously specced fixed table. No exaltation /
debilitation adjustment.

#### Scenario: Fixture durations
- **WHEN** computed for the 1990 fixture
- **THEN** durations are [6,11,7,9,3,8,6,1,1,9,7,8] and sum to 76,
  reproducing mainstream tradition exactly.

### Requirement: Forward order with proportional forward antardasas
Each Mahadasha SHALL subdivide into 12 equal antardasas (MD/12) in
modality-gated order with d = +1 for even MD signs and −1 for odd:
the cycle starts at the MD itself when MD is odd and at 7th-from-MD
when even; then movable MDs run plain zodiacal, dual MDs run
kendra-group order (groups [S, S+4d, S−4d], within-step +3d), and
fixed MDs run a constant +5d progression. Deeper levels rotate within
the antardasa order (uncompared).

#### Scenario: Antardasa integrity
- **WHEN** any Mahadasha is expanded
- **THEN** its 12 antardasas sum to the Mahadasha duration and the first
  names the Mahadasha sign itself.

#### Scenario: Observed mainstream tradition antardasas (informative, not normative)
- **WHEN** mainstream tradition expands Virgo MD (9y, Jan 1990 chart)
- **THEN** it shows 12 equal ~9-month splits in kendra-backward groups
  [Vi,Ge,Pi,Sg,Ta,Aq,Sc,Le,Cp,Li,Cn,Ar], and for Gemini MD (6y) equal
  ~6-month splits in kendra-forward groups
  [Sg,Pi,Ge,Vi,Ar,Cn,Li,Cp,Le,Sc,Aq,Ta]; grouping rule uninduced —
  a third MD sample decides it.

### Requirement: Mainstream scope only
The system SHALL NOT offer variant start rules (e.g. AK-seeded
Trikona, documented as an alternative school without implementation),
alternate year tables or D9-based computation in this change;
unsupported options SHALL be rejected or absent rather than guessed.

#### Scenario: Out-of-scope request
- **WHEN** a caller requests a non-standard Trikona variant
- **THEN** the system either uses the standard rule documented above or
  raises a clear error naming the unsupported option.
