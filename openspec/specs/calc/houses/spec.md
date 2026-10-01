# calc/houses Specification

## Purpose
TBD - created by archiving change 2026-09-23-fix-whole-sign-house. Update Purpose after archive.

## Requirements

### Requirement: Whole-sign house counting

Every calculator that reports a house from the lagna SHALL count whole signs
(house = the sign difference from the lagna's sign, 1-12), consistently across
modules.

#### Scenario: Next sign is not house one

- **WHEN** a planet is in the sign after the lagna but within 30° of the
  ascendant degree
- **THEN** it is reported in house 2, not house 1

#### Scenario: Modules agree

- **WHEN** the same longitude and lagna are passed to any house-from-lagna
  helper
- **THEN** every helper returns the same house
