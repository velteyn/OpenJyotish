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
| `jhcore/atlas/jhworld.adb` | 64 MB | JHora city/atlas database (custom `.adb` format) |
| `jhcore/atlas/jhlite.adb` | 56 KB | Lite atlas subset |
| `jhcore/ephe/*.se1` | ~94 MB | Swiss Ephemeris monthly files (Moon + planets, 0–162 months) |
| `jhora.hlp` | 3,820,452 B | Windows Help — extracted to `docs/help/` |
| `data/*.jhd` | 41–169 B each | 18 sample chart files (Gandhi, Vivekananda, PVR, etc.) — native `.jhd` format, line-based ASCII |

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
- `src/jhora/` — Python package with **43 modules** across 10 subpackages (7,700+ lines)
- Core types: Graha, Rasi, Nakshatra, Varga, Bhava, Dasa (6 types, 546 lines)
- Ephemeris: SweEngine wrapping all 18 SE APIs, sidereal positions, retrograde detection
- Chart: ChartBuilder + ChartData (frozen), planet dignity
- **Varga charts**: 23 levels (D-1 through D-150), 30+ variant mappings — fully implemented
- **Dasas**: Vimsottari (120-year), Ashtottari (108-year), **Yogini (36-year, 8-yogini cycle)**, **Sudasa (Sreelagna Kendradi Rasi Dasa)**, **Chara (78-year, rasi-based)**, **Narayana (rasi-based, lagna-progression)**, **Kalachakra (12-year, nakshatra pada deha/jeeva)** — MD/AD periods, all 7 systems selectable in GUI dasa combo box
- **Shadbala**: Six-fold planetary strength (sthana, dig, kala, chesta, naisargika, drik) — 491 lines, 48 tests
- **Yogas**: 10+ yoga types, 12 categories, 100+ combos (Pancha Mahapurusha, Raja, Dhana, Viparita Raja, Neecha Bhanga Raja, Parivartana, Chandra yogas, Surya yogas, Kemadruma, Amala, Dharma-Karma-Adhipati, Kala Sarpa)
- CLI: `chart`, `dasa` (vimsottari/ashtottari), `navamsa`, `varga`, `shadbala`, `yogas`, `ashtakavarga`, `interpret`, `knowledge`, `gui`, `kuta`
- GUI: PyQt6 dark theme, South/North/East Indian chart styles (3, with diamond lines for North, radial spokes for East), 11 tabs (planets, houses, dasa system selector, varga, yogas, shadbala, ashtakavarga, transit, arudha/karaka/sahama, tajaka, matchmaking)
- Interpreter: Chart reading generator (rule-based, connected to yogas engine)
- Knowledge base: 16 sources, 1.9M chars, full-text search
- Books: Author's textbook (515pp) + margabandhu (322pp) + 14 articles text-extracted
- **Tests: 552 passing** (20 test files, 3,500+ lines)
- **Docs**: `docs/help/chart_drawing_analysis.md` — comprehensive RE analysis of binary chart rendering vs current implementation
- **Tajaka (Solar Return)**: Varsha Pravesh (Sun return search via `swe.solcross_ut`), Muntha (progressed lagna), Harsha Bala (4-source strength), Patyayini Dasa (krisamsa/patyamsa), Mudda Dasa (compressed Vimsottari) — `src/jhora/calc/tajaka.py`, 19 tests, CLI `jhora tajaka` command, wired in 10th GUI tab
- **Kuta Porutham** (Matchmaking): Two scoring systems: 10 Porutham (Dina, Gana, Yoni, Rasi, Rasyadhipati, Nadi, Rajju, Vedha, Vashya, Mahendra, 19pt) + Ashta Koota (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoota, Nadi, 36pt — matching original JHora binary's `function_4b3b10` 36×36 lookup table). `compute_kuta()` with `ScoringSystem` enum, `--ashta-koota/-k` CLI flag. `gunanka_level()` for qualitative score bands. `src/jhora/calc/kuta.py`, 106 tests
- **Arudha Padas**: Bhava arudhas (AL, A2–A12) + Graha arudhas — `src/jhora/calc/arudha.py`, tested, wired in 9th GUI tab
- **Chara Karakas**: 8 planetary karakas by longitude ranking — `src/jhora/calc/karaka.py`, tested, wired in 9th GUI tab
- **Sahamas**: 36 sensitive points (Punya, Vidya, Samartha, Artha, etc.) — `src/jhora/calc/sahama.py`, 13 tests, wired in 9th GUI tab
- **Ashtakavarga**: BAV, SAV, PAV, Trikona/ Ekadhipatya Shodhana, Sodhya Pinda, and Kakshya-level bindu computation (8 sub-divisions per house) — `src/jhora/calc/ashtakavarga.py`
- **Wine testbench experiment**: Attempted to recompile original JHora with debug symbols via MinGW under Wine, but blocked by Wine 10 WoW64 architecture — 64-bit LD_PRELOAD cannot access 32-bit PE memory, ptrace_scope=1 prevents external attachment, and cannot install MinGW/wine32 without sudo. No viable in-process debugging path for the original binary.
- **Chart rendering RE**: Deep-dived binary function 0x004CB240 (15,614 B, 202 locals — guessed as "Main chart rendering" in function_map). Analysis with capstone reveals it's actually the **yoga description text builder** — calls string-append function 0x00513C3E 310× with 406 unique string references (yoga names, descriptions). Contains 3,187 instructions, zero GDI32 calls. Documented findings in `docs/help/chart_drawing_analysis.md`.
- **Complete IAT map** built: 493 entries across 15 DLLs. Key finding: JHora calls GDI32 functions via **direct `call [IAT]`** instructions from application code (0x004xxxxx), NOT through MFC CDC wrapper thunks — 0 direct callers found to 0x4FAxxx thunks.
- **Three chart drawing functions identified** in the binary: `fn44B9B6` (0x44B9B6, South Indian — 3×Rectangle + 3×CreatePen), `fn00481670` (0x481670, East Indian — 3×Ellipse + 5×CreateSolidBrush), `fn0051E3B0` (0x51E3B0, North Indian — MoveToEx+LineTo pair ×12). Dispatcher at `fn0044C170` (0x44C170) routes via 23-entry jump table on global `[0x8A4B58]`.
- Chart widget improvements: North Indian diamond diagonal lines added; East Indian radial planet positioning improved; fonts optimized for cell fitting. All 384 tests pass.
- **`jhcore/` data files** discovered: `atlas/*.adb` (62 MB jhworld.adb + 56 KB jhlite.adb, custom binary format — reads by atlas function 0x004c2250) and `ephe/*.se1` (~94 MB, standard Swiss Ephemeris monthly files). The `.adb` format needs RE to support native JHora atlas lookup.
- **`data/*.jhd` sample charts** — 18 `.jhd` files for famous personalities. Line-based ASCII format with two variants: 14-line (birth data only) and 18+ line (includes computed planet positions). Valuable for testing our JHD parser and chart calculations.
- **Graha→SE planet ID mapping fixed**: ChartBuilder uses explicit `_SE_TO_GRAHA` dict (Graha enum uses Vedic numbering, not SE IDs).
- **UTC time conversion fixed**: `utc_hour = local_hour + tz_offset`, signed offset (negative = east of GMT). Parses HHMM (`+0530` → `-5.5`) and decimal (`-5.36`) formats.
- **SweEngine.calc_planets() fixed**: Uses **Mean Node** for Rahu; computes Ketu as `(Mean Node + 180°) % 360` (was using `SE_OSCU_APOG` — Moon's apogee).
- **Node dignity**: DignityChecker returns `"node"` for Rahu/Ketu (regardless of sign position).
- **JHD parser planet order fixed**: Vedic order (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu), not Swiss Ephemeris order.
- **Date/Time pickers**: QDateEdit (calendar popup) + QTimeEdit (spinner) replacing raw text inputs. "Now" button auto-fills system date/time and detects TZ offset.
- **TZ auto-detect**: Reads system UTC offset via `time.timezone` + DST flag, writes signed decimal (e.g., `-2.0` for UTC+2).

### Deployed (atlas)
- **`.adb` atlas format fully reverse-engineered**:
  - 64-byte header: `"Jagannatha Hora\0\0\0\x01"` (version 1)
  - Big-endian 4-byte offset index at 0x60 pointing to `0xC0`-delimited country groups
  - **291 groups** covering ~2.63M cities globally
  - **10-byte city data block**: `[lon_int, lon_min, 0, lat_int, lat_min, 0, 0, 0, tz_qh, tz_dst_qh]`
  - **Sign encoding**: `byte[1] < 128` → WEST longitude (minutes stored directly); `byte[1] >= 128` → EAST longitude (`byte[1] - 128`). Same pattern for `byte[4]` (lat: < 128 = south, >= 128 = north)
  - **TZ encoding**: `byte[8]` as signed quarter-hours from UTC (÷4 → hours). `byte[9]` = DST offset (same encoding)
  - **`0x80` section markers**: 4-byte sub-region boundaries (e.g., UK counties) — skip to continue parsing
  - Minimum name length: 2 chars (e.g., "At" in India)
  - **US group**: Has a different sub‑group structure with state codes (not yet parsed)
- **AtlasReader class**: parses `jhworld.adb` (62 MB, 2.63M cities) and `jhlite.adb` (56 KB)
  - `search(query)` → substring match across all city names
  - `load_all()` → full dataset
  - Verified: London (51.50°N 0.12°W), Mumbai (18.97°N 72.83°E), Delhi (28.67°N 77.22°E)
- **City lookup widget**: `QLineEdit` + search button in birth data form (between Time and TZ)
  - Real-time search with 300ms debounce via `AtlasReader.search()`
  - Results in styled `QListWidget` below the form
  - Click selection auto-fills lat, lon, and TZ (converted from UTC offset to JHora convention)
  - Lazy-loads atlas on first search (62 MB, ~60ms)
- **JHD file save/load**: File → Open (`Ctrl+O`) parses `.jhd` files and fills all form fields. File → Save / Save As (`Ctrl+S` / `Ctrl+Shift+S`) writes form data back to `.jhd` in BIRTH_CITY format (14 lines). Auto-calculates chart on open, updates window title with chart name. `save_jhd()` in `jhd_parser.py` — symmetric write function for `parse_jhd()`.

### Deployed (atlas)
See [PLAN.md](PLAN.md) for competitive analysis, architecture, and phased roadmap.

## Reference
- Original JHora: `vedicastrologer.org/jh`
- Textbook: "Vedic Astrology: An Integrated Approach" (free download)
- Full help: `docs/help/` (56 topics extracted)
- Varga charts: `docs/varga_charts.md`
- Function map: `docs/function_map.md`
- SWE xrefs: `docs/swe_xrefs.md`
