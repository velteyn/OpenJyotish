# AI Chat History Specification

## Purpose

ChatGPT-shaped thread lifecycle for the AI Chat tab: a visible transcript with a
single follow-up input, explicit new-chat shelving, and per-chart persisted
history, so follow-up conversations are natural, resumable, and never silently
destroyed.

## Requirements

### Requirement: Transcript view of the thread

The AI Chat tab SHALL render the conversation as a scrollable transcript,
oldest exchange first, with user questions and guru answers clearly
distinguished. A streaming answer SHALL append to the tail entry as tokens
arrive. Markdown rendering of answers SHALL be preserved.

#### Scenario: Follow-up appends to the transcript

- **WHEN** the user asks a follow-up after receiving an answer
- **THEN** the new question and the streaming answer appear below the prior
  exchanges, which remain visible above

### Requirement: Single follow-up input below the transcript

Exactly one question input SHALL exist, placed below the transcript with a send
affordance; pressing Enter or send submits the text as the next turn. The input
SHALL be disabled while an answer is streaming and re-enabled when the turn
completes or fails, so overlapping turns are impossible.

#### Scenario: Input locked while thinking

- **WHEN** the user submits a question and the answer is still streaming
- **THEN** the input is disabled until the turn completes, and a second
  submission cannot start

### Requirement: Explicit new-chat shelving

A `[New chat]` control SHALL shelve the current thread into history, clear the
visible pane, and reset the context meter. Shelving MUST NOT delete the thread;
it SHALL remain resumable from the thread picker.

#### Scenario: Starting over preserves the old thread

- **WHEN** the user presses New chat with a non-empty thread
- **THEN** the pane clears for a fresh question and the previous thread appears
  in the history picker with its full transcript intact

### Requirement: Thread picker with resume and delete

The tab SHALL offer a thread picker listing shelved threads (title + date),
newest first. Selecting a thread SHALL restore its full transcript and its
model history so follow-ups continue with context. Each thread SHALL offer
delete; rename is out of scope.

#### Scenario: Resuming an old thread

- **WHEN** the user selects a shelved thread from the picker
- **THEN** its transcript renders in full and the next question continues that
  thread with prior context available to the model

### Requirement: History scoped to the birth chart

Threads SHALL be bound to the birth chart they were created under (birth
moment and place). The picker SHALL list only threads of the currently
calculated chart; with no chart calculated, no history SHALL be shown. This
prevents answering from the wrong chart's calculations.

#### Scenario: Chart switch filters history

- **WHEN** the user calculates a different birth chart
- **THEN** the picker shows only threads created under that chart, and threads
  of other charts stay shelved and hidden

### Requirement: Persisted history with sane bounds

Threads SHALL persist across application restarts in the existing local
database (auto-created tables, no migration). Each thread SHALL carry a title
derived from its first question (truncated, no model call needed). At most 50
threads per chart SHALL be kept; older threads beyond the cap SHALL be pruned.

#### Scenario: History survives restart

- **WHEN** the user restarts the application and recalculates the same chart
- **THEN** its shelved threads are listed in the picker with transcripts intact

### Requirement: Visible context meter and compaction divider

The tab SHALL display a context meter showing estimated usage against the ~70%
compaction threshold. When compaction triggers, a divider line SHALL be
inserted in the transcript noting the restart; the visible history above the
divider SHALL be retained and only the model's context restarts from the
summary.

#### Scenario: Compaction is transparent

- **WHEN** a thread reaches ~70% of the detected context window
- **THEN** the user sees the meter approach the threshold and a divider
  appears in the transcript, while all prior exchanges stay readable

### Requirement: Sticky scrolling

The transcript SHALL auto-scroll to follow a streaming answer only while the
view is already at the tail. If the user has scrolled up, incoming tokens MUST
NOT pull the view down.

#### Scenario: Reading while streaming

- **WHEN** the user scrolls up to re-read during a streaming answer
- **THEN** the view stays where placed until the user returns to the tail
