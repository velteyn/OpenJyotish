# arudha Specification

## Purpose
TBD - created by archiving change spec-implemented-capabilities. Update Purpose after archive.

## Requirements

### Requirement: Bhava arudha computation

The module SHALL compute the arudha pada of each of the twelve bhavas by the
classical rule (count from the bhava to its lord and again as far from the
lord), with the classical exception that a result falling in the bhava
itself or its 7th moves to the 10th therefrom.

#### Scenario: Arudha lagna and Dara pada
- **WHEN** the arudhas are computed for a chart
- **THEN** A1 (arudha lagna) and A7 (Dara pada) follow the classical
  counting rule and the 1/10 exception

### Requirement: Classical pada names

Each bhava arudha SHALL carry its classical name and the full synonym set
(A1 Arudha/Pada lagna, A2 Dhana/Vitta pada, …, A7 Dara pada, A12
Upapada/Gaunapada/Moksha pada), exposed through a name helper and the JSON
export.

#### Scenario: Names available per pada
- **WHEN** the pada name for house 7 or 12 is requested
- **THEN** "Dara pada" and "Upapada" are returned respectively

### Requirement: Graha arudhas and names

Arudhas SHALL be computed for all nine grahas from the sign occupied in the
chart of interest and the sign owned by that graha (stronger sign for dual
ownership), and each SHALL carry a classical name of the form
"<Sanskrit name> pada".

#### Scenario: Mercury's pada
- **WHEN** the graha arudha name for Mercury is requested
- **THEN** "Budha pada" is returned

### Requirement: Upapada and Darapada first-class

Upapada (A12) and Darapada (A7) SHALL be available as dedicated outputs and
as explicit JSON fields, in addition to their place in the twelve-pada
table.

#### Scenario: JSON exposes both
- **WHEN** a chart is exported to JSON
- **THEN** the arudha section contains explicit `upapada` and `darapada`
  signs alongside the twelve-pada list

### Requirement: Arudhas on any divisional chart

Arudhas SHALL be computable on any divisional chart by using the varga
signs of the planets and of the lagna; a CLI command SHALL expose the bhava
and graha arudhas for a chosen varga.

#### Scenario: Navamsa arudhas
- **WHEN** arudhas are requested with `--varga D-9`
- **THEN** the twelve bhava and nine graha arudhas are returned from the
  navamsa positions
