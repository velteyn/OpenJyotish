# Jagannatha Hora — Reborn: Project Plan

**Goal:** Build the most user-friendly, feature-complete, cross-platform Vedic astrology tool — free, open-source, AI-powered. Useful for both casual users and professional astrologers.

**Origin:** Reverse engineer JHora 8.0 Lite (PVR Narasimha Rao, 2015). All calculations verified against the original.

**Status:** Core engine ~92% complete (13,000+ lines, 646 tests). Tier 1 + Tier 2 COMPLETE.

---

## 1. North Star

> "A Vedic astrology tool so good that professionals switch from $300 Windows-only software, and casual users can get a meaningful chart reading in one click."

### What Makes Us Different

| Feature | JHora (original) | Parashara's Light ($299) | Kala ($255) | **Ours** |
|---------|:---:|:---:|:---:|:---:|
| **Price** | Free | $299-$450 | $255 | **Free** |
| **Cross-platform** | Windows only | Win/Mac | Windows only | **Linux/Mac/Win** |
| **Source** | Closed | Closed | Closed | **Open** |
| **AI interpretation** | ✗ | ✗ | ✗ | **✓ (Ollama/LM Studio/Unsloth)** |
| **Mundane astrology** | ✓ | ✗ | ✗ | **✓ (solar ingress, eclipses)** |
| **TUI** | ✗ | ✗ | ✗ | **✓ (16 panels)** |
| **Modern UI** | ✗ (MFC) | ✗ (dated) | ✗ (dated) | **✓ (PyQt6 dark)** |
| **Vector charts** | ✗ (bitmap) | Limited | Limited | **✓ (Canvas)** |
| **Scriptable** | ✗ | ✗ | ✗ | **✓ (Python API)** |
| **Knowledge base** | Help file | ✗ | ✗ | **✓ (full textbook search)** |

---

## 2. Feature Target — Professional Parity

### Tier 1: Core Calculations (Must Have)

- [x] Rasi chart (D-1) with 9 planets + lagna
- [x] Vimsottari dasa with sub-periods
- [x] **Varga charts D-2 through D-60** — 23 levels, all variants implemented (305 lines)
- [x] **Shadbala** (6-source planetary strength) — all 6 components (491 lines, 48 tests)
- [x] **Yogas detection** — 10+ types, 12 categories, 100+ combos (488 lines)
- [x] **Ashtottari dasa** (108-year system) — MD/AD periods, applicability conditions (142 lines)
- [x] **House cusps** — via SweEngine (12+ house systems supported by Swiss Ephemeris)
- [x] Ashtakavarga (8-bindu system)
- [x] 5 more dasa systems (Narayana, Kalachakra, Yogini, Chara, Sudasa)
- [x] 36 sahamas (sensitive points)
- [x] Arudha padas (AL, A2-A12, UL)
- [x] Chara karakas (Jaimini)
- [x] Tajaka (solar return with compressed dasas)

### Tier 2: Advanced Analysis (Professional Differentiator)

- [x] Ashtakavarga: SAV, BAV, SoAV, PAV, Sodhya Pinda, Kakshya
- [x] Bhava bala (house strength)
- [x] Vimsopaka bala (Shadvarga through Shodasa)
- [ ] Digbala, Kalabala, Cheshtabala details
- [x] Bhava/chalit chakra: cusp vs whole-sign for all Vargas
- [x] Transit analysis with vedha, tara, gochara
- [x] Matchmaking: Kuta matching — 10 Porutham (19-pt) + Ashta Koota (36-pt, original JHora binary scoring)
- [x] Prasna (horary): 108/249/1800 modes
- [x] Muhurta (electional) with planetary hour analysis
- [x] Tithi Pravesha charts (annual/monthly/daily)
- [x] Progressions (secondary: 1 day=1 year, solar arc, natal aspects)

### Tier 3: AI & UX (Our Moat)

