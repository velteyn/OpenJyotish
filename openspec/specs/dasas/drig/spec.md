# dasas/drig Specification

## Purpose
Drig (Drigdasa) is the phalita rasi dasa of religious and spiritual activity,
built on Jaimini rasi drishti (sign aspects). It gives twelve sign mahadasas
totalling 96 years, with twelve equal antardasas in a fixed sign cycle.

## Requirements

### Requirement: Mahadasa order

The mahadasa cycle SHALL start from the lagna and take the 9th, 10th and 11th
signs from it, in that order. For each such sign the cycle SHALL list the sign
itself together with the three signs that aspect it by Jaimini rasi drishti:
movable signs aspect the fixed signs and vice versa (excluding the adjacent
sign), and dual signs aspect the other dual signs.

#### Scenario: Aspect groups

- **WHEN** the mahadasa cycle is built
- **THEN** each of the 9th/10th/11th signs from lagna is expanded to a
  four-sign group of the sign plus its three aspecting signs

#### Scenario: Reference order

- **WHEN** Drig is computed for a Gemini lagna
- **THEN** the mahadasa order is Aquarius, Aries, Cancer, Libra, Pisces,
  Sagittarius, Virgo, Gemini, Aries, Aquarius, Scorpio, Leo

### Requirement: Sign durations

Each mahadasa SHALL last 7 years for a movable sign, 8 for a fixed sign and
9 for a dual sign, giving a 96-year cycle.

#### Scenario: 96-year cycle

- **WHEN** the twelve mahadasas are summed
- **THEN** the total is 96 years

### Requirement: Antardasas

Antardasas SHALL divide each mahadasa into twelve equal parts, in the fixed
sign cycle associated with the mahadasa sign.

#### Scenario: Equal splits

- **WHEN** a mahadasa's antardasas are listed
- **THEN** there are twelve of equal length and they fill the mahadasa
  contiguously
