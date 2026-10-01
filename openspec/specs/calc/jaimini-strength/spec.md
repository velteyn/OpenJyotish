# calc/jaimini-strength Specification

## Purpose
TBD - created by archiving change add-jaimini-rasi-strength. Update Purpose after archive.

## Requirements

### Requirement: Jaimini sign strength

The module SHALL return the stronger of two signs for a chart by the
mainstream Jaimini ladder, in order: occupancy (planet count), lord dignity
(rasi drishti of Mercury/Jupiter plus own sign), exaltation count,
debilitation count (fewer is stronger), different-oddity of each sign vs its
lord (Deha/Paka), and the degree-in-sign of the two sign-lords. Scorpio and
Aquarius SHALL use their co-lord picks.

#### Scenario: More planets wins

- **WHEN** one sign holds more planets than the other
- **THEN** the more-occupied sign is stronger

#### Scenario: Ladder tiebreaks

- **WHEN** both signs hold the same number of planets
- **THEN** lord dignity decides, then exaltation, then debilitation, then
  different-oddity, then the lords' degree-in-sign

### Requirement: Rasi drishti

The module SHALL expose Jaimini rasi drishti (movable signs aspect fixed,
dual aspect dual) used for lord dignity.

#### Scenario: Movable aspects fixed

- **WHEN** a movable sign is tested against a fixed sign
- **THEN** the aspect holds (except adjacent signs)
