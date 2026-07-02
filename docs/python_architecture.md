# Jagannatha Hora — Python Package Architecture

**Design Date:** July 2, 2026
**Package:** `jhora`
**Target:** Python 3.11+ with `pyswisseph` (Swiss Ephemeris bindings)
**License:** GPL v3 (derived from reverse engineering of GPL-incompatible original)

---

## 1. Package Overview

```
jhora/
├── __init__.py              # Version, public API exports
├── _version.py              # Single-source version string
├── exceptions.py            # Domain-specific exceptions
│
├── types/                   # Core domain types & enumerations
│   ├── __init__.py
│   ├── graha.py             # Planet enum (9 + optional Uranus/Neptune/Pluto)
│   ├── rasi.py              # Sign enum, sign properties (movable/fixed/dual, element, gender, etc.)
│   ├── bhava.py             # House enum, house meanings
│   ├── nakshatra.py         # 27 nakshatras, padas, lords, deities
│   ├── varga.py             # Varga chart levels (D-1..D-150), variant enum
│   ├── upagraha.py          # Upagraha definitions (Dhuma, Vyatipata, etc.)
│   ├── tithi.py             # Tithi enum, karana, yoga (as a time unit)
│   ├── karaka.py            # Chara, Sthira, Naisargika karaka types
│   ├── strength.py          # Strength measurement enums (Shadbala components, Amsa levels)
│   ├── dasa.py              # Dasa system enum, period type (MD/AD/PD/SD/PR/DE)
│   ├── sahama.py            # Sahama enum (40+ types)
│   ├── relation.py          # Relationship types (Adhimitra, Mitra, Sama, Satru, Adhisatru)
│   ├── yoga.py              # Yoga classification enums
│   └── aspect.py            # Aspect types (Graha drishti, Rasi drishti, Argala)
│
├── config/                  # Configuration management
│   ├── __init__.py
│   ├── manager.py           # ConfigManager — reads ~/.config/jhora/jhora.json
│   ├── defaults.py          # Factory default settings
│   ├── schema.py            # JSON schema validation for config
│   └── ayanamsa.py          # Ayanamsa definitions (Lahiri, Raman, Krishnamurti, etc.)
│
├── ephemeris/               # Pyswisseph wrapper (astronomy layer)
│   ├── __init__.py
│   ├── swe.py               # SweEngine — wraps swe_calc, swe_houses, swe_julday, etc.
│   ├── julian.py            # Julian day utilities (date <-> JD, ghati/vighati)
│   ├── ayanamsa.py          # Ayanamsa getter/setter (swe_set_sid_mode wrapper)
│   ├── rise_set.py          # Sunrise/sunset, moonrise/moonset (swe_rise_trans)
│   ├── topo.py              # Topocentric position utilities (swe_set_topo)
│   ├── eclipse.py           # Eclipse calculator (swe_lun_eclipse_when, swe_sol_eclipse_when_*)
│   └── refraction.py        # Atmospheric refraction (swe_refrac)
│
├── geo/                     # Atlas / geographical database
│   ├── __init__.py
│   ├── database.py          # AtlasDB — SQLite city/coordinate lookup
│   ├── timezone.py          # Timezone resolution (pytz integration)
│   ├── loader.py            # ADB importer (converts .adb binary → SQLite)
│   └── data/                # SQLite atlas files (git LFS or auto-download)
│       └── jh_atlas.sqlite
│
├── calendar/                # Vedic time calculations (panchanga)
│   ├── __init__.py
│   ├── panchanga.py         # PanchangaEngine — tithi, nakshatra, yoga, karana, weekday, hora
│   ├── sunrise.py           # Sunrise/sunset at location
│   ├── season.py            # Ritu (season), ayana determination
│   └── time_unit.py         # Ghati, vighati, hora (as time divisions), LMT ↔ STD conversion
│
├── charts/                  # Chart calculation engine
│   ├── __init__.py
│   ├── chart.py             # ChartData — central chart data structure
│   ├── planet_calc.py       # Planet position calculator (with digbala-aware dignity calcs)
│   ├── lagna.py             # Ascendant / special lagnas (BL, HL, GL, SL)
│   ├── houses.py            # House cusps, house systems (Parasara, Equal, Placidus, etc.)
│   ├── upagraha_calc.py     # Upagraha longitude computation
│   ├── varga.py             # VargaChartComputer — all D-1..D-150 with variants
│   ├── bhava_chart.py       # Bhava/chalit chakra (23 charts with bhava support)
│   ├── aspect.py            # Aspect calculator (graha drishti, rasi drishti, argala)
│   ├── arudha.py            # Arudha pada calculator (bhava arudhas, graha arudhas, UL, AL)
│   ├── karaka_calc.py       # Chara, Sthira, Naisargika karaka computation
│   ├── visualization.py     # ASCII chart drawing (3 styles: South/North/East Indian)
│   └── serialization.py     # Chart save/load (JSON, JHD-like binary)
│
├── strengths/               # Strength calculations
│   ├── __init__.py
│   ├── shadbala.py          # Shadbala — 6-source planetary strength
│   │   ├── sthanabala.py    #   Positional strength
│   │   ├── digbala.py       #   Directional strength
│   │   ├── kalabala.py      #   Temporal strength
│   │   ├── chestabala.py    #   Motional strength
│   │   ├── naisargikabala.py#   Natural strength
│   │   └── drigbala.py      #   Aspectual strength
│   ├── vimsopaka.py         # Vimsopaka bala (Shadvarga, Sapta, Dasa, Shodasa)
│   ├── ashtakavarga.py      # Ashtakavarga — BAV, SAV, SoAV, PAV, Sodhya Pinda
│   ├── amsabala.py          # Amsabala / Vaiseshikamsa
│   ├── avastha.py           # Avasthas (Kumara/Jagrita/Mudita/Sayanadi etc.)
│   ├── ishta_kashta.py      # Ishta phala / Kashta phala
│   ├── bhava_bala.py        # Bhava bala (house strength)
│   ├── pancha_vargeeya.py   # Pancha/Dwadasa Vargeeya Bala (Tajaka-specific)
│   ├── graha_yuddha.py      # Planetary war resolution
│   └── marana_karaka.py     # Marana karaka sthana detection
│
├── dasas/                   # Dasa engine (25+ systems)
│   ├── __init__.py
│   ├── base.py              # DasaBase — abstract dasa engine
│   ├── period.py            # DasaPeriod — period tree (MD/AD/PD/SD/PR/DE) with timing
│   ├── vimsottari.py        # Vimsottari (120-year nakshatra dasa)
│   ├── ashtottari.py        # Ashtottari (108-year nakshatra dasa)
│   ├── kalachakra.py        # Kalachakra dasa (with gatis, deha/jeeva)
│   ├── yogini.py            # Yogini dasa
│   ├── dwisaptati_sama.py   # Dwi-saptati sama dasa
│   ├── shat_trimsamsa.py    # Shat-trimsa sama dasa
│   ├── dwadasottari.py      # Dwadasottari dasa
│   ├── chaturaseeti.py      # Chaturaseeti sama dasa
│   ├── sataabdika.py        # Sataabdika dasa
│   ├── shodasottari.py      # Shodasottari dasa
│   ├── panchottari.py       # Panchottari dasa
│   ├── shashti_hayani.py    # Shashti-hayani dasa
│   ├── saptarshi.py         # Saptarshi dasa
│   ├── narayana.py          # Narayana dasa (rasi dasa, per divisional chart, seed-based)
│   ├── sudasa.py            # Sudasa (Sreelagna Kendradi Rasi dasa)
│   ├── drigdasa.py          # Drigdasa
│   ├── niryana_shoola.py    # Niryana Shoola dasa
│   ├── shoola.py            # Shoola dasa (per house for timing relative death)
│   ├── sudarsana.py         # Sudarsana Chakra dasa
│   ├── moola.py             # Moola dasa
│   ├── navamsa.py           # Navamsa dasa
│   ├── varnada.py           # Varnada dasa
│   ├── brahma.py            # Brahma dasa
│   ├── sthira.py            # Sthira dasa
│   ├── mandooka.py          # Mandooka dasa
│   ├── chara.py             # Chara dasa (Parasara, K.N. Rao variants)
│   ├── paryaya.py           # Paryaya dasas (Chara, Sthira, Ubhaya)
│   ├── yogardha.py          # Yogardha dasa
│   ├── lagna_kendradi.py    # Lagna Kendradi Rasi dasa
│   ├── ak_kendradi_rasi.py  # Atma Karaka Kendradi Rasi dasa
│   ├── ak_kendradi_graha.py # Atma Karaka Kendradi Graha dasa
│   ├── trikona.py           # Trikona dasa
│   ├── patyayini.py         # Patyayini dasa
│   ├── tithi_ashtottari.py  # Tithi Ashtottari dasa
│   ├── tithi_yogini.py      # Tithi Yogini dasa
│   ├── tara.py              # Tara dasa
│   ├── kaala.py             # Kaala dasa
│   ├── chakra.py            # Chakra dasa
│   ├── naisargika.py        # Naisargika dasa
│   ├── rasi_bhukta.py       # Rasi-bhukta Vimsottari / Mudda
│   ├── anti_zodiacal.py     # Anti-zodiacal dasa
│   ├── buddhi_gati.py       # Buddhi Gati dasa
│   └── ayur_narayana.py     # Ayur Narayana dasa
│
├── transits/                # Transit engine
│   ├── __init__.py
│   ├── transit.py           # TransitCalculator — planet positions for given datetime
│   ├── vedha.py             # Vedha / nakshatra transit analysis
│   ├── tara.py              # Tara transit (janma/sampat/vipat etc.)
│   ├── gochara.py           # Gochara (transit house analysis from Moon/lagna/AL)
│   └── search.py            # Transit search (find when planet crosses given point)
│
├── tajaka/                  # Tajaka (solar return)
│   ├── __init__.py
│   ├── yearly.py            # Varsha Pravesha (annual chart)
│   ├── monthly.py           # Maasa Pravesha (monthly chart)
│   ├── hora_60.py           # 60-hour / 5-hour / 25-minute / 2-minute charts
│   ├── dasa.py              # Compressed dasas (Patyayini, Tajaka-specific)
│   ├── muntha.py            # Muntha computation (3 variants)
│   └── strengths.py         # Pancha/Dwadasa Vargeeya Bala (Tajaka)
│
├── tithi_pravesha/          # Tithi Pravesha charts
│   ├── __init__.py
│   ├── annual.py            # Annual TP chart
│   ├── monthly.py           # Monthly TP chart
│   └── daily.py             # Daily TP chart
│
├── prasna/                  # Horary (Prasna) engine
│   ├── __init__.py
│   ├── prasna.py            # PrasnaEngine — 108 / 249 (KP) / 1800 (Nadi) modes
│   └── dash_compression.py  # Dasa compression for prasna charts
│
├── mundane/                 # Mundane astrology
│   ├── __init__.py
│   ├── ingress.py           # Solar ingress (Ar, Cp), lunar ingress
│   ├── full_moon.py         # Annual/Monthly Full Moon charts
│   ├── new_moon.py          # Lunar new year, new month charts
│   ├── financial.py         # Financial new year chart
│   ├── conjunction.py       # Planetary conjunction mode
│   ├── eclipse_chart.py     # Eclipse-based charts
│   └── lifecycle.py         # 144-year lifecycle charts
│
├── muhurta/                 # Electional astrology
│   ├── __init__.py
│   └── muhurta.py           # MuhurtaFinder — electional chart evaluation
│
├── matchmaking/             # Matchmaking / Kuta
│   ├── __init__.py
│   ├── kuta.py              # KutaEngine — 10+ compatibility criteria
│   ├── porutham.py          # Porutham scoring (Nakshatra-based)
│   └── compatibility.py     # Chart-level compatibility analysis
│
├── yogas/                   # Yoga detection engine
│   ├── __init__.py
│   ├── base.py              # YogaDetector — abstract base for yoga matching
│   ├── ravi.py              # Ravi Yogas (solar combinations)
│   ├── chandra.py           # Chandra Yogas (lunar combinations)
│   ├── mahaapurusha.py      # Mahapurusha Yogas (5 types: Hamsa, Malavya, etc.)
│   ├── nabhasa.py           # Nabhasa Yogas (Akriti/classified celestial: 32 sub-types)
│   ├── raja.py              # Raja Yogas (power-giving combinations)
│   ├── dhana.py             # Dhana Yogas (wealth-giving combinations)
│   ├── daridra.py           # Daridra Yogas (poverty-giving combinations)
│   ├── sambandha.py         # Raja Sambandha Yogas
│   ├── special.py           # Other popular yogas (Vesi, Vosi, Ubhayachara, etc.)
│   └── registry.py          # YogaRegistry — loads & manages all detector classes
│
├── sahamas/                 # Sensitive points
│   ├── __init__.py
│   ├── sahama.py            # SahamaCalculator — 40+ formulas (Punya, Vidya, Putra, etc.)
│   └── registry.py          # SahamaRegistry — formula definitions
│
├── progressions/            # Secondary progressions
│   ├── __init__.py
│   ├── progression.py       # ProgressionEngine — D-n based Sun progression
│   └── chart.py             # Progressed chart casting
│
├── chakras/                 # Special chakras
│   ├── __init__.py
│   ├── kalachakra.py        # Kalachakra (wheel of time) diagram
│   ├── sarvatobhadra.py     # Sarvatobhadra Chakra (with vedha analysis)
│   ├── kota.py              # Kota Chakra / Durga Chakra
│   └── sudarsana.py         # Sudarsana Chakra (3-ring lagna/Moon/Sun)
│
├── calc/                    # Shared calculation utilities
│   ├── __init__.py
│   ├── angles.py            # Longitudinal arithmetic (difference, addition, mod 360)
│   ├── dignities.py         # Planetary dignity checker (exalted, debilitated, moolatrikona, own)
│   ├── friendship.py        # Permanent/temporary/compound relationship calculator
│   ├── nakshatra_utils.py   # Nakshatra position, pada computation
│   ├── tithi_months.py      # Lunar month, year, leap month (adhika masa) calculation
│   ├── sphuta.py            # Sphuta (mathematical point) calculation helpers
│   └── trisphuta.py         # Trisphuta & associated sphutas
│
├── io/                      # Data input/output
│   ├── __init__.py
│   ├── chart_file.py        # JHD file format reader/writer
│   ├── csv_export.py        # CSV export for chart data
│   ├── json_export.py       # JSON export for chart data
│   └── pdf_export.py        # PDF report generation (optional, ReportLab)
│
├── cli/                     # Command-line interface
│   ├── __init__.py
│   ├── main.py              # Typer-based CLI entry point
│   ├── commands/
│   │   ├── chart.py         # `jhora chart` — chart display
│   │   ├── dasa.py          # `jhora dasa` — dasa listing
│   │   ├── transit.py       # `jhora transit` — transit calc
│   │   ├── panchanga.py     # `jhora panchanga` — panchanga
│   │   ├── match.py         # `jhora match` — compatibility
│   │   ├── prasna.py        # `jhora prasna` — horary
│   │   ├── muhurta.py       # `jhora muhurta` — electional
│   │   ├── strengths.py     # `jhora strengths` — shadbala etc.
│   │   ├── yogas.py         # `jhora yogas` — list yogas
│   │   ├── tajaka.py        # `jhora tajaka` — solar return
│   │   ├── sahama.py        # `jhora sahama` — sensitive points
│   │   └── config.py        # `jhora config` — manage settings
│   ├── output.py            # Rich-formatted terminal output
│   └── helpers.py           # Shared CLI utilities (birthdata parsing, etc.)
│
├── ui/                      # Future GUI (Tkinter or Qt)
│   ├── __init__.py          # Currently empty — placeholder
│   └── ...                  # TBD after CLI stabilization
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures (sample charts, ephemeris stubs)
│   ├── test_types/
│   ├── test_ephemeris/
│   ├── test_charts/
│   ├── test_dasas/
│   ├── test_strengths/
│   ├── test_yogas/
│   ├── test_transits/
│   ├── test_tajaka/
│   ├── test_prasna/
│   ├── test_sahamas/
│   ├── test_calendar/
│   ├── test_geo/
│   └── fixtures/            # JHD test files, expected outputs
│
└── docs/                    # Docstrings-based documentation
    └── ...                  # Generated via Sphinx / mkdocs
```

