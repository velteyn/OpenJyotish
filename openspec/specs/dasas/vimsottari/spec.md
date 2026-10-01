# dasas/vimsottari Specification

## Purpose
TBD - created by archiving change spec-core-dasa-systems. Update Purpose after archive.

## Requirements

### Requirement: 120-year nine-lord cycle

Vimsottari SHALL use the nine-lord cycle in the classical order beginning
with Ketu, with the classical year lengths summing to 120 years.

#### Scenario: Cycle shape
- **WHEN** the engine's cycle is inspected
- **THEN** it holds nine lords, begins with Ketu, and its years sum to 120

### Requirement: Nakshatra-seeded balance

The first mahadasha SHALL start from the birth nakshatra's lord with the
balance taken from the elapsed portion of the nakshatra, unless the caller
selects the full-period option; the seed reference SHALL be selectable
(Moon by default, plus lagna, Sun, and the Kshema/Utpanna/Adhana taras).

#### Scenario: Balance from the nakshatra
- **WHEN** a chart is computed with the default options
- **THEN** the first period begins at the birth instant and its length is
  the remaining fraction of the nakshatra times the lord's full period

### Requirement: Sub-periods rotate from the parent lord

Sub-periods SHALL run in cycle order starting from the parent period's own
lord, recursively at every level, and the tree SHALL be computable down to
the deepest supported level.

#### Scenario: First sub-period
- **WHEN** the sub-periods of any mahadasha are listed
- **THEN** the first sub-period lord is the mahadasha lord

### Requirement: Year definition respected

The engine SHALL honour the shared year-definition option (solar, savana,
tithi) when converting periods to dates.

#### Scenario: Savana year
- **WHEN** the savana year definition is selected
- **THEN** a one-year period spans 360 days

### Requirement: Additional classical seed points

Nakshatra dasas SHALL accept the remaining classical seed points in addition to
the Moon, lagna, Sun and the Kshema/Utpanna/Adhana taras: the Maandi and
Trisphuta seeds (from the upagraha and sphuta longitudes, computed when the
option is selected), and the Devi and Brahma nakshatra seeds.

#### Scenario: Maandi seed
- **WHEN** the Maandi seed is selected
- **THEN** the cycle starts from the nakshatra of the chart's Gulika/Maandi
  position

#### Scenario: Trisphuta seed
- **WHEN** the Trisphuta seed is selected
- **THEN** the cycle starts from the nakshatra of the Trisphuta longitude

#### Scenario: Default unchanged
- **WHEN** no seed option is given
- **THEN** the cycle starts from the Moon's nakshatra exactly as before

### Requirement: AD construction methods

The antardasa construction SHALL be selectable between the supported classical
methods: the Rao & Rath rotation (current default), Dr. Raman's
first-fraction method, continuous antardasas, and the Raghavacharya
navamsa-progression method. Each method SHALL be reachable through the option
set and SHALL leave the default unchanged.

#### Scenario: Method selection
- **WHEN** an AD method is selected
- **THEN** the antardasas are constructed by that method while mahadasas are
  unchanged

#### Scenario: Default unchanged
- **WHEN** no AD method is given
- **THEN** the Rao & Rath rotation is used exactly as before

#### Scenario: Mahadasa invariance
- **WHEN** only the AD method changes
- **THEN** the mahadasas are identical across methods
