# AGENTS.md — Development Guide for OpenJyotish / Jhora

## Two Repositories

| Repo | URL | Visibility | Purpose |
|------|-----|-----------|---------|
| **OpenJyotish** | `github.com/velteyn/OpenJyotish` | Public | Official release, public-facing |
| **Jhora** | `github.com/velteyn/jhora` | Private | Development, reverse-engineering reference |

Both repos share the same codebase. OpenJyotish is the clean public version.  
Jhora retains RE artifacts, original help files, and development docs.

## Keeping Them In Sync

```bash
# After making changes in either repo:

# 1. If working in Jhora (private) → push to OpenJyotish (public)
cd ~/projects/Reversing/Jhora
git push public main

# 2. If working in OpenJyotish (public) → pull to Jhora (private)
cd ~/projects/Reversing/Jhora
git pull public main
git push origin main

# 3. Verify both are in sync
git log --oneline -3
git log public/main --oneline -3
```

## Workflow

1. **Develop & test** in the private Jhora repo (has ephemeris data, binary reference)
2. **Consolidate** — run full test suite, fix all issues
3. **Push to public** only when stable — follow the full pipeline below:

### Feature Branch + PR + Merge Pipeline

Every feature/fix follows this exact sequence. **Never commit directly to `main` on `public`.**

```bash
# 1. Create feature branch from main
git checkout main
git checkout -b feature/<name>

# 2. Commit (only intentional source/test changes)
git add src/ tests/
# NEVER commit: data/jhora.db (test churn), RE artifacts (jhora.exe, *.dll, *.hlp, *.cnt)

# 3. Push branch to public
git push public feature/<name>

# 4. Open PR against public/main
gh pr create --repo velteyn/OpenJyotish \
  --base main --head feature/<name> \
  --title "..." --body "..."

# 5. Verify PR diff is clean
gh pr view <N> --repo velteyn/OpenJyotish --json files
# Confirm: only intended files, no data/jhora.db, no RE artifacts

# 6. Merge (squash or merge — default merge)
gh pr merge <N> --repo velteyn/OpenJyotish --merge --delete-branch

# 7. Sync back: public → local → origin
git fetch public
git checkout main
git merge --ff-only public/main
git push origin main

# 8. Cleanup
git branch -d feature/<name>
```

### After Every Merge — Update These

| What | When |
|------|------|
| `GAP-ANALYSIS.md` | New calculation added or gap closed |
| Wiki pages (see Wiki Maintenance) | New user-facing feature |
| `USL_CONTEXT.md` or equivalent | Session handoff files (clean up when feature is done) |

Never develop directly in the public repo — it lacks ephemeris data for testing.

## What Lives Where

### OpenJyotish (public) — what ships
- `src/jhora/` — all source code
- `tests/` — all tests
- `data/jhora.db` — prebuilt SQLite database
- `requirements.txt` — dependencies
- `pyproject.toml` — package config
- `install.sh/bat`, `run.sh/bat` — launchers
- `download_ephe.sh` — ephemeris downloader
- `make_release.sh` — Windows release builder
- `README.md`, `SECURITY.md`, `LICENSE`
- `.github/` — Dependabot, CI

### Jhora (private) — additional
- All of the above, PLUS:
- `jhora.exe`, `swedll32.dll`, `jhora.hlp` — original JHora binary
- `jhcore/ephe/` — ephemeris data (**not committed to git** in either repo — downloaded at install time by `install.bat` / `download_ephe.py`)
- `docs/help/` — original JHora help files
- `CONTEXT.md`, `PLAN.md`, `VISION.md`, `AGENTS.md` — dev docs
- Reverse-engineering artifacts

## Running Tests

```bash
# Linux / Mac — activate venv first
source venv/bin/activate
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
# Expected: 689 passed

# Windows (PowerShell) — use venv Python directly
$env:PYTHONPATH="src"; $env:QT_QPA_PLATFORM="offscreen"
.\venv\Scripts\python.exe -m pytest tests/ -q
# Expected: 689 passed
```

> **Note**: Always use the venv Python, not the system `python` / `python3`.
> The system Python does not have `swisseph` installed — tests will fail with
> `ModuleNotFoundError` if you use the wrong interpreter.

## Release Process

```bash
# 1. Update version in src/jhora/__init__.py
# 2. Build Windows package
./make_release.sh
# 3. Upload /tmp/openjyotish-v*.zip to GitHub Releases
# 4. Tag the release
git tag v$(python3 -c "import jhora; print(jhora.__version__)")
git push public --tags
```

## Security

