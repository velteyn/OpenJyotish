# Jagannatha Hora — Reborn: Project Plan

**Goal:** Build the most user-friendly, feature-complete, cross-platform Vedic astrology tool — free, open-source, AI-powered. Useful for both casual users and professional astrologers.

**Origin:** Reverse engineer JHora 8.0 Lite (PVR Narasimha Rao, 2015). All calculations verified against the original.

---

## 1. North Star

> "A Vedic astrology tool so good that professionals switch from $300 Windows-only software, and casual users can get a meaningful chart reading in one click."

### What Makes Us Different

| Feature | JHora (original) | Parashara's Light ($299) | Kala ($255) | **Ours** |
|---------|:---:|:---:|:---:|:---:|
| **Price** | Free | $299-$450 | $255 | **Free** |
| **Cross-platform** | Windows only | Win/Mac | Windows only | **Linux/Mac/Win** |
| **Source** | Closed | Closed | Closed | **Open** |
| **AI interpretation** | ✗ | ✗ | ✗ | **✓ (local LLM)** |
| **Modern UI** | ✗ (MFC) | ✗ (dated) | ✗ (dated) | **✓ (PyQt6 dark)** |
| **Vector charts** | ✗ (bitmap) | Limited | Limited | **✓ (SVG/Canvas)** |
| **Scriptable** | ✗ | ✗ | ✗ | **✓ (Python API)** |
| **Knowlege base** | Help file | ✗ | ✗ | **✓ (full textbook)** |

---

## 2. Feature Target — Professional Parity

### Tier 1: Core Calculations (Must Have)
_These match what every professional tool provides._

- [x] Rasi chart (D-1) with 9 planets + lagna
- [x] Vimsottari dasa with sub-periods
- [ ] **Varga charts D-2 through D-60** (16+ levels, all variants)
- [ ] Shadbala (6-source planetary strength)
- [ ] Ashtakavarga (8-bindu system)
- [ ] 25+ dasa systems (nakshatra + rasi + graha)
- [ ] 40+ sahamas (sensitive points)
- [ ] Yogas detection (100+ combinations)
- [ ] House cusps (12+ house systems)
- [ ] Arudha padas (AL, A2-A12, UL)
- [ ] Chara karakas (Jaimini)
- [ ] Tajaka (solar return with compressed dasas)

### Tier 2: Advanced Analysis (Professional Differentiator)
_These are what separates a hobbyist tool from a professional one._

- [ ] Ashtakavarga: SAV, BAV, SoAV, PAV, Sodhya Pinda, Kakshya
- [ ] Bhava bala (house strength)
- [ ] Vimsopaka bala (Shadvarga through Shodasa)
- [ ] Digbala, Kalabala, Cheshtabala details
- [ ] Bhava/chalit chakra for 23 varga charts
- [ ] Transit analysis with vedha, tara, gochara
- [ ] Matchmaking: Kuta matching (10+ criteria), Porutham
- [ ] Prasna (horary): 108/249/1800 modes
- [ ] Muhurta (electional) with planetary hour analysis
- [ ] Tithi Pravesha charts (annual/monthly/daily)
- [ ] Progressions (D-n based Sun progression)

### Tier 3: AI & UX (Our Moat)
_What no competitor can do because they're closed-source Windows apps._

- [ ] **Local LLM interpretation** (Ollama/LM Studio) — chart → plain English reading
- [ ] **Interactive Q&A** — ask "What does my 7th house lord in 10th mean?"
- [ ] **AI remedy suggestions** — gemstones, mantras, rituals from classical texts
- [ ] **Knowledge base** — search full textbook + 15 research articles
- [ ] **Export to PDF/HTML/SVG** — beautiful client-ready reports
- [ ] **Chart database** — SQLite client management with search/filter
- [ ] **Ephemeris viewer** — daily planet positions for any date range
- [ ] **Multi-chart comparison** — natal vs transit, synastry overlay
- [ ] **Dasa timeline** — interactive zoomable timeline with event markers
- [ ] **World atlas** — 50K+ cities with timezone/DST auto-resolution

---

## 3. Architecture

