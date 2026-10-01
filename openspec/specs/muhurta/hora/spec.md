# muhurta/hora Specification

## Purpose
TBD - created by archiving change add-hora-planetary-hours. Update Purpose after archive.

## Requirements

### Requirement: Hora cycle

The living day SHALL be divided into 24 horas: 12 equal day-horas
(sunrise → sunset) and 12 equal night-horas (sunset → next sunrise). The
first hora SHALL be ruled by the weekday lord, and each subsequent hora SHALL
follow the Chaldean order Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars
(cyclic), so the first hora of the next day is that day's lord.

#### Scenario: First hora is the weekday lord

- **WHEN** the day is a Tuesday
- **THEN** the first hora is ruled by Mars, the next by Sun, then Venus, …

#### Scenario: The cycle reproduces the weekday lords

- **WHEN** the 24th hora of Tuesday ends
- **THEN** the next hora (Wednesday's first) is ruled by Mercury

### Requirement: Current hora

The module SHALL report the hora ruling a given moment; a moment before
sunrise SHALL belong to the previous Hindu day's night horas.

#### Scenario: Pre-dawn belongs to the previous night

- **WHEN** the moment is 03:30 local
- **THEN** the reported hora is a Night hora of the previous day

### Requirement: Hora surfaces

The hora cycle SHALL be available from the CLI (`hora`), the TUI Special
menu, the GUI Muhurta tab, and the AI analysis/JSON export.

#### Scenario: JSON exposes the 24 horas

- **WHEN** the chart JSON export runs
- **THEN** it contains a `hora` block with 24 slots and the day lord
