# Jagannatha Hora — Vedic Astrology Software (Python Port)

**Status:** Complete — **v1.0.0** — all 35 planned features shipped
**Vision:** The most user-friendly, feature-complete, cross-platform, AI-powered Vedic astrology tool. Free and open-source.

## Origin
Reverse-engineered from **Jagannatha Hora 8.0 Lite** by PVR Narasimha Rao (SJVC, 2015). Original: PE32 GUI, C++ MFC, x86, 3,150 functions.

## Technology

| Layer | Technology |
|-------|-----------|
| **Core** | Python 3.11+, pyswisseph |
| **CLI** | Typer + Rich (18 commands) |
| **GUI** | PyQt6 dark theme, 3 chart styles, 17 tabs |
| **TUI** | Rich interactive terminal, 16 panels |
| **Data** | SQLite unified DB (jhora.db), FTS5 search |
| **AI** | Ollama / LM Studio / Unsloth (OpenAI-compatible API) |
| **Calc** | Pure Python, verified against original JHora |

## Current Status

### Scale
- **12,679 lines** Python source across **57 modules** in 11 subpackages
- **5,007 lines** of tests across **26 test files**, **646 tests** (all passing)
- **18 CLI commands**, **17 GUI tabs**, **16 TUI panels**

### Deployed — Computational
- **Chart**: ChartBuilder + ChartData (frozen), 9 planets + lagna + 12 house cusps
- **Varga**: 23 divisional charts (D-1 through D-150), 30+ variant mappings
- **Dasas**: 7 systems — Vimsottari, Ashtottari, Yogini, Sudasa, Chara, Narayana, Kalachakra
- **Shadbala**: Six-fold planetary strength (sthana/dig/kala/chesta/naisargika/drik)
- **Bhava Bala**: Five-factor house strength (sthana/drishti/dig/adhipati/drig)
- **Vimsopaka Bala**: Four schemes (Shadvarga/Saptavarga/Dashavarga/Shodasavarga), varga-weighted
- **Yogas**: 10+ types, 200+ combinations
- **Ashtakavarga**: BAV, SAV, PAV, Trikona/Ekadhipatya Shodhana, Kakshya
- **Arudha Padas**: Bhava (AL, A2-A12) + Graha arudhas
- **Chara Karakas**: 8 significators by longitude ranking
- **Sahamas**: 36 sensitive points
- **Transit**: Current transit vs natal with Ashtakavarga scores
- **Tajaka**: Solar return, Muntha, Harsha Bala, Patyayini/Mudda Dasa
- **Tithi Pravesha**: Annual tithi return charts (solar-tithi matching, sub-0.6° accuracy)
- **Matchmaking**: 10 Porutham (19pt) + Ashta Koota (36pt)
- **Prasna**: 108/249/Nadi horary modes
- **Muhurta**: 11 task types, inauspicious periods, Abhijit, day scanning

### Deployed — Interpretive / AI
- **Interpreter**: Rule-based chart reading with planet-by-planet analysis
- **Knowledge base**: 16 textbooks/articles (1.96M chars), FTS5 full-text search
- **AI Engine**: OpenAI-compatible client for Ollama/LM Studio/Unsloth
- **RAG Pipeline**: Chart data + computed analysis + textbook citations → LLM prompt
- **AI Teacher**: Interactive Guru — teaches Vedic astrology using textbook embeddings
- **Context Budgeting**: Auto-truncation for local model limits (2K-8K tokens)
- **7 AI Topics**: general, relationship, career, health, spirituality, children, finance
- **Mundane AI**: Medini Jyotisha topic with national house meanings

### Deployed — Mundane Astrology
- **Solar Ingresses**: All 12 Sankrantis via `swe.solcross_ut()`
- **Eclipses**: Upcoming solar/lunar eclipse detection
- **Major Conjunctions**: Jupiter-Saturn, Mars-Saturn, etc.
- **Mundane Houses**: 12 houses mapped to national meanings (H6=military, H7=war/peace)

### Deployed — Infrastructure
- **Unified DB**: `data/jhora.db` (SQLite) — atlas, knowledge base, charts, preferences
- **Atlas**: 34,006 cities from GeoNames (CC BY 4.0), FTS5 search
- **Chart storage**: Save/load/list/delete charts in SQLite
- **Chart browser**: GUI dialog (Ctrl+B) for browsing saved charts
- **JHD parser**: Import/export original `.jhd` format
- **City lookup**: Real-time search with 300ms debounce, SQLite fallback
- **Preferences**: Key-value store (ready to use, not yet wired to GUI widgets)

### Deployed — Interfaces

| Interface | Count | Coverage |
|-----------|-------|----------|
| **GUI tabs** | 17 | All modules except ephemeris viewer |
| **TUI panels** | 16 | All single-chart modules (keyboard-navigable) |
| **CLI commands** | 18 | Every module has a command |

## Remaining (Tier 2 → Tier 3)

| Feature | Effort | Priority |
|---------|--------|----------|
| PDF/HTML/SVG export | Large | High — makes app shareable |
| Tithi Pravesha charts | Medium | Medium — completes predictive system |
| Dasa timeline (interactive) | Large | Medium — visualization |
| Ephemeris viewer | Small | Low — daily planet table |
| Progressions | Medium | Low |

## Files

| File | Size | Description |
|------|------|-------------|
| `jhora.exe` | 2.3 MB | Original binary (reference only, not distributed) |
| `data/jhora.db` | 6.8 MB | Unified DB (atlas + knowledge + charts + prefs) |
| `data/*.jhd` | 41-169 B | 18 sample chart files |
| `jhcore/ephe/*.se1` | ~94 MB | Swiss Ephemeris data (not in git) |

## Reference
- Original JHora: `vedicastrologer.org/jh`
- Textbook: "Vedic Astrology: An Integrated Approach"
- Full help: `docs/help/` (56 topics)
- Function map: `docs/function_map.md`
- SWE xrefs: `docs/swe_xrefs.md`
