# strengths Specification

## Purpose
TBD - created by archiving change widen-dasa-options-and-parity. Update Purpose after archive.

## Requirements

### Requirement: BHPS-parity strength tables

The engine SHALL expose the per-component strength tables the tradition prints
alongside the totals: the kala-bala sub-parts (nathonnatha, paksha, tribhaga,
varsha-masa-dina-hora, ayana, yuddha), the dwadasa-vargeeya bala, and the
ishta and kashta phala per planet.

#### Scenario: Kala bala breakdown
- **WHEN** a planet's kala bala is inspected
- **THEN** its named sub-parts are individually available

#### Scenario: Dwadasa vargeeya bala
- **WHEN** dwadasa-vargeeya bala is requested
- **THEN** each planet's twelve-varga strength is reported

#### Scenario: Ishta and kashta
- **WHEN** ishta/kashta phala is requested
- **THEN** each planet reports its benefic and difficult strength