---

## 2. Module Responsibilities

### 2.1 `jhora/types/` — Core Domain Types

All fundamental astronomy/astrology constants live here. Pure enums and dataclasses with no computation logic.

| Class/Module | Responsibility |
|---|---|
| `Graha` (enum) | 9 planets: SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU. Properties: natural benefic/malefic, gender, element, varna, guna, taste, dhatu, abode, deity, ayana, weekday lord, etc. |
| `Rasi` (enum) | 12 signs: ARIES through PISCES. Properties: element, gender, mobility (movable/fixed/dual), footprint (odd/even-footed), limbs of Vishnu, bhava mapping, lord, exaltation/debilitation degrees, moolatrikona. |
| `Bhava` (enum) | House meanings (1-12), natural significations |
| `Nakshatra` (enum) | 27 nakshatras with start/end positions, Vimsottari lords, deities |
| `VargaLevel` (enum) | D-1 through D-150, plus custom/sub-divisional. Each with division count. |
| `VargaVariant` (enum) | `DEFAULT`, `TRD`, `REV`, `REV2`, `PV`, `B`, `K`, `KM`, `UKM`, `JN`, `SN`, `US`, `RA`, `RM`, `RMM`, `NI`, `NIM`, `MD`, `LM`, `CNL`, `SN2`, `KN`, `AR`, `RVAR`, `SH`, `1_7`, `7_1`, `5_8`, `6_9`, `9_12` |
| `Upagraha` (enum) | Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu, Kaala, Mrityu, Arthapraharaka, Yamaghantaka, Gulika, Mandi |
| `Karaka` (class) | Chara karakas (Atma, Amatya, etc.), Sthira karakas, Naisargika karakas |
| `SahamaType` (enum) | All 40+ sahama types |
| `DasaSystem` (enum) | Identifiers for all 25+ dasa systems |
| `YogaClass` (enum) | Classification: Ravi, Chandra, Mahapurusha, Nabhasa, Raja, Dhana, Daridra, Sambandha |

