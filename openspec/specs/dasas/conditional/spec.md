# dasas/conditional Specification

## Purpose
TBD - created by archiving change spec-implemented-capabilities. Update Purpose after archive.

## Requirements

### Requirement: Eight conditional systems with true gates

The module SHALL provide the conditional nakshatra dasas with their true
positional applicability gates, not merely a birth-nakshatra test:
Dwisaptati Sama (72), Shodasottari (116), Dwadasottari (112), Panchottari
(105), Shashtihayani (60), Sataabdika (100), Chaturaaseeti Sama (84) and
Shattrimsa Sama (36).

#### Scenario: Lagna-lord placement gate
- **WHEN** the lagna lord is in the 7th or the 7th lord is in the lagna
- **THEN** Dwisaptati Sama is applicable

#### Scenario: Hora and paksha gate
- **WHEN** the lagna is in the Sun's hora in Shukla paksha, or in the Moon's
  hora in Krishna paksha
- **THEN** Shodasottari is applicable

#### Scenario: Vargas and house gates
- **WHEN** the lagna is vargottama, or in a Venus navamsa, or Cancer in both
  rasi and dwadasamsa, or the 10th lord is in the 10th
- **THEN** Sataabdika, Dwadasottari, Panchottari and Chaturaaseeti Sama are
  respectively applicable

### Requirement: Classical totals and order

Each system SHALL use its classical total and lord order, and SHALL
distribute the mahadashas from the birth nakshatra with the balance of the
first period taken from the elapsed portion of the nakshatra.

#### Scenario: Totals
- **WHEN** each system's periods are summed
- **THEN** the totals are 72, 116, 112, 105, 60, 100, 84 and 36 years
  respectively

### Requirement: Applicability listing

A CLI command SHALL list the systems applicable to a chart together with a
human-readable description of the gate that admitted each of them.

#### Scenario: Gate reasons shown
- **WHEN** the conditional list is requested for a chart
- **THEN** each applicable system is printed with its condition text

### Requirement: Deferred pravesha-keyed systems

Tithi Ashtottari and Karana Chaturaseeti Sama SHALL NOT be shipped as natal
systems; they are pravesha-chart dasas and are documented as deferred until
the pravesha plumbing is available.

#### Scenario: Not listed for natal charts
- **WHEN** the conditional systems are listed
- **THEN** Tithi Ashtottari and Karana Chaturaseeti do not appear among the
  natal conditional dasas
