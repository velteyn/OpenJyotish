# dasas/pravesha Specification

## Purpose
TBD - created by archiving change spec-implemented-capabilities. Update Purpose after archive.

## Requirements

### Requirement: Yoga Pravesha return chart

The module SHALL find the annual moment at which the (Sun + Moon) longitude
returns to its natal value, computing in the chart's sidereal frame and
rebuilding the chart from the local wall clock.

#### Scenario: Angle recurs
- **WHEN** the Yoga Pravesha chart for a target year is computed
- **THEN** the (Sun + Moon) longitude at that moment matches the natal angle
  within a fraction of a degree

### Requirement: Nakshatra Pravesha return chart

The module SHALL find the monthly moment at which the Moon returns to its
natal sidereal longitude.

#### Scenario: Lunar return
- **WHEN** the Nakshatra Pravesha chart for a month is computed
- **THEN** the Moon's longitude at that moment matches the natal longitude
  within a fraction of a degree

### Requirement: Tithi Pravesha wall-clock correctness

The Tithi Pravesha chart SHALL be rebuilt from local wall-clock time, not
from the UT returned by the ephemeris, so the chart matches the birth
place's timezone.

#### Scenario: Local rebuild
- **WHEN** a Tithi Pravesha chart is computed for a non-UTC birth place
- **THEN** the chart's local time corresponds to the computed instant

### Requirement: Pravesha-keyed dasas

The module SHALL provide Tithi Ashtottari, Tithi Yogini, Karana
Chaturaseeti Sama and Yoga Vimsottari, each selecting its starting lord and
span from the chart's tithi / karana / yoga index, with the balance taken
from the elapsed fraction of that span.

#### Scenario: Totals
- **WHEN** each system's periods are summed
- **THEN** the totals are 108, 36, 84 and 120 years respectively

#### Scenario: Index selection
- **WHEN** a chart's tithi, karana and yoga indices are derived
- **THEN** the corresponding starting lords follow the classical tables

### Requirement: No invented Karana Pravesha finder

A standalone Karana Pravesha finder SHALL NOT be shipped, because no
canonical definition was found in the mainstream sources; the Karana
Chaturaseeti dasa remains available for use on Tithi Pravesha charts.

#### Scenario: Dasa without finder
- **WHEN** the Karana Chaturaseeti dasa is computed for a chart
- **THEN** it uses that chart's karana, with no dedicated finder offered
