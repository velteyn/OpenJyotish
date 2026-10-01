# transits Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Gochara from the natal Moon

Transit (gochara) evaluation SHALL compare the current planetary positions
against the natal chart, expressing each transiting planet's position from
the natal Moon as well as its sign and house from the lagna.

#### Scenario: Transit report
- **WHEN** transits are computed for a moment
- **THEN** each planet's current sign, house from lagna and house from the
  natal Moon are reported

### Requirement: Ashtakavarga scoring of transits

Transit favourability SHALL be scored using the natal Ashtakavarga, so a
transit's assessment reflects the chart's own BAV/SAV values rather than a
generic rule.

#### Scenario: Score present
- **WHEN** a transit is evaluated
- **THEN** an Ashtakavarga-based score accompanies the position

### Requirement: Transits never replay natal positions

Transit output SHALL be derived from freshly computed positions for the
requested moment, never reused from natal placements.

#### Scenario: Distinct moment
- **WHEN** transits are requested for a date different from the birth date
- **THEN** the reported positions reflect that date

### Requirement: Public graha-drishti API

The engine SHALL expose what each planet aspects and which planets aspect each
planet, as a first-class call independent of the strength computation.

#### Scenario: Give
- **WHEN** drishti is requested for a planet
- **THEN** the list of planets and the houses it aspects is returned

#### Scenario: Receive
- **WHEN** drishti on a planet is requested
- **THEN** the list of planets aspecting it is returned, consistent with the
  givers' lists

### Requirement: Classical special aspects

The aspect rules SHALL follow the classical scheme: all planets aspect the 7th
in full; Mars additionally the 4th and 8th; Jupiter the 5th and 9th; Saturn the
3rd and 10th; and Rahu/Ketu the 5th, 7th and 9th.

#### Scenario: Mars special aspects
- **WHEN** Mars aspects are listed
- **THEN** the 4th, 7th and 8th houses are included

#### Scenario: Jupiter special aspects
- **WHEN** Jupiter aspects are listed
- **THEN** the 5th, 7th and 9th houses are included

#### Scenario: Saturn special aspects
- **WHEN** Saturn aspects are listed
- **THEN** the 3rd, 7th and 10th houses are included

### Requirement: Mutual consistency

The give and receive views SHALL describe the same relation, so that if A
aspects B then A appears among B's aspecting planets.

#### Scenario: Symmetry of the report
- **WHEN** the give and receive views are compared for a chart
- **THEN** every aspect in one view has its counterpart in the other

### Requirement: Correct graha identity in transits

Each transit entry SHALL carry the position of the planet it names: the
Swiss-Ephemeris planet IDs SHALL be mapped in SE order (Sun, Moon, Mercury,
Venus, Mars, Jupiter, Saturn).

#### Scenario: Transits at the birth instant match the natal chart

- **WHEN** transits are computed for the birth moment
- **THEN** every planet's transit sign and longitude equal its natal values

### Requirement: Vedha of favourable transits

Gochara SHALL mark each planet whose transit house from the natal Moon is
favourable (the classical table), and SHALL flag a vedha when another planet
transits the paired obstruction house. The Sun and Saturn SHALL be exempt from
obstructing each other, and the Moon and Mercury likewise.

#### Scenario: Favourable house

- **WHEN** a planet transits a house from the Moon listed as favourable
- **THEN** its entry is marked as a good transit

#### Scenario: Obstruction

- **WHEN** a planet is in a favourable house and another planet occupies the
  paired vedha house
- **THEN** the entry is flagged as obstructed

#### Scenario: Exempt pair

- **WHEN** the only planet in the vedha house is the transiting planet's
  exempt partner (Sun↔Saturn or Moon↔Mercury)
- **THEN** the transit is not flagged as obstructed

#### Scenario: Surfaces

- **WHEN** the CLI `transit`, the report or the JSON export runs
- **THEN** the vedha state is shown alongside each transit
