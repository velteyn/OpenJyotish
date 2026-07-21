# OpenJyotish — Free Vedic Astrology Toolkit

Free, open-source, cross-platform Vedic astrology software.  
**CLI** + **GUI** (PyQt6) + **TUI** (terminal). AI-powered readings via local LLMs.

```
27 CLI commands  |  8 GUI categories + sub-tabs  |  9 TUI menus + sub-menus
16-section JSON API for AI agents  |  684 tests  |  AGPL v3.0
```

## Quick Install

### Option 1: Release (Windows — no Python needed)
Download the latest `openjyotish-v*-windows.zip` from [Releases](https://github.com/velteyn/OpenJyotish/releases).  
Extract, double-click `OpenJyotish.bat`. Includes ephemeris data.

### Option 2: From source (Linux / Mac / Windows with Python)

```bash
# Linux / Mac
git clone https://github.com/velteyn/OpenJyotish.git
cd OpenJyotish
./install.sh
./run.sh

# Windows
git clone https://github.com/velteyn/OpenJyotish.git
cd OpenJyotish
install.bat
run.bat
```

**Requires**: Python 3.11+

Ephemeris data is auto-downloaded by `install.sh` / `install.bat` (2 files, ~1MB).

## One-Minute Examples

```bash
# Get your chart
jhora chart "1973-03-14 14:55 +0100 45.41 11.88"

# Everything at a glance (AI-friendly JSON)
jhora analyze "1973-03-14 14:55 +0100 45.41 11.88"

# Current dasa period
jhora dasa-timeline "1973-03-14 14:55 +0100 45.41 11.88"

# Strengths
jhora shadbala --bhava --vimsopaka "birthdata"

# Prediction (Tithi Pravesha)
jhora tithi-pravesha "birthdata"

# Matchmaking
jhora kuta "girl_birthdata" "boy_birthdata"

# AI interpretation (needs Ollama)
# Full guide: https://github.com/velteyn/OpenJyotish/wiki/AI-Complete-Guide
jhora ai "birthdata"
jhora teach "How do I read my 7th house?" --chart "birthdata"

# Launch desktop app
./run.sh
```

## Birth Data Format

All commands accept birth data as: `"YYYY-MM-DD HH:MM TZ LAT LON"`

```
"1973-03-14 14:55 +0100 45.41 11.88"
  │         │     │     │      └─ Longitude (E positive)
  │         │     │     └─ Latitude (N positive)  
  │         │     └─ Timezone (+0100 = UTC+1, +0530 = India, -0500 = EST)
  │         └─ Local time (24h)
  └─ Date
```

## GUI

`jhora gui` or `./run.sh` — 8 main categories with sub-tabs:

| Category | Contains |
|----------|----------|
| **Dashboard** | Current dasa, transits, strengths, upcoming |
| **Chart & Varga** | Chart View, Planets, Houses & Chalit, Varga Charts, Yogas |
| **Strengths** | Shadbala, Arudha & Karaka, Ashtakavarga |
| **Dasas** | Dasa Periods with interactive bar chart |
| **Transits & Tajaka** | Transits, Tajaka & TP, Mundane |
| **Special** | Matchmaking, Prasna, Muhurta |
| **AI & Learn** | AI Chat, AI Teacher, Knowledge, Reading |
| **Tools** | Ephemeris |

**Getting started**: Fill form → "Find" city → "Now" button → "Calculate"

## TUI

`jhora tui` — interactive terminal app with the same 9-category structure.  
Arrow keys ↑↓ to navigate, letters to jump, Enter to select, `b` to go back, `q` to quit.

```
Main Menu:
  1  Birth Data Input          d  Dashboard
  c  Chart & Varga             s  Strengths
  a  Dasas & Timing            t  Transits & Tajaka
  x  Special                   i  AI & Knowledge
  u  Tools                     q  Quit
```

## AI Tool-Calling (JSON API)

One command, everything computed. Pipe to AI agents, `jq`, or Python:

```bash
jhora analyze "birthdata"
# → 10KB JSON — 16 sections, every calculation

# Pipe it around
jhora analyze "..." | jq '.planets.Su.house'
jhora analyze "..." | jq '.dasa.mahadashas[] | select(.current)'
```

```python
import json, subprocess
data = json.loads(subprocess.run(
    ["jhora", "analyze", birthdata], capture_output=True, text=True
).stdout)
```

## All CLI Commands (27)

| Command | What it does |
|---------|-------------|
| `chart` | Rasi chart + planets + upagrahas + outer planets |
| `analyze` | AI-friendly JSON dump (16 sections) |
| `shadbala` | Six-fold planetary strength (+ --bhava + --vimsopaka) |
| `yogas` | Detect 200+ planetary combinations |
| `ashtakavarga` | BAV, SAV, Sodhya Pinda, Kakshya bindu |
| `dasa` | Vimsottari dasa periods (MD/AD) |
| `dasa-timeline` | Text bar chart with now-marker |
| `conditional-dasas` | List additional dasa systems that apply |
| `transit` | Current transits with SAV scores |
| `tajaka` | Solar return chart |
| `tithi-pravesha` | Annual solar-tithi ingress |
| `progression` | Secondary progressions (1 day = 1 year) |
| `kuta` | Marriage compatibility (Porutham + Ashta Koota) |
| `prasna` | Horary (108/249/Nadi modes) |
| `muhurta` | Electional — 11 task types |
| `mundane` | World events, eclipses, ingresses |
| `compare` | Natal vs transit or two-chart comparison |
| `interpret` | Rule-based chart reading |
| `knowledge` | Search 16 Vedic textbooks (FTS5) |
| `ai` | LLM chart reading (Ollama/LM Studio/Unsloth) |
| `teach` | AI Teacher — learn Vedic astrology |
| `export` | HTML report (printable to PDF) |
| `ephemeris` | Daily planet table |
| `varga` | Any divisional chart (D-1 to D-150) |
| `navamsa` | D-9 Navamsa |
| `panchanga` | Monthly calendar (tithi/nakshatra/rahu kalam) |
| `chakras` | Sarvatobhadra + Kota chakras |
| `lagnas` | All special lagnas with meanings |
| `learning` | Marana karaka, KP sub-lords, vaiseshikamsas |
| `tui` | Launch interactive terminal UI |
| `gui` | Launch desktop GUI |

## Features

### Calculation Engine
Rasi chart (D-1) with South/North/East styles · 23 varga charts (D-2 to D-150) ·
7 dasa systems · 5 conditional dasas · Shadbala · Bhava Bala · Vimsopaka Bala (4 schemes) ·
200+ yogas · Ashtakavarga (BAV/SAV/Kakshya) · Arudha Padas · Chara Karakas ·
36 Sahamas · 20 ayanamsa modes (Lahiri/Raman/KP/Fagan/Tropical/etc.) ·
Outer planets (Uranus/Neptune/Pluto) · Upagrahas (5 solar + Gulika/Mandi) ·
Special lagnas (Bhrigu Bindu/Indu/Varnada/Pranapada/Vighati) ·
KP sub-lords (5 levels) · Chalit/Bhava charts

### Forecasting
Transits with SAV scores · Tajaka solar return · Tithi Pravesha ·
Progressions · Dasa timeline · Mundane (ingresses/eclipses/conjunctions) ·
Matchmaking (10 Porutham + Ashta Koota 36pt) · Muhurta · Prasna

### AI & Data
Local LLM (Ollama/LM Studio/Unsloth) · RAG pipeline with textbook citations ·
AI Teacher mode · 8 AI topic templates · Context budgeting for small models ·
Unified SQLite DB (atlas 34K cities + knowledge + charts) · HTML export ·
JHD import/export · Chart browser · JSON API for AI agents

## Architecture

```
src/jhora/
├── types/          Enums: Graha, Rasi, Nakshatra, Varga, Bhava, Dasa
├── ephemeris/      Swiss Ephemeris wrapper (18 API functions)
├── charts/         ChartBuilder, ChartData (frozen), VargaChartComputer
├── calc/           18 modules: strengths, yogas, dasas, transits, chakras...
├── dasas/          12 dasa systems
├── ai/             AI engine, RAG pipeline, JSON export, teacher
├── interpreter/    Chart reading, knowledge base
├── export/         HTML report generator
├── io/             Atlas (SQLite/FTS5), JHD parser
├── core/           Unified database
├── cli/            Typer CLI (27 commands)
├── tui/            prompt_toolkit menu system
└── ui/             PyQt6 GUI (8-category tabs, chart widget, dasa timeline)
```

### 💬 Community & Support
If you want to discuss the project, ask questions, or share your own astrology software tools, join our official community on Reddit: [r/AstrologySoftware](https://www.reddit.com/r/AstrologySoftware/).

## Credits

Based on **OpenJyotish 8.0 Lite** by PVR Narasimha Rao (Sri Jagannath Vedic Centre).  
Atlas data: GeoNames.org (CC BY 4.0).  

## License

**GNU GENERAL PUBLIC LICENSE v3.0** — free forever.  
Modifications must remain open. Network use counts as distribution.
