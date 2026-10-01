# dasas/kaala Specification

## Purpose
Kaala rasi dasa (time-of-day-based) — included only in its canonical
mainstream form pinned in design.md, else excluded with rationale.

## Requirements

### Requirement: Canonical form or documented exclusion
The system SHALL implement Kaala dasa in the cross-verified against published tables
mainstream form pinned in design.md — or, if no canonical form holds,
SHALL exclude it and document the rationale, leaving no stub engine
behind.

#### Scenario: Canonical form found
- **WHEN** design research confirms a mainstream Kaala computation
- **THEN** the engine runs contiguous Mahadashas with antardasas on
  the 1990 fixture.

#### Scenario: No canonical form
- **WHEN** design research finds only contradictory or proprietary
  forms
- **THEN** Kaala is excluded with a documented rationale and no engine,
  registry, or surface entry.
