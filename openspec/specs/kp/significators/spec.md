# kp/significators Specification

## Purpose
TBD - created by archiving change 2026-09-23-add-kp-significators. Update Purpose after archive.

## Requirements

### Requirement: Bhava significators

The module SHALL expose `significators(cd)`, returning the significators of
each bhava (1-12) in Krishnamurti's order of strength:

1. planets in the star of an occupant of the bhava,
2. the occupants of the bhava,
3. planets in the star of the owner of the bhava,
4. the owner of the bhava.

The owner SHALL be the lord of the sign in which the bhava's Placidus cusp
falls. A planet playing several roles SHALL list them all.

#### Scenario: Owner is the cusp sign lord

- **WHEN** a bhava cusp falls in a sign
- **THEN** that sign's lord appears with the role `owner`

#### Scenario: Occupants are significators

- **WHEN** a planet occupies a bhava by Placidus cusp
- **THEN** it appears among that bhava's significators with the role `occupant`

### Requirement: Inverse significator view

The module SHALL expose `significator_houses(cd)`, mapping each planet to the
bhavas it signifies; it SHALL be consistent with `significators`.

#### Scenario: Inverse is consistent

- **WHEN** a planet signifies a bhava in `significators`
- **THEN** that bhava appears in the planet's list in `significator_houses`

### Requirement: KP significator surfaces

The significators SHALL be available from the CLI (`kp`), the GUI KP tab and
the AI JSON export, and the KP dasa view SHALL show the bhavas each dasa lord
signifies.

#### Scenario: JSON exposes the significators

- **WHEN** the chart JSON export runs
- **THEN** the `kp` block contains `significators` with twelve entries, each
  listing planets and their roles
