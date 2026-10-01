# dasas/narayana-variants Specification

## Purpose
TBD - created by archiving change add-narayana-family-variants. Update Purpose after archive.

## Requirements

### Requirement: Lagnamsaka dasa

Lagnamsaka SHALL be a Narayana-family rasi dasa seeded from the **stronger of
the lagna and its 7th house** (the satya-peetha rule), resolved by the Jaimini
sign-strength ladder, sharing Narayana's progression, period lengths and
antardasas.

#### Scenario: First period is the lagna

- **WHEN** the lagna is stronger than the 7th from it
- **THEN** the first mahadasa is the lagna sign

#### Scenario: First period is the 7th when it is stronger

- **WHEN** the 7th from the lagna is stronger than the lagna
- **THEN** the first mahadasa is the 7th sign

### Requirement: Padanaathaamsa dasa

Padanaathaamsa SHALL be a Narayana-family rasi dasa seeded from the sign
occupied by the lord of the Arudha Lagna (pada = arudha, natha = lord,
amsa = sign).

#### Scenario: First period is the AL lord's sign

- **WHEN** Padanaathaamsa dasa is computed
- **THEN** the first mahadasa is the sign the Arudha Lagna's lord occupies

### Requirement: Single-direction twelve-sign progression

The Narayana-family sign sequence SHALL be a single-direction run of all twelve
signs from the seed, the direction set by the foot of the ninth sign from the
seed (odd ninth → zodiacal, even ninth → anti-zodiacal).

#### Scenario: Twelve distinct signs

- **WHEN** any seed is used
- **THEN** the sequence contains twelve distinct signs
