# dasas/rasi-bhukta-vimsottari Specification

## Purpose
TBD - created by archiving change add-rasi-bhukta-vimsottari. Update Purpose after archive.

## Requirements

### Requirement: Rasi-Bhukta Vimsottari dasa

Rasi-Bhukta Vimsottari SHALL use the standard Vimsottari mahadasas (nine
planets from the Moon's nakshatra balance), and within each mahadasa SHALL
divide the period into twelve equal antardasas whose signs run zodiacally from
the mahadasa lord's sign.

#### Scenario: Mahadasas are Vimsottari

- **WHEN** Rasi-Bhukta Vimsottari is computed
- **THEN** its mahadasas equal the Vimsottari mahadasas (same lords, durations)

#### Scenario: Antardasas are twelve rasis from the lord's sign

- **WHEN** a mahadasa is expanded
- **THEN** its twelve equal antardasas run from the mahadasa lord's sign
  zodiacally through all twelve rasis
