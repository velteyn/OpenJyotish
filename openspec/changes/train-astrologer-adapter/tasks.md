## 1. Dataset generator (`tools/train/`)

- [x] 1.1 Chart sampler: diverse birth-data grid (signs × houses × dasa
      lords × hemispheres), deterministic seed, N configurable (default 2000)
- [x] 1.2 Fact emitter: engine ground truth per chart (placements, lords,
      strengths, dasa periods, yogas) in a fixed schema the drafter must use
- [x] 1.3 Drafter: frontier/teacher model writes readings and Primer Q&A
      from facts + passages; provenance recorded per pair
- [x] 1.4 Verifier filter: keep only zero-flag pairs (`verify_answer`
      against the pair's own chart); log rejection reasons for tuning
- [x] 1.5 Manifest + provenance CI check: every pair tagged
  primer/pd-classic/engine-generated; any non-allowlisted source fails
  the build
- [x] 1.6 Held-out split: fixed eval chart set excluded from training output
      by construction (disjoint birth-data grid)

## 2. Training recipe (user hardware)

- [x] 2.1 Unsloth QLoRA config: 8B-class base, rank 16–32, pinned versions,
      single-GPU VRAM notes (8B ≈ 10–12GB, 14B ≈ 20–24GB)
- [x] 2.2 Repro script: dataset hash → trained adapter, one command,
      deterministic seeds where Unsloth allows
- [x] 2.3 Model card template: base, dataset hash, eval numbers, limitations

## 3. Eval harness

- [x] 3.1 Flag-rate + citation-genuineness scorer over the held-out set,
      identical prompts, base vs adapter
- [x] 3.2 Mock-LLM mode for CI (no server needed); live mode against
      LM Studio/Ollama/Unsloth endpoints
- [x] 3.3 Ship-threshold gate: adapter must beat base to release

## 4. Publishing

- [ ] 4.1 Release artifact naming (`openjyotish-astrologer-lora-vN`) +
      upload procedure
- [ ] 4.2 Loader docs: LM Studio / Ollama / Unsloth Studio + app provider
      setting
- [ ] 4.3 Full suite green; README/wiki updated with adapter docs
