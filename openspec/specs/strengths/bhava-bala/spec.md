# strengths/bhava-bala Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: House strength from classical components

Bhava Bala SHALL evaluate the strength of each of the twelve bhavas from
the classical components — positional (kendra/panapara/apoklima), aspect
strength on the bhava madhya, directional strength, the house lord's
Shadbala, and the aspect contribution on that lord.

#### Scenario: Twelve houses scored
- **WHEN** Bhava Bala is computed for a chart
- **THEN** all twelve houses receive a strength value derived from those
  components

### Requirement: House ranking available

The engine SHALL allow the houses to be ordered by strength, which is the
form readings use.

#### Scenario: Ranking
- **WHEN** the houses are ranked
- **THEN** they are returned from strongest to weakest with their values

### Requirement: Bhava Bala for any varga

Bhava Bala SHALL be computable for any divisional chart, using that varga's
house cusps, positions and lord strength, and SHALL leave the rasi-chart result
unchanged.

#### Scenario: Varga house strength
- **WHEN** Bhava Bala is requested for a varga
- **THEN** all twelve houses of that varga receive strength values

#### Scenario: Rasi unchanged
- **WHEN** Bhava Bala is computed with no varga
- **THEN** the rasi result matches the existing computation

### Requirement: Selectable on the surfaces

Per-varga Bhava Bala SHALL be selectable from the CLI and shown in the report.

#### Scenario: CLI
- **WHEN** a varga is passed with the Bhava Bala command
- **THEN** that varga's house strengths are displayed