- [x] **Knowledge base** — full-text search of textbook + 14 research articles (1.9M chars, 16 sources)
- [x] **Rule-based interpreter** — chart reading generator connected to yogas engine
- [x] **Local LLM interpretation** (Ollama/LM Studio/Unsloth) — chart → plain English reading
- [x] **Interactive Q&A** — ask specific questions about the chart
- [x] **AI remedy suggestions** — gemstones, mantras, rituals from classical texts
- [ ] **Export to PDF/HTML/SVG** — beautiful client-ready reports
- [x] **Chart database** — SQLite storage + browser dialog (save/list/load/delete)
- [ ] **Ephemeris viewer** — daily planet positions for any date range
- [ ] **Multi-chart comparison** — natal vs transit, synastry overlay
- [x] **Dasa timeline** — interactive colored bar chart with click-to-expand antardasas
- [x] **World atlas** — 34K+ cities with timezone auto-resolution (GeoNames FTS5)
- [x] **AI Teacher** — interactive Vedic astrology instructor powered by textbook embeddings

---

## 3. Architecture

### Actual Directory Structure (what's implemented)

```
src/jhora/
├── __init__.py              # Version, public API exports
├── __main__.py              # `python -m jhora` entry point
│
├── types/                   # 6 types, 546 total lines
│   ├── graha.py             # Planet enum (9 grahas + properties)
│   ├── rasi.py              # Sign enum (12 rasis + lords, elements, etc.)
│   ├── nakshatra.py         # 27 nakshatras, padas, lords, from_longitude()
│   ├── bhava.py             # House enum (1-12 + kendra/trikona/duhsthana queries)
│   ├── varga.py             # VargaLevel (D-1..D-150) + VargaVariant enum
│   └── dasa.py              # DasaSystem, PeriodLevel, DasaPeriod
│
├── calc/                    # 4 modules, 1,131 total lines
│   ├── angles.py            # Longitude arithmetic (diff, add, aspect, midpoint)
│   ├── dignities.py         # DignityChecker (exalted/debilitated/moolatrikona/own/neutral)
│   ├── shadbala.py          # ShadbalaComputer (sthana, dig, kala, chesta, naisargika, drik)
│   └── yogas.py             # detect_all() + helpers (10+ yoga types, 100+ combos)
│
├── ephemeris/               # 1 module, 200 lines
│   └── swe.py               # SweEngine — wraps 18 Swiss Ephemeris API calls
│
├── charts/                  # 2 modules, 486 lines
│   ├── chart.py             # ChartBuilder, ChartData (frozen), PlanetChartData
│   └── varga.py             # VargaChartComputer — all D-1..D-150 with 30+ variant mappings
│
├── dasas/                   # 3 modules, 398 lines
│   ├── base.py              # DasaBase, DasaOptions — abstract engine with period tree builder
│   ├── vimsottari.py        # VimsottariDasa (120-year, 9 planets, MD/AD)
│   └── ashtottari.py        # AshtottariDasa (108-year, 8 planets, applicability conditions)
│
├── interpreter/             # 3 modules, 335 lines
│   ├── engine.py            # ChartInterpreter — rule-based reading generator
│   ├── knowledge_base.py    # KnowledgeBase — full-text search across 16 sources
│   └── texts.py             # Reference texts (planet/house/rasi/nakshatra meanings)
│
├── cli/                     # 1 module, 491 lines
│   └── main.py              # 9 Typer commands: chart, dasa, navamsa, varga, shadbala,
│                            #   yogas, interpret, knowledge, gui
│
├── ui/                      # 2 modules, 800 lines
│   ├── main_window.py       # MainWindow — dark theme PyQt6 app with tabs
│   └── chart_widget.py      # ChartWidget — South/North/East Indian chart rendering
│
└── (19 empty stub directories for future modules)
```

### Actual vs Aspirational

The `docs/python_architecture.md` describes the **target** architecture with 50+ modules. Currently **10 out of 32 directories** contain code (32 `.py` files, 4,442 lines). 19 directories are empty stubs for future development.

### Key Design Principles

1. **Core is deterministic, pure Python** — no AI in the calculation path
2. **AI only for interpretation** — LLM reads `ChartData`, never touches numbers
3. **Everything cached** — memoized per `ChartData`
4. **Pluggable dasas** — one abstract base, 25+ implementations, registry-based
5. **Immutable ChartData** — thread-safe, cacheable, serializable to JSON

