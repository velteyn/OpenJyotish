# dasas/yogini Specification

## Purpose
TBD - created by archiving change spec-core-dasa-systems. Update Purpose after archive.

## Requirements

### Requirement: Eight-yogini cycle

Yogini SHALL run the eight classical Yoginis in order with years 1 to 8
(a 36-year cycle), each Yogini mapped to its planet.

#### Scenario: Cycle shape
- **WHEN** the Yogini definitions are inspected
- **THEN** there are eight entries whose years run 1..8 and whose total is 36

### Requirement: Nakshatra-seeded start

The starting Yogini SHALL be derived from the lord of the Moon's nakshatra,
with the first period reduced by the elapsed fraction of the nakshatra.

#### Scenario: Seeded from the Moon's nakshatra
- **WHEN** a chart is computed
- **THEN** the first period's Yogini corresponds to the nakshatra lord and
  begins at the birth instant