```
jhora/
├── core/                  ← All calculations (the 2000 functions)
│   ├── charts/            ← ChartData, vargas, houses, arudhas
│   ├── dasas/             ← 25+ dasa systems
│   ├── strengths/         ← Shadbala, Ashtakavarga, Vimsopaka
│   ├── yogas/             ← Pattern detection engine
│   ├── transits/          ← Transit, gochara, vedha, tara
│   ├── tajaka/            ← Solar return
│   ├── prasna/            ← Horary
│   ├── matchmaking/       ← Compatibility
│   ├── muhurta/           ← Electional
│   ├── sahamas/           ← Sensitive points
│   ├── kalachakra/        ← Wheel of time
│   └── panchanga/         ← Daily Vedic calendar
│
├── ai/                    ← LLM integration (our moat)
│   ├── knowledge/         ← Book text + research article index
│   ├── interpreter/       ← Chart → natural language
│   └── chat/              ← Interactive Q&A session
│
├── data/                  ← Databases
│   ├── atlas/             ← City coordinates + timezones
│   └── texts/             ← Classical text excerpts
│
├── ui/                    ← PyQt6 desktop app
│   ├── charts/            ← Vector chart rendering (3 styles)
│   ├── dasa_view/         ← Timeline visualization
│   ├── database/          ← Client management
│   └── reports/           ← Print/export
│
├── cli/                   ← Terminal interface
│   ├── commands/          ← chart, dasa, transit, etc.
│   └── output/            ← Rich-formatted terminal display
│
└── api/                   ← RESTful API (future)
    └── routes/            ← Chart, dasa, transit endpoints
```

### Key Design Principles

1. **Core is deterministic, pure Python** — no AI in the calculation path. Same inputs → same chart, always.
2. **AI only for interpretation** — LLM reads computed `ChartData` and generates natural language. Never touches numbers.
3. **Everything cached** — varga charts, strengths, dasas computed once per `ChartData` and memoized.
4. **Pluggable dasas** — one abstract base, 25+ implementations, registry-based discovery.
5. **Immutable ChartData** — thread-safe, cacheable, serializable to JSON.

---

## 4. AI Integration Architecture

```
User birth data
    │
    ▼
Core Engine ──► ChartData (pure numbers)
    │
    ├── ► Rule-based interpreter (planet dignities, house lords, yogas)
    │        │
    │        ▼
    ├── ► LLM Interpreter (Ollama / LM Studio / OpenAI API)
    │        │
    │        ├── ChartData formatted as structured text
    │        ├── Knowledge base excerpts (retrieved via semantic search)
    │        ├── System prompt: "You are PVR Narasimha Rao..."
    │        └── Output: natural language chart reading
    │
    ├── ► Interactive Chat (context = chart + knowledge)
    │        │
    │        └── User: "When will I get married?"
    │            AI: consults dasa periods, 7th house, Venus position...
    │
    └── ► Remedy Engine (text-based, from classical sources)
             │
             └── "Jupiter in 8th: remedy with Yellow Sapphire..."
```

**Supported LLM backends:**
- Ollama (local, free, private) — `llama3`, `qwen2.5`, etc.
- LM Studio (local, free, private)
- OpenAI API / OpenRouter (cloud, for users without local GPU)
- Configurable: model, temperature, system prompt

---

## 5. UI Design Philosophy

### For Casual Users
- "Enter birth data → get reading" in 2 clicks
- Beautiful dark theme, no clutter
- Plain English interpretation with AI
- Learn astrology interactively (click any planet → explanation)

### For Professionals
- ALL the numbers: shadbala virupas, ashtakavarga bindus, varga charts
- Side-by-side chart comparison
- Export client-ready PDF reports
- Chart database with search/filter
- Customizable chart styles and display options

### Chart Styles
- **South Indian** — fixed rasi grid (4×4) ✓ implemented
- **North Indian** — bhava diamond with house numbers ✓ implemented
- **East Indian** — circular Sun chart ✓ implemented
- **D-9 Navamsa** overlay on D-1 ✓ planned
- **Multi-wheel** — natal + transit + dasa lord ✓ planned

---

## 6. Roadmap

### Phase 1: Core Engine (Weeks 1–3)
_Get all calculations working. CLI-first, verify against JHora._

| Week | Focus | Deliverables |
|------|-------|-------------|
| 1 | Vargas + Houses | D-1 through D-60, all variants, bhava support |
| 2 | Dasas + Strengths | 10 dasa systems, Shadbala, Ashtakavarga |
| 3 | Yogas + Sahamas | 100+ yogas, 40+ sahamas, Arudhas, Karakas |

### Phase 2: Professional Features (Weeks 4–6)
_Match or exceed Parashara's Light feature set._

