# Astrologer adapter — data, recipe, eval, publishing

A domain LoRA that makes local chat models write Vedic readings with fewer
verifier flags, Primer-accurate language and citation discipline. It assists
**wording only** — the engine owns the facts and verify-repair stays on.

Training runs on your own hardware; nothing here trains in CI. Dataset
generation and the eval harness are unit-tested in CI (mock-LLM mode).

## Pipeline

```bash
# 1. Generate a verifier-filtered dataset (needs an LM Studio endpoint for
#    drafting; provenance is allow-listed to primer / pd-classic / generated).
PYTHONPATH=. python3 tools/train/build.py --n 400 --seed 42 \
    --lmstudio http://LAN-IP:1234 --model <draft-model> \
    --out /tmp/dataset --repair --verify-facts

# 2. Train (single NVIDIA GPU; see recipe/requirements-train.txt).
python3 tools/train/recipe/train_unsloth.py \
    --dataset /tmp/dataset --base unsloth/qwen3-8b \
    --rank 16 --epochs 2 --out /path/to/openjyotish-astrologer-lora-v1

# 3. Score base vs adapter on held-out charts (verifier as judge).
PYTHONPATH=. python3 tools/train/eval_adapter.py --mock clean --n 20 \
    --out /tmp/eval-base.json
PYTHONPATH=. python3 tools/train/eval_adapter.py \
    --lmstudio http://LAN-IP:1234 --model <adapter-key> --n 20 \
    --out /tmp/eval-adapter.json
PYTHONPATH=. python3 tools/train/eval_adapter.py \
    --compare /tmp/eval-base.json /tmp/eval-adapter.json
```

Sources are public-tier only: our Primer, the four public-domain classics,
and engine-verified generated pairs. The dataset manifest records each pair's
provenance and is hash-checked before training.

## Release artifact naming (task 4.1)

One adapter per version, named **`openjyotish-astrologer-lora-vN`** (N = 1, 2,
…). The training output directory already has this shape:

```
openjyotish-astrologer-lora-v1/
├── adapter/            # PEFT LoRA (adapter_config.json + adapter_model.safetensors)
└── MODEL_CARD.md       # filled in by train_unsloth.py
```

Package it and attach it to a GitHub release. The tag follows the app's
version, the asset name carries the adapter version:

```bash
cd /path/to
tar czf openjyotish-astrologer-lora-v1.tar.gz openjyotish-astrologer-lora-v1
sha256sum openjyotish-astrologer-lora-v1.tar.gz > openjyotish-astrologer-lora-v1.tar.gz.sha256

# Create the release once (or reuse an existing tag), then upload the assets.
gh release create astrologer-lora-v1 \
    --repo velteyn/OpenJyotish \
    --title "Astrologer LoRA v1" \
    --notes-file openjyotish-astrologer-lora-v1/MODEL_CARD.md
gh release upload astrologer-lora-v1 \
    --repo velteyn/OpenJyotish \
    openjyotish-astrologer-lora-v1.tar.gz \
    openjyotish-astrologer-lora-v1.tar.gz.sha256 \
    openjyotish-astrologer-lora-v1/MODEL_CARD.md
```

Rules for a release:

- `MODEL_CARD.md` must have **base, dataset hash, eval numbers and the
  verdict** filled in; `--compare` must show strictly fewer flags than base at
  equal-or-better citation genuineness, or the adapter does not ship.
- Attach the `.tar.gz`, its `.sha256`, and the model card.
- Record the dataset hash in the release notes so the recipe is reproducible.

## Loading the adapter (task 4.2)

The adapter is a PEFT LoRA over its base model. Run it behind an
OpenAI-compatible server and point OpenJyotish at that server.

### LM Studio

1. LM Studio → **My Models**, load the base model the adapter was trained on.
2. Open the model's **LoRA / adapters** panel and add the adapter directory
   (`.../openjyotish-astrologer-lora-v1/adapter`).
3. Start the local server (**Developer → Start Server**, default
   `http://localhost:1234`).

### Ollama

Ollama needs the adapter merged into a GGUF or referenced from a Modelfile.
With a GGUF export of the merged model in `./`:

```bash
cat > Modelfile <<'EOF'
FROM ./openjyotish-astrologer-v1.gguf
PARAMETER temperature 0.6
EOF
ollama create openjyotish-astrologer-v1 -f Modelfile
ollama serve            # http://localhost:11434
```

### Unsloth Studio

Unsloth Studio serves the adapter directly: load the base + adapter, start
`unsloth serve` (default `http://localhost:8000`).

### Pointing the app at it

The app has no adapter-specific switch — it already talks to any
OpenAI-compatible endpoint through the normal provider setting:

| Surface | Setting |
|---------|---------|
| CLI `ai` / `teach` | `--provider lmstudio|ollama|unsloth|custom`, `--model <key>`, `--url <base>` |
| GUI | **AI & Learn → AI Chat → provider** dropdown + **Prefer** model field (auto-loads with a VRAM-safe context) |
| TUI | AI & Knowledge section (same provider/model prompt) |

Examples:

```bash
openjyotish ai "birthdata" --provider lmstudio --model openjyotish-astrologer-v1
openjyotish ai "birthdata" --provider ollama   --model openjyotish-astrologer-v1
openjyotish ai "birthdata" --provider custom --url http://localhost:8000/v1 \
    --model openjyotish-astrologer-v1
```

Whatever the provider, **verify-repair stays on**: readings are mechanically
checked and repaired before display. Fine-tuning never does arithmetic.
