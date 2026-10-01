# karakas Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Eight chara karakas by degree

The engine SHALL rank the eight chara karakas by the degrees a planet has
travelled in its sign, in descending order, assigning Atma, Amatya,
Bhratru, Matru, Pitru, Putra, Gnati and Dara karaka in turn, with the
lord of the descending order as Dara karaka.

#### Scenario: Ranking and roles
- **WHEN** chara karakas are computed for a chart
- **THEN** the eight roles are assigned in descending degree order

### Requirement: Rahu mirrored

For the purpose of ranking, Rahu SHALL be measured from the end of its
sign (its degrees mirrored) so its rank compares correctly with the other
planets.

#### Scenario: Rahu's degrees
- **WHEN** Rahu participates in the ranking
- **THEN** its sort value is the mirror of its longitude within the sign

### Requirement: Positions accompany roles

Each karaka SHALL be reported with the planet holding the role and that
planet's sign and degree, so a reading can quote the karaka's placement.

#### Scenario: Karaka placement
- **WHEN** karakas are listed
- **THEN** each role names its planet together with that planet's sign
