# AI Lessons Learned — model audits, engine errata, setup laws

Distilled from weeks of auditing LLM answers against our own engine
(September 2026). Every rule below was paid for with a real wrong answer.
The eval harness (`tools/eval/`) re-verifies the falsifiable ones; run it
before trusting any new model or prompt change.

## 1. The faithfulness hierarchy (models copy, rarely compute)

Ranked by where errors concentrate, most to least reliable:

1. **Numbers copied from context** — dates, longitudes, SAV/bala values:
   near-perfect across all tested models. Ketu/Moon/Mars antardasa dates
   came back exact to the day repeatedly.
2. **Entity mapping** (which planet a number belongs to) — the main failure
   zone for small models: Sun's longitude attributed to Moon, "Mars-ruled
   8th" for a Saturn-ruled house, sign names attached to the wrong longitude
   ("Aries 320.2°" for Aquarius).
3. **Parametric lore** (gems, lordships, month names, mantra–planet links) —
   confabulated freely: emerald for Venus (it's Mercury's), ruby for Mars
   (Sun's; Mars is coral), Jupiter "lord of the 7th", Simha = July.
4. **Fabricated provenance** — invented verbatim quotes from the classics
   and invented spouse data (lagna/nakshatra without birth time). The most
   dangerous class: fluent, confident, checkable-only-against-sources.

Corollary: when the model and the engine disagree, **check the anchor
first** — twice the model was faithfully repeating our own bugs (below).

## 2. Engine errata found *through* AI answers

- **Ashtakavarga zeros**: single benefic table + spurious occupancy rule
  zeroed every unoccupied rasi (SAV totaled 155). Fixed to the classical
  7×8 (subject, contributor) matrix, no occupancy test. Invariants that
  must hold forever: SAV == 337 in every chart; BAV totals exactly
  48/49/39/54/56/52/39; all 7 BAVs match jyotishganit house-for-house.
- **Chara Karaka ranking**: sorted by absolute longitude instead of
  in-sign degrees, and the 8th role was a bogus "Sthira" mixing two
  systems. Correct: rank by `longitude % 30`; order ends PutK/GnK/DK.
  (Every "Moon is DK" answer was anchor-faithful — the engine was wrong.)
- **Dashboard natal-vs-transit**: Sade Sati and Retrograde Watch read
  natal positions under "current" labels. Transit facts must come from
  `compute_transits`, never `cd.planet`.
- **Next-Mahadasha off-by-one**: strict `>` on contiguous boundaries
  skipped Venus 2031 and showed Sun 2051. Use `>=` (now `next_mahadasa`).
- **IANA timezones resolved at today, not the birth date**: a winter birth
  computed in DST season gained an hour (wrong lagna). Always thread the
  event date into zone lookups.
- **Atlas DST contamination**: a 34k-city import baked summer offsets
  (Padua +2.0, New York −4, London +1). Static atlases must store standard
  time; DST resolves per birth date or not at all.

## 3. Model scorecard (single-question audits + harness shorts)

| Model | Dates | Entities | Lore | Notes |
|---|---|---|---|---|
| Qwen 27B (good quant) | exact | mostly right | slips | reference reader; needs VRAM to host |
| Qwen3.5-9B instruct | exact *when it answers* | swaps (Moon↔Sun) | bad | severe thinking burn (see §5) |
| Ministral-3-14B-Reasoning | drifts on long answers | best when focused | fake citations | strict template (§4); slow on small GPUs |
| Mythos/abliterated merges | — | — | poison | roleplay tuning destroys factual fidelity |
| IQ1_S and below | untested | predicted last | — | fits VRAM by destroying weights |

n=1 per model per question: suggestive, not conclusive. Re-run the
harness before promoting any new model.

## 4. Prompt-format laws (template strictness is per-model)

- **Strict role alternation always**: `[system(+anchor), user, assistant,
  …]` — never two user messages in a row. Ministral-3's Jinja template
  HTTP-500s otherwise (Qwen tolerates it; don't rely on tolerance).
- **Never send `max_thinking_tokens`** (Qwen reasoning templates end the
  completion where thinking trips instead of answering). Proven live;
  see `AiEngine._call`.
- **Reasoning burn is real**: Qwen3.5 spent 16/16 and 4096/4096 tokens
  thinking with zero answer text. Tight `max_tokens` starves thinking
  models — keep answer budgets generous (app sends 16384).
- **Shorter is truer**: date drift and fabrication grow with answer
  length. Focused probes stay exact; 5k-token readings wander. Prefer
  several short answers over one epic.

## 5. Anchor laws (make truth copy-pasteable)

- Explicit sign names next to **every** longitude (models mis-map
  degrees→signs: "Aries 320.2°").
- Lordship, karaka role, and retro status **inline** with each planet
  (never assume the model knows them).
- Timelines as exact date ranges; instruct: copy dates verbatim.
- Spouse-unknown guard: without partner birth time, forbid asserting
  partner lagna/nakshatra/dasha.
- No classical quotes except from provided RAG passages (else the model
  invents provenance).

## 6. Setup laws (8GB-VRAM class hardware is the design target)

- Qwen-9B Q4 + 8k context fits and flies; Ministral-14B Q4 spills to CPU
  (slow but best quality); 27B-Q4 is physically unusable; IQ1_S fits by
  being lossy.
- Auto-selection: **loaded-ness dominates** (a ready model beats any
  download — a wrong pick costs minutes of JIT reload + VRAM churn).
  Never auto-pick sub-1B toys. Never evict user-loaded instances; idle
  TTL handles those. Track and free only what the app loaded.
- Context arithmetic: prompt + thinking + answer ≤ loaded window.
  The 8k wall truncated a 5.5k-token answer mid-sentence; the truncation
  notice is the backstop, not the fix — load adequate context instead.
- GPU contention is real: video playback on the same card starved the
  server for minutes. Pause GPU-heavy apps during long readings.

## 7. Harness discipline (`tools/eval/`)

- Short probes first (date/entity fidelity in minutes), long-form rarely.
- Deterministic substring assertions + human reading of every transcript;
  scores alone never promote a model.
- Follow-ups test history use (seeded-history variant isolates mechanism
  from first-turn luck).
- One model resident at a time; unload only harness-loaded instances.
- Config and transcripts stay local and gitignored — never commit birth
  data or server addresses.

## 8. Guru (RAG teacher) findings

- Retrieval works: 5905 vectors over 16 texts, top hits score ~0.80 and
  are genuinely on-topic (a DK question retrieves karaka chapters).
- Generation obeys numbers but disobeys passages: with the true
  definition ("Dara karaka DK Spouse") retrieved, the model still taught
  "Dara = enemy", invented positions (Saturn in Capricorn H7 — actually
  Taurus H11), denied computed Kuja Dosha, and fabricated a quote.
  Verify every classical quotation against the corpus
  (`textbook_chunks LIKE '%phrase%'`) — zero hits means invented.
- Consequences encoded in `TEACHER_SYSTEM_PROMPT`: grounding rules
  (passages override memory; quote only provided excerpts with [source];
  positions/dates only from chart data; spouse-unknown guard) plus an
  exact-syntax command allowlist (verified against `--help`; the model
  invents flags like `--karaka-dasa` otherwise).
- The corpus itself is a correctness oracle: it confirmed the 8-karaka
  order (Putra 6th, Jnaati 7th, Dara 8th) behind the karaka fix.

## 9. Mechanical verification (reputation guarantee)

- Prompts don't converge: free prose from 9–14B models swaps ~30% of
  attached signs and invents provenance. `jhora/ai/verify.py` parses each
  answer for checkable claims (planet-in-sign, houses, lagna, dasa/birth
  dates, strength numbers, karaka roles, quoted passages) and checks them
  against engine truth before display — ✓ when clean, ⚠ with corrections.
- Precision rules that mattered: skip transit sentences (moving sky),
  examples/hypotheticals, questions, code spans and mantras in quote
  checks; whole-sign houses from lagna as the house convention.
- Live result on a real bad answer: 24 of 36 claims flagged, zero false
  positives on review. Temperature 0.2 default everywhere.