### 2.2 `jhora/ephemeris/` — Astronomy Layer

Thin wrapper around `pyswisseph` with caching, error handling, and Vedic defaults.

| Class | Responsibility |
|---|---|
| `SweEngine` | Singleton-ish wrapper. Wraps all 18 SE API functions. Handles initialization (`swe_set_ephe_path`), cleanup (`swe_close`), coordinate system settings. Caches recent planet calculations. |
| `JulianDay` | `date ↔ JD` conversion, ghati/vighati support, Surya Siddhanta time utilities. Handles negative JD (pre-4713 BCE). |
| `AyanamsaManager` | Sets sidereal mode (`swe_set_sid_mode`). Supports: Lahiri, Raman, Krishnamurti, SSS, Pushya-paksha, Rohini-paksha, Fixed-star custom, Traditional Lahiri, user-defined. Computes ayanamsa corrections. |
| `RiseSetCalc` | Sunrise/sunset, moonrise/moonset times at given location. Wraps `swe_rise_trans`. |
| `TopoCalc` | Topocentric position setup (`swe_set_topo`). |
| `EclipseCalc` | Lunar/solar eclipse timing (`swe_lun_eclipse_when`, `swe_sol_eclipse_when_glob/loc`). |

**Data flow:**
```
ChartData → JulianDay.get_jd() → SweEngine.calc_planet() → (longitudes, speeds, lat/lon)
                                 → AyanamsaManager.subtract_ayanamsa() → sidereal positions
                                 → RiseSetCalc.rise_set() → sunrise/sunset times
                                 → SweEngine.houses() → house cusps
```

