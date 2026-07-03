# Jagannatha Hora — Vedic Astrology Software (Python Port)

**Status:** Active development — core engine ~60% complete
**Vision:** The most user-friendly, feature-complete, cross-platform, AI-powered Vedic astrology tool. Free and open-source. Useful for both casual users and professional astrologers.

## Origin
Reverse-engineered from **Jagannatha Hora 8.0 Lite** by **PVR Narasimha Rao**, published by Sri Jagannath Vedic Centre (SJVC). Original: PE32 GUI, C++ MFC, VC++ 6.0, x86, compiled 2015-12-31.

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
| **CLI** | Typer + Rich (9 commands) |
| **GUI** | PyQt6 dark theme, 3 chart styles, 6 tabs |
| **AI** | Ollama / LM Studio (planned) |
| **Data** | Pure Python (SQLite planned) |
| **Calc** | Pure Python, verified against original JHora |

## Current Status

### Deployed
- `src/jhora/` — Python package with **32 modules** across 10 subpackages (4,442 lines)
- Core types: Graha, Rasi, Nakshatra, Varga, Bhava, Dasa (6 types, 546 lines)
- Ephemeris: SweEngine wrapping all 18 SE APIs, sidereal positions, retrograde detection
- Chart: ChartBuilder + ChartData (frozen), planet dignity
- **Varga charts**: 23 levels (D-1 through D-150), 30+ variant mappings — fully implemented
- **Dasas**: Vimsottari (120-year), Ashtottari (108-year) — MD/AD periods
- **Shadbala**: Six-fold planetary strength (sthana, dig, kala, chesta, naisargika, drik) — 491 lines, 48 tests
- **Yogas**: 10+ yoga types, 12 categories, 100+ combos (Pancha Mahapurusha, Raja, Dhana, Viparita Raja, Neecha Bhanga Raja, Parivartana, Chandra yogas, Surya yogas, Kemadruma, Amala, Dharma-Karma-Adhipati, Kala Sarpa)
- CLI: `chart`, `dasa` (vimsottari/ashtottari), `navamsa`, `varga`, `shadbala`, `yogas`, `interpret`, `knowledge`, `gui`
- GUI: PyQt6 dark theme, South/North/East Indian chart styles, 6 tabs (planets, houses, dasa system selector, varga, yogas, shadbala)
- Interpreter: Chart reading generator (rule-based, connected to yogas engine)
- Knowledge base: 16 sources, 1.9M chars, full-text search
- Books: Author's textbook (515pp) + margabandhu (322pp) + 14 articles text-extracted
- **Tests: 338 passing** (13 test files, 2,400 lines)

### Building Next
- Ashtakavarga (SAV, BAV, SoAV, PAV) — #1 professional feature
- More dasa systems (Narayana, Kalachakra, Yogini, Chara, Sudasa, etc.)
- Arudha padas, Chara karakas, Sahamas
- Tajaka solar return, Transit analysis
- AI chat integration (Ollama)

### Full Roadmap
See [PLAN.md](PLAN.md) for competitive analysis, architecture, and phased roadmap.

## Reference
- Original JHora: `vedicastrologer.org/jh`
- Textbook: "Vedic Astrology: An Integrated Approach" (free download)
- Full help: `docs/help/` (56 topics extracted)
- Varga charts: `docs/varga_charts.md`
- Function map: `docs/function_map.md`
- SWE xrefs: `docs/swe_xrefs.md`
