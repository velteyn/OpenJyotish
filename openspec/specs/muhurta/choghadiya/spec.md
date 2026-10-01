# Muhurta Choghadiya Specification

## Purpose

Daily and nightly Choghadiya (Chogadia / Chaughadia) computation for Vedic electional
astrology: an auspicious-time table that divides daytime (sunrise → sunset) into 8 slots and
nighttime (sunset → next sunrise) into 8 slots, each rated auspicious, inauspicious, or neutral
according to the weekday sequence. Surface the table in the calculation layer, CLI, TUI, GUI,
and AI pipeline, matching what the reference `the source material` Gouri Panchanga view provides.

## Requirements

### Requirement: Day Choghadiya slots

Daytime (sunrise → sunset for the given date and location) MUST be divided into 8 equal
Choghadiya slots. Each slot SHALL carry its name, rating, optional ruling graha, and exact
start/end times in the local timezone offset.

#### Scenario: Eight equal daytime slots
- **WHEN** daytime spans N minutes for a date and location
- **THEN** exactly 8 day slots are produced, each of duration N/8, contiguous from sunrise to sunset

### Requirement: Night Choghadiya slots

Nighttime (sunset → next sunrise) MUST be divided into 8 equal Choghadiya slots. Night slots
that fall after local midnight SHALL be attributed to the next calendar date in their end/start
labels while still belonging to the panchang day that begins at the given sunrise.

#### Scenario: Eight equal nighttime slots crossing midnight
- **WHEN** daytime has ended and the night begins
- **THEN** exactly 8 night slots are produced from sunset to the next sunrise, with post-midnight slots marked with the next date

### Requirement: Per-weekday category sequences

The 8 slot names per day and per night SHALL follow the planetary-hour cycle (Chaldean order:
Sun → Venus → Mercury → Moon → Saturn → Jupiter → Mars), seeded by the weekday lord of the
panchang day (Sun=0 … Saturn=6). The day sequence starts at the weekday lord and steps +1;
the night sequence starts at the fixed `_NIGHT_START` offset and steps +5. Slot 8 of each half
repeats slot 1 (the weekday lord).

#### Scenario: Sunday day table
- **WHEN** the panchang weekday is Sunday
- **THEN** the day sequence starts at the slot ruled by the Sun (Udveg) and follows the canonical cycle (Udveg, Char, Labh, Amrit, Kaal, Shubh, Rog, Udveg)

#### Scenario: Monday night table
- **WHEN** the panchang weekday is Monday
- **THEN** the night sequence follows the canonical Monday night sequence, independent of the day table

### Requirement: Good / bad / neutral rating

Each slot SHALL expose an explicit rating derived from its name: **Good** = Amrit, Shubh, Labh ·
**Bad** = Rog, Kaal, Udveg · **Neutral** = Char. A summary MUST state whether a given moment falls
in a Good, Bad, or Neutral slot. (There is no "Chandra" slot in this convention.)

#### Scenario: Rating for an auspicious slot
- **WHEN** the slot name is Shubh
- **THEN** its rating is Good

#### Scenario: Rating for an inauspicious slot
- **WHEN** the slot name is Kaal
- **THEN** its rating is Bad

#### Scenario: Rating for a neutral slot
- **WHEN** the slot name is Char
- **THEN** its rating is Neutral

### Requirement: Ruling graha resolution

Each slot SHALL be resolvable to its ruling graha (Sun, Moon, Mars, Mercury, Jupiter, Venus,
Saturn) and the current-slot lookup SHALL indicate which graha is ruling at that moment.

#### Scenario: Resolve ruling graha
- **WHEN** a slot of name Shubh is present
- **THEN** its ruling graha is Jupiter

### Requirement: Current-slot lookup and moment evaluation

The calculation SHALL provide a lookup of the active slot for an arbitrary moment on the day,
and a convenience evaluation ("is this a good time?") returning the slot name, rating, lord,
and the remaining duration in the slot.

