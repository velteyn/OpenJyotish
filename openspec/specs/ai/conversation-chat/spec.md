# AI Conversation Chat Specification

## Purpose

Multi-turn threaded chat for the local AI service (AI Chat and AI Teacher), so
users can ask follow-up questions and the model sees its prior answers. The
thread carries a fixed chart/RAG anchor plus a growing history, and the engine
detects the server's real context window and compacts the thread into a fresh
session when the budget is nearly exhausted.

## Requirements

### Requirement: Threaded conversation across turns

The AI Chat "Ask" and the AI Teacher "Ask Guru" interactions MUST be
multi-turn. Each new user question SHALL be appended to the prior
user/assistant history, and the server request SHALL include that history so
the model can build on its earlier answers.

#### Scenario: Asking a follow-up question
- **WHEN** a user has already received an answer in the current thread and asks a new question
- **THEN** the model request includes the prior question/answer pairs, and the response is appended to the thread

### Requirement: Fixed conversation anchor

A conversation SHALL carry a once-computed anchor (chart positions, computed
analysis, and textbook excerpts for the teacher) that is reused across turns in
that thread, rather than recomputed every turn. The anchor SHALL additionally
be budget-scaled to the detected context window — at most 40% of the window
(floor 800 tokens, cap 6000) — so small windows keep room for history,
questions, and answers.

#### Scenario: Reusing the anchor across turns
- **WHEN** a thread produces its second and later turns
- **THEN** the fixed chart/analysis anchor is not recomputed per turn and is reused for the thread

#### Scenario: Small window gets a scaled anchor
- **WHEN** the detected window is 8192 tokens
- **THEN** the anchor budget is ~3276 tokens, leaving headroom below the 70%
  trip wire for history and follow-up turns

### Requirement: Runtime context window detection

The engine MUST determine the local server's actual context window at connect /
health-check time (e.g. LM Studio catalog `max_context_length`, Ollama
`/api/show`), rather than hardcoding a value, so the same logic works on any
hardware. When the catalog reports both a theoretical maximum and an
actually-loaded length, the loaded length SHALL win, since only it reflects
the live window. If the server does not report one, a conservative documented
default SHALL be used.

#### Scenario: Context detected from a large model
- **WHEN** the connected model reports a large context window (e.g. 128K)
- **THEN** the thread's budget and compaction threshold use that detected value

#### Scenario: Context falls back to a default
- **WHEN** the server does not report a context length
- **THEN** a conservative default is used and compaction still triggers to avoid overflowing

#### Scenario: Loaded window wins over theoretical maximum
- **WHEN** the catalog reports a theoretical maximum (e.g. 1M) alongside a
  smaller actually-loaded length (e.g. 8K)
- **THEN** the thread's budget and compaction threshold use the loaded length

### Requirement: Budget monitor with compact-and-restart

As a conversation grows, the engine MUST monitor the prompt token budget
(anchor + history + reserved response). When the used budget reaches ~70% of the
detected context window, the thread SHALL be compacted into a summary and a
fresh clean session SHALL be started seeded from that summary, so the prompt
never overflows and the model does not garble from truncation.

#### Scenario: Threshold reached mid-thread
- **WHEN** the current thread's prompt reaches ~70% of the detected context window
- **THEN** the thread is compacted into a summary and a fresh session starts seeded from that summary, preserving continuity

#### Scenario: Below threshold
- **WHEN** the thread's prompt is below the ~70% threshold
- **THEN** the thread continues normally without compaction

### Requirement: Visible session reset

When a compaction / fresh-session reset occurs, the UI or CLI MUST surface it to
the user (e.g. a status message), so the reset is transparent rather than
silent.

#### Scenario: Reset is reported
- **WHEN** a compaction reset is triggered during a conversation
- **THEN** the user sees a message indicating the conversation was summarized and a fresh thread started

### Requirement: No regression to one-shot actions

The existing single-turn "Interpret", "Remedies", "Ask", and "Ask Guru" engine
paths (and equivalent CLI modes) MUST keep their current behavior and context
budget. The conversation path SHALL remain additive and MUST NOT change
existing one-shot engine output. The GUI MAY render one-shot results as entries
in the chat transcript instead of overwriting a single output pane, provided the
answer content is identical.

#### Scenario: One-shot engine output unchanged
- **WHEN** a user uses an existing one-shot action without starting a thread
- **THEN** the engine behavior, context budget, and answer content match the
  pre-change behavior, and existing tests remain green

#### Scenario: One-shot actions unchanged
- **WHEN** a user uses an existing one-shot action without starting a thread
- **THEN** the behavior and output match the pre-change behavior, and existing tests remain green

#### Scenario: One-shot result appears in the transcript
- **WHEN** a user runs Interpret or Remedies in the AI Chat tab
- **THEN** the result is appended as a transcript entry with identical content to
  the former single-pane output, and the thread history records the exchange

### Requirement: Teacher threads with per-turn RAG

The AI Teacher MUST be conversational: each turn SHALL search the textbook
corpus for passages relevant to the *current* question (per-turn RAG) while
carrying the prior user/assistant thread, subject to the same budget monitor and
compact-and-restart behavior.

#### Scenario: Teacher follow-up with fresh passages
- **WHEN** a user asks a follow-up teaching question in a thread
- **THEN** the request includes the prior thread and fresh textbook passages for the new question, and the answer is appended

#### Scenario: Teacher threshold reset
- **WHEN** the teacher thread reaches ~70% of the detected context window
- **THEN** the teacher thread is compacted into a summary and a fresh session starts seeded from that summary