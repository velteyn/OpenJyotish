# Dasas Sthira Specification

## Purpose

Sthira rasi dasa times longevity through fixed modality periods from the
Brahma planet's sign, for charts where ayur (longevity and health-crisis)
questions dominate the reading.

## Requirements

### Requirement: Sthira sequence starts at the Brahma planet's sign
The system SHALL start the 12-Mahadasha sequence at the rasi occupied
by the Brahma planet (same determination as `BrahmaDasa`: stronger of
6th/8th/12th lords from the stronger of lagna and 7th).

#### Scenario: Fixture start sign
- **WHEN** computed for the 1990 Bangalore fixture (Brahma Venus in
  Capricorn)
- **THEN** the first Mahadasha lord is Capricorn.

### Requirement: Fixed 7/8/9 modality durations totaling 96
The system SHALL assign each sign 7 years if movable (Aries, Cancer,
Libra, Capricorn), 8 if fixed (Taurus, Leo, Scorpio, Aquarius), 9 if
dual (Gemini, Virgo, Sagittarius, Pisces), totaling exactly 96 years on
every chart.

#### Scenario: Fixture durations
- **WHEN** computed for the 1990 fixture
- **THEN** durations are [7,8,9,7,8,9,7,8,9,7,8,9] and sum to 96.

### Requirement: Forward order with proportional forward antardasas
The system SHALL run Mahadashas forward zodiacally from the start sign;
each Mahadasha SHALL subdivide into 12 antardasas cycling forward from
itself, durations proportional to the cycle signs' own year values.

#### Scenario: Antardasa integrity
- **WHEN** any Mahadasha is expanded
- **THEN** its 12 antardasas sum to the Mahadasha duration and the first
  names the Mahadasha sign itself.

### Requirement: Mainstream scope only
The system SHALL NOT offer variant start rules or alternate year tables
in this change; unsupported options SHALL be rejected or absent rather
than guessed.

#### Scenario: Out-of-scope request
- **WHEN** a caller requests a non-standard Sthira variant
- **THEN** the system either uses the standard rule documented above or
  raises a clear error naming the unsupported option.