- `SECURITY.md` in public repo for vulnerability reporting
- Dependabot enabled for automatic dependency updates (Mondays)
- Code scanning active — fix alerts promptly
- Never commit `jhcore/ephe/` to public repo (use `download_ephe.sh`)
- Redact PII from logs and exports (lat/lon → `[REDACTED]`)

## AI & Vector DB

The vector database uses auto-detection:
- LM Studio (port 1234) — preferred if running
- Ollama (port 11434) — fallback
- FTS5 keyword search — always available without any server

Textbooks are pre-loaded in `data/jhora.db` (16 sources, 1.96M chars).

## Cross-Surface Consistency Invariants

These are **hard rules** that apply to EVERY new calculation or feature. Failing them
ships an inconsistent tool where the AI and one of the UIs silently disagree with the
rest of the app. Treat any violation as a release-blocking bug.

### 1. The AI system must always be aware of new calculations

When any calculation is added, changed, or given new options, the AI pipeline **must**
consume it too. Do **not** leave the AI reading only defaults while the GUI/CLI offer the
full option set.

Enforcement checklist:
- Add the new/updated data to the AI context builders.
  - `src/jhora/ai/analysis.py` — `full_analysis()`, `dasa_snapshot()`, and the section
    builders (e.g. `("DASA PERIODS", lambda: dasa_snapshot(cd))` in `json_export.py` too).
  - `src/jhora/ai/json_export.py` — `result["dasa"]`, `sahamas`, `lagnas`, `sphutas`, etc.
  - `src/jhora/ai/prompts.py` — the system prompt inventory of what the model can see.
  - `src/jhora/ai/teacher.py` — lesson generation should reference the same data.
- Whenever a computation gets a new `DasaOptions`/config dimension (seed, sesham, year
  definition, ayurveda, method, variant, ...), the AI context must either:
  (a) honor an explicit choice, or
  (b) document which default it uses **in the prompt context so the model knows**.
  Never silently compute with a stale default while the UI offers a choice.
- After touching `src/jhora/calc/**` or `src/jhora/dasas/**`, grep the AI modules for the
  feature name and verify it flows through `analysis.py` / `json_export.py`.
- Test with `tests/test_ai.py` (and any targeted AI test) so drift is caught automatically.

### 2. GUI and TUI must expose the same capabilities

Every option/calculation reachable in the GUI **should** be reachable in the TUI (and the
CLI), modulo the TUI's inherent limits (no rich interactive charts, no mouse, simpler
widgets). "TUI limitation" is a real, acceptable reason for a pared-back presentation —
but **not** for a missing capability.

