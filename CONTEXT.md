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
- `src/jhora/` — Python package with **33 modules** across 10 subpackages (4,972 lines)
- Core types: Graha, Rasi, Nakshatra, Varga, Bhava, Dasa (6 types, 546 lines)
- Ephemeris: SweEngine wrapping all 18 SE APIs, sidereal positions, retrograde detection
- Chart: ChartBuilder + ChartData (frozen), planet dignity
- **Varga charts**: 23 levels (D-1 through D-150), 30+ variant mappings — fully implemented
- **Dasas**: Vimsottari (120-year), Ashtottari (108-year) — MD/AD periods
- **Shadbala**: Six-fold planetary strength (sthana, dig, kala, chesta, naisargika, drik) — 491 lines, 48 tests
- **Yogas**: 10+ yoga types, 12 categories, 100+ combos (Pancha Mahapurusha, Raja, Dhana, Viparita Raja, Neecha Bhanga Raja, Parivartana, Chandra yogas, Surya yogas, Kemadruma, Amala, Dharma-Karma-Adhipati, Kala Sarpa)
- CLI: `chart`, `dasa` (vimsottari/ashtottari), `navamsa`, `varga`, `shadbala`, `yogas`, `ashtakavarga`, `interpret`, `knowledge`, `gui`
- GUI: PyQt6 dark theme, South/North/East Indian chart styles (3, with diamond lines for North, radial spokes for East), 8 tabs (planets, houses, dasa system selector, varga, yogas, shadbala, ashtakavarga, transit)
- Interpreter: Chart reading generator (rule-based, connected to yogas engine)
- Knowledge base: 16 sources, 1.9M chars, full-text search
- Books: Author's textbook (515pp) + margabandhu (322pp) + 14 articles text-extracted
- **Tests: 380 passing** (15 test files, 2,700 lines)
- **Docs**: `docs/help/chart_drawing_analysis.md` — comprehensive RE analysis of binary chart rendering vs current implementation
- **Ashtakavarga**: BAV, SAV, PAV, Trikona/ Ekadhipatya Shodhana, Sodhya Pinda, and Kakshya-level bindu computation (8 sub-divisions per house) — `src/jhora/calc/ashtakavarga.py`
- **Wine testbench experiment**: Attempted to recompile original JHora with debug symbols via MinGW under Wine, but blocked by Wine 10 WoW64 architecture — 64-bit LD_PRELOAD cannot access 32-bit PE memory, ptrace_scope=1 prevents external attachment, and cannot install MinGW/wine32 without sudo. No viable in-process debugging path for the original binary.
- **Chart rendering RE**: Deep-dived binary function 0x004CB240 (15,614 B, 202 locals — guessed as "Main chart rendering" in function_map). Analysis with capstone reveals it's actually the **yoga description text builder** — calls string-append function 0x00513C3E 310× with 406 unique string references (yoga names, descriptions). Contains 3,187 instructions, zero GDI32 calls. GDI32 drawing functions (91 imported: TextOutA, MoveToEx, LineTo, Rectangle, etc.) are likely called through MFC CDC wrappers in other functions. Documented findings in `docs/help/chart_drawing_analysis.md`.
- Chart widget improvements: North Indian diamond diagonal lines added; East Indian radial planet positioning improved; fonts optimized for cell fitting. All 380 tests pass.

### Building Next
- More dasa systems (Narayana, Kalachakra, Yogini, Chara, Sudasa, etc.)
- Arudha padas, Chara karakas, Sahamas
- Tajaka solar return
- **Gochara (Transit)**: Done — `src/jhora/calc/gochara.py`, CLI `jhora transit`, GUI tab — shows per-planet transit house, BAV/SAV scores, favorable flags
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
