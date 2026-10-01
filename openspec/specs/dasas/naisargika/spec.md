# dasas/naisargika Specification

## Purpose
TBD - created by archiving change spec-implemented-capabilities. Update Purpose after archive.

## Requirements

### Requirement: Fixed natural ages

The Naisargika dasa SHALL run seven planetary periods from birth in the
fixed classical order and lengths: Moon 1, Mars 2, Mercury 9, Venus 20,
Jupiter 18, Sun 20, Saturn 50 years (120 total), with no balance
computation and no dependence on the birth chart.

#### Scenario: Periods and ages
- **WHEN** the dasa is computed for any chart
- **THEN** the seven periods have the classical lengths and the same age
  boundaries for every native (Moon 0–1, …, Saturn 70–120)

### Requirement: No lagna period

The eighth "Lagna" period recorded by one commentator SHALL NOT be
included, consistent with the classical texts that object to it.

#### Scenario: Seven lords only
- **WHEN** the mahadashas are listed
- **THEN** exactly seven lords appear and none of them is the lagna

### Requirement: Proportional sub-periods

Antardasas SHALL subdivide each mahadasha proportionally to the seven
planetary period lengths, starting from the mahadasha lord.

#### Scenario: Sub-period order
- **WHEN** the antardasas of a mahadasha are listed
- **THEN** the first is the mahadasha lord and their durations sum to the
  mahadasha length

### Requirement: Year definition respected

The engine SHALL honour the shared year-definition option (solar or savana)
when converting periods to dates.

#### Scenario: Savana year
- **WHEN** the savana year definition is selected
- **THEN** a one-year period spans 360 days
