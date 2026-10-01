# Panchanga Karana Specification

## Purpose

Karana names follow the classical 60-half-tithi rule everywhere they appear,
computed once from Sun/Moon elongation instead of three divergent formulas.

## Requirements

### Requirement: Elongation-exact karana

Karana SHALL be derived from the half-tithi serial k = floor(elongation/6):
k=0 Kimstughna; k=1..56 the movable cycle Bava, Balava, Kaulava, Taitila,
Gara, Vanija, Vishti repeating; k=57/58/59 Shakuni, Chatushpada, Naga. All
surfaces (calculator, panel, AI snapshot) SHALL share this computation.

#### Scenario: First-half Krishna Chaturthi

- **WHEN** elongation falls in 216–222°
- **THEN** karana is Balava (not Taitula)

#### Scenario: Fixed karanas at the junctions

- **WHEN** elongation falls in 342–348° / 348–354° / 354–360° / 0–6°
- **THEN** karana is Shakuni / Chatushpada / Naga / Kimstughna respectively

#### Scenario: AI snapshot carries panchanga

- **WHEN** analysis text builds for any chart
- **THEN** it contains a panchanga section with tithi, nakshatra, yoga,
  karana, and weekday drawn from real fields
