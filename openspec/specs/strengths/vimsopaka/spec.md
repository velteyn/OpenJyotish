# strengths/vimsopaka Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Four classical schemes

Vimsopaka SHALL provide the four classical schemes (Shadvarga, Saptavarga,
Dasavarga and Shodasavarga), each weighting the included divisional charts
so the total contribution is twenty points.

#### Scenario: Scheme weights
- **WHEN** a scheme's weights are inspected
- **THEN** the weights for its vargas sum to twenty

### Requirement: Per-planet score

Each scheme SHALL produce a per-planet score out of twenty, derived from
the planet's dignity in each contributing varga.

#### Scenario: Score range
- **WHEN** Vimsopaka is computed for a chart
- **THEN** every planet's score lies between zero and twenty inclusive
