# calc/angles Specification

## Purpose
TBD - created by archiving change 2026-09-23-fix-angles-aspect. Update Purpose after archive.

## Requirements

### Requirement: Sign-based aspect predicate

`is_aspected` SHALL report whether a longitude aspects a target by the
whole-sign 7th-sign rule: the target's sign is the 6th from the planet's sign.

#### Scenario: Opposite signs aspect

- **WHEN** a planet is in Aries and the target is in Libra
- **THEN** the aspect is reported

#### Scenario: Boundary is whole-sign

- **WHEN** a planet is at 29° Aries and the target at 1° Libra
- **THEN** the aspect is reported (the signs are opposite, regardless of degree)

#### Scenario: Special aspects elsewhere

- **WHEN** a planet-specific special aspect is needed
- **THEN** the caller uses `calc.drishti` (graha-aware), not this helper
