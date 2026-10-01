# Dasas Niryana-Shoola Specification

## Purpose

Niryana-Shoola rasi dasa tracks the motion of prana (life) from the
stronger of the 2nd and 8th houses, for longevity readings where the
8th-house (randhra) condition dominates the question.

## Requirements

### Requirement: Seed at the stronger of 2nd and 8th houses
The system SHALL seed the 12-Mahadasha sequence at the stronger of the
2nd and 8th houses from lagna (same BPHS stronger-sign determination
as Brahma), running forward when the seed is odd (1-based odd sign)
and backward otherwise.

#### Scenario: Fixture seed and direction
- **WHEN** computed for the 1990 Bangalore fixture (8th Capricorn
  beats 2nd Cancer by occupancy; Capricorn 1-based even → reverse)
- **THEN** the sequence runs backward from Capricorn: Capricorn,
  Sagittarius, Scorpio, Libra, Virgo, Leo, Cancer, Gemini, Taurus,
  Aries, Pisces, Aquarius.

### Requirement: Fixed 7/8/9 modality durations totaling 96
The system SHALL assign each sign 7 years if movable, 8 if fixed, 9 if
dual, totaling exactly 96 years on every chart.

#### Scenario: Fixture durations
- **WHEN** computed for the 1990 fixture
- **THEN** durations are [7,9,8,7,9,8,7,9,8,7,9,8] and sum to 96.

### Requirement: Forward proportional antardasas
Each Mahadasha SHALL subdivide into 12 antardasas cycling forward from
itself, durations proportional to the cycle signs' own year values.

#### Scenario: Antardasa integrity
- **WHEN** any Mahadasha is expanded
- **THEN** its 12 antardasas sum to the Mahadasha duration and the first
  names the Mahadasha sign itself.

### Requirement: Mainstream scope only
The system SHALL NOT offer variant seeds or year tables in this change;
unsupported options SHALL be rejected or absent rather than guessed.

#### Scenario: Out-of-scope request
- **WHEN** a caller requests a non-standard Niryana-Shoola variant
- **THEN** the system either uses the standard rule documented above or
  raises a clear error naming the unsupported option.
