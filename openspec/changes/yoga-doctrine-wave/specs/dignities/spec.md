# Spec Delta

## ADDED Requirements

### Requirement: Natural friend/enemy dignity

Planets placed outside exaltation, debilitation, moolatrikona and own
sign SHALL be graded friend, enemy or neutral by the sign lord's
natural (naisargika) relationship to the planet; nodes ruling a sign
count as neutral.

#### Scenario: Friend
- **WHEN** a planet occupies a natural friend's sign
- **THEN** dignity is friend

#### Scenario: Enemy
- **WHEN** a planet occupies a natural enemy's sign
- **THEN** dignity is enemy

### Requirement: Inimical Vimsopaka quarter

Vimsopaka SHALL score inimical placements at one quarter of the varga
weight (matching the published 1 / 3-4 / 1-2 / 1-4 / 0 ladder).

#### Scenario: Quarter share
- **WHEN** a planet is inimical in a varga
- **THEN** its component score is weight times 0.25
