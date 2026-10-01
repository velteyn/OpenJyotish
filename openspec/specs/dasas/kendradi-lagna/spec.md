# Dasas Kendradi Lagna Specification

## Purpose

Lagna Kendradi Rasi dasa runs the kendras from the stronger of lagna
and 7th house for career and status timing where angular strength
dominates the reading.

## Requirements

### Requirement: Kendra-jump order from lagna/7th seed
The system SHALL seed at the stronger of lagna and 7th (BPHS
determination), run MDs in kendra jumps ([0,3,6,9,1,4,7,10,2,5,8,11]
offsets) times the cycle direction: forward if Saturn occupies the
seed, backward if Ketu does, else forward for odd (index-even) seeds.

#### Scenario: Fixture seed and order
- **WHEN** computed for the 1990 Bangalore fixture (7th Sagittarius
  beats lagna Gemini by occupancy; Saturn occupies it → forward)
- **THEN** MDs run Sagittarius, Pisces, Gemini, Virgo, Capricorn,
  Aries, Cancer, Libra, Aquarius, Taurus, Leo, Scorpio.

### Requirement: Counted durations with equal directed antardasas
Each MD SHALL last its Narayana-style counted duration (same
footed-minus-one Chara rule with the Rao exception, no exaltation
adjustment); antardasas SHALL split it equally among 12 signs in the
directed order of the same Saturn/Ketu/parity rule.

#### Scenario: Antardasa integrity
- **WHEN** any Mahadasha is expanded
- **THEN** 12 equal antardasas sum to the Mahadasha duration starting
  from the directed child order.
