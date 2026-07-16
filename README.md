# Jagannatha Hora — Vedic Astrology Software

Free, open-source, cross-platform Vedic astrology toolkit. CLI + PyQt6 GUI + Terminal UI. AI-powered chart readings via local LLMs.

```
📊 19 GUI tabs   |   🖥 25 CLI commands   |   ⌨ 24 TUI menu items
🔮 36 features   |   📝 14,500 lines Python   |   ✅ 646 tests
```

## Quick Start

```bash
# Install
pip install -e .

# GUI
jhora gui                          # Launch desktop app

# CLI — chart reading
jhora chart "1973-03-13 13:55 +0100 45.41 11.88"
jhora chart --chalit "..."         # Show cusp-based (bhava) positions

# CLI — strengths
jhora shadbala "..."               # Six-fold planetary strength
jhora shadbala --bhava "..."       # House strength
jhora shadbala --vimsopaka "..."   # Varga-weighted strength

# CLI — forecasting
jhora dasa "..."                   # Vimsottari dasa periods
jhora dasa-timeline "..."          # Bar chart visualization
jhora progression "..."            # Secondary progressions
jhora tithi-pravesha "..."         # Annual tithi-solar return
jhora transit "..."                # Current transits vs natal
jhora compare "..." transit        # Natal vs transit side-by-side

# CLI — special topics
jhora mundane 2026                 # World events, eclipses, ingresses
jhora prasna 108                   # Horary — 108, 249, or Nadi
jhora muhurta "..." --task marriage  # Electional (auspicious timing)
jhora kuta "girl" "boy"            # Matchmaking compatibility
jhora knowledge "query"            # Search 16 Vedic textbooks

# CLI — AI interpretation (requires Ollama/LM Studio)
jhora teach "question"                # AI teacher — learn Vedic astrology
jhora teach "question" --chart "..."     # Learn with your chart
jhora ai "..."                     # Full chart reading via local LLM
jhora ai --topic career "..."      # Career-focused reading
jhora ai --mode remedies "..."     # Gemstone/mantra suggestions

# CLI — export + utilities
jhora export "..." -o report.html  # Styled HTML report
jhora ephemeris 2026-07-01         # Daily planet table
jhora tui "..."                    # Interactive terminal UI
```

## GUI Manual

Launch with `jhora gui`. The desktop app has 19 tabs:

```
┌─ File ─┬─ Left Panel ────┬─ Right Panel (Tabs) ─────────────────────────┐
│ Import │ Planets          │ Planets  Houses  Dasa  Varga  Yogas         │
│ Export │ Houses + Chalit  │ Shadbala  Arudha  Ashtakavarga  Transit     │
│ Browse │ Dasa Periods     │ Tajaka  Matchmaking  Prasna  Muhurta        │
│ Report │                  │ Knowledge  Reading  AI Chat  AI Teacher     │
│ Exit   │                  │ Mundane  Ephemeris                          │
└────────┴──────────────────┴─────────────────────────────────────────────┘
```

### Getting started
1. Fill the form: Date, Time, Latitude, Longitude, Timezone
2. Click **Search** to find a city by name (fills lat/lon/tz automatically)
3. Click **Now** to use current date/time with auto-detected timezone
4. Click **Calculate** or press Enter

### Tab guide

| Tab | What it shows | How to use |
|-----|--------------|------------|
| **Planets** | 9 planets + lagna positions, nakshatras, dignity | Read at a glance |
| **Houses** | 12 house cusps + Chalit shifts (cusp vs sign) | Check which planets moved houses |
| **Dasa** | Select system → full MD/AD text + interactive bar chart | Click bars to expand antardasas |
| **Varga** | Select divisional chart → planet positions + navamsa toggle | Dropdown for D-1 through D-150 |
| **Yogas** | All detected yogas with planets and descriptions | Scroll to review combinations |
| **Shadbala** | Planet strengths + House strengths + Vimsopaka Bala | Three tables stacked |
| **Arudha & Karaka** | Arudha padas + Chara karakas + 36 Sahamas | Tabular view |
| **Ashtakavarga** | BAV, SAV, Sodhya Pinda, Kakshya detail | Toggle Parasara/Varahamihira |
| **Transit** | Current transits with SAV scores + filtered by planet | Dropdown to select planet |
| **Tajaka** | Solar return + Muntha + Harsha + Patyayini + Mudda + Tithi Pravesha + Progressions | Enter target year |
| **Matchmaking** | 10 Porutham + Ashta Koota scores for two charts | Fill both charts, click Match |
| **Prasna** | Horary chart from number | Enter 1-108, 1-249, or 1-1800 |
| **Muhurta** | Task evaluation + Find Auspicious Times | Select task, set date/time/location |
| **Knowledge** | FTS5 search across 16 textbooks | Type query, set result count |
| **Reading** | Rule-based chart interpretation | Click Generate Reading |
| **AI Chat** | LLM-powered interpretation (needs Ollama/LM Studio) | Select provider, click Interpret/Ask/Remedies |
| **AI Teacher** | Interactive Vedic astrology instructor | Ask questions, auto-searches textbooks |
| **Mundane** | Solar ingresses + eclipses + conjunctions | Set year/lat/lon, click Compute |
| **Ephemeris** | Daily planet table for any date range | Set start/end/step, click Generate |

