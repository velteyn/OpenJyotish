# remedies Specification

## Purpose
TBD - created by archiving change add-remedy-engine. Update Purpose after archive.

## Requirements

### Requirement: Ishta Devata

The engine SHALL derive the Ishta Devata from the Karakamsa (the navamsa sign
of the Atmakaraka): the deity of the planet occupying the 12th sign from the
Karakamsa, or of that sign's lord when unoccupied. It SHALL likewise derive the
Palana Devata from the 9th from the Karakamsa.

#### Scenario: Occupied 12th from Karakamsa

- **WHEN** a planet occupies the 12th sign from the Karakamsa
- **THEN** that planet's deity is the Ishta Devata

#### Scenario: Empty 12th from Karakamsa

- **WHEN** the 12th sign from the Karakamsa is empty
- **THEN** the deity of that sign's lord is the Ishta Devata

### Requirement: Gemstone recommendation

The engine SHALL recommend the gemstone of the lagna lord or the yogakaraka,
keeping only functional benefics that are not the 6th/8th/12th lord, choosing
by highest Shadbala, and SHALL emit an explicit avoid-list (gemstones of the
6th/8th/12th lords and the nodes).

#### Scenario: Functional-benefic lagna lord

- **WHEN** the lagna lord is a functional benefic
- **THEN** its gemstone is a candidate for the primary recommendation

#### Scenario: Functional-malefic lagna lord

- **WHEN** the lagna lord is a functional malefic
- **THEN** no primary gemstone is recommended and the reason is stated

### Requirement: Planetary mantra

The engine SHALL target the planet with the lowest Shadbala (preferring a
functional benefic within 10% of the lowest) and SHALL give its beeja mantra
and the classical japa count.

#### Scenario: Weakest planet gets the mantra

- **WHEN** a chart is computed
- **THEN** the recommended mantra belongs to the lowest-Shadbala planet

### Requirement: Charity and fasting

The engine SHALL give charity items, direction and the fast day for the mantra
target planet and, when a date is supplied, for the current mahadasa lord.

#### Scenario: Charity for the weak planet

- **WHEN** a chart is computed
- **THEN** charity and fasting are given for the targeted planet

### Requirement: Dosha remedies

The engine SHALL detect Kuja (Mangal), Kaala Sarpa, Sade Sati (needs a date),
Grahana, Pitru, **Guru-Chandala**, **Shrapit (Shani-Rahu)**, **Kemadruma** and
**Daridra** doshas, and SHALL emit a remedy for each present dosha, including
the detection detail so it can be audited.

#### Scenario: Kuja dosha detected

- **WHEN** Mars occupies house 1, 2, 4, 7, 8 or 12 from the lagna
- **THEN** a Kuja-dosha remedy is emitted with the Mars house cited

#### Scenario: No dosha

- **WHEN** a dosha is absent
- **THEN** no remedy is emitted for it

### Requirement: Sourced output

Every emitted recommendation SHALL carry a non-empty `source` naming its
classical authority.

#### Scenario: Source present

- **WHEN** any recommendation is emitted
- **THEN** its `source` field is non-empty

### Requirement: Surfaces

The engine SHALL be available via a `remedies` CLI command, an AI JSON
`remedies` block, a report section, and a **GUI Remedies panel** (computing
from the current chart, with an optional partner for marriage remedies).

#### Scenario: CLI

- **WHEN** `remedies` runs for valid birth data
- **THEN** it prints the Ishta/Palana devata and the remedy items with sources

#### Scenario: GUI

- **WHEN** the Remedies panel is computed for the current chart
- **THEN** it shows the Ishta/Palana devata and the remedy items in a table

### Requirement: Yantra

The engine SHALL recommend the standard Navagraha yantra for the targeted
planet.

#### Scenario: Yantra present

- **WHEN** remedies are computed
- **THEN** a yantra recommendation is emitted for the mantra target planet

### Requirement: Dasha-lord remedy

When a date is supplied, the engine SHALL identify the running Vimsottari
mahadasa lord and emit a propitiation remedy (deity, mantra, charity), plus the
lord's gemstone when it is a functional benefic.

#### Scenario: Running lord propitiated

- **WHEN** remedies are computed with a date
- **THEN** a dasha-lord remedy is emitted for the current mahadasa lord

### Requirement: Remedy timing

The engine SHALL advise the weekday on which to begin the targeted planet's
remedies.

#### Scenario: Weekday given

- **WHEN** remedies are computed
- **THEN** a timing recommendation names the target planet's weekday

### Requirement: Marriage dosha remedies

The engine SHALL, given two charts, run the Ashta Koota and emit a sourced
remedy for each weak factor (Nadi, Bhakoota, Gana, Graha Maitri, Yoni, Vashya,
Tara/Dina, Varna), plus a Kuja/Mangal remedy for either chart when Mars is in a
Kuja house.

#### Scenario: Weak factor remedied

- **WHEN** an Ashta-Koota factor scores below its maximum
- **THEN** a marriage remedy naming that factor is emitted, with its source

#### Scenario: Strong factor skipped

- **WHEN** a factor scores full marks
- **THEN** no remedy is emitted for it

#### Scenario: Kuja from either chart

- **WHEN** Mars occupies a Kuja house in the girl's or boy's chart
- **THEN** a Kuja remedy is emitted naming whose chart it came from
