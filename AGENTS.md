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
# Expected: 678 passed
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