### Keyboard shortcuts
- `Ctrl+O` — Import .jhd file
- `Ctrl+S` — Save chart to database
- `Ctrl+Shift+S` — Export .jhd file
- `Ctrl+B` — Browse saved charts (load/delete)
- `Ctrl+Q` — Exit

### File menu
- **Import .jhd** — Load original JHora format charts
- **Save to Database** — Stores chart in SQLite for later browsing
- **Export .jhd** — Save in original JHora format
- **Browse Charts** — Dialog listing all saved charts (double-click to load)
- **Export Report (HTML)** — Save styled HTML report (printable to PDF)

## TUI Manual

Launch with `jhora tui` (fully interactive, no birth data needed upfront)
or `jhora tui "1973-03-13 13:55 +0100 45.41 11.88"` (pre-load a chart).

Built on **prompt_toolkit** with **Rich** rendering. Navigate with arrow keys
or press the letter key to jump directly. Enter selects, q quits.

### Main Menu (24 items)

```
 1  Birth Data Input      → sequential dialogs for date/time/lat/lon/tz
 2  Planets + Upagrahas   → full position table + shadow planets + special lagnas
 3  Houses + Chalit       → 12 cusps with chalit shifts highlighted
 4  Yogas                 → all detected planetary combinations
 5  Shadbala              → six-fold planetary strength table
 6  Bhava Bala            → five-factor house strength table
 7  Vimsopaka Bala        → varga-weighted strength (Shadvarga + Shodasavarga)
 8  Dasa Periods          → Vimsottari MD/AD with current period marked
 9  Dasa Timeline         → text bar chart with ● now indicator
 a  Transits              → current transits vs natal with SAV scores
 b  Tajaka               → solar return chart for any target year
 c  Varga Charts          → 8-level grid (D-1 through D-60)
 d  Matchmaking           → enter second chart for Kuta Porutham score
 e  Prasna               → horary by number (108/249/Nadi modes)
 f  Muhurta              → electional — task scores for today
 g  Mundane              → world events, eclipses, ingresses
 h  Learning Aids         → KP sub-lords, Marana Karaka, Ishta/Kashta
 i  Chart Reading         → rule-based interpretation
 j  Ashtakavarga          → SAV table
 k  Knowledge Search      → FTS5 search across 16 textbooks
 l  Export HTML           → styled report to file
 m  Save to Database      → store chart in SQLite
 n  Birth Data (Re-enter) → change chart without restarting
```

### Navigation

| Key | Action |
|-----|--------|
| `↑` `↓` | Move selection up/down |
| Letter (`1`-`n`) | Jump directly to item |
| `Enter` | Select / execute |
| `q` or `Ctrl+C` | Back to menu (from action) or quit (from main menu) |

### Workflow

```
jhora tui
  → press 1 → enter birth data → chart computed
  → press 2 → view planets
  → press 5 → view Shadbala
  → press 8 → view dasa periods
  → press d → enter partner chart → matchmaking score
  → press l → export HTML report
  → press q → quit
```

All output rendered with Rich tables/panels. Dialogs use prompt_toolkit for clean
text input with validation.

## Prerequisites

- Python 3.11+
- Swiss Ephemeris data files (`.se1` files) in `jhcore/ephe/` — these are the original JHora ephemeris files (not distributed in git)

```bash
# If you have the original JHora installation, copy the ephemeris files:
cp -r /path/to/jhora/jhcore/ephe/ jhcore/ephe/

# Or download from: https://www.astro.com/ftp/swisseph/ephe/
```

## Features

