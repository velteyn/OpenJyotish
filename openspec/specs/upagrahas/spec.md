# upagrahas Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Solar upagrahas

The engine SHALL compute the five solar upagrahas — Dhuma, Vyatipata,
Parivesha, Indrachapa and Upaketu — from the Sun's longitude by their
classical formulas (Dhuma at Sun plus 133 degrees 20 minutes, and the
remaining chain derived from it).

#### Scenario: Dhuma derivation
- **WHEN** the solar upagrahas are computed
- **THEN** Dhuma lies 133 degrees 20 minutes from the Sun and the others
  follow from it

### Requirement: Temporal upagrahas

The engine SHALL compute the time-based upagrahas from the division of the
day and night into eight portions, taking Gulika from the start of
Saturn's portion and Mandi from the middle of Saturn's portion, with the
remaining portions attributed to their planets.

#### Scenario: Gulika and Mandi
- **WHEN** the temporal upagrahas are computed for a chart
- **THEN** Gulika falls at the start of Saturn's portion and Mandi at its
  middle

### Requirement: Placements reported with signs

Every upagraha SHALL be reported with its longitude resolved to a sign and
degree so it can be placed in the chart.

#### Scenario: Chart placement
- **WHEN** upagrahas are listed
- **THEN** each carries a sign and degree
