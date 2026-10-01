# tajaka Specification

## Purpose
TBD - created by archiving change add-tajaka-subperiod-charts. Update Purpose after archive.

## Requirements

### Requirement: Six duodecimal return levels

The engine SHALL provide the six Tajaka return levels, whose period lengths are
the successive duodecimal divisions of the Tajaka year: annual (1 year),
monthly (1/12), 2.5-day (1/144), 5-hr (1/1728), 25-min (1/20736) and 2-min
(1/248832), using a solar year of 365.2425 days.

#### Scenario: Level durations
- **WHEN** the level durations are reported
- **THEN** each equals the solar year divided by the corresponding power of
  twelve (annual 365.2425 d, monthly ≈ 30.437 d, 2.5-day ≈ 2.536 d,
  5-hr ≈ 5.073 h, 25-min ≈ 25.36 min, 2-min ≈ 2.114 min)

#### Scenario: Level nesting
- **WHEN** a level is compared with the next finer level
- **THEN** exactly twelve finer periods make one period of the coarser level

### Requirement: Annual chart is the solar return

The annual level SHALL remain the varsha pravesh solar return — the moment the
Sun returns to its natal longitude — and SHALL honour the existing tropical and
true variants.

#### Scenario: Solar return
- **WHEN** the annual chart for a target year is computed
- **THEN** it is cast at the moment the Sun returns to the natal Sun longitude

### Requirement: Sub-period charts at period commencement

A chart for a level and an index SHALL be cast at the commencement of that
sub-period. The index SHALL be one-based, so index 1 of every level is the
moment its parent period begins, and the moment of index i SHALL be the level's
anchor plus (i − 1) times the level's duration. An out-of-range index SHALL be
rejected rather than silently wrapped.

#### Scenario: Index one is the parent moment
- **WHEN** index 1 of any sub-level is requested
- **THEN** its moment equals the anchor moment of that level's parent period

#### Scenario: Offsets are uniform
- **WHEN** successive indices of a level are requested
- **THEN** their moments are separated by exactly one level duration

#### Scenario: Invalid index
- **WHEN** an index of zero, a negative index, or an index beyond the level's
  twelve periods is requested
- **THEN** the engine reports an error instead of wrapping

### Requirement: Anchor of the Tajaka year

Sub-period offsets SHALL be measured from the varsha pravesh solar-return
moment, which begins the Tajaka year, and the anchor used SHALL be reported
with every computed chart so the reading is never implicit.

#### Scenario: Anchor is the solar return
- **WHEN** any sub-period chart is computed
- **THEN** its moment is the varsha pravesh moment plus the level offset

#### Scenario: Anchor reported
- **WHEN** any level chart is computed
- **THEN** the anchor moment and the level offset are reported with the chart

### Requirement: Sunrise variant

Each level SHALL offer a sunrise variant that casts the chart at the sunrise of
the computed day instead of at the exact computed moment.

#### Scenario: Sunrise cast
- **WHEN** the sunrise variant of a level is requested
- **THEN** the chart is cast at sunrise on the day of the level's computed
  moment, for the birth place

### Requirement: Sub-charts carry the Tajaka apparatus

Every level chart SHALL expose the same Tajaka apparatus as the annual chart —
Muntha, Harsha Bala, Patyayini dasa and Mudda dasa — computed for that chart's
own lagna and positions.

#### Scenario: Apparatus on a sub-chart
- **WHEN** a monthly chart is computed
- **THEN** its Muntha, Harsha Bala, Patyayini and Mudda dasas are available
  for that chart

### Requirement: Dasa pravesh charts

The engine SHALL cast a dasa pravesh (period-commencement) chart at the start
of a chosen Mudda or Patyayini period of a parent Tajaka chart.

#### Scenario: Period start
- **WHEN** a dasa pravesh chart is requested for a period of a parent chart
- **THEN** the chart is cast at that period's start moment

### Requirement: Tajaka dasa seed options

The Tajaka dasas SHALL accept the seed options: seeding from the natal chart
instead of the annual chart, and advancing the seed by the number of completed
years. The chosen options SHALL be reflected in the reported periods.

#### Scenario: Natal seed
- **WHEN** the natal seed option is enabled
- **THEN** the dasa seed is taken from the natal chart rather than the annual
  chart

#### Scenario: Progressed seed
- **WHEN** the seed-progression option is enabled
- **THEN** the seed is advanced by the completed years before the periods are
  laid out

### Requirement: Determinism

Level charts SHALL depend only on the natal chart, the target year and the
level options, so repeated computation yields identical moments and periods.

#### Scenario: Repeat computation
- **WHEN** the same level chart is computed twice
- **THEN** its moment, Muntha and dasa periods are identical

### Requirement: Surfaces

The levels, sunrise variant and seed options SHALL be reachable from the CLI
`tajaka` command, the AI JSON export, the GUI Tajaka tab and the TUI, and the
CLI SHALL expose the level and index as options.

#### Scenario: CLI level selection
- **WHEN** a user passes a level and index to the `tajaka` command
- **THEN** the corresponding sub-period chart is displayed

#### Scenario: JSON export
- **WHEN** a chart is exported for AI use
- **THEN** the available Tajaka levels for the current year are included

### Requirement: Exaltation scoring in Harsha Bala

Harsha Bala SHALL award the exaltation bonus when a planet occupies its true
exaltation sign, using the canonical exaltation table.

#### Scenario: Moon in Taurus

- **WHEN** the Moon is in Taurus (its exaltation sign)
- **THEN** its Harsha Bala is exactly the exaltation bonus higher than the
  same placement in a non-exaltation sign

#### Scenario: No Aries false positive

- **WHEN** a planet that does not exalt in Aries occupies Aries
- **THEN** it receives no exaltation bonus
