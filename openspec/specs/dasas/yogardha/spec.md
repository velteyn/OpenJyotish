# Dasas Yogardha Specification

## Purpose

Yogardha rasi dasa (mainstream tradition's Parasara & Jaimini forms) for charts where
yoga-fructification timing dominates — included only if a canonical
mainstream form is found during design research.

## Requirements

### Requirement: Averaged Chara/Sthira durations from lagna/7th seed
The system SHALL seed 12 Mahadashas at the stronger of lagna and 7th
house (same BPHS stronger-sign determination as Brahma), running
forward (reverse iff the seed index is odd), with each Mahadasha
lasting the mean of its Chara lord-distance duration (Rao exception,
no exaltation adjustment) and its Sthira modality duration (7/8/9);
antardasas proportional in cycle direction.

#### Scenario: Fixture cycle
- **WHEN** computed for the 1990 fixture (Sagittarius beats Gemini by
  occupancy)
- **THEN** 12 contiguous Mahadashas run forward from Sagittarius with
  proportional antardasas summing to each Mahadasha.
