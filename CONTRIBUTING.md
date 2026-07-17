# Contributing to OpenJyotish

Thanks for your interest in contributing. OpenJyotish is a free, open-source
Vedic astrology toolkit — we welcome fixes, features, and documentation.

## Quick Start

```bash
git clone https://github.com/velteyn/OpenJyotish.git
cd OpenJyotish
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e .
./download_ephe.sh   # one-time: download Swiss Ephemeris data
```

## Running Tests

```bash
python3 -m pytest tests/ -q
# Expected: 678 passed
```

Write tests for new features. Run the full suite before submitting.

## What We Need

| Priority | Area | Examples |
|----------|------|----------|
| High | **Bug fixes** | Crashes, wrong calculations, UI glitches |
| High | **Tests** | New test cases, edge cases, regression tests |
| Medium | **Documentation** | README improvements, docstrings, examples |
| Medium | **Additional dasa systems** | Dwisaptati, Shodasottari, Panchottari etc. |
| Low | **Chakras** | Sudarsana, Shoola, Tripataki |
| Low | **UI polish** | Chart rendering, theme improvements |

### What NOT to contribute
- **Ephemeris data** — these are large binary files from astro.com. Use `download_ephe.sh`.
- **Copyrighted content** — no books, PDFs, or extracted text from copyrighted sources.
- **Breaking API changes** — the `jhora` CLI and Python API must remain stable.

## Code Style

- Follow existing patterns. Look at neighboring files.
- No comments unless the logic is genuinely non-obvious.
- Use `from jhora.types.graha import Graha` style (explicit imports).
- Functions that compute: pure, testable, no side effects.
- Functions that render: accept `ChartData`, return strings/tables.
- Keep the CLI, GUI, and TUI in sync — every feature needs all three.

## Pull Request Process

1. **Fork** the repository
2. **Create a branch**: `fix/short-description` or `feat/short-description`
3. **Write tests** for your changes
4. **Run the full suite**: `python3 -m pytest tests/ -q`
5. **Submit a PR** against `main`
6. **Wait for CI** — all tests must pass
7. **Code review** — at least one maintainer reviews

PR titles should be short and descriptive. Use the commit style:
```
feat: description of new feature
fix: description of bug fix
test: description of test change
docs: description of doc change
```

## Architecture

```
src/jhora/
├── types/          Enums: Graha, Rasi, Nakshatra, Varga, Bhava, Dasa
├── ephemeris/      Swiss Ephemeris wrapper — do not modify lightly
├── charts/         ChartBuilder → ChartData (immutable, frozen dataclass)
├── calc/           Pure calculation modules — no UI code
├── dasas/          Dasa systems — extend DasaOptions, not existing APIs
├── ai/             AI engine, RAG pipeline, JSON export, teacher
├── interpreter/    Chart reading, knowledge base
├── export/         HTML report generator
├── io/             Atlas (SQLite/FTS5), JHD parser
├── core/           Unified database — get_db() singleton
├── cli/            Typer CLI — one command per calc module
├── tui/            prompt_toolkit menu system
└── ui/             PyQt6 GUI — MainWindow with nested QTabWidget
```

### Key Design Principles
- **ChartData is immutable** — never modify it after creation
- **All calculations are pure** — same input → same output, no state
- **Database via get_db()** — do not open SQLite directly
- **CLI, GUI, TUI parity** — features added to calc/ must be wired into all three

## Adding a New Feature

1. **Calculator** in `src/jhora/calc/your_feature.py` — pure function, takes `ChartData`
2. **CLI command** in `src/jhora/cli/main.py` — one `@app.command()` function
3. **GUI integration** in `src/jhora/ui/main_window.py` — new tab or table
4. **TUI integration** in `src/jhora/tui/main.py` — new menu item + action method
5. **Tests** in `tests/test_your_feature.py` — at least 5 test cases
6. **AI prompt** in `src/jhora/ai/analysis.py` — add to `build_analysis_text()`

## License

By contributing, you agree that your code will be licensed under the
**GNU Affero General Public License v3.0**. 

## Questions?

Open an issue on GitHub: https://github.com/velteyn/OpenJyotish/issues
