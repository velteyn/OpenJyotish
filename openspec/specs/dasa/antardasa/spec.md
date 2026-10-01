# Dasa Antardasa Specification

## Purpose

Vimsottari sub-periods follow the universal rule: within any period,
sub-periods run in cycle order starting from the period's own lord.

## Requirements

### Requirement: Sub-periods rotate from the parent lord

Within a mahadasa ruled by planet X, antardashas SHALL run X first, then the
following cycle lords in order. The rule SHALL apply recursively at every
subdivision level (pratyantardasa within antardasa starts from the AD lord,
and so on). Mahadasa-level sequencing and birth-balance fractions SHALL NOT
change.

#### Scenario: Mars MD opens with Mars AD

- **WHEN** a Mars mahadasa is computed
- **THEN** its first antardasa is Mars, followed by Rahu, Jupiter, and so on
  in cycle order

#### Scenario: Rotation recurses to deeper levels

- **WHEN** a pratyantardasa list is built inside a Venus antardasa
- **THEN** its first entry is Venus, followed in cycle order

#### Scenario: Sibling dasa systems unchanged

- **WHEN** any non-Vimsottari dasa computes its periods
- **THEN** its sub-period order is byte-identical to before this change
