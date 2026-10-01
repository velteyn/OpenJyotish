# dignities Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Classical dignity states

The engine SHALL determine a planet's dignity in a sign as one of
exaltation, debilitation, moolatrikona, own sign or neutral, using the
classical tables including the moolatrikona degree ranges, and SHALL
report the nodes under a node-appropriate state rather than misapplying
the planetary tables.

#### Scenario: Moolatrikona degree range
- **WHEN** a planet sits inside its moolatrikona degree range
- **THEN** it is reported as moolatrikona

#### Scenario: Exaltation and debilitation
- **WHEN** a planet sits in its sign of exaltation or debilitation
- **THEN** the corresponding state is reported

### Requirement: Nodes handled distinctly

Rahu and Ketu SHALL be evaluated by their own rule (with their own
exaltation/debilitation conventions) instead of the seven-planet table.

#### Scenario: Node dignity
- **WHEN** a node's dignity is requested
- **THEN** it is determined by the nodal rule

### Requirement: Tattva of planets and signs

The engine SHALL report the tattva (element) of each planet and each sign:
planets by their classical element (Sun/Venus fire, Moon/water, Mars fire,
Mercury earth, Jupiter akasha, Saturn air, nodes air), and signs by their
element group (Aries/Leo/Sagittarius fire, Taurus/Virgo/Capricorn earth,
Gemini/Libra/Aquarius air, Cancer/Scorpio/Pisces water).

#### Scenario: Planet tattva
- **WHEN** a planet's tattva is requested
- **THEN** it returns that planet's classical element

#### Scenario: Sign tattva
- **WHEN** a sign's tattva is requested
- **THEN** it returns the sign's element group

### Requirement: Friendly tattva relation

The engine SHALL expose the friendly-tattva relation, treating fire and air as
friendly and earth and water as friendly, with akasha friendly to all, and it
SHALL name the pair's relationship.

#### Scenario: Friendly pair
- **WHEN** the relation between two friendly elements is requested
- **THEN** it is reported as friendly

#### Scenario: Opposite pair
- **WHEN** the relation between fire and water is requested
- **THEN** it is reported as inimical

### Requirement: Tattva in the dignity result

The dignity computation SHALL carry the planet tattva and the sign tattva
alongside the existing dignity state, without changing the existing state.

#### Scenario: Dignity with tattva
- **WHEN** a planet's dignity is computed
- **THEN** the result includes its dignity state and both tattvas