---

## 4. AI Integration Architecture (Target)

```
User birth data → Core Engine → ChartData (pure numbers)
  ├── Rule-based interpreter (planet dignities, house lords, yogas) ✓ done
  ├── LLM Interpreter (Ollama / LM Studio / OpenAI API) — planned
  │     ├── ChartData formatted as structured text
  │     ├── Knowledge base excerpts (semantic search) ✓ done
  │     ├── System prompt: "You are PVR Narasimha Rao..."
  │     └── Output: natural language chart reading
  ├── Interactive Chat (context = chart + knowledge) — planned
  └── Remedy Engine (text-based, from classical sources) — planned
```

**Supported LLM backends (planned):** Ollama, LM Studio, OpenAI API / OpenRouter. Configurable model, temperature, system prompt.

---

## 5. UI Design Philosophy

**Casual Users:** "Enter birth data → get reading" in 2 clicks, beautiful dark theme, plain English with AI, interactive learning.

**Professionals:** ALL the numbers (shadbala virupas, varga charts, dasa periods), PDF reports, chart database, customizable styles.

**Chart Styles:**
- South Indian — fixed rasi grid (4×4) ✓ implemented
- North Indian — bhava diamond with house numbers ✓ implemented
- East Indian — circular Sun chart ✓ implemented
- D-9 Navamsa overlay on D-1 ✓ implemented (toggle)
- Multi-wheel — natal + transit + dasa lord — planned

---

## 6. Roadmap (Phased)

### Phase 1: Core Engine (Weeks 1-6) ← we are here

| Area | Status | Remaining |
|------|--------|-----------|
| Vargas (D-1..D-150) | ✅ 23 levels, all variants | — |
| Dasas | ✅ Vimsottari + Ashtottari + Yogini + Sudasa + Chara + Narayana + Kalachakra | ~20 more systems |
| Strengths | ✅ Shadbala + Ashtakavarga | Vimsopaka, Bhava bala |
| Yogas | ✅ 10+ types, 100+ combos | Nabhasa, finer sub-types |
| CLI commands | ✅ chart, dasa, navamsa, varga, shadbala, yogas, interpret, knowledge, gui, tajaka | strengths, match, prasna, config, atlas |
| GUI tabs | ✅ planets, houses, dasa, varga, yogas, shadbala, ashtakavarga, transit, arudha, tajaka, matchmaking | client DB |

### Phase 2: Professional Features (Weeks 7-12)

| Area | Deliverables |
|------|-------------|
| Dasa engine | Narayana, Kalachakra, Yogini, Chara, Sudasa + 18 more |
| Strengths | Ashtakavarga (SAV/BAV/SoAV/PAV), Vimsopaka, Bhava bala |
| Specialized | Tithi Pravesha |
| CLI | matchmaking, prasna, muhurta, config commands |
| GUI | Dasas tab → system selector + AD/PD drilldown, Ashtakavarga tab |

### Phase 3: AI Layer (Weeks 13-14)

| Area | Deliverables |
|------|-------------|
| Knowledge base | Semantic search (vector embeddings) |
| LLM interpreter | Chart → natural language via Ollama/LM Studio |
| Chat | Interactive Q&A session with chart context |

### Phase 4: GUI Polish & Release (Weeks 15-18)

| Area | Deliverables |
|------|-------------|
| Chart rendering | Multi-wheel views, PDF/HTML export |
| Client database | SQLite add/edit/search, batch operations |
| Packaging | PyPI package, AppImage/Flatpak/Windows installer |
| Documentation | User guide, API reference, example gallery |

---

## 7. Competitive Comparison

