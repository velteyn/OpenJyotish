# Birth Time Specification

## Purpose

Birth time displays and day/night-sensitive calculations must use the true
local birth time derived from the chart's Julian day, never the
date-only birth date field which is always midnight.

## Requirements

### Requirement: Day/night determination uses true local time

Sahamas day/night selection SHALL be driven by the true local birth time:
births at 06:00–18:00 local use the day formula, all others the night
formula. The date-only birth date field SHALL NOT be used for this decision.

#### Scenario: Day birth gets day-formula Sahamas

- **WHEN** a chart has a 10:30 local birth time
- **THEN** its Sahamas match the day-formula computation, not the night one

#### Scenario: Night birth keeps night-formula Sahamas

- **WHEN** a chart has a 02:00 local birth time
- **THEN** its Sahamas match the night-formula computation

### Requirement: Pranapada/Vighati lagnas use true birth time

Pranapada and Vighati lagnas SHALL be computed from the true local birth
time, so charts sharing a day and place but differing in birth time get
markedly different lagnas instead of near-identical midnight-based ones.

#### Scenario: Lagnas shift with birth time

- **WHEN** two charts share a day and place but differ by 8.5 h of birth time
- **THEN** Pranapada and Vighati differ markedly between the charts (over 90°
  apart), where the midnight-based computation keeps them within a degree

### Requirement: Saved chart time uses true birth time

Charts saved to the database from the TUI SHALL store the true local birth
time in hours, not midnight.

#### Scenario: TUI save preserves birth time

- **WHEN** a 10:30 chart is saved from the TUI
- **THEN** the stored `time_hours` reads 10.5, not 0.0

### Requirement: Janma Ghatis uses true birth time

The displayed Janma Ghatis SHALL be measured from the true local birth time,
not from midnight.

#### Scenario: Ghatis reflect the birth hour

- **WHEN** a chart has a non-midnight birth time
- **THEN** the reported Ghatis differ from the midnight-based value by the
  birth time offset
