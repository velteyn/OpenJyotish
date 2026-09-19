# openjyotish-astrologer-lora-vN — model card

Domain adapter for Vedic-astrology readings. It assists **wording**; the
engine owns the facts and verify-repair stays on (see limitation below).

- **Base model:** {{base}}
- **Method:** 4-bit QLoRA (Unsloth), rank {{rank}}, {{epochs}} epoch(s)
- **Training dataset hash:** `{{dataset_hash}}` (provenance: {{dataset_counts}})
- **Environment:** {{torch_cuda}}
  {{versions}}
- **Eval (held-out charts, verifier as judge):**
  - base: _fill after `tools/train/eval_adapter.py --mock clean`_
  - adapter: _fill after `tools/train/eval_adapter.py --lmstudio …`_
  - ship verdict: _fill after `--compare` (strictly fewer flags at
    equal-or-better citation genuineness, or it does not release)_

## Intended use

Loaded in LM Studio / Ollama / Unsloth Studio as the chat model behind
OpenJyotish AI readings: fewer verifier flags per answer, Primer-accurate
language, citation discipline (`[Source]` names from the bundled library).

## Standing limitation

Fine-tuning teaches style, domain language and citation discipline —
**never arithmetic**. House numbers, signs, lords, dasa dates and
strengths come from the engine; every answer is still mechanically
verified and repaired before display.
