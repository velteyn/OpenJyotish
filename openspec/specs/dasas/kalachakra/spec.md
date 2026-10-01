# dasas/kalachakra Specification

## Purpose
TBD - created by archiving change spec-core-dasa-systems. Update Purpose after archive.

## Requirements

### Requirement: Nakshatra-based sign sequence

Kalachakra SHALL use the Raghavaacharya method: the **nine-sign** sequence
belonging to the Moon's nakshatra group (Savya-I/II, Apasavya-I/II) and pada,
with the fixed sign durations (Aries 7 … Pisces 10), the running sign taken
from the fraction of the pada the Moon has traversed, and antardasas by
iteration (the sequence associated with the mahadasa sign).

#### Scenario: Sequence shape
- **WHEN** a chart is computed
- **THEN** the mahadasa signs follow the nine-sign sequence of the birth
  group and pada, and the first period is the running sign with the balance
  from the pada fraction

### Requirement: Paramayush context

The engine SHALL expose the birth group's paramayush together with the deha
and jiva rasis, which the classical system uses to interpret the periods.

#### Scenario: Context available
- **WHEN** the dasa is computed for a chart
- **THEN** the paramayush, deha and jiva information is available to the
  caller alongside the periods
