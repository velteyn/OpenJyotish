# dasas/sudasa Specification

## Purpose
TBD - created by archiving change spec-core-dasa-systems. Update Purpose after archive.

## Requirements

### Requirement: Sree Lagna seeded rasi dasa

Sudasa SHALL run twelve rasi mahadashas seeded from the Sree Lagna (the
Lakshmi point, the Moon's nakshatra fraction), forward through the signs.

#### Scenario: Seed and coverage
- **WHEN** a chart is computed
- **THEN** the first mahadasha is the sign of the Sree Lagna and the twelve
  mahadashas cover all twelve signs

### Requirement: Sign durations and proportional sub-periods

Each sign's duration SHALL follow the classical rasi-dasa count from the
sign to its lord, and the sub-periods SHALL divide the mahadasha
proportionally, starting from the mahadasha sign.

#### Scenario: Continuity
- **WHEN** the periods are listed
- **THEN** each period ends where the next begins and the sub-periods sum
  to the mahadasha duration
