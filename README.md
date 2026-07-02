# Jagannatha Hora — Vedic Astrology Software

Python port of **Jagannatha Hora 8.0 Lite** by PVR Narasimha Rao (published by Sri Jagannath Vedic Centre).

Free, open-source, cross-platform Vedic astrology tool. CLI + PyQt6 GUI.

## Features

- **Rasi chart** (D-1) — South Indian, North Indian, East Indian styles
- **Navamsa overlay** — D-9 positions shown inline on rasi chart
- **All 23 varga charts** — D-2 through D-150 with 21 variants
- **Vimsottari Dasa** — full MD/AD periods
- **Planet dignity** — exalted, debilitated, own, moolatrikona, friendly
- **Chart interpretation** — rule-based reading generator
- **Knowledge base** — full-text search over 16 Vedic astrology PDFs (textbook + articles)
- **PyQt6 dark-themed GUI** — polished, responsive

## Quick Start

```bash
pip install -e .
jhora gui             # Launch GUI
jhora chart "1970-04-04 17:48:20 +0530 13.08 80.27"
jhora navamsa "1970-04-04 17:48:20 +0530 13.08 80.27"
jhora varga --list    # Show all 23 divisional charts
jhora varga "birthdata" D-60 --variant trd
jhora interpret "birthdata" --search "yoga"
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `chart` | Rasi chart (D-1) |
| `navamsa` | Navamsa chart (D-9) |
| `dasa` | Vimsottari dasa periods |
| `varga` | Any divisional chart (D-1..D-150) |
| `interpret` | Chart reading / knowledge search |
| `knowledge` | Search book PDFs |
| `gui` | Launch PyQt6 interface |

## Technology

| Layer | Tech |
|-------|------|
| Core | Python 3.11+, pyswisseph |
| CLI | Typer + Rich |
| GUI | PyQt6 (dark theme) |
| AI | Ollama / LM Studio (coming soon) |
| Ephemeris | Swiss Ephemeris (37 API functions) |

## Architecture

```
src/jhora/
  types/        — Graha, Rasi, Nakshatra, Varga, Bhava, Dasa enums
  ephemeris/    — SweEngine wrapper (Swiss Ephemeris)
  charts/       — ChartBuilder, ChartData (immutable), VargaChartComputer
  calc/         — Dignities, strengths, yogas
  dasas/        — Vimsottari, Ashtottari, Narayana (WIP)
  interpreter/  — ChartInterpreter, KnowledgeBase, reference texts
  cli/          — Typer CLI (6 commands)
  ui/           — PyQt6 chart widget, main window
```

## Roadmap

- [x] Rasi chart, dignity, navamsa CLI
- [x] Vimsottari dasa (full MD/AD)
- [x] PyQt6 GUI (3 chart styles)
- [x] All 23 varga charts (D-2..D-150)
- [x] Chart interpretation + knowledge base (16 PDFs)
- [ ] Ashtottari, Narayana, Kalachakra dasas
- [ ] Shadbala strength computation
- [ ] Yogas detection engine (100+ combos)
- [ ] AI chat integration (Ollama)
- [ ] Transit charts
- [ ] Match making / compatibility

## Credits

Original software: **PVR Narasimha Rao** (pvr108@yahoo.com), Sri Jagannath Vedic Centre.

This port is a clean-room reimplementation. No original source code was used — only the compiled binary and its documented behavior.

## License

GNU Affero General Public License v3.0
