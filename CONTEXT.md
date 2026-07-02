# Jagannatha Hora — Vedic Astrology Software (Python Port)

**Status:** Active development — Day 3 (July 2, 2026)
**Vision:** The most user-friendly, feature-complete, cross-platform, AI-powered Vedic astrology tool. Free and open-source. Useful for both casual users and professional astrologers.

## Origin
Reverse-engineered from **Jagannatha Hora 8.0 Lite** by **PVR Narasimha Rao** (pvr108@yahoo.com), published by Sri Jagannath Vedic Centre (SJVC). Original: PE32 GUI, C++ MFC, VC++ 6.0, x86, compiled 2015-12-31.

## Files

| File | Size | Description |
|------|------|-------------|
| `jhora.exe` | 2,375,680 B | Original binary (PE32, C++ MFC, 3,150 functions) |
| `swedll32.dll` | 536,576 B | Swiss Ephemeris DLL (18 API functions) |
| `jhora.hlp` | 3,820,452 B | Windows Help — extracted to `docs/help/` |

## Technology

| Layer | Technology |
|-------|-----------|
| **Core** | Python 3.11+, pyswisseph |
| **CLI** | Typer + Rich |
| **GUI** | PyQt6 (dark theme, vector charts) |
| **AI** | Ollama / LM Studio (local LLM) |
| **Data** | SQLite (charts, atlas, clients) |
| **Calc** | Pure Python, verified against original JHora |

## Current Status

### Deployed
- `src/jhora/` — Python package with **30 modules** across 15 subpackages
- Core types: Graha, Rasi, Nakshatra, Varga, Bhava, Dasa
- Ephemeris: SweEngine wrapping all 18 SE APIs
- Chart: ChartBuilder + ChartData (immutable), planet dignity
- Dasa: Vimsottari (full MD/AD periods)
- CLI: `chart`, `dasa`, `navamsa`, `interpret`, `knowledge`, `gui`
- GUI: PyQt6 dark theme, South/North/East Indian chart styles, planet/house/dasa tables
- Interpreter: Chart reading generator, knowledge base search
- Books: Author's textbook (515pp) + margabandhu (322pp) + 14 articles downloaded & text-extracted

### Building Now
- **Varga charts** (D-2 through D-60) — the #1 professional feature
- Ashtottari, Narayana, Kalachakra dasas
- Shadbala strength computation
- Yogas detection engine
- AI chat integration (Ollama)

### Full Roadmap
See [PLAN.md](PLAN.md) for competitive analysis, architecture, and 12-week roadmap.

## Reference
- Author's website: `vedicastrologer.org/jh`
- Textbook: "Vedic Astrology: An Integrated Approach" (free download)
- Full help: `docs/help/` (56 topics extracted)
- Varga charts: `docs/varga_charts.md`
