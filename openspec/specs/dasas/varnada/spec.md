# Dasas Varnada Specification

## Purpose

Varnada rasi dasa times life through the Varnada Lagna (social order and
duty), for charts where profession and dharma questions dominate the reading.

## Requirements

### Requirement: Varnada Lagna from Lagna and Hora Lagna
The system SHALL compute the Varnada sign as: odd lagna (0-based even
index) → VL = (lagN + hlN − 2) mod 12 + 1; even lagna → VL = (lagN −
hlN + 12) mod 12 + 1, where lagN/hlN are 1-based and hlN comes from the
Hora Lagna longitude (Sun's sign fallback when Hora Lagna is absent).

#### Scenario: Fixture Varnada sign
- **WHEN** computed for the 1990 fixture (Gemini lagna, Hora Lagna in Scorpio)
- **THEN** Varnada Lagna is Capricorn.

### Requirement: VL-parity sequence with Chara durations
The system SHALL run 12 Mahadashas from Varnada Lagna — forward for odd
Varnada, backward for even — with Chara lord-distance durations (odd
signs forward, even signs backward, own sign 12, full circle 11, dual
Scorpio/Aquarius lords under the mainstream Rao own-sign exception: a
planet sitting in its own dual-ruled sign alone loses to its co-lord).
Counts run forward from odd-footed signs and backward from even-footed
ones, minus one (own sign 12, full circle 11); no exaltation /
debilitation adjustment.

#### Scenario: Fixture sequence
- **WHEN** computed for the 1990 fixture (Varnada Capricorn, even)
- **THEN** the sequence runs backward: Capricorn, Sagittarius, Scorpio,
  Libra, Virgo, Leo, Cancer, Gemini, Taurus, Aries, Pisces, Aquarius,
  with durations [1,6,8,3,9,7,11,6,8,7,9,1].

### Requirement: Proportional forward antardasas
Each Mahadasha SHALL subdivide into 12 antardasas cycling forward from
itself, durations proportional to the cycle signs' own year values.

#### Scenario: Antardasa integrity
- **WHEN** any Mahadasha is expanded
- **THEN** its 12 antardasas sum to the Mahadasha duration and the first
  names the Mahadasha sign itself.

### Requirement: Hora Lagna input plumbing
Callers SHALL supply the true Hora Lagna longitude as `hora_lagna_lon`
on every app surface that holds a full chart (CLI, GUI, TUI, AI, JSON
export); only callers without ephemeris access SHALL fall back to the
Sun's sign, documented as a fallback.

#### Scenario: Missing Hora Lagna
- **WHEN** computed without hora_lagna_lon
- **THEN** the sequence still completes using the documented fallback.

#### Scenario: App surfaces use the true Hora Lagna
- **WHEN** computed for the 1990 fixture through the CLI/GUI chart path
  (Hora Lagna in Scorpio)
- **THEN** Varnada Lagna is Capricorn and the sequence runs backward
  from Capricorn.

### Requirement: Every implemented dasa on every surface
Every dasa system implemented in `src/jhora/dasas/` SHALL be selectable
in the CLI `dasa` command, the GUI Dasas combo, the TUI dasa engine, the
AI dasa snapshot, and the JSON `dasa.systems` export — no implemented
system SHALL be silently absent from any surface.

#### Scenario: Surface completeness
- **WHEN** the 1990 fixture is run through each surface's dasa listing
- **THEN** karaka, moola, shoola, trikona and varnada are all available
  alongside the nakshatra and earlier rasi systems.
