# Spec Delta

## ADDED Requirements

### Requirement: Raja Yoga sambandha and grading

Raja Yoga SHALL be reported for a kendra lord and a kona lord in
conjunction or in mutual 7th aspect, graded medium; mutual exchange
stays covered by Parivartana Yoga (strong).

#### Scenario: Mutual aspect
- **WHEN** a kendra lord and a kona lord aspect each other mutually
- **THEN** Raja Yoga is reported with medium strength

#### Scenario: Conjunction grade
- **WHEN** a kendra lord and a kona lord are conjoined
- **THEN** Raja Yoga is reported with medium strength

### Requirement: Viparita Raja Yoga placement rule

Viparita Raja Yoga SHALL be reported when a 6th/8th/12th lord is
placed in a trik house (Harsha for the 6th lord, Sarala for the 8th,
Vimala for the 12th), or in its own sign; two trik lords conjoined
outside trik houses SHALL NOT report it.

#### Scenario: Harsha
- **WHEN** the 6th lord occupies the 6th, 8th or 12th house
- **THEN** Viparita Raja Yoga (Harsha) is reported once

#### Scenario: Conjunction elsewhere
- **WHEN** two trik lords conjoin in a non-trik house
- **THEN** no Viparita Raja Yoga is reported

### Requirement: Amala Yoga benefic restriction

Amala Yoga SHALL be reported only for a natural benefic
(Jupiter, Venus, Mercury) in the 10th from the lagna.

#### Scenario: Moon in the 10th
- **WHEN** only the Moon occupies the 10th
- **THEN** Amala Yoga is not reported

### Requirement: Kala Sarpa both arcs

The engine SHALL report Kala Sarpa Yoga when all planets lie between
Rahu and Ketu, and Kala Amrita Yoga when all lie between Ketu and
Rahu.

#### Scenario: Reverse arc
- **WHEN** all planets fall in the Ketu-to-Rahu half
- **THEN** Kala Amrita Yoga is reported

### Requirement: Flanking exclusions

Sunapha/Anapha/Durudhara, Vesi/Vosi/Ubhayachari and Kemadruma SHALL
count only the five star-planets as company; the luminaries, Rahu
and Ketu never qualify.

#### Scenario: Nodal flanker
- **WHEN** only Ketu flanks the Moon
- **THEN** Kemadruma Yoga is reported and no Anapha Yoga is
