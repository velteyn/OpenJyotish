# chalit Specification

## Purpose
TBD - created by archiving change spec-core-calculation. Update Purpose after archive.

## Requirements

### Requirement: Cusp-based houses beside whole-sign houses

The Chalit (Bhava) chart SHALL report, for each planet, both its
whole-sign house and its cusp-based house, and SHALL state whether the
planet changed house between the two.

#### Scenario: Moved planet
- **WHEN** a planet's longitude falls past a cusp boundary
- **THEN** its chalit house differs from its sign house and the move is
  reported

### Requirement: Cusps from the lagna

House cusps SHALL be derived from the lagna longitude on an equal-house
basis, and a longitude SHALL be assigned to the house whose cusp interval
contains it, including across the zero-degree boundary.

#### Scenario: Cusp interval
- **WHEN** a longitude is evaluated against the cusps
- **THEN** it falls in exactly one house, including when the interval
  wraps past 360 degrees

### Requirement: Available for every varga

Chalit analysis SHALL be computable for each divisional chart, using that
varga's positions and lagna.

#### Scenario: Per-varga chalit
- **WHEN** chalit is requested for a varga level
- **THEN** the report is built from that varga's lagna and positions

### Requirement: Any varga on every surface

Chalit SHALL be selectable for any supported varga on the CLI, the GUI and the
report, not only D-1 and D-9, using the same cusp-based computation for every
level.

#### Scenario: CLI varga selection
- **WHEN** a user requests chalit for a specific varga level
- **THEN** the sign-house, cusp-house and moved flag for each planet are shown
  for that varga

#### Scenario: GUI varga selection
- **WHEN** the user changes the varga in the Houses & Chalit view
- **THEN** the chalit table is recomputed for that varga

### Requirement: Varga chalit uses the varga lagna

For any varga other than D-1, the chalit cusps SHALL be derived from that
varga's own lagna and the planets' varga longitudes, never from the rasi
positions.

#### Scenario: Varga positions drive the result
- **WHEN** chalit is computed for a divisional chart
- **THEN** the houses and shifts are those of the varga chart

### Requirement: Present in the report

The report SHALL include a chalit section for at least the rasi chart, showing
each planet's sign house, cusp house and whether it moved.

#### Scenario: Report section
- **WHEN** a report is generated
- **THEN** a chalit table appears with the moved planets marked
