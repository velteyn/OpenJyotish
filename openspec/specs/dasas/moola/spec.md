# dasas/moola Specification

## Purpose
TBD - created by archiving change add-moola-dasa. Update Purpose after archive.

## Requirements

### Requirement: Per-planet year correction

Moola dasa SHALL give each planet a period of `abs(vimsottari_years[planet]
- correction)` years, where the correction is the distance from the planet's
sign to its moolatrikona sign reduced modulo twelve, set to twelve when the
planet occupies its moolatrikona sign, increased by one when the planet is
exalted in its sign, and reduced by one when it is debilitated. A correction
that cancels the Vimsottari period SHALL fall back to the full period.

#### Scenario: Ordinary correction
- **WHEN** a planet's correction is computed
- **THEN** it is `(moolatrikona_sign - planet_sign) mod 12`

#### Scenario: In moolatrikona
- **WHEN** a planet occupies its moolatrikona sign
- **THEN** the correction is twelve

#### Scenario: Exalted
- **WHEN** a planet occupies its sign of exaltation
- **THEN** the correction is one more than the ordinary correction

#### Scenario: Debilitated
- **WHEN** a planet occupies its sign of debilitation
- **THEN** the correction is one less than the ordinary correction

#### Scenario: Years never negative
- **WHEN** the correction exceeds the planet's Vimsottari years
- **THEN** the period is the absolute difference

#### Scenario: Zero falls back to the full period
- **WHEN** the correction equals the planet's Vimsottari years
- **THEN** the period is the full Vimsottari period

### Requirement: Mahadasa sequence

The mahadasa order SHALL anchor at the sign holding the most bodies among the
Lagna, Sun and Moon signs (the Lagna counting as a body in its own sign). From
that sign it SHALL walk the twelve signs by the kendra jumps (1st, 4th, 7th,
10th, then 2nd, 5th, 8th, 11th, then 3rd, 6th, 9th, 12th) in three four-sign
groups. Within each group signs SHALL be ranked by the number of planets they
hold, then by exaltation and debilitation counts, then by the sign's own/ruled
strength and modality. Within a sign, planets SHALL be ranked by dignity
(exalted, then non-debilitated, then own sign, then rulership) and finally by
longitude.

#### Scenario: Base anchor
- **WHEN** the mahadasas are laid out
- **THEN** the sign with the most bodies among the Lagna, Sun and Moon signs
  leads the cycle

#### Scenario: Validated reference order
- **WHEN** Moola is computed for the 1970-04-04 23:18 Chennai chart
- **THEN** the planet order is Sun, Moon, Rahu, Ketu, Mars, Venus, Mercury,
  Saturn, Jupiter

### Requirement: Antardasa rotation

Antardasas SHALL rotate to start from the mahadasa lord, as in the other
planetary dasas.

#### Scenario: Rotation
- **WHEN** a mahadasa's antardasas are listed
- **THEN** the first is the mahadasa's own lord

### Requirement: Repeated cycles

The engine SHALL repeat the cycle to cover the requested span, recomputing
the planet periods each cycle, since the correction depends on the
progressed placement.

#### Scenario: Second cycle
- **WHEN** more than one cycle is requested
- **THEN** a further cycle is appended with its periods recomputed

### Requirement: Tara variant

Tara dasa SHALL be available as the same construction without the
moolatrikona correction, plus dasa sesham, and SHALL be selectable wherever
Moola is.

#### Scenario: Tara differs from Moola
- **WHEN** Tara is computed
- **THEN** planets in their moolatrikona sign are not given the correction-of-twelve

### Requirement: Node exaltation

The nodes SHALL use the Saravali/Parasara reading: Rahu exalted in Gemini and
Ketu exalted in Sagittarius (with the corresponding debilitations), and their
own signs Rahu in Virgo and Ketu in Pisces.

#### Scenario: Rahu in Gemini
- **WHEN** Rahu occupies Gemini
- **THEN** the correction receives the exaltation adjustment

#### Scenario: Ketu in Sagittarius
- **WHEN** Ketu occupies Sagittarius
- **THEN** the correction receives the exaltation adjustment

### Requirement: Base reference inclusion switches

The engine SHALL allow each of the Lagna, Sun and Moon base references to be
disabled independently. A disabled reference SHALL count as empty when the
anchor sign is chosen, and the anchor SHALL otherwise be the most-occupied of
the enabled references (ties resolved by sign strength).

#### Scenario: One reference disabled

- **WHEN** the Sun is disabled and the Moon shares the Sun's sign
- **THEN** the anchor is unchanged, because that sign is still occupied by the
  Moon

#### Scenario: Two references disabled

- **WHEN** both the Sun and the Moon are disabled
- **THEN** the anchor is chosen from the Lagna sign alone

### Requirement: Tara dasa definitions

Tara dasa SHALL offer two definitions. **Parasara's** SHALL be the Vimsottari
planetary sequence starting from the lord of the 9th sign from the lagna.
**Pt Sanjay Rath's** SHALL be the Moola sign-family walk anchored at the lagna.
Both SHALL use the full Vimsottari years.

#### Scenario: Parasara definition

- **WHEN** Tara dasa is computed for a chart with the Parasara definition
- **THEN** the mahadasas are the Vimsottari sequence from the 9th-from-lagna
  lord, each with its full Vimsottari period

#### Scenario: Rath definition

- **WHEN** Tara dasa is computed with Rath's definition
- **THEN** the mahadasas are the planets collected in the Moola family walk
  from the lagna, each with its full Vimsottari period

### Requirement: Tara sesham and direction options

The engine SHALL allow the first mahadasa's balance to be the Moon's nakshatra
fraction remaining (optionally reversed for apasavya nakshatras) or dropped
entirely, and SHALL allow the walk direction to be reckoned from the Moon's
nakshatra instead of the sign.

#### Scenario: Sesham moves the anchor before birth

- **WHEN** the sesham is enabled
- **THEN** the first mahadasa begins before birth, with birth falling inside it

#### Scenario: No sesham starts at birth

- **WHEN** the sesham is disabled
- **THEN** the first mahadasa begins at birth
