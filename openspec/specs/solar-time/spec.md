# Solar Time Specification

## Purpose

Every surface that needs sunrise or sunset uses one precise computation, day
phases follow the true sun, and saved charts carry east-positive timezones
that reload correctly.

## Requirements

### Requirement: Single precise sunrise/sunset source

All sunrise/sunset needs SHALL resolve through one swe-based computation
returning local hours; formula guesses and incompatible raw swe calls SHALL
not be used. The natal panel SHALL display live Sunrise/Sunset times instead
of "N/A".

#### Scenario: Panel shows live sun times

- **WHEN** the natal panel populates for a chart with valid ephemeris data
- **THEN** Sunrise/Sunset render as clock times and Janma Ghatis is nonzero
  for a non-sunrise birth

#### Scenario: Special lagnas track the true sun

- **WHEN** Pranapada/Vighati compute for a chart
- **THEN** their sunrise reference equals the canonical computation within a
  minute

### Requirement: True-sun day phases in Shadbala

Nathonnata, Tribhaga, and Hora strengths SHALL key day/night and phase
boundaries off true sunrise/sunset (not 6:00/18:00), keeping each component's
established shape and lord tables (noon/midnight peaks, solar-anchored
periods, 7-lord hora cycle). Hora length SHALL be one twelfth of the true
day/night span, not one clock hour.

#### Scenario: Dawn birth differs from noon birth

- **WHEN** two charts share a day and place, one born near sunrise and one at
  noon
- **THEN** their Hora/Tribhaga/Nathonnata grades differ where the old
  clock-hour math agreed

#### Scenario: Noon behavior preserved

- **WHEN** a birth falls well inside undisputed day hours
- **THEN** grades match the pre-change values (same lords, same peaks)

### Requirement: East-positive saved timezones

GUI save, GUI JHD export, and TUI save SHALL store `tz_offset` as signed
hours east of UTC (matching both load paths and the JHD format), instead of
the internal west-positive value or unparsed strings.

#### Scenario: Save/load round-trip preserves timezone

- **WHEN** an IST (+0530) chart is saved and reloaded into the form
- **THEN** the timezone field reads east-positive (+5.5), not inverted,
  garbage, or blank
