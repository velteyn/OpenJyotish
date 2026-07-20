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
3. **Push to public** only when stable:
   

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
- `jhcore/` — ephemeris data (not in public git)
- `docs/help/` — original JHora help files
- `CONTEXT.md`, `PLAN.md`, `VISION.md`, `AGENTS.md` — dev docs
- Reverse-engineering artifacts

## Running Tests

```bash
cd ~/projects/Reversing/Jhora
python3 -m pytest tests/ -q
# Expected: 684 passed
```

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

- [AI Complete Guide](https://github.com/velteyn/OpenJyotish/wiki/AI-Complete-Guide) —
  comprehensive manual for AI features (CLI + GUI)
- Screenshot placeholders exist for 7 GUI screens. Upload to wiki repo's `screenshots/` folder.
- Update `_Sidebar.md` when adding new wiki pages
