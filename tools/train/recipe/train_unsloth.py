"""Unsloth QLoRA recipe: dataset hash -> trained adapter, one command.

Runs ONLY on the user's own machine (single NVIDIA GPU). Nothing here is
imported in CI: ``torch``/``unsloth`` load lazily inside ``train()``, so
this module stays importable (and tested) without a GPU stack.

Hardware guidance (spec task 2.1):
- 8B-class base (e.g. Qwen3-8B, Llama-3.1-8B, Ministral-8B): ~10-12 GB VRAM
  at 4-bit QLoRA, max_seq_length 2048, batch 2 x accum 4.
- 14B-class base (e.g. Qwen3-14B): ~20-24 GB VRAM; same recipe, halve the
  batch or enable gradient checkpointing (already on).

Reproducibility (spec task 2.2):
- deterministic seeds where Unsloth allows (``random_state`` + HF seed),
- the dataset manifest hash is re-checked before training; a mismatch
  aborts instead of training on the wrong data,
- installed package versions are written into the model card (spec 2.3).

Usage (after ``pip install -r requirements-train.txt``):
  python3 tools/train/recipe/train_unsloth.py \\
      --dataset /path/to/dataset --base unsloth/qwen3-8b \\
      --rank 16 --epochs 2 --out /path/to/openjyotish-astrologer-lora-v1

Then score it against base (spec task 3.x, needs an LM Studio endpoint):
  PYTHONPATH=. python3 tools/train/eval_adapter.py --mock clean \\
      --n 20 --out /tmp/eval-base.json
  PYTHONPATH=. python3 tools/train/eval_adapter.py \\
      --lmstudio http://LAN-IP:1234 --model <adapter-key> \\
      --n 20 --out /tmp/eval-adapter.json
  PYTHONPATH=. python3 tools/train/eval_adapter.py \\
      --compare /tmp/eval-base.json /tmp/eval-adapter.json
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict

TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj",
                  "gate_proj", "up_proj", "down_proj"]
MIN_RANK, MAX_RANK = 16, 32


def build_train_config(args: argparse.Namespace) -> Dict:
    """Pure config assembly + validation (no torch needed)."""
    if not (MIN_RANK <= args.rank <= MAX_RANK):
        raise ValueError(f"--rank must be {MIN_RANK}-{MAX_RANK}, "
                         f"got {args.rank}")
    if args.epochs < 1:
        raise ValueError("--epochs must be >= 1")
    return {
        "base": args.base,
        "rank": args.rank,
        "lora_alpha": args.rank,  # alpha == rank is the Unsloth default
        "target_modules": list(TARGET_MODULES),
        "lora_dropout": 0,  # 0 is the optimized setting
        "bias": "none",
        "use_gradient_checkpointing": "unsloth",
        "load_in_4bit": True,
        "max_seq_length": args.max_seq_len,
        "per_device_batch": args.batch,
        "grad_accum": args.accum,
        "lr": args.lr,
        "epochs": args.epochs,
        "seed": args.seed,
        "random_state": args.seed,
        "out": args.out,
    }


def check_dataset(dataset_dir: Path) -> Dict:
    """Recompute the manifest hash; abort on mismatch (pure, no torch)."""
    dataset_dir = Path(dataset_dir)
    manifest = json.loads((dataset_dir / "manifest.json").read_text())
    blob = "".join(
        json.dumps(json.loads(line)["messages"], sort_keys=True)
        for line in (dataset_dir / "pairs.jsonl").read_text(
            encoding="utf-8").splitlines() if line.strip())
    digest = hashlib.sha256(blob.encode()).hexdigest()[:16]
    if digest != manifest.get("dataset_hash"):
        raise ValueError(
            f"dataset hash mismatch: manifest {manifest.get('dataset_hash')} "
            f"!= recomputed {digest} — refusing to train on wrong data")
    return manifest


def installed_versions() -> Dict[str, str]:
    """Recorded into the model card for exact rebuilds."""
    from importlib.metadata import version
    out = {}
    for pkg in ("unsloth", "torch", "transformers", "trl", "peft",
                "datasets", "accelerate", "bitsandbytes"):
        try:
            out[pkg] = version(pkg)
        except Exception:
            out[pkg] = "unknown"
    return out


def train(cfg: Dict, dataset_dir: Path) -> Path:
    """Full QLoRA run. Heavy imports live here — never at module top."""
    import torch
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer
    from unsloth import FastLanguageModel

    manifest = check_dataset(dataset_dir)
    rows = [json.loads(line) for line in
            (dataset_dir / "pairs.jsonl").read_text(
                encoding="utf-8").splitlines() if line.strip()]
    ds = Dataset.from_list([{"messages": r["messages"]} for r in rows])

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=cfg["base"],
        max_seq_length=cfg["max_seq_length"],
        dtype="auto",
        load_in_4bit=cfg["load_in_4bit"],
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=cfg["rank"],
        target_modules=cfg["target_modules"],
        lora_alpha=cfg["lora_alpha"],
        lora_dropout=cfg["lora_dropout"],
        bias=cfg["bias"],
        use_gradient_checkpointing=cfg["use_gradient_checkpointing"],
        random_state=cfg["random_state"],
        max_seq_length=cfg["max_seq_length"],
    )

    def _format(ex):
        text = tokenizer.apply_chat_template(
            ex["messages"], tokenize=False, add_generation_prompt=False)
        return {"text": text}

    ds = ds.map(_format)
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=ds,
        args=SFTConfig(
            dataset_text_field="text",
            per_device_train_batch_size=cfg["per_device_batch"],
            gradient_accumulation_steps=cfg["grad_accum"],
            learning_rate=cfg["lr"],
            num_train_epochs=cfg["epochs"],
            seed=cfg["seed"],
            output_dir=str(Path(cfg["out"]) / "checkpoints"),
        ),
    )
    trainer.train()

    out = Path(cfg["out"])
    model.save_pretrained(str(out / "adapter"))
    tokenizer.save_pretrained(str(out / "adapter"))
    card = (Path(__file__).parent / "MODEL_CARD.md").read_text()
    versions = "\n".join(f"- {k}=={v}"
                         for k, v in installed_versions().items())
    (out / "MODEL_CARD.md").write_text(
        card.replace("{{base}}", cfg["base"])
            .replace("{{rank}}", str(cfg["rank"]))
            .replace("{{epochs}}", str(cfg["epochs"]))
            .replace("{{dataset_hash}}", manifest.get("dataset_hash", "?"))
            .replace("{{dataset_counts}}",
                     json.dumps(manifest.get("provenance", {})))
            .replace("{{versions}}", versions)
            .replace("{{torch_cuda}}", f"{torch.__version__} "
                     f"(cuda={torch.version.cuda})"))
    print(f"adapter saved to {out / 'adapter'} "
          f"(dataset {manifest.get('dataset_hash')})")
    return out / "adapter"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Train the astrologer LoRA "
                                 "(user GPU machine only)")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--base", default="unsloth/qwen3-8b")
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--max-seq-len", type=int, default=2048)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--accum", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--seed", type=int, default=3407)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    cfg = build_train_config(args)
    train(cfg, Path(args.dataset))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
