# export Specification

## Purpose
TBD - created by archiving change add-chalit-varga-and-report-tables. Update Purpose after archive.

## Requirements

### Requirement: Reports cover the computed subsystems

The report SHALL include the chart's special lagnas, arudha padas, chara
karakas and KP lord chains, in addition to the existing positions, cusps,
strength, ashtakavarga, yoga, sahama, vimsopaka, dasa and transit sections.

#### Scenario: Special lagnas
- **WHEN** a report is generated
- **THEN** a special-lagna table lists each lagna with its sign

#### Scenario: Arudha padas
- **WHEN** a report is generated
- **THEN** a table lists the twelve bhava arudha padas with their classical
  names, and the graha padas, with the upapada and darapada identifiable

#### Scenario: Chara karakas
- **WHEN** a report is generated
- **THEN** the eight chara karakas are listed with their planets and signs

#### Scenario: KP chains
- **WHEN** a report is generated
- **THEN** a KP table shows the sign, star, sub and sub-sub lord for each
  house cusp and planet

### Requirement: Report values match the engine

Every table SHALL be produced from the same computation functions used by the
CLI, so a reported value never disagrees with the corresponding command.

#### Scenario: Consistency
- **WHEN** a value in a report is compared with the CLI output for the same
  chart
- **THEN** they agree

### Requirement: Reports remain printable

New sections SHALL follow the existing styling and remain printable (the
print stylesheet SHALL apply to them).

#### Scenario: Print
- **WHEN** a report is printed
- **THEN** the new tables render readably with the rest of the report

### Requirement: Per-varga strength in the export

The report SHALL include a strength section with Shadbala and Bhava Bala
computed for every divisional chart, and the JSON export SHALL expose the same
data in a `varga_strength` block.

#### Scenario: Report matrices
- **WHEN** a full report is generated
- **THEN** it shows a Shadbala matrix (vargas × planets) and a Bhava Bala
  matrix (vargas × houses)

#### Scenario: JSON block
- **WHEN** the chart JSON export runs
- **THEN** `varga_strength` contains `shadbala` and `bhava_bala` keyed by
  varga name, each covering all planets/houses

#### Scenario: Engine parity
- **WHEN** a per-varga value is compared with the engine for the same varga
- **THEN** they agree
