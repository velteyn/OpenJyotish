# dasas/narayana Specification

## Purpose
TBD - created by archiving change spec-core-dasa-systems. Update Purpose after archive.

## Requirements

### Requirement: Rasi dasa from the lagna lord's sign

Narayana SHALL run twelve rasi mahadashas seeded at the **stronger of the
lagna and its 7th** (the satya-peetha rule, resolved by the Jaimini
sign-strength ladder), running in a single direction through all twelve signs
(set by the foot of the 9th sign from the seed).

#### Scenario: Seed and coverage
- **WHEN** a chart is computed
- **THEN** the first mahadasha is the stronger of the lagna and its 7th, and
  the twelve mahadashas cover all twelve signs

### Requirement: Sign durations from the lord's Vimsottari years

Each rasi's duration SHALL be the Vimsottari year count of that sign's
lord, and sub-periods SHALL divide the mahadasha proportionally from the
mahadasha sign.

#### Scenario: Duration source
- **WHEN** a sign whose lord has a known Vimsottari period is reached
- **THEN** the mahadasha length equals that lord's Vimsottari years

### Requirement: Narayana variants

Narayana dasa SHALL support its classical variants (Sama, Paka, Ayur) in
addition to the current base form, selected through the option set.

#### Scenario: Base unchanged
- **WHEN** no variant is selected
- **THEN** the current base form is produced exactly as before

#### Scenario: Variant selection
- **WHEN** a variant is selected
- **THEN** the period structure follows that variant's rule

### Requirement: Narayana chart seed

Narayana dasa SHALL accept a chart seed (such as D-9, D-60 or D-144) so the
seed rasi is taken from that divisional chart instead of the rasi chart.

#### Scenario: Chart seed
- **WHEN** a divisional chart seed is selected
- **THEN** the seed rasi comes from that varga's positions

#### Scenario: Default seed unchanged
- **WHEN** no chart seed is given
- **THEN** the seed uses the rasi chart as before
