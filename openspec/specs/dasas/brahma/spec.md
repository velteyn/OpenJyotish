# dasas/brahma Specification

## Purpose
TBD - created by archiving change spec-core-dasa-systems. Update Purpose after archive.

## Requirements

### Requirement: 96-year ayur cycle

Brahma SHALL run the twelve signs with modality-based durations — movable 7,
fixed 8, dual 9 years — giving a 96-year cycle.

#### Scenario: Modality durations
- **WHEN** the mahadashas are listed
- **THEN** each duration follows the sign's modality and the total is 96

### Requirement: Brahma planet seed

The seed SHALL be the stronger of the lagna and the 7th, with the
classical Brahma-planet rules (including the sixth-planet exception) used
to determine the starting point.

#### Scenario: Birth balance
- **WHEN** a chart is computed
- **THEN** the first mahadasha is reduced by the elapsed portion, so the
  periods cover the whole life from birth

### Requirement: No benefic/malefic correction

The classical exaltation/debilitation adjustments to the Brahma seed SHALL
NOT be applied where they were not verified; durations depend only on
sign modality.

#### Scenario: Plain modality durations
- **WHEN** a sign's lord is exalted or debilitated
- **THEN** the sign still runs its modality duration (7, 8 or 9 years)
