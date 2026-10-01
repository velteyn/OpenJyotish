# ashtakavarga Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Bhinnashtakavarga per planet

Ashtakavarga SHALL compute the Bhinnashtakavarga (BAV) of each of the
seven grahas over the twelve signs, using the classical benefic-point
contributions, and each BAV's total SHALL equal the classical constant for
that planet (Sun 48, Moon 49, Mars 39, Mercury 54, Jupiter 56, Venus 52,
Saturn 39).

#### Scenario: BAV totals
- **WHEN** a chart's BAVs are computed
- **THEN** each planet's BAV total equals its classical constant

### Requirement: Sarvashtakavarga invariant

The Sarvashtakavarga (SAV) of a sign SHALL be the sum of the seven
planets' BAV values in that sign, and the SAV total across all signs
SHALL be 337 for every chart.

#### Scenario: SAV total
- **WHEN** the SAV is computed for any chart
- **THEN** its total is 337

### Requirement: Kakshya detail

Each sign's BAV SHALL be decomposable into its Kakshya subdivisions, so
transit timing can be refined below sign level.

#### Scenario: Kakshya breakdown
- **WHEN** a sign's BAV is inspected
- **THEN** its benefic points are attributable to the individual Kakshyas