### 2.3 `jhora/geo/` — City Atlas

Replaces the binary `.adb` atlas with SQLite.

| Class | Responsibility |
|---|---|
| `AtlasDB` | SQLite-backed city lookup. `find_city(name, country)` → (lat, lon, tz, alt). `find_nearest(lat, lon, radius)`. Supports fuzzy name matching. |
| `TimezoneResolver` | Wraps `pytz`/`zoneinfo`. Resolves timezone by country + coordinates. Stores timezone name in DB for efficient lookup. |
| `AdbImporter` | Parses `jhlite.adb` / `jhworld.adb` binary format and populates SQLite. Self-contained one-time migration tool. |

**Schema `jh_atlas.sqlite`:**
```sql
CREATE TABLE cities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    country_code TEXT,
    region TEXT,
    latitude REAL,
    longitude REAL,
    timezone_name TEXT,
    altitude REAL,
    population INTEGER
);
CREATE INDEX idx_cities_name ON cities(name);
CREATE INDEX idx_cities_coords ON cities(latitude, longitude);
```

### 2.4 `jhora/calendar/` — Vedic Time

| Class | Responsibility |
|---|---|
| `PanchangaEngine` | Given JD + location, computes: lunar year, lunar month, tithi, nakshatra, yoga, karana, weekday (Vedic: starts at sunrise), hora (Satya + Mahakala), rahu kalam, gulika kalam, yama gandam. Handles adhika masa (leap month). |
| `SunriseCalc` | Sunrise/sunset at location (delegates to ephemeris/rise_set.py) |
| `SeasonCalc` | Ritu (6 seasons), ayana (Uttara/Dakshina), determination from Sun position |
| `LmtConverter` | Local Mean Time ↔ Standard Time conversion |

### 2.5 `jhora/charts/` — Chart Calculation

This is the heart of the application.

