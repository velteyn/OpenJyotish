# Muhurta Adjuncts Specification

## Purpose

Daily muhurta "avoid" and "strength" adjuncts for Vedic electional astrology:
Durmuhurta, Varjya, and Panchaka inauspicious windows plus Chandra Bala and
Tara Bala personal day strengths, surfaced through the calculator, CLI, GUI,
JSON API, and AI pipeline and folded into muhurta scoring.

## Requirements

### Requirement: Durmuhurta windows

For a given date and location, the day (sunrise → sunset) SHALL be divided
into 15 equal day-muhurtas. Exactly one or two contiguous Durmuhurta windows
SHALL be returned for the panchang day, selected by the weekday lord of the
panchang day. Selection table SHALL be: Sunday → 14th, Monday → 9th,
Tuesday → 4th, Wednesday → 8th, Thursday → 6th, Friday → 4th,
Saturday → 1st day-muhurta. DurMuhurta1 spans the selected day-muhurta;
DurMuhurta2 spans the same index over the 15 equal night-muhurtas
(sunset → next sunrise). Windows SHALL be expressed in the local timezone
offset of the location.

#### Scenario: Sunday uses the 14th day-muhurta

- **WHEN** the panchang day's weekday lord is Sun
- **THEN** the Durmuhurta window spans the 14th of the 15 equal day-muhurtas
  between sunrise and sunset

#### Scenario: Tuesday and Friday share the 4th day-muhurta

- **WHEN** the panchang day's weekday lord is Mars or Venus
- **THEN** the Durmuhurta window spans the 4th of the 15 equal day-muhurtas
  between sunrise and sunset

#### Scenario: Two windows follow the reference table

- **WHEN** a weekday convention and the reference table yield DurMuhurta1 and
  DurMuhurta2
- **THEN** both windows are returned in chronological order with exact local
  start/end times

### Requirement: Varjya windows

For a given date and location, the Varjya (avoided) span(s) SHALL be computed
for the panchang day from the Nakshatra Varjyam rule (Visha Ghatis): each
nakshatra has a fixed starting longitude fraction X (the beginning of the
~96-minute avoid window, expressed as a fraction of a 24-hour nakshatra) and
the window lasts one fifteenth (1/15) of the nakshatra's span (≈1.6 hours per
24-hour nakshatra). Windows SHALL be returned as zero, one, or two contiguous
windows (Varjya1/2) inside the civil day (00:00–24:00 local) — for the
nakshatra the Moon occupies at the civil-day start and the next nakshatra,
each clamped to the civil day — expressed in the local timezone offset.
Windows SHALL not overlap.

#### Scenario: Single Varjya window from the day nakshatra

- **WHEN** a panchang day has a single classical Varjya span from its ruling
  nakshatra
- **THEN** exactly one Varjya window is returned with start and end times in
  local time

#### Scenario: Two Varjya windows

- **WHEN** the next nakshatra's Varjya window also falls within the same civil
  day
- **THEN** a second Varjya window (Varjya2) is returned in chronological order

#### Scenario: No Varjya in effect

- **WHEN** no nakshatra Varjya window falls within the evaluated civil day
- **THEN** no Varjya window is returned (empty list), and scoring is
  unaffected by Varjya

### Requirement: Panchaka windows

For a given date and location, the five-type Panchaka cycle (Roga, Chora,
Mrityu, Agni, Raja) SHALL be laid over daytime and nighttime, producing the
alternating "good" (Rahita) and named "Panchaka" segments known as Panchaka
Rahita muhurta. Each segment SHALL carry its Panchaka name (or Rahita/good
marker) and deterministic start/end times. The category for each candidate
moment SHALL be the classical `(Tithi# + Vara# + Nakshatra# + Udaya-Lagna#)
mod 9` rule, with categories 1 Mrityu, 2 Agni, 4 Raja, 6 Chora, 8 Roga and
0/3/5/7 Rahita; consecutive equal categories form the segments. The same
inputs SHALL always produce the same segmentation (deterministic and
reproducible).

#### Scenario: Panchaka Rahita alternation over the day

- **WHEN** a day is evaluated for Panchaka
- **THEN** daytime and nighttime each expose consecutive segments alternating
  between a named Panchaka (Roga, Chora, Mrityu, Agni, or Raja) and Rahita
  (avoid-free) segments, with the first segment's type fixed by the date's
  tithi/weekday/nakshatra/ascendant

#### Scenario: Reproducible window boundaries

- **WHEN** the same date, location, and timezone are evaluated twice
- **THEN** identical Panchaka segment boundaries and names are produced

### Requirement: Chandra Bala personal strength

Chandra Bala SHALL grade the panchang day's Moon strength for the given date,
location, and a provided Janma nakshatra using the personal classical rule:
derive the Janma rashi from the Janma nakshatra, count inclusively from the
Janma rashi to the day's Moon rashi, and grade the resulting house. Houses 1,
3, 6, 7, 10, 11 SHALL be GOOD, houses 2, 5, 9 SHALL be NEUTRAL, and houses 4,
8, 12 SHALL be BAD. The grade SHALL be one of an enumerated set
(GOOD / NEUTRAL / BAD), the same inputs always yield the same grade, and the
strength SHALL be included in panchanga adjunct output as a named field. When
no Janma nakshatra is provided, Chandra Bala SHALL be reported as unavailable
rather than guessed.

#### Scenario: Favorable house yields a Good grade

- **WHEN** the inclusive house count from the Janma rashi (derived from the
  Janma nakshatra) to the day's Moon rashi is 1, 3, 6, 7, 10, or 11
- **THEN** Chandra Bala is reported GOOD and the favorable house is documented
  in the output

