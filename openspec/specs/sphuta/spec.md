# Sphuta Specification

## Purpose

Prasna Marga Sphuta (auspicious-point) longitudes computed from explicit
planetary/upagraha longitudes, exposed through the CLI.

## Requirements

### Requirement: Sphuta computation

The module SHALL compute TriSphuta (Lagna+Moon+Gulika), ChatusSphuta
(+Sun), PanchaSphuta (+Rahu), Prana (5×Lagna+Gulika), Deha (8×Moon+Gulika),
Mrityu (7×Gulika+Sun), Beeja (Jupiter+Venus+Sun), Kshetra
(Jupiter+Moon+Mars), Yoga (Sun+Moon), Tithi (Moon−Sun), Rahu Tithi (Rahu−Sun),
Yogi (Yoga+93°20') and Avayoga (Yogi+186°40'), all modulo 360°, as pure
functions of explicit longitudes.

#### Scenario: Worked-example agreement

- **WHEN** the Sphutas compute for 2001-02-24 06:11 +0530 Jalkot
- **THEN** the planet-only Sphutas, Tithi and Rahu Tithi match the reference
  within 0.1°

#### Scenario: Structural identities hold

- **WHEN** any inputs are given
- **THEN** Chatus−Tri ≡ Sun, Pancha−Chatus ≡ Rahu (mod 360)

### Requirement: CLI Sphuta surface

A `sphutas` CLI command SHALL print the nine Sphutas with local longitudes
for birth data, taking Gulika from the temporal upagrahas.

#### Scenario: CLI prints the table

- **WHEN** `sphutas` runs for valid birth data
- **THEN** output lists all nine Sphutas with degree values

### Requirement: Yogi family

The module SHALL derive the Yogi planet (nakshatra lord of the Yogi
Sphuta), the Avayogi planet (nakshatra lord of the Avayoga Sphuta) and the
Sahayogi (Duplicate Yogi, the sign lord of the Yogi point).

#### Scenario: Worked example

- **WHEN** Sun = 24°19'06" and Moon = 85°31'45" (IndiaDivine example)
- **THEN** Yogi is Jupiter, Avayogi is Sun and Sahayogi is Venus
