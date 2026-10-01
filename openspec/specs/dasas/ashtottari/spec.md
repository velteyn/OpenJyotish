# dasas/ashtottari Specification

## Purpose
TBD - created by archiving change spec-core-dasa-systems. Update Purpose after archive.

## Requirements

### Requirement: 108-year eight-lord cycle

Ashtottari SHALL use eight lords (Ketu excluded) with the classical years
Sun 6, Moon 15, Mars 8, Mercury 17, Saturn 10, Jupiter 19, Rahu 12, Venus
21, summing to 108 years.

#### Scenario: Cycle shape
- **WHEN** the engine's cycle is inspected
- **THEN** it holds eight lords, Ketu is absent, and the years sum to 108

### Requirement: Nakshatra mapping and balance

The starting lord SHALL be taken from the Ashtottari nakshatra-lord mapping
for the Moon's nakshatra, with the first period reduced by the elapsed
fraction of that nakshatra.

#### Scenario: First period starts at birth
- **WHEN** a chart is computed
- **THEN** the first period begins at the birth instant with its balance
  taken from the nakshatra

### Requirement: Applicability options

The engine SHALL expose the classical applicability views (unconditional,
Rahu in a quadrant/trine from the lagna lord, and the day/night paksha
rule) so callers can gate the system explicitly.

#### Scenario: Unconditional default
- **WHEN** applicability is queried with the default condition
- **THEN** the system reports itself applicable