#### Scenario: Evaluate the current moment
- **WHEN** a user supplies a moment within a Good slot
- **THEN** the lookup returns that slot, its rating Good, its lord, and its end time

#### Scenario: Moment before sunrise
- **WHEN** the supplied moment lies before sunrise
- **THEN** the lookup returns the preceding night slot (from the previous panchang day)

### Requirement: Partial-slot aware lookup

The current-slot lookup MUST be robust to arbitrary offset cities and long daylight/short
daylight boundaries such that cumulative slot-end arithmetic sums exactly to sunrise/sunset
without drift or rounding gaps between adjacent slots.

#### Scenario: No gaps or overlaps in slot boundaries
- **WHEN** all 16 slots are laid end to end
- **THEN** each successive slot starts exactly when the previous one ends, day starts at sunrise, night ends at next sunrise

### Requirement: CLI command

A `choghadiya` CLI command SHALL render the full day+night table (slot name, rating, times,
lord) for a given date/location, defaulting to today's date, and SHALL include its expected
part of the normal `--help` documentation. When a `--now` flag or no timestamp is given, the
current slot SHALL be highlighted.

#### Scenario: Render the table
- **WHEN** a user runs `jhora choghadiya --lat 28.6 --lon 77.2 --tz 5.5`
- **THEN** a 16-row day+night table with name, rating, lord, start, end is printed for today

#### Scenario: Highlight the current slot
- **WHEN** the user passes `--now`
- **THEN** the active slot at the current moment is flagged in the output

### Requirement: GUI panel

The Muhurta tab SHALL expose a Choghadiya panel that lists the day and night table for the
selected chart date/location, highlights the current slot when the date is today, and shows each
slot's rating with the same good/bad/neutral coloring used by the Gouri Panchanga output in the
published tables.

#### Scenario: Open the Choghadiya panel
- **WHEN** a user opens the Muhurta tab and selects Choghadiya
- **THEN** the day and night slot tables appear with ratings and times for the chart's date and location

### Requirement: TUI entry

The TUI SHALL expose a Choghadiya menu entry (e.g. under the Match/Muhurta section) that prints
the same table as the CLI, with an unambiguous header showing the date, location, and whether it
is day or night.

#### Scenario: Run from TUI
- **WHEN** a user selects the Choghadiya entry in the TUI menu
- **THEN** the full table prints for the requested date and location

### Requirement: AI pipeline visibility

The AI analysis pipeline MUST be aware of Choghadiya: for a given chart location and date, the
AI context SHALL include the current/next Choghadiya slot rating and timing (documented if a
default date is used), so the assistant can answer auspicious-time questions consistently with
the GUI/CLI/TUI.

#### Scenario: Assistant answers with Choghadiya
- **WHEN** a user asks the AI about the auspiciousness of a time for a known chart
- **THEN** the AI context includes the relevant Choghadiya slot information and the answer is consistent with the table surfaces

### Requirement: Golden-table correctness

The sequences and ratings MUST be validated against reference output. At minimum, the standard
per-weekday day and night tables SHALL be encoded as golden tests, and the implementation SHALL
be cross-checked against live drikpanchang.com data (Sunday/Thursday tables verified; full-day
Kolkata 2026-09-03 verified within ~1 min) plus any recoverable `the source material` Gouri Panchanga
output during development.

#### Scenario: Golden test coverage
- **WHEN** the test suite runs
- **THEN** each of the 7 weekday day sequences and 7 weekday night sequences is asserted against an encoded reference table

### Requirement: No regression to existing muhurta

The existing panchang, Rahu Kalam, Gulika Kalam, Yamaganda, Abhijit, and muhurta evaluation must
keep their current output and tests green. The Choghadiya path SHALL be additive.

#### Scenario: Existing muhurta unchanged
- **WHEN** a user runs the existing muhurta/panchang flows after this change
- **THEN** the outputs and tests match the pre-change behavior