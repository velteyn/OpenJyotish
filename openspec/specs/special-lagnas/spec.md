# special-lagnas Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Special lagna set

The engine SHALL compute the chart's special lagnas — including Bhava,
Hora, Ghati, Sree, Upapada, Pranapada, Vighati, Indu, Nakshatra, Varnada
and Bhrigu Bindu — each as a longitude resolved to a sign, together with a
short description of its meaning.

#### Scenario: Full set returned
- **WHEN** special lagnas are computed for a chart
- **THEN** each named special lagna is returned with its sign and a
  description

### Requirement: Time-derived lagnas use true sunrise

Special lagnas that are functions of elapsed time SHALL be derived from
the chart's true sunrise and sunset for the birth place, consistent with
the solar-time rules.

#### Scenario: Sunrise dependence
- **WHEN** a time-derived special lagna is computed
- **THEN** it uses the chart's true sunrise rather than a fixed hour

### Requirement: User-configurable special lagna

The engine SHALL support a user-defined special lagna parameterised by a
planet, a multiplier and an optional reverse direction, and SHALL surface
it wherever special lagnas are displayed or exported.

#### Scenario: Configured special lagna
- **WHEN** a user special lagna is configured (for example a planet-based
  ninth harmonic)
- **THEN** it appears in the special-lagna output alongside the built-in
  ones

### Requirement: Correct body for the User's Special Lagna base

The User's Special Lagna base SHALL use the correct Swiss-Ephemeris body for
the chosen planet, mapped in SE order (Sun, Moon, Mercury, Venus, Mars,
Jupiter, Saturn).

#### Scenario: Rise longitude matches the body

- **WHEN** the rise longitude for a planet is computed
- **THEN** it equals that body's longitude at the computed rise time
