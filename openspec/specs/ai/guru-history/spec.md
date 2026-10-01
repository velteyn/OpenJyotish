# AI Guru History Specification

## Purpose

ChatGPT-shaped thread lifecycle for the AI Guru (teacher) tab: a visible lesson
transcript with a single follow-up input, explicit new-lesson shelving, and
per-chart persisted history including chart-free study, so teaching
conversations are natural, resumable, and never silently destroyed.

## Requirements

### Requirement: Transcript view of the lesson

The Guru tab SHALL render the teaching conversation as a scrollable transcript,
oldest exchange first, with student questions and guru answers clearly
distinguished. A streaming answer SHALL append to the tail entry as tokens
arrive. Markdown rendering of answers SHALL be preserved.

#### Scenario: Follow-up appends to the lesson

- **WHEN** the student asks a follow-up after receiving a teaching answer
- **THEN** the new question and the streaming answer appear below the prior
  exchanges, which remain visible above

### Requirement: Single follow-up input below the transcript

Exactly one question input SHALL exist, placed below the transcript with a send
affordance; pressing Enter or send submits the text as the next turn. The input
SHALL be disabled while an answer is streaming and re-enabled when the turn
completes or fails, so overlapping turns are impossible.

#### Scenario: Input locked while the guru is thinking

- **WHEN** the student submits a question and the answer is still streaming
- **THEN** the input is disabled until the turn completes, and a second
  submission cannot start

### Requirement: Explicit new-lesson shelving

A `[New chat]` control SHALL shelve the current lesson into history, clear the
visible pane, and reset the context meter. Shelving MUST NOT delete the lesson;
it SHALL remain resumable from the thread picker.

#### Scenario: Starting over preserves the old lesson

- **WHEN** the student presses New chat with a non-empty lesson
- **THEN** the pane clears for a fresh question and the previous lesson appears
  in the history picker with its full transcript intact

### Requirement: Thread picker with resume and delete

The tab SHALL offer a thread picker listing shelved lessons (title + date),
newest first. Selecting a lesson SHALL restore its full transcript and its
model history so follow-ups continue with context and fresh per-turn textbook
passages. Each lesson SHALL offer delete; rename is out of scope.

#### Scenario: Resuming an old lesson

- **WHEN** the student selects a shelved lesson from the picker
- **THEN** its transcript renders in full and the next question continues that
  lesson with prior context available to the model

### Requirement: History scoped to the birth chart, plus chartless study

Lessons created with a calculated chart SHALL be bound to that chart (birth
moment and place), and the picker SHALL list only lessons of the currently
calculated chart. Lessons asked without a chart SHALL live in a "General
study" group that is always visible. With no chart calculated, only the
General study group SHALL be shown.

#### Scenario: Chart switch filters lessons

- **WHEN** the student calculates a different birth chart
- **THEN** the picker shows only lessons created under that chart plus the
  General study group, and other charts' lessons stay shelved and hidden

### Requirement: Persisted history with sane bounds

Lessons SHALL persist across application restarts in the existing local
database (auto-created tables, no migration), in a store owned by the Guru
tab and separate from the chat tab's store. Each lesson SHALL carry a title
derived from its first question (truncated, no model call needed). At most 50
lessons per chart scope SHALL be kept; older lessons beyond the cap SHALL be
pruned.

#### Scenario: Lessons survive restart

- **WHEN** the student restarts the application and recalculates the same chart
- **THEN** its shelved lessons are listed in the picker with transcripts intact

### Requirement: Visible context meter and compaction divider

The tab SHALL display a context meter showing estimated usage against the ~70%
compaction threshold. When compaction triggers, a divider line SHALL be
inserted in the transcript noting the restart; the visible lesson above the
divider SHALL be retained and only the model's context restarts from the
summary.

#### Scenario: Compaction is transparent

- **WHEN** a lesson reaches ~70% of the detected context window
- **THEN** the student sees the meter approach the threshold and a divider
  appears in the transcript, while all prior exchanges stay readable

### Requirement: Sticky scrolling

The transcript SHALL auto-scroll to follow a streaming answer only while the
view is already at the tail. If the student has scrolled up, incoming tokens
MUST NOT pull the view down.

#### Scenario: Reading while streaming

- **WHEN** the student scrolls up to re-read during a streaming answer
- **THEN** the view stays where placed until the student returns to the tail

### Requirement: Per-answer sources display

Each guru answer SHALL carry a compact Sources block listing the textbook
passages cited for that turn (source name plus excerpt). Sources of older
turns SHALL remain visible in the transcript after resume.

#### Scenario: Checking what grounded an answer

- **WHEN** the student reads any answer in the transcript
- **THEN** the cited passages for that turn are shown with their source names

### Requirement: Topic presets feed the input

The existing topic presets SHALL fill the bottom follow-up input instead of
submitting directly, so the student can edit the question before sending.

#### Scenario: Preset fills but does not send

- **WHEN** the student picks a topic preset
- **THEN** the preset text appears in the input, editable, and nothing is
  submitted until send