| Week | Focus | Deliverables |
|------|-------|-------------|
| 4 | Transits + Tajaka | Transit analysis, solar return, TP charts |
| 5 | Matchmaking + Prasna | Kuta matching, horary engine, muhurta |
| 6 | Panchanga + Mundane | Daily calendar, world astrology, progressions |

### Phase 3: AI Layer (Weeks 7–8)
_The moat — what no competitor has._

| Week | Focus | Deliverables |
|------|-------|-------------|
| 7 | Knowledge base + Interpreter | Semantic search, rule-based reading, LLM integration |
| 8 | Chat + Remedies | Interactive Q&A, remedy suggestions, report generation |

### Phase 4: GUI Polish (Weeks 9–12)
_Beautiful, professional desktop app._

| Week | Focus | Deliverables |
|------|-------|-------------|
| 9 | Chart rendering | Vector charts (all 3 styles), multi-chart view, D-9 overlay |
| 10 | Dasa visualization | Timeline with zoom/scroll, event markers, print export |
| 11 | Client database | Add/edit/search clients, chart history, batch operations |
| 12 | Release | PDF reports, packaging, documentation, website |

---

## 7. Competitive Comparison

| Feature | JHora | PL ($299) | Kala ($255) | SJS ($300+) | **Ours** |
|---------|:-----:|:---------:|:-----------:|:-----------:|:--------:|
| Free | ✓ | ✗ | ✗ | ✗ | **✓** |
| Open source | ✗ | ✗ | ✗ | ✗ | **✓** |
| Cross-platform | ✗ | ✗ | ✗ | ✗ | **✓** |
| Vargas (D-1–D-60) | ✓ | ✓ | ✓ | ✓ | **✓** |
| 25+ Dasas | ✓ | ✓ | ✓ | ✓ | **✓** |
| Shadbala | ✓ | ✓ | ✓ | ✓ | **✓** |
| Ashtakavarga | ✓ | ✓ | ✓ | ✓ | **✓** |
| Yogas | ✓ | ✓ | ✓ | ✓ | **✓** |
| Tajaka | ✓ | ✓ | ✓ | ✓ | **✓** |
| Matchmaking | ✓ | ✓ | ✓ | ✓ | **✓** |
| Prasna | ✓ | ✓ | ✓ | ✓ | **✓** |
| Muhurta | ✓ | ✓ | ✓ | ✓ | **✓** |
| Transit analysis | ✓ | ✓ | ✓ | ✓ | **✓** |
| World atlas | ✗ | ✓ (5M) | ✓ | ✓ | **Planned** |
| Auto interpretation | ✗ | ✓ (textbook) | ✓ | ✓ | **✓ + AI** |
| AI Q&A | ✗ | ✗ | ✗ | ✗ | **✓** |
| Vector charts | ✗ | ✗ | ✗ | ✗ | **✓** |
| PDF reports | ✗ | ✓ | ✓ | ✓ | **✓** |
| Dark UI theme | ✗ | ✗ | ✗ | ✗ | **✓** |
| Python API | ✗ | ✗ | ✗ | ✗ | **✓** |
| Local LLM | ✗ | ✗ | ✗ | ✗ | **✓** |

---

## 8. Current Status

```
DONE:
├── Core types (Graha, Rasi, Nakshatra, Varga, Bhava, Dasa)
├── SweEngine wrapper (all 18 SE API calls)
├── ChartBuilder + ChartData (frozen dataclass)
├── Planet dignity calculator
├── Vimsottari Dasa (full MD/AD periods)
├── Dark PyQt6 GUI (3 chart styles, planet table, house table, dasa tab)
├── CLI (chart, dasa, navamsa, gui, interpret, knowledge commands)
├── Book knowledge base (16 sources, 1.9M chars, full-text search)
├── Chart interpreter (rule-based reading generator)
└── Author's textbook + 15 research articles downloaded

NEXT:
├── Varga charts (D-2 through D-60) ← STARTING HERE
├── Ashtottari, Narayana, Kalachakra dasas
├── Shadbala strength computation
├── Yogas detection engine
├── Dasa timeline visualization
├── Client database
└── AI chat integration (Ollama)
```

---

## 9. References

- Original JHora 8.0: `vedicastrologer.org/jh`
- Textbook: "Vedic Astrology: An Integrated Approach" by PVR Narasimha Rao (free download)
- Swiss Ephemeris: `swisseph.com`
- pyswisseph: `pypi.org/project/pyswisseph`
- Parashara's Light: `parasharaslight.com`
- Kala: `vedic-astrology.net`
- Shri Jyoti Star: `vedicsoftware.com`