### Calculation Engine
- **Rasi chart** (D-1) with South/North/East Indian chart styles
- **23 varga charts** — D-2 through D-150 with 30+ variant mappings
- **7 dasa systems** — Vimsottari, Ashtottari, Yogini, Sudasa, Chara, Narayana, Kalachakra
- **Shadbala** — six-fold planetary strength (sthana/dig/kala/chesta/naisargika/drik)
- **Bhava Bala** — five-factor house strength
- **Vimsopaka Bala** — four schemes (Shadvarga through Shodasavarga)
- **Yogas** — 200+ planetary combinations detected
- **Ashtakavarga** — BAV, SAV, PAV, Trikona Shodhana, Kakshya bindu
- **Arudha Padas** — bhava and graha arudhas
- **Chara Karakas** — 8 Jaimini significators
- **36 Sahamas** — sensitive points

### Forecasting & Special Topics
- **Transits** — current transits with Ashtakavarga scores
- **Tajaka** — solar return with Muntha, Harsha Bala, Patyayini/Mudda Dasa
- **Tithi Pravesha** — annual tithi-solar return charts
- **Progressions** — secondary (1 day = 1 year) + solar arc
- **Chalit/Bhava** — cusp-based house positions vs whole-sign
- **Dasa timeline** — interactive bar chart with click-to-expand
- **Matchmaking** — 10 Porutham + Ashta Koota (36-point)
- **Muhurta** — 11 electional task types, inauspicious periods
- **Prasna** — 108/249/Nadi horary modes
- **Mundane** — solar ingresses, eclipses, major conjunctions, world events

### AI & Interpretation
- **Local LLM** — Ollama / LM Studio / Unsloth Studio (OpenAI-compatible API)
- **RAG pipeline** — chart data + computed analysis + textbook citations → LLM prompt
- **Context budgeting** — auto-truncates for local model limits
- **8 AI topics** — general, relationship, career, health, spirituality, children, finance, mundane
- **Rule-based interpreter** — planet-by-planet chart reading
- **Knowledge base** — 16 Vedic textbooks (1.96M chars), FTS5 search

### Data
- **Unified SQLite DB** — atlas (34K cities), knowledge base, saved charts, preferences
- **Chart browser** — save/load/delete charts from database
- **JHD import/export** — compatible with original JHora `.jhd` format
- **HTML export** — printable dark-themed chart reports

## CLI Commands (all 24)

| Command | Description |
|---------|-------------|
| `chart` | Rasi chart with planetary positions |
| `dasa` | Dasa periods (Vimsottari default) |
| `dasa-timeline` | Text bar chart visualization |
| `navamsa` | D-9 Navamsa chart |
| `varga` | Any divisional chart (D-1 through D-150) |
| `shadbala` | Six-fold strength (+ bhava + vimsopaka flags) |
| `ashtakavarga` | BAV, SAV, Sodhya Pinda, Kakshya |
| `yogas` | Detect planetary combinations |
| `tajaka` | Solar return chart |
| `tithi-pravesha` | Annual tithi-solar ingress |
| `progression` | Secondary progressions |
| `kuta` | Marriage compatibility |
| `prasna` | Horary astrology |
| `muhurta` | Electional astrology |
| `mundane` | World events, eclipses |
| `transit` | Current transits vs natal |
| `compare` | Two-chart or natal-vs-transit comparison |
| `interpret` | Rule-based reading |
| `knowledge` | Search textbook knowledge base |
| `ai` | LLM-powered reading via local AI |
| `teach` | AI Teacher — learn Vedic astrology |
| `ephemeris` | Daily planet table |
| `export` | HTML report |
| `tui` | Interactive terminal UI |
| `gui` | Desktop GUI |

## Architecture

```
src/jhora/
├── types/          # Graha, Rasi, Nakshatra, Varga, Bhava, Dasa enums
├── ephemeris/      # SweEngine — Swiss Ephemeris wrapper (18 SE APIs)
├── charts/         # ChartBuilder, ChartData (frozen), VargaChartComputer
├── calc/           # 18 calculation modules (strengths, yogas, dasas, etc.)
├── dasas/          # 7 dasa systems
├── interpreter/    # Chart reading, knowledge base
├── ai/             # AI engine (Ollama/LM Studio/Unsloth), RAG pipeline, analysis
├── export/         # HTML report generator
├── io/             # Atlas (SQLite), JHD parser
├── core/           # Unified database manager
├── cli/            # Typer CLI (24 commands)
├── tui/            # Rich interactive terminal UI (16 panels)
└── ui/             # PyQt6 GUI (18 tabs, chart widget, dasa timeline)
```

## Credits

Original software: **PVR Narasimha Rao**, Sri Jagannath Vedic Centre.  
This port is a clean-room reimplementation from the compiled binary and documented behavior.

## License

GNU Affero General Public License v3.0
