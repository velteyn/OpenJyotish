# ai Specification

## Purpose
TBD - created by archiving change add-tattva-drishti-jsonld. Update Purpose after archive.

## Requirements

### Requirement: JSON-LD output

The engine SHALL serialise a chart summary as JSON-LD, reusing the values of
the existing JSON export rather than recomputing them, so the two never
disagree.

#### Scenario: Self-describing document
- **WHEN** the JSON-LD view is produced
- **THEN** it carries a context defining its terms and an identity for the chart

#### Scenario: Values agree with the JSON export
- **WHEN** a value in the JSON-LD output is compared with the JSON export
- **THEN** they agree

### Requirement: Additive only

The JSON-LD view SHALL NOT change the existing JSON export or its consumers.

#### Scenario: Existing export unchanged
- **WHEN** the JSON export is produced
- **THEN** its sections and structure are exactly as before
