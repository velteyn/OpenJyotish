# AI Truncation Specification

## Purpose

Generations that end incomplete must say so: truncated or interrupted answers
are surfaced with explicit notices instead of a bare completion marker, and
the teacher's static prompt cost is cached so more room remains for answers.

## Requirements

### Requirement: Truncation notice on exhausted budget

When a streamed completion ends with `finish_reason: length`, the returned
text SHALL carry a `[truncated — output budget exhausted]` notice after the
partial content, in both the engine and teacher stream readers. Natural stops
(`stop`) and the existing empty-answer behavior SHALL be unchanged.

#### Scenario: Long answer cut by the server

- **WHEN** the final stream chunk reports `finish_reason: length`
- **THEN** the visible answer ends with the truncation notice instead of
  looking complete

### Requirement: Interruption notice on dead streams

When a stream ends with no `[DONE]` marker and no finish reason (dropped
connection, killed generation), the returned text SHALL carry an
`[interrupted — connection ended before completion]` notice. A non-stop,
non-length finish reason SHALL surface as `[stopped early — reason: X]`.

#### Scenario: Connection drops mid-answer

- **WHEN** stream chunks stop arriving with no terminator
- **THEN** the partial answer carries the interruption notice

### Requirement: Teacher static prompt cached per chart

The teacher's per-turn message SHALL reuse a cached static chart/analysis
block per chart; only the textbook passages stay freshly retrieved per
question. Cache behavior SHALL mirror the existing chat anchor cache.

#### Scenario: Static block built once per chart

- **WHEN** two teacher turns run for the same chart
- **THEN** the static chart/analysis block is built once and reused
