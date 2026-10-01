# Dasas Karaka Specification

## Purpose

Karaka rasi dasa times life through the sign of a chosen chara karaka
(Dara for marriage, Putra for children, Matri, Bhratri), for relationship
and family readings in the standard SJC form.

## Requirements

### Requirement: Sequence starts at the chosen karaka's sign
The system SHALL start the 12-Mahadasha sequence at the rasi occupied by
the holder of the requested chara karaka role (Putra, Matri, Bhratri,
Dara; unknown roles rejected with a clear error), running forward
zodiacally from that sign. Roles rank planets by degrees traversed
within their sign — except Rahu, ranked by mirrored degrees (30° minus
in-sign longitude, reflecting retrograde motion), and Ketu, which is
excluded; exact ties keep input order.

#### Scenario: Fixture Dara start
- **WHEN** computed for the 1990 fixture with the default Dara role
  (Dara Karaka Sun in Capricorn)
- **THEN** the first Mahadasha lord is Capricorn and the sequence runs
  forward: Capricorn, Aquarius, Pisces, Aries, Taurus, Gemini, Cancer,
  Leo, Virgo, Libra, Scorpio, Sagittarius.

### Requirement: Chara durations with the Rao dual-lord exception
The system SHALL use Chara lord-distance durations (inclusive
sign-to-lord count minus one, footed directions, own sign 12, full
circle 11) with the mainstream Rao exception for Scorpio/Aquarius (a
planet sitting in its own dual-ruled sign alone loses to its co-lord),
consistent with Varnada on the same chart. No exaltation /
debilitation adjustment.

#### Scenario: Fixture durations
- **WHEN** computed for the 1990 fixture (Mars in Scorpio, Ketu in
  Cancer: Ketu wins, Scorpio runs 8 years)
- **THEN** durations are [1,1,9,7,8,6,11,7,9,3,8,6] and sum to 76.

### Requirement: Parity antardasas with proportional durations
Each Mahadasha SHALL subdivide into 12 antardasas cycling from itself in
parity direction (odd MD forward, even MD backward), durations
proportional to each cycle sign's own year value.

#### Scenario: Antardasa parity and sums
- **WHEN** the fixture Capricorn (even) Mahadasha is expanded
- **THEN** antardasas run backward from Capricorn, sum to the Mahadasha
  duration, and the first names Capricorn itself.
