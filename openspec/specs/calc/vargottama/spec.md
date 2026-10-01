# calc/vargottama Specification

## Purpose
Vargottama: a planet or the lagna holding the same rasi in the rasi chart
(D-1) and a divisional chart. D-9 is the classical case, where a vargottama
planet is strengthened; the concept extends to every varga.

## Requirements

### Requirement: Vargottama detection

The system SHALL report, for every planet and the lagna, the varga levels in
which the body occupies the same rasi as in D-1, and SHALL expose this through
the CLI.

#### Scenario: Per-planet vargottama vargas

- **WHEN** vargottama is computed for a chart
- **THEN** each body lists the vargas whose sign equals its D-1 sign, with D-1
  itself excluded

#### Scenario: CLI view

- **WHEN** the `vargottama` command is run
- **THEN** it prints each planet's rasi, whether it is D-9 vargottama, and the
  full list of vargottama vargas, plus the lagna row
