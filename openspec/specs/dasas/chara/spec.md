# Dasas Chara Specification

## Purpose

Chara rasi dasa is the general-purpose Jaimini timing system: twelve rasi
Mahadashas of variable Chara-rule lengths run once through all signs in a
single direction, for life-direction and status readings cross-checked
against Vimsottari.

## Requirements

### Requirement: Twelve distinct signs in a single direction
The system SHALL run the 12 Mahadashas through 12 distinct rasis in one
direction for the whole cycle — direct (savya, zodiacal) or reverse
(apasavya) — set once from the lagna by the K.N. Rao 9th-from-lagna rule
(direct when the 9th sign from lagna is odd-footed — Aries, Taurus,
Gemini, Libra, Scorpio, Sagittarius (Jaimini footedness, not index
parity); reverse otherwise), matching the mainstream tradition reference. Verified
against the lagna group tables (all 12 lagnas) and the dual-source
rule statement.

#### Scenario: Fixture runs twelve distinct signs
- **WHEN** computed for the 1990 Bangalore fixture (Gemini lagna, 9th
  Aquarius not odd-footed → reverse)
- **THEN** the 12 Mahadasha lords are Gemini, Taurus, Aries, Pisces,
  Aquarius, Capricorn, Sagittarius, Scorpio, Libra, Virgo, Leo, Cancer
  with contiguous dates from birth.

### Requirement: Chara durations with the Rao dual-lord exception
The system SHALL assign each sign its Chara lord-distance duration:
inclusive sign-to-lord count minus one (forward from odd-footed signs
— Aries, Taurus, Gemini, Libra, Scorpio, Sagittarius — backward from
even-footed ones; own sign 12, full circle 11), with Scorpio
(Mars/Ketu) and Aquarius (Saturn/Rahu) following the mainstream Rao
exception: a planet sitting in its own dual-ruled sign alone loses to
its co-lord; otherwise the stronger lord applies. No exaltation /
debilitation adjustment.

#### Scenario: Fixture durations match the shared cycle
- **WHEN** computed for the 1990 fixture (Scorpio runs 8 via Ketu under
  the Rao exception)
- **THEN** durations are [7,8,6,11,7,9,3,8,6,1,1,9] and sum to 76.

### Requirement: Proportional antardasas in cycle direction
Each Mahadasha SHALL subdivide into 12 antardasas running the cycle
direction from the MD sign, durations proportional to each cycle sign's
own year value.

#### Scenario: Antardasa integrity
- **WHEN** any Mahadasha is expanded
- **THEN** its 12 antardasas sum to the Mahadasha duration and the first
  names the Mahadasha sign itself.

### Requirement: Exaltation exception option

Chara dasa SHALL offer the classical Exaltation Exception. When enabled, a
sign's Chara duration SHALL be raised by one year if the sign's resolved lord
occupies its exaltation sign, and lowered by one if the lord occupies its
debilitation sign. When disabled, the plain sign-to-lord count SHALL be used.

#### Scenario: Exalted lord adds a year

- **WHEN** the option is on and a sign's lord sits in its exaltation sign
- **THEN** that sign's duration is one year longer than the plain count

#### Scenario: Debilitated lord removes a year

- **WHEN** the option is on and a sign's lord sits in its debilitation sign
- **THEN** that sign's duration is one year shorter than the plain count

#### Scenario: Option off

- **WHEN** the option is off
- **THEN** the durations are the plain sign-to-lord counts, unchanged
