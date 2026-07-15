# Jagannatha Hora — Vedic Astrology Software (Python Port)

**Status:** Active development — core engine ~85% complete
**Vision:** The most user-friendly, feature-complete, cross-platform, AI-powered Vedic astrology tool. Free and open-source. Useful for both casual users and professional astrologers.

## Origin
Reverse-engineered from **Jagannatha Hora 8.0 Lite** by **PVR Narasimha Rao**, published by Sri Jagannath Vedic Centre (SJVC). Original: PE32 GUI, C++ MFC, VC++ 6.0, x86, compiled 2015-12-31.

## Technology

| Layer | Technology |
|-------|-----------|
| **Core** | Python 3.11+, pyswisseph |
| **CLI** | Typer + Rich (16 commands) |
| **GUI** | PyQt6 dark theme, 3 chart styles, 15 tabs |
| **TUI** | Rich interactive terminal, 15 tabs |
| **Data** | SQLite (atlas), Pure Python |
| **Calc** | Pure Python, verified against original JHora |

## Current Status

### Deployed
- `src/jhora/` — Python package with **52 modules** across 10 subpackages (10,093 lines)
- Core types: Graha, Rasi, Nakshatra, Varga, Bhava, Dasa (6 types)
- Ephemeris: SweEngine wrapping all 18 SE APIs, sidereal positions, retrograde detection
- Chart: ChartBuilder + ChartData (frozen), planet dignity
- **Varga charts**: 23 levels (D-1 through D-150), 30+ variant mappings
- **Dasas**: 7 systems — Vimsottari, Ashtottari, Yogini, Sudasa, Chara, Narayana, Kalachakra
- **Shadbala**: Six-fold planetary strength (sthana, dig, kala, chesta, naisargika, drik)
- **Bhava Bala**: Five-factor house strength (sthana, drishti, dig, adhipati, drig) — shown in GUI Shadbala tab, CLI `--bhava` flag, TUI
- **Yogas**: 10+ types, 200+ combinations
- **Ashtakavarga**: BAV, SAV, PAV, Trikona/Ekadhipatya Shodhana, Kakshya-level bindu
- **Arudha Padas**: Bhava (AL, A2-A12) + Graha arudhas
- **Chara Karakas**: 8 planetary significators by longitude ranking
- **Sahamas**: 36 sensitive points
- **Transit**: Current transit vs natal with Ashtakavarga scores
- **Tajaka**: Solar return, Muntha, Harsha Bala, Patyayini/Mudda Dasa
- **Matchmaking**: 10 Porutham (19pt) + Ashta Koota (36pt)
- **Prasna**: 108/249/Nadi horary modes
- **Muhurta**: 11 task types, inauspicious periods, Abhijit detection, day scanning
- **Interpreter**: Rule-based chart reading + 16-source knowledge base (1.9M chars)
- **Atlas**: SQLite database (GeoNames CC BY 4.0, 34,006 cities), FTS5 search
- **JHD parser**: Save/load `.jhd` chart files (18 sample files)
- **CLI**: 16 commands — chart, dasa, navamsa, varga, interpret, knowledge, yogas, gui, shadbala, ashtakavarga, tajaka, kuta, transit, prasna, muhurta, tui
- **GUI**: PyQt6 dark theme, 3 chart styles, 15 tabs (Planets, Houses, Dasa, Varga, Yogas, Shadbala, Arudha & Karaka, Ashtakavarga, Transit, Tajaka, Matchmaking, Prasna, Muhurta, Knowledge, Reading)
- **TUI**: Rich-based interactive terminal, 15 keyboard-navigable tabs
- **Tests: 629 passing** (25 test files, 4,800+ lines)
- **Atlas**: SQLite database from GeoNames.org (CC BY 4.0), 34,006 cities, FTS5 full-text search, 3.8 MB — replaces proprietary `.adb` format

## Files

| File | Size | Description |
|------|------|-------------|
| `jhora.exe` | 2,375,680 B | Original binary (PE32, C++ MFC, 3,150 functions) |
| `swedll32.dll` | 536,576 B | Swiss Ephemeris DLL (18 API functions) |
| `jhora.hlp` | 3,820,452 B | Windows Help — extracted to `docs/help/` |
| `data/cities.db` | 3.8 MB | City atlas (GeoNames.org) — SQLite + FTS5 |
| `data/*.jhd` | 41-169 B each | 18 sample chart files |
| `data/jhd_samples.json` | 9 KB | Parsed sample chart data for testing |

## Reference
- Original JHora: `vedicastrologer.org/jh`
- Textbook: "Vedic Astrology: An Integrated Approach" (free download)
- Full help: `docs/help/` (56 topics extracted)
- Varga charts: `docs/varga_charts.md`
- Function map: `docs/function_map.md`
- SWE xrefs: `docs/swe_xrefs.md`