#### Scenario: Deterministic grade

- **WHEN** a date with the same Moon longitude and Janma nakshatra is
  evaluated repeatedly
- **THEN** Chandra Bala returns the identical grade each time

#### Scenario: Missing birth nakshatra

- **WHEN** no Janma nakshatra is supplied
- **THEN** Chandra Bala is reported as unavailable and does not affect scoring

### Requirement: Tara Bala personal strength

Tara Bala SHALL classify the muhurta nakshatra relative to a given Janma
(birth) nakshatra using the nine-tara count: count positions inclusively from
Janma to the muhurta nakshatra, reduce the count modulo 9 (maps 9→0), and
classify by remainder: 1 Janma, 2 Sampat, 3 Vipat, 4 Kshema, 5 Pratyari,
6 Sadhaka, 7 Nidhana, 8 Mitra, 0 Parama Mitra. Remainders 2, 4, 6, 8, 0 SHALL
be auspicious; 3, 5, 7 inauspicious; 1 neutral. When no Janma nakshatra is
provided, Tara Bala SHALL be reported as unavailable rather than guessed.

#### Scenario: Auspicious Sampat tara

- **WHEN** the muhurta nakshatra is the 2nd counted from Janma
- **THEN** Tara Bala is classified Sampat and marked auspicious

#### Scenario: Inauspicious Vipat tara

- **WHEN** the muhurta nakshatra is the 3rd counted from Janma
- **THEN** Tara Bala is classified Vipat and marked inauspicious

#### Scenario: Missing birth nakshatra

- **WHEN** no Janma nakshatra is supplied
- **THEN** Tara Bala is reported as unavailable and does not affect scoring

### Requirement: Scoring integration

`evaluate_time` and `find_muhurta` SHALL penalize candidate moments that fall
inside a Durmuhurta, Varjya, or (non-Rahita) Panchaka window and SHALL reward
moments inside none of them. The penalty SHALL be visible as a lowered score
and a labeled issue (e.g., "Durmuhurta!", "Varjya!", "Raja Panchaka!") in the
per-candidate issue list, alongside existing tithi/weekday/abhijit checks.
Grade-only adjuncts (Chandra Bala, Tara Bala) SHALL inform the score without
hard-excluding a moment.

#### Scenario: Moment inside Durmuhurta is penalized

- **WHEN** a candidate time falls inside the Durmuhurta window for that day
- **THEN** its score is lowered and an issue "Durmuhurta!" appears in its issue
  list

#### Scenario: Clean window scores higher than a Panchaka window

- **WHEN** two otherwise-identical candidate moments differ only in that one
  lies in a non-Rahita Panchaka segment
- **THEN** the Rahita moment scores strictly higher

### Requirement: CLI adjuncts surface

The `muhurta` CLI command SHALL accept an `--adjuncts` flag and an optional
`--janma-nakshatra` argument. With `--adjuncts`, output SHALL include a
dedicated adjuncts section listing Durmuhurta, Varjya, and Panchaka windows
with local start/end times plus Chandra Bala and Tara Bala grades, both
computed when `--janma-nakshatra` is provided and reported unavailable
otherwise. Without `--adjuncts` the command SHALL behave exactly as before.

#### Scenario: Adjuncts printed for a date

- **WHEN** `muhurta <date> <time> --adjuncts` is run with a valid birth
  nakshatra via `--janma-nakshatra`
- **THEN** output contains a Durmuhurta row, Varjya row(s), Panchaka segments,
  Chandra Bala grade, and Tara Bala entry, each with local times

#### Scenario: Backward-compatible default

- **WHEN** `muhurta <date> <time>` is run without `--adjuncts`
- **THEN** output is identical to the current verb output (no adjuncts
  section, no new columns)

### Requirement: JSON API adjuncts section

The `chart_to_json` export SHALL include a `muhurta_adjuncts` object (or
equivalent named section consistent with existing JSON layout) containing
`durmuhurta`, `varjya`, `panchaka`, `chandra_bala`, and `tara_bala` entries
for the chart date, with the same time/label/classification fields as the
CLI. When no Janma nakshatra is available, the `chandra_bala` and `tara_bala`
entries SHALL be present with an explicit unavailable marker.

#### Scenario: Adjuncts present in JSON export

- **WHEN** a chart for a date/location is exported with `chart_to_json`
- **THEN** the export contains the muhurta adjuncts section with windows and
  grades

#### Scenario: Bala unavailable markers

- **WHEN** export runs without Janma nakshatra data
- **THEN** `chandra_bala` and `tara_bala` are present and marked unavailable,
  and other adjuncts remain populated

### Requirement: GUI and AI exposure

The GUI Muhurta tab SHALL render an adjuncts block showing
Durmuhurta/Varjya/Panchaka windows plus Chandra Bala and Tara Bala grades
when a saved birth chart is selected (reported unavailable otherwise) for the
selected date/location. The AI daily-summary pipeline prompt SHALL incorporate
the adjuncts section (durmuhurta/varjya/panchaka/chandra-bala/tara-bala) so
generated summaries can mention avoid windows and strengths.

#### Scenario: GUI shows adjuncts

- **WHEN** a Muhurta tab is populated for a date and location with a selected
  birth chart
- **THEN** the tab displays Durmuhurta, Varjya, Panchaka, Chandra Bala, and
  Tara Bala entries

#### Scenario: AI summary receives adjuncts

- **WHEN** a daily summary is generated for a chart with a saved birth
  nakshatra
- **THEN** the prompt context includes the adjuncts section values and the
  summary may reference Durmuhurta/Varjya/Panchaka avoidance and Tara/Chandra
  strengths
