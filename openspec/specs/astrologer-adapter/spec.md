# astrologer-adapter Specification

## Purpose
A fine-tuned OpenJyotish astrologer adapter SHALL be trained exclusively on
public-tier sources (our Primer, public-domain classics, engine-verified
generated pairs) and SHALL be measurably more reliable than its base model
under the mechanical verifier, so readings need fewer repair rounds.

## Requirements

### Requirement: Public-tier sources only

The training dataset SHALL contain no copyrighted extracts: only
`src/jhora/data/books/` texts (Primer + PD classics) and generated pairs
whose every checkable claim verifies clean against the engine. A dataset
manifest SHALL record the source of every pair, and a CI check SHALL reject
any pair whose provenance is not public-tier.

#### Scenario: Extracts cannot leak into the dataset

- **WHEN** the generator runs on a machine that also holds private extracts
- **THEN** no pair in the output JSONL derives from them (provenance allowlist:
  primer, pd-classic, engine-generated)

### Requirement: Verifier-filtered pairs

Every generated chart-reading pair SHALL pass `verify_answer` with zero flags
before entering the dataset, using the same chart it was generated from.
Primer Q&A pairs SHALL pass citation checks against the library source list.

#### Scenario: Dirty drafts never ship

- **WHEN** a drafted reading flags 3 claims
- **THEN** it is repaired or discarded; the dataset contains only the
  zero-flag final (or nothing)

### Requirement: Held-out eval with ship threshold

A fixed held-out chart set (never trained on) SHALL score every candidate
adapter by verifier flag-rate and citation-genuineness vs the base model on
identical prompts. An adapter SHALL ship only if it flags strictly fewer
claims than base at equal-or-better citation genuineness.

#### Scenario: No regression ships

- **WHEN** an adapter flags 8/100 claims where base flags 6/100
- **THEN** it is rejected regardless of fluency or user preference votes

### Requirement: Reproducible recipe and model card

The release adapter SHALL be reproducible from a pinned recipe (base model,
Unsloth version, rank, epochs, dataset hash) run on user hardware, and SHALL
ship with a model card stating base, dataset hash, eval numbers, and the
standing limitation: the adapter assists wording, the engine owns the facts
(verify-repair stays on).

#### Scenario: Independent rebuild matches

- **WHEN** the recipe is re-run against the published dataset hash
- **THEN** the resulting adapter scores within the published eval tolerance
