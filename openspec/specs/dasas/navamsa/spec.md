# Dasas Navamsa Specification

## Purpose

Navamsa rasi dasa times life through fixed 9-year periods from the D1
lagna lord's sign, for marriage and dharma readings where the navamsa
carries the judgment, in the mainstream standard form
(cross-verified on three charts).

## Requirements

### Requirement: Chara cycle on D-9 positions
The system SHALL seed 12 Mahadashas at the sign occupied by the D1
lagna lord — cross-verified replacement for the previously specced
D-9-lagna Chara cycle — running forward zodiacally with fixed 9-year
Mahadashas (108 total). Antardasas cycle forward proportionally
(house convention; mainstream tradition's AD method uncompared). The Chara-on-D9
school is documented as an alternative without implementation.

#### Scenario: Fixture completes a contiguous cycle
- **WHEN** computed for the 1990 Bangalore fixture (lagna lord
  Mercury in Sagittarius)
- **THEN** 12 Mahadashas run forward from Sagittarius with [9] * 12:
  Sagittarius, Capricorn, Aquarius, Pisces, Aries, Taurus, Gemini,
  Cancer, Leo, Virgo, Libra, Scorpio.

### Requirement: Mainstream form gate
The system SHALL implement only the cross-verified against published tables mainstream
form; variant seeds or count rules SHALL be rejected or absent rather
than guessed.

#### Scenario: Out-of-scope request
- **WHEN** a caller requests a non-standard Navamsa variant
- **THEN** the system either uses the standard rule pinned in design.md
  or raises a clear error naming the unsupported option.