| Class | Responsibility |
|---|---|
| `ChartData` | Central data structure. Holds: birth datetime, location, JD, ayanamsa, planet positions (9 planets + upagrahas + all lagnas), house cusps, varga positions (for all D-n), aspects, arudhas. Immutable after construction. |
| `PlanetCalculator` | Computes geocentric/topocentric planet positions. Returns `PlanetPosition` namedtuple: (longitude, latitude, speed, rasi, nakshatra, pada, dignity, is_retrograde). |
| `LagnaCalculator` | Computes lagna (ascendant), special lagnas: Bhava Lagna (BL), Hora Lagna (HL), Ghati Lagna (GL), Sree Lagna (SL). |
| `HouseCalculator` | Computes house cusps. Supports systems: Parasara (rasi = house), Equal (30°), Nakshatra Pada-based, Sripathi, Porphyry, Koch, Placidus, Regiomontanus, Campanus. |
| `VargaChartComputer` | The most algorithmically dense module. For each of D-1..D-150: given planet longitude, compute varga position. Handles all variants (Trd, Rev, Pv, etc.). Returns `VargaPosition: (rasi, degrees_in_rasi, variant_used)`. |
| `BhavaChartComputer` | Computes bhava/chalit chakra for 23 charts that support it. See `docs/varga_charts.md` for the list. |
| `AspectCalculator` | Computes graha drishti (special aspects for Mars/Jupiter/Saturn + 7th for all), rasi drishti, argala (2nd/4th/11th primary, 5th secondary), virodhargala (12th/10th/3rd/9th). Handles Ketu anti-zodiacal exception. |
| `ArudhaCalculator` | Computes bhava arudha padas (AL = A1 through A12 + UL = A12), graha arudhas. Handles dual lordship strength comparison for Sc/Aq. |
| `KarakaCalculator` | Computes 8 chara karakas (Jaimini: Atma, Amatya, Bhratri, Matri, Putra, Gnati, Dara, Anu), 7 sthira karakas (Parasara), and 9 naisargika karakas. |
| `ChartRenderer` | Generates ASCII chart diagrams in 3 styles: South Indian (fixed rasi positions), North Indian (bhava diamond), East Indian (Sun-style with/without frame). Multilingual planet names. |
| `ChartSerializer` | Chart save/load as JSON, optionally JHD-compatible format. |

**Varga computation algorithm (pseudocode):**
```
def compute_varga_position(planet_long, varga_level, variant):
    n = varga_level.division_count  # e.g. 9 for D-9
    sign = floor(planet_long / 30)
    pos_in_sign = planet_long % 30
    part_size = 30 / n
    part_index = floor(pos_in_sign / part_size)
    # Apply variant-specific mapping rules
    target_sign = mapping_table[variant][sign][part_index]
    return VargaPosition(target_sign, pos_in_sign - part_index * part_size, variant)
```

### 2.6 `jhora/strengths/` — Planetary & Chart Strength

| Class | Responsibility |
|---|---|
| `ShadbalaComputer` | 6-source strength: Sthanabala (Uchcha, Saptavargaja, Ojayugmarasi, Kendradi, Drekkana), Digbala, Kalabala (Natonna, Paksha, Tribhaga, Abda, Maasa, Vaara, Hora, Ayana, Yuddha), Cheshtabala (motional), Naisargikabala, Drigbala. Returns virupas. |
| `VimsopakaComputer` | Vimsopaka bala (20 sources) for Shadvarga, Sapta Varga, Dasa Varga, Shodasa Varga. |
| `AshtakavargaComputer` | Full AV system: Bhinna Ashtakavarga (BAV) for each planet, Sarva Ashtakavarga (SAV), Shodhya Ashtakavarga (SoAV), Prastara Ashtakavarga (PAV), Sodhya Pindas. Handles Parasara vs Varahamihira definition differences. |
| `AvasthaCalculator` | Age-based (Kumara, etc.), alertness-based (Jagrita, etc.), mood-based (Mudita, etc.), activity-based (Sayanadi) states. |
| `BhavaBalaCalculator` | House strength computations. |
| `MaranaKarakaDetector` | Detects planets in marana karaka sthana (death-inflicting house positions). |

### 2.7 `jhora/dasas/` — Dasa Engine

The largest subsystem with 25+ dasa systems.

| Base Class | Responsibility |
|---|---|
| `DasaBase` | Abstract interface: `compute(birth_jd, chart, options) → List[DasaPeriod]`. Handles year definitions (solar 365.2425d, savana 360d, tithi, user-defined). Manages period tree (MD → AD → PD → SD → PR → DE). |
| `DasaPeriod` | Dataclass: `(lord: Graha | Rasi, start_jd, end_jd, level: PeriodLevel, cycle: int, lords: List)`. Supports subdivision to next level. |

**Nakshatra dasas** (Moon-star-based): Vimsottari, Ashtottari, Kalachakra, Yogini, Dwi-saptati sama, Shat-trimsa sama, Dwadasottari, Chaturaseeti sama, Sataabdika, Shodasottari, Panchottari, Shashti-hayani, Saptarshi.

**Rasi dasas (phalita):** Narayana (per divisional chart, seed-based), Sudasa, Drigdasa, Lagna Kendradi, Atma Karaka Kendradi Rasi, Trikona, Chara (Parasara/K.N. Rao), Yogardha, Paryaya (Chara/Sthira/Ubhaya).

**Rasi dasas (ayur):** Shoola, Niryana Shoola, Brahma, Sthira, Mandooka, Navamsa, Varnada.

**Other:** Moola, Tara, AK Kendradi Graha, Patyayini, Sudarsana Chakra, Rasi-bhukta Vimsottari/Mudda, Tithi Ashtottari, Tithi Yogini, Anti-zodiacal, Buddhi Gati, Ayur Narayana.

### 2.8 `jhora/transits/` — Transit Engine

