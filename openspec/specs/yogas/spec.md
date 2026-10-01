# yogas Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Yoga detection over the whole chart

The engine SHALL detect the supported classical yogas from the chart's
positions, and each detected yoga SHALL carry its name, category, the
planets involved, a strength or intensity value and a description.

#### Scenario: Detection result shape
- **WHEN** yogas are detected for a chart
- **THEN** every returned yoga states its name, category, involved planets
  and description

### Requirement: Pancha Mahapurusha yogas

The five Pancha Mahapurusha yogas (Ruchaka, Bhadra, Hamsa, Malavya,
Sasa) SHALL be detected when the ruling planet occupies a kendra in its
own sign, moolatrikona or exaltation.

#### Scenario: Ruchaka
- **WHEN** Mars is in a kendra in Aries, Scorpio or Capricorn
- **THEN** Ruchaka is reported

### Requirement: Deterministic detection

Yoga detection SHALL be a pure function of the chart, so the same chart
always yields the same set of yogas.

#### Scenario: Repeat detection
- **WHEN** yoga detection runs twice on one chart
- **THEN** the detected sets are identical

### Requirement: Conjunction yogas

The engine SHALL detect Budha-Aditya Yoga when the Sun and Mercury occupy one
sign, and Chandra-Mangala Yoga when the Moon and Mars occupy one sign.

#### Scenario: Budha-Aditya
- **WHEN** the Sun and Mercury are in the same sign
- **THEN** Budha-Aditya Yoga is reported

#### Scenario: Chandra-Mangala
- **WHEN** the Moon and Mars are in the same sign
- **THEN** Chandra-Mangala Yoga is reported

### Requirement: Adhi Yoga

The engine SHALL detect Adhi Yoga when natural benefics occupy the 6th, 7th or
8th house from the Moon, graded by how many of those houses are occupied
(one → a leader, two → a minister, three → a king).

#### Scenario: Graded strength
- **WHEN** benefics occupy all three of the 6th, 7th and 8th from the Moon
- **THEN** Adhi Yoga is reported with strong intensity

### Requirement: Lagnaadhi Yoga

The engine SHALL detect Lagnaadhi Yoga when benefics occupy both the 7th and
8th houses from the lagna and no malefic conjoins or aspects them.

#### Scenario: Affliction blocks the yoga
- **WHEN** a malefic conjoins or aspects a benefic in the 7th or 8th
- **THEN** Lagnaadhi Yoga is not reported

### Requirement: Vasumati Yoga

The engine SHALL detect Vasumati Yoga when benefics occupy the upachaya houses
(3, 6, 10, 11) from the lagna, with full strength only when no malefic
occupies an upachaya.

#### Scenario: Malefic weakens
- **WHEN** a benefic and a malefic both occupy upachaya houses
- **THEN** Vasumati Yoga is reported with reduced intensity
