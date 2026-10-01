# panchanga/daily-calendar Specification

## Purpose
TBD - created by archiving change fix-trikalam-panchanga-calendar. Update Purpose after archive.

## Requirements

### Requirement: Canonical trikalam windows

Rahu Kalam, Gulika Kalam and Yamaganda SHALL each be one eighth of the actual
sunrise→sunset day, assigned by weekday per the standard drik-panchanga
tables (eighth counted from sunrise, Sun..Sat):
Rahu `[8,2,7,5,6,4,3]`, Gulika `[7,6,5,4,3,2,1]`, Yama `[5,4,3,2,1,7,6]`
(1-based eighths). Windows SHALL track the real sunrise and sunset.

#### Scenario: Tuesday Rahu Kalam is the seventh eighth

- **WHEN** the day is a Tuesday
- **THEN** Rahu Kalam spans the seventh eighth of the sunrise→sunset day

#### Scenario: Gulika follows the weekday table

- **WHEN** the day is a Saturday
- **THEN** Gulika Kalam spans the first eighth (sunrise → sunrise + 1/8 day)

### Requirement: Daily calendar limbs at sunrise

The monthly panchanga calendar SHALL report each day's paksha, tithi,
nakshatra, yoga and karana as computed at local sunrise, with the correct
weekday, named yoga/karana, and sunrise/sunset in the requested timezone.

#### Scenario: Weekday and names are correct

- **WHEN** the calendar is computed for a Tuesday
- **THEN** the weekday reads Tue, and yoga/karana are their classical names
  (not numeric indices)

### Requirement: Durmuhurta and Varjya windows in the calendar

The monthly panchanga calendar SHALL be able to report, per day, the
Durmuhurta1/2 and Varjya1/2 windows in local time, taken from the same
verified muhurta adjuncts engine the `muhurta` command uses.

#### Scenario: Windows match the muhurta engine

- **WHEN** the calendar is computed with adjuncts for a date
- **THEN** its Durmuhurta1 and Varjya1 start times equal the muhurta
  adjuncts for that date and place

#### Scenario: Absent windows are blank

- **WHEN** a day has a single Varjya window
- **THEN** Varjya2 reads as an empty placeholder
