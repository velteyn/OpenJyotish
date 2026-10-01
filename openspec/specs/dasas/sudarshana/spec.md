# dasas/sudarshana Specification

## Purpose
Sudarshana Chakra dasa: Parasara's progression dasa for annual, monthly and
daily fortune — the lagna progresses one sign per year.

## Requirements

### Requirement: Mahadasa progression

The mahadasas SHALL be the twelve signs from the lagna, one year each, on a
twelve-year cycle.

#### Scenario: One year per sign from the lagna

- **WHEN** Sudarshana Chakra dasa is computed
- **THEN** the signs run from the lagna zodiacally, each lasting one year

### Requirement: Antardasas

Each mahadasa SHALL divide into twelve equal antardasas, running zodiacally
from the sign of the mahadasa sign's lord by default, or from the mahadasa sign
when the option is off.

#### Scenario: Antardasas from the lord's sign

- **WHEN** the option is on (default)
- **THEN** the antardasas start at the sign occupied by the mahadasa sign's lord

#### Scenario: Antardasas from the mahadasa sign

- **WHEN** the option is off
- **THEN** the antardasas start at the mahadasa sign
