# Jagannatha Hora — Vedic Astrology Software

Free, open-source, cross-platform Vedic astrology toolkit. CLI + PyQt6 GUI + Terminal UI. AI-powered chart readings via local LLMs.

```
📊 18 GUI tabs   |   🖥 24 CLI commands   |   ⌨ 16 TUI panels
🔮 35 features   |   📝 13,967 lines Python   |   ✅ 646 tests
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
jhora ai "..."                     # Full chart reading via local LLM
jhora ai --topic career "..."      # Career-focused reading
jhora ai --mode remedies "..."     # Gemstone/mantra suggestions

# CLI — export + utilities
jhora export "..." -o report.html  # Styled HTML report
jhora ephemeris 2026-07-01         # Daily planet table
jhora tui "..."                    # Interactive terminal UI
```

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