Enforcement checklist:
- When adding a GUI control (combo, checkbox, button, tab), add the equivalent:
  - **CLI flag** in `src/jhora/cli/main.py` (e.g. the `--start`, `--sesham`, `--year-def`
    flags added to `dasa`).
  - **TUI menu item / settings action** in `src/jhora/tui/main.py` (e.g. the "Dasa
    Settings (seed/sesham/year)" entry).
- The TUI should show the currently selected option value in its output header so the
  result is unambiguous (e.g. the dasa table title includes `seed=... sesham=...`).
- If a capability genuinely cannot work in the TUI, document the reason in the menu label
  or a comment — do not silently omit it.
- Verify with the GUI populate tests (`tests/test_gui_populate.py`) and the CLI tests
  (`tests/test_cli.py`).

#### Known TUI limitations (acceptable reasons to pare back, never to omit)

These are the current, documented reasons a TUI presentation may be simpler than its GUI
equivalent. A capability falling outside this list is **not** exempt — it must ship in the
TUI too.

- **No rich interactive charts** — the GUI renders SVG/north-indian/south-indian wheel
  charts, divisional charts, and dashboards. The TUI renders text tables and ASCII only.
- **No mouse** — no drag, hover, double-click, context menus. Navigation is keyboard-driven.
- **Simpler widgets** — no full QComboBox/QSpinBox/QCheckBox; the TUI uses text prompts
  and menu selections with typed values.
- **No inline images/screenshots** — GUI uses images; TUI can only show text.
- **Output is ephemeral** — no persistent window state; each command prints and returns.

Anything else (a calculation, a dasa option, a special lagna, an AI output view) that the
GUI exposes must have a TUI entry. If a genuinely GUI-only capability cannot be represented,
state the reason in the TUI menu label or a comment.

### Example — what "done" looks like (the Vimsottari options feature)

When the Vimsottari seed/sesham/year options were added, ALL of these shipped together:
- **Engine**: `DasaOptions(start_variation, sesham_method, year_definition)` in
  `src/jhora/dasas/base.py`, honored in `src/jhora/dasas/vimsottari.py`.
- **CLI**: `dasa --start --sesham --year-def` in `src/jhora/cli/main.py`.
- **GUI**: Seed/Sesham/Year dropdowns on the Dasa tab in `src/jhora/ui/main_window.py`.
- **TUI**: "Dasa Settings (seed/sesham/year)" in `src/jhora/tui/main.py`.
- **Tests**: engine + GUI coverage added.

This is the default scope for any future feature. If a surface is missing, the feature is
not complete — take it back before committing.

## Lessons Learned — GUI Development Rules

These rules come from multiple failed attempts at fixing the AI Settings tab.
Violating any of them caused regressions, disabled buttons, memory leaks, or crashes.

### NEVER do these

1. **Never move provider/model config between tabs carelessly** — The AI Settings tab now owns
   `ai_provider`, `ai_model`, `ai_check_btn`, `ai_status`. Moving these REQUIRES updating
   ALL references in `_get_ai_engine()`, `_on_ai_health_check()`, `_on_ai_vdb_build()`,
   `_on_ai_vdb_status()`, and the Teacher tab. Test with `tests/test_gui_populate.py`.

2. **Never disable AI buttons based on health check state** — buttons should always be enabled.
   If the server is down, the action fails gracefully with a message. Disabled buttons
   create an unsolvable UX puzzle for users.

3. **Never run health checks in a QThread** — the synchronous `requests.get()` is 2-6 seconds.
   That's acceptable for a one-time manual action. Threads introduce signal delivery
   issues, race conditions, and stale result problems. Keep it simple.

4. **Never refactor without running integration tests** — `tests/test_gui_populate.py`
   exists for a reason. It catches widget existence, button state, and attribute errors.
   If a test fails after refactoring, the refactoring is wrong.

5. **Never add QThread helper classes without testing them** — `_VdbWorker`, `_HealthWorker`,
   `_TeacherWorker` all use pyqtSignal. These must be tested with `QT_QPA_PLATFORM=offscreen`
   to verify signals fire and slots execute on the GUI thread.

### Vector DB Build Rules

1. **Always use batches** — 5 texts per request, never one at a time. 4000 individual
   HTTP calls flood the server and freeze the PC.

2. **Always throttle** — 1000ms between batches. Without this, the network stack and
   LM Studio become unresponsive.

3. **Always call gc.collect()** after each source — the EmbeddingStore holds large
   numpy arrays in memory. Without gc, memory grows unboundedly.

4. **Never block the UI thread** — the build runs in `_VdbWorker` QThread. The button
   starts it, progress signals update the text area, done signal re-enables the button.

### Rich Markup Rules

1. **Use `[bold]`, `[bold yellow]`, `[red]`, `#RRGGBB` in Dashboard text** — the
   `_to_html()` function in `_populate_dashboard` converts Rich markup to HTML spans.
   This is the ONLY place that uses this format. QTextEdit uses `setHtml()`.

2. **Dashboard font**: Consolas monospace 15px. Strength bars align perfectly with
   this font. Don't change it without verifying bar alignment.

3. **AI output uses `self._format_plain()`** — converts `**bold**` to `<b>bold</b>`,
   strips broken HTML fragments from LLM output.

### Git Rules

1. **Never push to public before testing** — private repo has ephemeris data for real testing.
2. **Always clear `__pycache__`** when debugging stale behavior — Python caches old `.pyc`
   files that persist across git pulls.
3. **Always commit from the private repo** — the public repo is a mirror, not a workspace.

### Wiki Maintenance

Wiki lives at `/tmp/opencode/wiki` (remote `https://github.com/velteyn/OpenJyotish.wiki.git`).
Push changes: `cd /tmp/opencode/wiki && git add . && git commit -m "..." && git push`.

#### Per-Feature Update Checklist

| What changed | Which wiki pages to update |
|---|---|
| New calculation (e.g. special lagna) | CLI Reference, GUI Guide, TUI Guide, AI Complete Guide |
| New CLI command/flag | CLI Reference |
| New GUI widget/control | GUI Guide (+ screenshot if visual) |
| New TUI menu/command | TUI Guide |
| New AI pipeline section | AI Complete Guide, AI & Predictions |
| New dasa option (seed/sesham/etc.) | Vimsottari Dasa Options, CLI Reference, GUI Guide, TUI Guide |
| Architecture change (new module) | Architecture, Development Handbook |
| Installation change | Installation |

#### Rules

- **Always update `_Sidebar.md`** when adding a new wiki page.
- **Screenshot placeholders** exist for GUI screens. Upload to `wiki/screenshots/` when available.
- **Never leave a stale page**: if a feature's behavior changes, update all pages that reference it.
- **AI Complete Guide** is the comprehensive manual — it must cover both CLI and GUI usage of any AI feature.
