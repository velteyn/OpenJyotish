# kuja-dosha Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Mars affliction from three references

Kuja Dosha SHALL be assessed from Mars's placement in houses 1, 2, 4, 7,
8 or 12 counted from the lagna, from the Moon and from Venus, and SHALL
report which of those references are afflicted.

#### Scenario: Afflicted reference
- **WHEN** Mars occupies one of the affliction houses from a reference
- **THEN** that reference is reported as afflicted

### Requirement: Classical cancellations

The engine SHALL apply the classical cancellation rules before concluding
the dosha, including Mars in its own sign weakening the dosha, Mars
conjoined with or aspected by Jupiter cancelling it, and lagna-specific
exemptions where Mars rules favourable houses for that ascendant.

#### Scenario: Jupiter cancellation
- **WHEN** Mars is conjoined with or aspected by Jupiter
- **THEN** the dosha is reported as cancelled

#### Scenario: Lagna exemption
- **WHEN** the ascendant is such that Mars rules a trine or quadrant
- **THEN** the dosha is reported as weakened for that lagna

### Requirement: Verdict with reasoning

The result SHALL state an overall verdict together with the observed
placements and the cancellation rules that applied, so a reading can
explain the conclusion.

#### Scenario: Explained verdict
- **WHEN** Kuja Dosha is computed
- **THEN** the verdict is accompanied by the placements and applied
  cancellations

### Requirement: Whole-sign counting in Kuja Dosha

Kuja Dosha SHALL count whole-sign houses from the lagna, Moon and Venus, and
its graha-drishti cancellation check SHALL use sign-based aspects.

#### Scenario: Sign boundary

- **WHEN** Mars is in the sign after the reference but within 30° of it
- **THEN** it is counted in house 2, not house 1

#### Scenario: Aspect is sign-based

- **WHEN** a planet in the 7th sign from Mars is checked for aspect
- **THEN** it is treated as aspecting Mars regardless of the exact degrees
