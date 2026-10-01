# sahama Specification

## Purpose
TBD - created by archiving change spec-implemented-capabilities. Update Purpose after archive.

## Requirements

### Requirement: Classical sahama set

The module SHALL provide the 36 classical Tajaka sahamas with the formula
A − B + C (mod 360), adding one sign (30°) when the ascendant does not fall
between the subtrahend and the minuend, matching the classical statements
of Raman's Varshaphala and Balabhadra's Hayanaratna.

#### Scenario: Punya sahama
- **WHEN** the Punya sahama is computed
- **THEN** it equals Moon − Sun + lagna (with the 30° rule applied)

#### Scenario: House-lord and fixed-point forms
- **WHEN** a sahama is defined from a house cusp, a house lord or a fixed
  longitude (e.g. Artha, Paradesa, Jalapatana, Mrityu)
- **THEN** the corresponding reference is resolved and the same formula
  and 30° rule apply

### Requirement: Day/night determination from true sunrise

Day/night selection SHALL be derived from the birth moment's position
between sunrise and sunset at the birth place (single precise source),
falling back to a documented clock heuristic only when ephemeris data is
unavailable. The crude 06:00–18:00 test SHALL NOT be the primary rule.

#### Scenario: Pre-sunrise birth is night
- **WHEN** a birth falls after 06:00 but before the actual sunrise
- **THEN** the night formulae are used

### Requirement: Night reversal rule

For night births the subtrahend and minuend SHALL be exchanged, keeping the
additive third term, except for the sahamas documented as same day/night
(Bhratri, Vyapara, Roga, Mrityu, Paradesa, Artha, Labha). Satru SHALL
reverse at night, per both classical statements.

#### Scenario: Satru flips at night
- **WHEN** the Satru sahama is computed for a night birth
- **THEN** it is Saturn − Mars + lagna (the day form being Mars − Saturn +
  lagna)

### Requirement: Sahama surface

A `sahamas` CLI command SHALL print the sahamas with meaning, longitude,
sign and house, announcing the day/night basis; the GUI, TUI, HTML report
and JSON export SHALL expose the same table. A name lookup helper SHALL
return a single sahama by name.

#### Scenario: CLI prints the table
- **WHEN** `sahamas` runs for valid birth data
- **THEN** all 36 sahamas are listed with sign and house, and the
  day/night basis is stated
