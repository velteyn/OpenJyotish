# dasa/chart Specification

## Purpose
TBD - created by archiving change 2026-09-23-add-dasa-chart-view. Update Purpose after archive.

## Requirements

### Requirement: Dasa chart rows

The module SHALL expose `dasa_chart_rows(periods, when_jd, depth=3)`, returning
the period tree flattened around `when_jd`: every top-level period, then the
children of the running period at each deeper level, up to `depth` levels.
Exactly one period per level SHALL be flagged active.

#### Scenario: Running branch only

- **WHEN** the tree is flattened to depth 3
- **THEN** all mahadasas are listed, and only the running mahadasa's
  antardasas and the running antardasa's pratyantardasas are listed

#### Scenario: Nesting

- **WHEN** a child period is active
- **THEN** its interval lies within its active parent's interval

### Requirement: Dasa chart surfaces

The dasa chart SHALL be available from the CLI (`dasa-chart`, with `--at` and
`--depth`) and the GUI dasa tab.

#### Scenario: CLI default date

- **WHEN** `dasa-chart` runs without `--at`
- **THEN** the running branch is computed for the current instant