| Feature | JHora Orig | PL ($299) | Kala ($255) | SJS ($300+) | **Ours** |
|---------|:---:|:---:|:---:|:---:|:---:|
| Rasi chart | ✓ | ✓ | ✓ | ✓ | ✓ |
| 20+ Vargas | ✓ | ✓ | ✓ | ✓ | ✓ |
| Vimsottari dasa | ✓ | ✓ | ✓ | ✓ | ✓ |
| 25+ dasa systems | ✓ | ✓ | ✓ | ✓ | ~2 built |
| Shadbala | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ashtakavarga | ✓ | ✓ | ✓ | ✓ | — |
| Yogas | ✓ | ✓ | ✓ | ✓ | ✓ |
| Sahamas | ✓ | ✓ | ✓ | ✓ | — |
| Arudha padas | ✓ | ✓ | ✓ | ✓ | — |
| Chara karakas | ✓ | ✓ | ✓ | ✓ | — |
| Tajaka (solar return) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Transits + Gochara | ✓ | ✓ | ✓ | ✓ | ✓ |
| Matchmaking | ✓ | ✓ | ✓ | ✓ | ✓ |
| Prasna (horary) | ✓ | ✓ | ✓ | ✓ | — |
| Muhurta (electional) | ✓ | ✓ | ✓ | ✓ | — |
| Panchanga | ✓ | ✓ | ✓ | ✓ | — |
| World Atlas | ✓ | ✓ | ✓ | ✓ | — |
| **Free** | ✓ | ✗ | ✗ | ✗ | **✓** |
| **Open source** | ✗ | ✗ | ✗ | ✗ | **✓** |
| **Cross-platform** | ✗ | ✓ | ✗ | ✗ | **✓** |
| **AI Q&A** | ✗ | ✗ | ✗ | ✗ | **Planned** |
| **Vector charts** | ✗ | ✗ | ✗ | ✗ | **✓** |
| **Python API** | ✗ | ✗ | ✗ | ✗ | **✓** |
| **Knowledge base search** | Help only | ✗ | ✗ | ✗ | **✓** |
| **Dark theme UI** | ✗ | ✗ | ✗ | ✗ | **✓** |

---

## 8. Current Implementation Status

**DONE (72% of core engine):**
- Core types (Graha, Rasi, Nakshatra, Varga, Bhava, Dasa) — 6 types, 546 lines
- SweEngine — all 18 Swiss Ephemeris API calls, sidereal mode, retrograde detection
- ChartBuilder + ChartData (frozen dataclass) with planet dignity
- VargaChartComputer — 23 levels (D-1..D-150), 30+ variant mappings
- 7 dasa systems: Vimsottari, Ashtottari, Yogini, Sudasa, Chara, Narayana, Kalachakra
- Shadbala (all 6 components: sthana, dig, kala, chesta, naisargika, drik) — 491 lines, 48 tests
- Ashtakavarga (BAV, SAV, PAV, Sodhya Pinda, Kakshya)
- Yogas engine (10+ types: Raja, Dhana, Mahapurusha, Viparita Raja, etc.)
- CLI (10 commands: chart, dasa, navamsa, varga, shadbala, yogas, interpret, knowledge, gui, tajaka)
- GUI (PyQt6 dark theme, 3 chart styles, 10 tabs)
- Arudha padas (Bhava + Graha)
- Chara karakas (Jaimini, 8 karakas)
- Sahamas (36 sensitive points)
- Tajaka (solar return, Muntha, Harsha Bala, Patyayini Dasa, Mudda Dasa)
- Kuta Porutham (matchmaking): 10 Porutham, 19-point scoring, CLI `jhora kuta`, GUI tab 11
- Transit analysis (Gochara with BAV/SAV scores)
- Rule-based chart interpreter (connected to yogas engine)
- Knowledge base (16 sources, 1.9M chars, full-text search)
- Reference texts (planet/house/rasi/nakshatra meanings)
- **490 tests** across 20 test files (3,200+ lines of tests)

**NEXT:**
- AI chat integration (Ollama)

---

## 9. References

- Original JHora 8.0: `vedicastrologer.org/jh`
- Textbook: "Vedic Astrology: An Integrated Approach" by PVR Narasimha Rao
- Swiss Ephemeris: `swisseph.com`
- pyswisseph: `pypi.org/project/pyswisseph`
- Parashara's Light: `parasharaslight.com`
- Kala: `vedic-astrology.net`
- Shri Jyoti Star: `vedicsoftware.com`
