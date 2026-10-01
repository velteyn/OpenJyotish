# kp/dasa-view Specification

## Purpose
TBD - created by archiving change 2026-09-23-add-kp-vimsottari-view. Update Purpose after archive.

## Requirements

### Requirement: KP reading of a Vimsottari mahadasa

The module SHALL expose `kp_dasa_lords(cd)`, returning the nine Vimsottari
mahadasas in order. Each row SHALL carry the lord, its start/end Julian day,
its duration, and — read from the lord's *natal* position — the Placidus
bhava it occupies and its fourfold chain (sign / star / sub / sub-sub lord).
The years SHALL be the standard Vimsottari periods, unmodified.

#### Scenario: Nine mahadasas, one per graha

- **WHEN** `kp_dasa_lords` runs for a chart
- **THEN** it returns nine rows whose lords are the nine grahas

#### Scenario: The chain is the lord's natal chain

- **WHEN** a row's lord is Jupiter
- **THEN** its chain equals `lord_chain(jupiter_natal_longitude)` and its
  bhava is the Placidus house of that longitude

### Requirement: KP reading of the running chain

The module SHALL expose `kp_dasa_levels(cd, when=None, max_levels=3)`,
returning the active Mahadasa → Antardasa → Pratyantardasa chain at a local
date/time (default: the current instant). Each level SHALL be annotated with
the lord's Placidus bhava and fourfold chain.

#### Scenario: The chain nests

- **WHEN** a running chain is returned
- **THEN** each level's interval is contained in the level above it and the
  Mahadasa matches the corresponding row of `kp_dasa_lords`

#### Scenario: Deterministic for a fixed date

- **WHEN** `kp_dasa_levels` is called twice with the same date
- **THEN** the lord sequence is identical

### Requirement: KP dasa surfaces

The KP dasa view SHALL be available from the CLI (`kp`, with `--when`), the
GUI KP tab, and the AI JSON export.

#### Scenario: JSON exposes the dasa lords

- **WHEN** the chart JSON export runs
- **THEN** the `kp` block contains `dasa_lords` with nine entries, each
  carrying the lord, period, bhava and the four chain lords
