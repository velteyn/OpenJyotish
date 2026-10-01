# varga-charts Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Divisional charts from longitudes

The engine SHALL compute the divisional (varga) chart for every supported
division (D-2 through D-144, twenty-three levels) from the planets'
sidereal longitudes, and SHALL compute the varga position of the lagna by
the same rule.

#### Scenario: Navamsa mapping
- **WHEN** a longitude is mapped to D-9
- **THEN** the resulting sign follows the classical navamsa rule for that
  longitude (the same rule applied to the lagna gives the navamsa lagna)

#### Scenario: Identity at D-1
- **WHEN** the varga is D-1
- **THEN** every position equals the rasi position

### Requirement: Named variants per division

Divisions that admit more than one reading SHALL expose the classical
variants (in addition to the default) so the caller can select them
explicitly instead of relying on a hidden convention.

#### Scenario: Variant selection
- **WHEN** a division with variants is requested with a named variant
- **THEN** the mapping for that variant is applied and the default is
  unchanged when no variant is given

### Requirement: Varga chart data

A computed varga SHALL carry, for each planet, its varga sign, the degrees
within that sign's division, and the varga lagna, so downstream modules
(chalit, arudhas, karakas) can consume it without recomputing.

#### Scenario: Downstream consumption
- **WHEN** a varga is computed
- **THEN** its per-planet signs and the varga lagna are available together

### Requirement: Classical default start signs

The DEFAULT mapping for a division SHALL start each sign's divisions from the
classical start sign:

- D-2 Hora: odd signs Leo then Cancer; even signs Cancer then Leo.
- D-3 Drekkana: sign, 5th, 9th.
- D-4 Chaturthamsa: sign, 4th, 7th, 10th.
- D-7 Saptamsa: odd signs from the sign; even signs from the 7th.
- D-9 Navamsa: movable from itself, fixed from the 9th, dual from the 5th.
- D-10 Dasamsa: odd signs from the sign; even signs from the 9th.
- D-12 Dwadasamsa: from the sign.

#### Scenario: Navamsa of a fixed sign

- **WHEN** a planet is at 17° Taurus
- **THEN** its navamsa is Gemini (Taurus → Capricorn start, 6th part)

#### Scenario: Navamsa of a dual sign

- **WHEN** a planet is at 22° Gemini
- **THEN** its navamsa is Aries (Gemini → Libra start, 7th part)

#### Scenario: Hora

- **WHEN** a planet is in the first half of an odd sign
- **THEN** its D-2 sign is Leo

### Requirement: Remaining classical default start signs

The DEFAULT mapping SHALL start each sign's divisions from the classical start
sign for these divisions:

- D-16 Shodasamsa: movable → Aries, fixed → Leo, dual → Sagittarius.
- D-20 Vimsamsa: movable → Aries, fixed → Sagittarius, dual → Leo.
- D-24 Siddhamsa: odd signs → Leo, even signs → Cancer.
- D-27 Bhamsa: fire → Aries, earth → Cancer, air → Libra, water → Capricorn.
- D-30 Trimsamsa: the five unequal bands, each mapped to its lord's own sign.
- D-40 Khavedamsa: odd signs → Aries, even signs → Libra.
- D-45 Akshavedamsa: movable → Aries, fixed → Leo, dual → Sagittarius.

#### Scenario: Shodasamsa of a fixed sign

- **WHEN** a planet is in a fixed sign
- **THEN** its D-16 starts from Leo

#### Scenario: Trimsamsa bands

- **WHEN** a planet is at 3° of an odd sign
- **THEN** its D-30 is Aries (Mars's band); at 7° it is Aquarius (Saturn's)

#### Scenario: Bhamsa by element

- **WHEN** a planet is in a watery sign
- **THEN** its D-27 starts from Capricorn