| Class | Responsibility |
|---|---|
| `TransitCalculator` | For given datetime + natal chart: computes planet positions, house placement from lagna/Moon/AL in all divisional charts, tara analysis (janma/sampat/vipat/pratyak), vedha (piercing) analysis. |
| `GocharaAnalyzer` | Analyzes transit house positions. Integrates Ashtakavarga analysis (transit planet's AV score, kakshya placement). |
| `TransitSearch` | Finds date/time when a given planet transits a specified longitude/sahama/natal point. |

### 2.9 `jhora/tajaka/` — Solar Return

| Class | Responsibility |
|---|---|
| `TajakaYearly` | Annual solar return chart (Varsha Pravesha): find Sun return to natal Sun position. |
| `TajakaMonthly` | Monthly chart (Maasa Pravesha). |
| `TajakaSubHora` | 60-hour / 5-hour / 25-minute / 2-minute charts (Sudarsana subdivision). |
| `MunthaCalculator` | Muntha (progressed ascendant): 3 variants (sign-per-year, Sudarsana-based with AD from dasa sign/lord). |

### 2.10 `jhora/tithi_pravesha/` — Tithi Pravesha

| Class | Responsibility |
|---|---|
| `TpChartEngine` | Annual/monthly/daily Tithi Pravesha charts. TP chart is cast when Sun-Moon longitude difference equals that at birth (tithi match). |

### 2.11 `jhora/prasna/` — Horary

| Class | Responsibility |
|---|---|
| `PrasnaEngine` | 3 modes: Prasna-108 (number → rasi + navamsa), Prasna-249/KP (→ rasi + nakshatra + sub), Nadi (1-1800 → all 16 vargas). Dasa compression support. |

### 2.12 `jhora/mundane/` — World Astrology

| Class | Responsibility |
|---|---|
| `MundaneEngine` | Ingress charts (Ar/Cp), Full/New Moon charts, Financial New Year, planetary conjunction charts, eclipse charts, lifecycle charts (144-year). All use dasa compression. |

### 2.13 `jhora/yogas/` — Combination Detection

| Class | Responsibility |
|---|---|
| `YogaRegistry` | Discovers all `YogaDetector` subclasses. `detect_all(chart_data, varga) → List[Yoga]`. |
| `YogaDetector` (base) | Abstract: `matches(chart_data, varga_level) → bool`. Each subclass implements one yoga. |
| Individual detectors | ~100+ individual yogas across all categories. See subtopics in help docs. |

### 2.14 `jhora/sahamas/` — Sensitive Points

| Class | Responsibility |
|---|---|
| `SahamaCalculator` | Computes all 40+ sahamas using `(A - B + C)` formulas with day/night reversal and C-between-B-and-A adjustment (+30°). |

### 2.15 `jhora/progressions/` — Secondary Progressions

| Class | Responsibility |
|---|---|
| `ProgressionEngine` | Progresses Sun by D-n division amount per year (e.g., D-10 = 3°/year, D-24 = 1.25°/year). Finds date when Sun reached progressed position. Casts chart for that date. |

### 2.16 `jhora/chakras/` — Special Wheels

| Class | Responsibility |
|---|---|
| `Kalachakra` | 27×9 cell wheel. Base nakshatra from Sun (natal) or lagna (Tajaka/TP). Displays planets, upagrahas, lagnas, sahamas, sphutas. |
| `SarvatobhadraChakra` | 28×8 grid. Vedha analysis. Configurable special points (tara, tithi, house). |
| `KotaChakra` | Durga Chakra. Moon-nakshatra-based. |
| `SudarsanaChakra` | 3-ring diagram: lagna (inner), Moon (middle), Sun (outer). |

### 2.17 `jhora/cli/` — Command-Line Interface

Typer-based CLI with rich terminal output.

```
jhora chart <birthdata>             # Display charts (D-1 default, --varga D-n, --style)
jhora dasa <birthdata> <dasa_name>  # List periods, --level AD/PD, --event date
jhora transit <birthdata> <datetime> # Show transit positions
jhora panchanga <datetime> <place>  # Show panchanga
jhora strengths <birthdata>         # Show shadbala, vimsopaka, ashtakavarga
jhora yogas <birthdata>             # List active yogas
jhora match <bd1> <bd2>             # Compatibility analysis
jhora prasna <number> <datetime>    # Horary chart
jhora tajaka <birthdata> <year>     # Solar return
jhora sahama <birthdata> [name]     # Sahama positions
jhora config [key] [value]          # Configuration
jhora atlassearch <city>            # Search city atlas
```

**Birthdata input format:**
```
"1970-04-04 17:48:20 +0530 81E12 16N15"    # ISO datetime + timezone + coordinates
"1970-04-04 17:48:20 Asia/Kolkata Chennai"  # tz name + city name (uses atlas)
```

---

## 3. Data Flow

### 3.1 Chart Calculation Pipeline

```
User input (birthdata)
    │
    ▼
Geo/AtlasDB ──► (lat, lon, tz)
    │
    ▼
JulianDay ──► birth JD
    │
    ▼
AyanamsaManager.set_mode(lahiri)
    │
    ▼
SweEngine.calc_planets(jd, flags) ──► raw tropical positions
    │                                  + speeds, lat, lon
    ├── Ayanamsa subtraction ──► sidereal positions
    ├── Keenness for retrogression
    │
    ▼
PlanetCalculator ──► PlanetPositions (rasi, nakshatra, pada, dignity)
    │
    ▼
LagnaCalculator ──► Lagna, BL, HL, GL, SL
    │
    ▼
HouseCalculator ──► House cusps
    │
    ▼
VargaChartComputer ──► VargaPositions (for all D-x requested)
    │
    ▼
AspectCalculator ──► Graha drishti, Rasi drishti, Argala
    │
    ▼
ArudhaCalculator ──► AL, A2..A12, UL, Graha arudhas
    │
    ▼
KarakaCalculator ──► Chara Karakas (8), Sthira (7), Naisargika (9)
    │
    ▼
ChartData (immutable structure with all computed fields)
    │
    ├──► StrengthEngines ──► Shadbala, Vimsopaka, Ashtakavarga
    ├──► DasaEngine ──► DasaPeriods
    ├──► TransitEngine ──► Transit analysis
    ├──► YogaDetectors ──► Active yogas
    ├──► SahamaCalculator ──► Sahama positions
    └──► ChartRenderer ──► ASCII / JSON output
```

### 3.2 Dasa Computation Flow

```
ChartData (with VargaPositions, Karakas, Arudhas)
    │
    ▼
DasaBase.factory(dasa_system) ──► concrete Dasa engine
    │
    ├── DasaOptions (year definition, seed, cycle params)
    │
    ▼
Engine.compute(birth_jd, chart, options)
    │
    ├── Resolve seed reference (Moon nakshatra / lagna / special reference)
    ├── Compute lord sequence (planet or rasi order)
    ├── Compute period lengths (120/108/etc. year total, fractional first period)
    └── Build period tree
            │
            ▼
    List[DasaPeriod] (MD → AD → PD → SD → PR → DE)
        │
        ├── Period subdivision (click to drill down)
        ├── Event location (find running period at given date)
        └── Dasa visualization (timeline / table)
```

### 3.3 Transit Analysis Flow

```
NatalChart (ChartData)
    │
    ▼
TransitCalculator.compute(transit_datetime)
    │
    ├── SweEngine.calc_planets(transit_jd) ──► transit planet positions
    ├── Compute transit houses from lagna / Moon / AL (in rasi + each divisional chart)
    ├── Compute tara (janma/sampat/vipat/pratyak/naidhana/mitra/atma-mitra/janma-adhi-vipat)
    ├── Compute vedha (Sarvatobhadra-based)
    ├── Compute Ashtakavarga for transit positions (SAV score, kakshya)
    └── Compute murthi classification
            │
            ▼
    TransitAnalysis result
```

### 3.4 Strength Computation Flow

```
ChartData (VargaPositions for all D-n)
    │
    ▼
ShadbalaComputer
    ├── SthanaBala: Uchcha (exaltation), Saptavargaja, Ojayugmarasi, Kendradi, Drekkana
    ├── DigBala: quadrant-based directional strength
    ├── KalaBala: Natonna (midnight), Paksha (fortnight), Tribhaga (day/night division),
    │             Abda (year), Maasa (month), Vaara (weekday), Hora (hour), Ayana (solstice), Yuddha (war)
    ├── CheshtaBala: based on planetary speed/motion (6 degrees of cheshta)
    ├── NaisargikaBala: inherent strength (fixed per planet)
    └── DrikBala: aspect-based strength
            │
            ▼
    Shadbala (6 virupas + total virupa per planet)
    │
    ▼
VimsopakaComputer
    ├── Shadvarga Vimsopaka (6 charts: D-1, D-2, D-3, D-9, D-12, D-30)
    ├── Sapta Varga Vimsopaka (+D-7)
    ├── Dasa Varga Vimsopaka (+D-10, D-16, D-60)
    └── Shodasa Varga Vimsopaka (+D-4, D-20, D-24, D-27, D-40, D-45)
            │
            ▼
    Vimsopaka Bala (20-source strength per planet per scheme)
    │
    ▼
AshtakavargaComputer
    ├── BAV (Bhinna Ashtakavarga: 7 planets + lagna, 8 reference points)
    ├── SAV (Sarva Ashtakavarga: sum of all BAVs)
    ├── Rekha counting per house per planet
    ├── Trikona shodhana, Ekadhipatya shodhana
    └── Sodhya Pinda computation
```

---

## 4. Key Design Decisions

### 4.1 Immutable ChartData

`ChartData` is a frozen dataclass constructed via a builder pattern. Once built, all derived computations (dasas, strengths, yogas, transits) take `ChartData` as input. This enables:
- Caching of expensive VargaChart computations
- Thread-safe access
- Deterministic test fixture creation from JSON

### 4.2 Pluggable Dasa Architecture

Dasa engines implement `DasaBase` and register via `DasaRegistry`. New dasa systems can be added without modifying existing code. Each dasa engine handles:
1. Seed resolution (which reference point starts the dasa)
2. Lord sequence computation (order of planets/rasis)
3. Period length computation (years per lord, fractional first period)
4. Period tree subdivision (MD → AD → PD → ...)

### 4.3 Lazy Varga Computation

Varga charts are computed on demand and cached. Computing all 23 D-n levels at once is expensive; the system computes only requested vargas. `ChartData.varga_positions` is a lazy dictionary keyed by `(VargaLevel, VargaVariant)`.

### 4.4 Date/Time Handling

All internal datetime is `datetime.datetime` with `pytz` timezone. Julian Day is `float`. The `PanchangaEngine` works exclusively off JD + coordinates. Timezone conversion is handled at input/output boundaries.

### 4.5 Configuration

JSON-based config file at `~/.config/jhora/jhora.json`. Replaces `jhora.ini`. Config categories:
- `ayanamsa` — mode, custom offset
- `house_system` — Parasara/Equal/Placidus/etc.
- `planet_options` — geocentric/topocentric, true/apparent, mean/true nodes
- `upagraha_options` — definition switches (sunrise vs 6 AM, etc.)
- `strength_options` — Parasara vs Varahamihira AV, relationship scheme
- `dasa_options` — year definition, default systems
- `display` — chart style, language, colors (for future GUI)
- `ephemeris_path` — custom path to SE data files

### 4.6 Plugin/Yoga Registration

YogaDetectors and Sahama calculators use class-level registration. On import, they register with the central registry. This makes adding new yogas/sahamas trivial — just create a new file with a subclass.

---

## 5. Test Strategy

### 5.1 Test Fixtures

Pre-computed expected values from Jhora for known birth charts (e.g., the examples in help docs: Lord Rama, various worked examples in topics 19-25).

### 5.2 Testing Layers

| Layer | What to test | Example |
|---|---|---|
| Unit | Individual functions | `longitude_difference(30, 350) == 40` |
| Integration | Module interactions | `VargaChartComputer.compute(D-9, NAVAMSA_DEFAULT) == Virgo` |
| Golden | Full chart vs Jhora output | `ChartData.from_birth("1970-04-04...").planets["Sun"].longitude ≈ 0.5° Jhora output` |
| Regression | All known charts | 100+ birth charts with expected outputs |

### 5.3 Key Cross-Checks

- **Ayanamsa**: verify against known Lahiri ayanamsa tables
- **Vimsottari**: verify period start dates against help examples (topics 19-25)
- **Varga D-9 Navamsa**: verify all 4 variant types (Normal, K, KM, UKM)
- **Shadbala**: verify virupa counts match known charts

---

## 6. Implementation Order

### Phase 1 — Foundation (Week 1)
1. `jhora/types/` — all domain enums and dataclasses
2. `jhora/config/` — JSON config manager
3. `jhora/ephemeris/` — SweEngine, JulianDay, AyanamsaManager
4. `jhora/geo/` — AtlasDB (SQLite schema + ADB importer)
5. `jhora/calc/` — angles, dignities, friendship, nakshatra utilities

### Phase 2 — Chart Engine (Week 2)
6. `jhora/charts/` — ChartData, PlanetCalculator, LagnaCalculator, HouseCalculator
7. `jhora/charts/varga.py` — VargaChartComputer (all 23 levels, key variants)
8. `jhora/charts/aspect.py` + `jhora/charts/arudha.py`
9. `jhora/calendar/` — PanchangaEngine
10. `jhora/charts/visualization.py` — ASCII chart output

### Phase 3 — Analysis (Weeks 3-4)
11. `jhora/strengths/` — Shadbala (all 6 subcomponents), Vimsopaka
12. `jhora/strengths/ashtakavarga.py` — full AV system
13. `jhora/dasas/vimsottari.py`, `ashtottari.py`, `narayana.py`, `yogini.py`
14. `jhora/yogas/` — key yoga detectors (Raja, Dhana, Mahapurusha)
15. `jhora/transits/` — basic transit calculator

### Phase 4 — Specialized (Weeks 5-6)
16. Remaining dasa systems (~20 more)
17. `jhora/tajaka/`, `jhora/tithi_pravesha/`
18. `jhora/prasna/`, `jhora/muhurta/`
19. `jhora/matchmaking/`, `jhora/progressions/`
20. `jhora/sahamas/`, `jhora/chakras/`

### Phase 5 — CLI & Polish (Week 7+)
21. `jhora/cli/` — full CLI with all subcommands
22. Test suite with golden test fixtures
23. Documentation (Sphinx/mkdocs)
24. Package (pip installable)

---

## 7. Dependencies

| Package | Purpose | Required | Version |
|---|---|---|---|
| `pyswisseph` | Swiss Ephemeris bindings | Yes | ≥2.10 |
| `numpy` | Array math for planet calculations | Yes | ≥1.24 |
| `pytz` | Timezone data | Yes | ≥2023.3 |
| `typer` | CLI framework | Yes | ≥0.9 |
| `rich` | Terminal output formatting | Yes | ≥13.0 |
| `pydantic` | Data validation (ChartData, Config) | Yes | ≥2.0 |
| `orjson` | Fast JSON parsing | Optional | ≥3.9 |
| `reportlab` | PDF generation | Optional | ≥4.0 |
| `pytest` | Testing | Dev | ≥8.0 |
| `pytest-cov` | Code coverage | Dev | ≥4.1 |

---

## 8. Public API Surface

```python
# Top-level convenience API (from jhora/__init__.py)

from jhora import Chart, Varga, Dasa, Transit

# Compute chart
chart = Chart.from_birth(
    date="1970-04-04", time="17:48:20",
    tz="Asia/Kolkata", city="Chennai"
    # OR: lat=13.08, lon=80.27, tz="Asia/Kolkata"
)

# Access data
chart.planets["Sun"].longitude_deg   # 24.5 (in Taurus)
chart.planets["Moon"].nakshatra      # Nakshatra.HASTA
chart.planets["Mars"].dignity        # Dignity.OWN_RASI
chart.lagna.rasi                     # Rasi.LEO
chart.house_cusps[1]                 # 120.5 degrees
chart.varga(Varga.D_9).planet_positions["Jupiter"].rasi  # Rasi.VIRGO

# Analysis
chart.shadbala()                     # Shadbala result
chart.ashtakavarga()                 # Ashtakavarga data
chart.dasa(DasaSystem.VIMSOTTARI)    # List of DasaPeriod
chart.yogas()                        # List of active Yogas
chart.transit("2024-06-21 12:00")    # TransitAnalysis

# Derived charts
chart.tajaka(2024)                   # Annual Tajaka chart
chart.progressed(Varga.D_10, "2024-06-21")  # Progressed chart
chart.tithi_pravesha(2024)           # TP chart
chart.prasna(42)                     # Horary chart from number 42

# Panchanga
from jhora import Panchanga
p = Panchanga("2024-06-21 12:00", lat=13.08, lon=80.27)
p.tithi         # Tithi.SUKLA_DASAMI
p.nakshatra     # Nakshatra.HASTA
p.yoga          # Yoga.VISHKUMBHA
p.sunrise       # datetime(2024, 6, 21, 5, 45)

# Atlas
from jhora import Atlas
db = Atlas.open()
cities = db.search("Chennai", country="India")
# [City(name="Chennai", lat=13.08, lon=80.27, tz="Asia/Kolkata")]
```
