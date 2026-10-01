# strengths/shadbala Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Six strength components

Shadbala SHALL be computed from the six classical components — Sthana
(positional, including the varga, ojhayugma, kendra and drekkana
sub-components), Dig, Kala, Chesta, Naisargika and Drik — for the seven
grahas, and the total SHALL equal the sum of its components in virupas
(60 virupas = one rupa).

#### Scenario: Total equals the sum
- **WHEN** a planet's Shadbala is computed
- **THEN** the reported total virupas equal the sum of the six components

### Requirement: Component sub-strengths exposed

Each component SHALL retain its own named sub-strengths so a reading can
show where a planet's strength comes from, not only the total.

#### Scenario: Component breakdown
- **WHEN** a planet's strength is inspected
- **THEN** the Sthana sub-components and the other five components are
  individually available

### Requirement: Deterministic and reproducible

Shadbala SHALL depend only on the chart's positions and ephemeris data, so
the same chart always yields the same values.

#### Scenario: Repeat computation
- **WHEN** the same chart is scored twice
- **THEN** the component and total values are identical
