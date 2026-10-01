# Dasas Shoola Specification

## Purpose

Shoola rasi dasa shows the force of Shiva (destruction) through fixed
9-year periods from the stronger of lagna and 7th, for longevity,
maraka and severe-illness timing.

## Requirements

### Requirement: Seed at the stronger of lagna and 7th
The system SHALL seed the 12-Mahadasha sequence at the stronger of
a reference house and 7th from it, resolved by the Jaimini sign-strength
ladder (`calc/jaimini_strength.stronger_rasi`), running forward zodiacally.
The reference house defaults to lagna (self, house 1); callers SHALL be able
to pass house 9 (Pitri/father), 7 (Dara/spouse) or 5 (Putra/children).

#### Scenario: Fixture seed
- **WHEN** computed for the 1990 Bangalore fixture (7th Sagittarius
  beats lagna Gemini by occupancy)
- **THEN** the sequence runs forward from Sagittarius: Sagittarius,
  Capricorn, Aquarius, Pisces, Aries, Taurus, Gemini, Cancer, Leo,
  Virgo, Libra, Scorpio.

#### Scenario: Fixture Pitri seed
- **WHEN** computed for the 1990 fixture with house 9 (Aquarius;
  7th from it Leo holds the Moon)
- **THEN** the sequence runs forward from Leo with [9] * 12.

#### Scenario: Ladder tie-break
- **WHEN** both candidate signs are empty (house 5, Libra vs Aries)
- **THEN** the Jaimini ladder decides — Aries wins

### Requirement: Fixed 9-year durations totaling 108
The system SHALL assign every sign 9 years, totaling exactly 108 years
on every chart.

#### Scenario: Fixture durations
- **WHEN** computed for the 1990 fixture
- **THEN** durations are [9] * 12 and sum to 108.

### Requirement: Forward proportional antardasas
Each Mahadasha SHALL subdivide into 12 antardasas cycling forward from
itself, durations proportional to the cycle signs' own year values
(equal 9-year shares here, preserving the house convention; mainstream tradition's
antardasa-start variants remain out of scope).

#### Scenario: Antardasa integrity
- **WHEN** any Mahadasha is expanded
- **THEN** its 12 antardasas sum to 9 years and the first names the
  Mahadasha sign itself.
