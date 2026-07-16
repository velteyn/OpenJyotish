# Original JHora 8.0 — Complete UI Layout Reference
## Reverse-engineered from jhora.exe binary strings (3,150 functions, PE32 MFC)

================================================================================
                           APPLICATION WINDOW LAYOUT
================================================================================

┌──────────────────────────────────────────────────────────────────────────────┐
│ MENU: File  Edit  Modes  View  Preferences  Websites  MoreMenus  Help        │
├──────────────────────────────────────────────────────────────────────────────┤
│ TOOLBAR: [New] [Open] [Save] [Print] [D-1/D-9] [Transit] [Min/Day/Hour]     │
├──────────────────────────────────────────────────────────────────────────────┤
│ TOP TABS: [Chakras] [*Basics*] [Strengths] [Dasas] [Transits] [Tajaka]      │
│           [Tithi Pravesha] [Mundane] [Miscellany]                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌── LEFT ────────────┬── CENTER ──────────────────┬── RIGHT ────────────┐  │
│  │                    │                            │                     │  │
│  │  RASI CHART (D-1)  │  PLANET TABLE + NATAL DATA │  ASHTAKAVARGA       │  │
│  │  ┌──┬──┬──┬──┐     │  ┌──────────────────────┐  │  ┌────┬────┬────┐   │  │
│  │  │SL│  │HL│BB│     │  │Body          DMS    Nk│  │  │32  │34  │36  │   │  │
│  │  │Sa│  │Ma│Md│     │  │Lagna        7Ge16 Ar│  │  ├────┼────┼────┤   │  │
│  │  ├──┼──┼──┼──┤     │  │Sun - DK     0Cn43 Pu│  │  │29  │ SAV│27  │   │  │
│  │  │GL│        │Mo│   │  │Moon - AK   27Cn06 As│  │  ├────┼────┼────┤   │  │
│  │  │Ra│  Rasi  │Ju│   │  │Mars - MK   19Ta14 Ro│  │  │21  │    │28  │   │  │
│  │  ├──┤  Chart ├──┤   │  │Merc(R)-AmK 25Ge36 Pu│  │  ├────┼────┼────┤   │  │
│  │  │  │        │Ke│   │  │Jup - GK    10Cn24 Pu│  │  │25  │30  │26  │   │  │
│  │  │  │        │Ve│   │  │Ven - PiK   14Le12 PP│  │  └────┴────┴────┘   │  │
│  │  ├──┼──┼──┼──┤     │  │Sat - BK    21Pi33 Re│  │                     │  │
│  │  │PP│  │  │  │     │  │Rahu         7Aq06 Sa│  │  BAV (8 planets)    │  │
│  │  │  │  │  │  │     │  │Ketu         7Le06 Ma│  │  [As][Su][Mo][Ma]   │  │
│  │  └──┴──┴──┴──┘     │  │Maandi       8Ge52 Ar│  │  [Me][Ju][Ve][Sa]   │  │
│  │                    │  │Gulika       0Ge45 Mr│  │  (each 4×3 grid)    │  │
│  │  NAVAMSA (D-9)     │  │Bhava Lg     3Ge12 Mr│  │                     │  │
│  │  ┌──┬──┬──┬──┐     │  │Hora Lg      5Ta41 Kr│  │  Options:           │  │
│  │  │Mo│  │Ke│Ma│     │  │Ghati Lg    13Aq09 Sa│  │  Parasara /         │  │
│  │  │  │  │Md│As│     │  │Vighati Lg  20Sg26 PS│  │  Varahamihira       │  │
│  │  ├──┼──┼──┼──┤     │  │Pranapada Lg ...     │  │                     │  │
│  │  │HL│        │Su│   │  │Bhrigu Bindu...     │  │  Kakshya detail     │  │
│  │  │Sa│ Navamsa│  │   │  │Indu Lagna   ...     │  │  (8 sub-divisions   │  │
│  │  ├──┤  Chart ├──┤   │  │Varnada Lg   ...     │  │   per sign)         │  │
│  │  │GL│        │Ve│   │  └──────────────────────┘  │                     │  │
│  │  │Ra│        │  │   │                            │                     │  │
│  │  ├──┼──┼──┼──┤     │  NATAL DATA                │                     │  │
│  │  │AL│PP│Gk│  │     │  Date: July 16, 2026       │                     │  │
│  │  │  │Ju│  │  │     │  Time: 3:39:04             │                     │  │
│  │  └──┴──┴──┴──┘     │  TZ: 4:00:00 (West of GMT) │                     │  │
│  │                    │  Place: South Grafton, MA   │                     │  │
│  └────────────────────│  Lunar Yr-Mo: Parabhava    │                     │  │
│                       │  Tithi: Sukla Tritiya (Ma) │                     │  │
│                       │  Vedic Day: Wednesday (Me) │                     │  │
│                       │  Nakshatra: Aashresha (Me) │                     │  │
│                       │  Yoga: Siddhi (Ma)         │                     │  │
│                       │  Karana: Taitula (Me)      │                     │  │
│                       │  Hora Lord: Moon           │                     │  │
│                       │  Sunrise: 5:29:07          │                     │  │
│                       │  Sunset: 20:16:02          │                     │  │
│                       │  Janma Ghatis: 55.4143     │                     │  │
│                       │  Ayanamsa: 23-05-34.92     │                     │  │
│                       │  Sid Time: 22:28:59         │                     │  │
│                       └────────────────────────────│                     │  │
│                                                    └─────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘


================================================================================
                          TAB 1: CHAKRAS — Sub-tabs
================================================================================

┌──────────────────────────────────────────────────────────────────────────┐
│ [Many Vargas] [Mixed 2-Vargas] [Kalachakra] [Sarvatobhadra] [Kota]      │
│ [Surya Kalanala] [Chandra Kalanala] [Sudarsana] [Shoola] [Tripataki]    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     MANY VARGAS (3×4 Grid)                       │   │
│  │                                                                  │   │
│  │  ┌──────────┬──────────┬──────────┬──────────┐                   │   │
│  │  │ Rasi     │ Navamsa  │ Trimsamsa│ Drekkana │                   │   │
│  │  │ (D-1)    │ (D-9)    │ (D-30)   │ (D-3)    │                   │   │
│  │  │ ┌──┬──┐  │ ┌──┬──┐  │ ┌──┬──┐  │ ┌──┬──┐  │                   │   │
│  │  │ │Su│Mo│  │ │  │  │  │ │  │  │  │ │  │  │  │                   │   │
│  │  │ ├──┼──┤  │ ├──┼──┤  │ ├──┼──┤  │ ├──┼──┤  │                   │   │
│  │  │ │Ma│Me│  │ │  │  │  │ │  │  │  │ │  │  │  │                   │   │
│  │  │ └──┴──┘  │ └──┴──┘  │ └──┴──┘  │ └──┴──┘  │                   │   │
│  │  ├──────────┼──────────┼──────────┼──────────┤                   │   │
│  │  │ Dasamsa  │Shashtyam │ Saptamsa │Dwadasamsa│                   │   │
│  │  │ (D-10)   │ (D-60)   │ (D-7)    │ (D-12)   │                   │   │
│  │  ├──────────┼──────────┼──────────┼──────────┤                   │   │
│  │  │ Vimsamsa │ Siddhamsa│Shodasamsa│ Hora     │                   │   │
│  │  │ (D-20)   │ (D-24)   │ (D-16)   │ (D-2)    │                   │   │
│  │  └──────────┴──────────┴──────────┴──────────┘                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  OTHER SUB-TABS:                                                         │
│  Kalachakra:    9×9 wheel showing Moon's navamsa progression             │
│  Sarvatobhadra: 9×9 nakshatra grid with vedha (obstruction) lines       │
│  Kota Chakra:   4 concentric fort squares + exterior for protection      │
│  Surya/Chandra  Solar/lunar fire wheels for transit impact               │
│  Sudarsana:     Chakra wheel for annual/monthly/daily prediction         │
│  Shoola:        Trident chart — ayur (longevity) analysis                │
│  Tripataki:     Triangular chart                                         │
│                                                                          │
│  Chart styles: South Indian regular, South Indian irregular,             │
│                North Indian, East Indian                                 │
│                                                                          │
│  Two charts can be superimposed (e.g., natal navamsa + transit dasamsa) │
└──────────────────────────────────────────────────────────────────────────┘


================================================================================
                          TAB 2: BASICS — as shown above
================================================================================

================================================================================
                          TAB 3: STRENGTHS
================================================================================

┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─ Shadbala ────────────────────────────────────────────────────────┐  │
│  │ Planet  Sthana  Dig  Kala  Chesta  Naisarg  Drik  Total(R) Total(V)│  │
│  │ Sun     4.11   1.00  2.01  0.50    1.00     0.00  8.62     517    │  │
│  │ Moon    4.47   0.50  2.70  0.43    0.86     0.25  9.21     552    │  │
│  │ ...                                                                │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Bhava Bala ───────────────────────┐ ┌─ Vimsopaka Bala ────────────┐ │
│  │ H  Sign  Sth  Dri  Dig  Adh  Total │ │ Planet  Sadv  Saptv Dashv    │ │
│  │ 1  Vi    60   30   60   23   173   │ │ Sun     14.5 12.8  8.8      │ │
│  │ 2  Li    30   60   50   0    132   │ │ Moon    11.0 11.0  9.0      │ │
│  │ ...                                │ │ ...                         │ │
│  └────────────────────────────────────┘ └──────────────────────────────┘ │
│                                                                          │
│  ┌─ Additional Strengths ─────────────────────────────────────────────┐ │
│  │ Vaiseshikamsa:     Shadvarga (6), Saptavarga (7), Dashavarga (10), │ │
│  │                    Shodasavarga (16) — Parijata→Brahmaloka ranks   │ │
│  │ Ishta/Kashta Phala: Beneficence vs maleficence per planet          │ │
│  │ Pancha Vargeeya:    5-fold Tajaka strength                         │ │
│  │ Dwadasa Vargeeya:   12-fold Tajaka strength                        │ │
│  │ Avasthas:           Sayanadi (lying→fighting), Alertness, Mood,    │ │
│  │                     Basic (age-based: infant→dead)                  │ │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘


================================================================================
                             TAB 4: DASAS
================================================================================

┌──────────────────────────────────────────────────────────────────────────┐
│  DASA SELECTOR: [Vimsottari ▼]  Options...  [Find Dasa]  [Dasa Pravesh] │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─ Nakshatra Dasas (11) ─────────────────────────────────────────────┐ │
│  │ Vimsottari (120yr) — universal, from Moon's nakshatra               │ │
│  │ Ashtottari (108yr) — conditional, Rahu in kendra/trikona            │ │
│  │ Kalachakra — Moon's navamsa progression, 9 navamsa MDs              │ │
│  │ Yogini (36yr) — 8 Yoginis: Mangala, Pingala, Dhanya, Bhramari...   │ │
│  │ Yogini (Vara) — weekday-based variation                             │ │
│  │ Dwisaptati Sama (72yr) — conditional                                │ │
│  │ Shattrimsa Sama (36yr) — conditional                                │ │
│  │ Shodasottari (16yr) — lagna in Moon's/Sun's hora                    │ │
│  │ Dwadasottari (12yr) — from Venus's nakshatra                        │ │
│  │ Panchottari (5yr) — lagna in Cancer in rasi+D-12                    │ │
│  │ Shashtihayani (60yr) — Sun in lagna                                 │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Rasi Dasas (~15) ─────────────────────────────────────────────────┐ │
│  │ Narayana (all Vargas) — universal progression                       │ │
│  │   Lagnamsaka Dasa — variant                                        │ │
│  │   Padanadamsa Dasa — variant                                       │ │
│  │ Chara Dasa — Parasara + K.N. Rao versions                          │ │
│  │ Sthira Dasa — fixed sign progression                                │ │
│  │ Sudasa — Sree Lagna Kendradi                                       │ │
│  │ Drigdasa — aspect-based, spiritual evolution                       │ │
│  │ Shoola Dasa — from any house, ayur indicator                       │ │
│  │ Trikona Dasa — trinal progression                                   │ │
│  │ Yogardha Dasa                                                       │ │
│  │ Brahma Dasa                                                         │ │
│  │ Navamsa Dasa                                                        │ │
│  │ Varnada Dasa                                                        │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Other Dasas ──────────────────────────────────────────────────────┐ │
│  │ Moola Dasa — planetary, past karma roots                            │ │
│  │ Tara Dasa — conditional if all 4 quadrants occupied                 │ │
│  │ Sudarsana Chakra Dasa — annual/monthly/daily fortune                │ │
│  │ Rasi-Bhukta Vimsottari — rasis used for AD                          │ │
│  │ Tithi Ashtottari — tithi-based, good for TP charts                  │ │
│  │ Tithi Yogini — tithi-based                                          │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Dasa Features ────────────────────────────────────────────────────┐ │
│  │ Start from: Moon/Lagna star, Kshema/Utpanna/Adhana taras,          │ │
│  │ Maandi, Gulika, Trisphuta, Sun, Bhrigu Bindu, Pranapada Lagna     │ │
│  │ Levels: MD → AD → PD → SD → PAD → DAD (6 levels)                   │ │
│  │ Year types: 365.2425 solar, 360-day, custom, tithi-based, Sun-angle│ │
│  │ Dasa Pravesh: chart at start of any period for fine timing          │ │
│  │ Transit search: find transits during dasa periods                   │ │
│  │ Tribhagi: each dasa divided into 3 parts for finer division         │ │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘


================================================================================
                            TAB 5: TRANSITS
================================================================================

┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─ Transit Table ─────────────────────────────────────────────────────┐ │
│  │ Planet  Transit Sign  House  SAV  Fav  Vedha  Tara  Special         │ │
│  │ Sun     Gemini        11     36   ✓    —      Janma N/A             │ │
│  │ Moon    Cancer        12     0    ✗    Sat    Sampat N/A            │ │
│  │ ...                                                                  │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Reference points: Lagna, Moon, Navamsa Lagna, Navamsa Moon              │
│                                                                          │
│  Transit analysis:                                                       │
│    - Ashtakavarga scores (SAV + Kakshya)                                 │
│    - Tara-based: Navatara from Moon + Lagna                              │
│    - Special taras: Karma, Samudayika, Sanghatika, Jaati, Desa          │
│    - Nakshatra aspects of transiting planets                             │
│    - Latta (planetary kick) on important nakshatras                      │
│    - Vedha: obstruction analysis                                         │
│                                                                          │
│  ┌─ Graphical Transit Calendar ───────────────────────────────────────┐ │
│  │ Month view with colored cells showing all transit scores            │ │
│  │ Rows: planets   Cols: dates   Colors: green=good, red=bad           │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Transit Search ───────────────────────────────────────────────────┐ │
│  │ "When does Jupiter reach 1° behind natal Sun?"                      │ │
│  │ "When does Saturn enter Scorpio before 2027?"                       │ │
│  │ Search by: planet degree, sign ingress, aspect to natal             │ │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘


================================================================================
                    TAB 6: TAJAKA — Sub-tabs
================================================================================

┌──────────────────────────────────────────────────────────────────────────┐
│ [Annual] [Monthly] [2.5-day] [5-hr] [25-min] [2-min]                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─ Annual Tajaka Chart ──────────────────────────────────────────────┐ │
│  │ Varsha Pravesh (Sun return to natal longitude)                      │ │
│  │ ┌──────────────────────────────────────────────────────────────┐   │ │
│  │ │ Planet  Tajaka Sign  Deg    Natal Sign  Deg    Diff          │   │ │
│  │ │ Sun     Aries        21.2°  Aquarius     329.3° —            │   │ │
│  │ │ ...                                                            │   │ │
│  │ └──────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Tajaka Components ────────────────────────────────────────────────┐ │
│  │ Muntha: progressed lagna (1 sign per year from natal lagna)        │ │
│  │ Harsha Bala: 4-source cheerfulness strength                        │ │
│  │ Pancha Vargeeya Bala: 5-fold strength for Tajaka                   │ │
│  │ Dwadasa Vargeeya Bala: 12-fold strength                            │ │
│  │ Patyayini Dasa: compressed dasa (krisamsa/patyamsa)                │ │
│  │ Mudda/Vimsottari Dasa: compressed Vimsottari for the year          │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Options:                                                                │
│    - True solar motion or mean solar motion for Sun return               │
│    - Dasa compression from lagna/Moon star or progressed                 │
│    - Sunrise chart variant for all periods                               │
│    - Muntha from each varga chart, various AD start options              │
└──────────────────────────────────────────────────────────────────────────┘


================================================================================
                     TAB 7: TITHI PRAVESHA
================================================================================

┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─ Annual Tithi Pravesha ─────────────────────────────────────────────┐ │
│  │ When Sun returns to birth tithi angle + solar month                  │ │
│  │ ┌──────────────────────────────────────────────────────────────┐   │ │
│  │ │ Year  Date (UT)           Lagna  Sun    Moon   Tithi Angle   │   │ │
│  │ │ 2025  2025-03-08 09:21   Ta     Aq     Ge     110.87°       │   │ │
│  │ │ 2026  2026-02-26 03:21   Sg     Aq     Ge     110.84° ◀     │   │ │
│  │ └──────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Yoga Pravesha (YP) ───────────────────────────────────────────────┐ │
│  │ When Sun-Moon yoga angle returns to birth yoga                       │ │
│  │ Annual + Monthly charts                                              │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Nakshatra Pravesha (NP) ──────────────────────────────────────────┐ │
│  │ When Moon returns to birth nakshatra                                 │ │
│  │ Annual + Monthly charts                                              │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Options: Solar month used for TP month start (Sun sign change)          │
│           True solar motion vs mean solar motion                         │
│           Dasa compression options                                       │
└──────────────────────────────────────────────────────────────────────────┘


================================================================================
                         TAB 8: MUNDANE
================================================================================

┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─ Solar Ingress Charts ──────────────────────────────────────────────┐ │
│  │ Mesha Sankranti (Aries ingress) — annual world chart                │ │
│  │ Makara Sankranti (Capricorn ingress) — alternative new year         │ │
│  │ Solar month chart (each sign ingress with compressed dasas)         │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Lunar Charts ──────────────────────────────────────────────────────┐ │
│  │ Annual Full Moon chart (Vaisakha Purnima)                           │ │
│  │ Monthly Full Moon chart                                             │ │
│  │ Lunar new year / new month / new day charts                         │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Financial New Year ────────────────────────────────────────────────┐ │
│  │ Chart for financial year start with compressed dasas                │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Conjunctions & Oppositions ────────────────────────────────────────┐ │
│  │ Find last/next conjunction of any two planets                       │ │
│  │ Find last/next opposition of any two planets                        │ │
│  │ Compress dasas to period between two successive conjunctions        │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Eclipses ──────────────────────────────────────────────────────────┐ │
│  │ Last/next lunar eclipse                                             │ │
│  │ Local solar eclipse (for specific coordinates)                      │ │
│  │ Global solar eclipse                                                │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Planet Ingress ────────────────────────────────────────────────────┐ │
│  │ Find when a planet changes sign/nakshatra/navamsa/any varga         │ │
│  │ Compress dasas to period planet stays in that division              │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Features: "Swearing-in" mode — compress dasas to any years/days        │
│            Add time to go to next lifecycle (useful for country charts) │
└──────────────────────────────────────────────────────────────────────────┘


================================================================================
                       TAB 9: MISCELLANY
================================================================================

┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─ Progressions ──────────────────────────────────────────────────────┐ │
│  │ Solar progression: Sun moves 1 division per varga chart              │ │
│  │ D-30 progression: 1° per year, D-10: 3° per year, etc.             │ │
│  │ Next lifecycle: add 144 years to cast next-life chart               │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Prasna (Horary) ───────────────────────────────────────────────────┐ │
│  │ Prasna-108: number 1-108 → rasi + navamsa lagna                     │ │
│  │ Prasna-249 (KP): number 1-249 → rasi + nakshatra + sub              │ │
│  │ Prasna-1800 (KP): number 1-1800 → all 16 varga positions            │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Krishnamoorthy Paddhati (KP) ──────────────────────────────────────┐ │
│  │ Nakshatra sub-lords up to 5 levels (sub, sub-sub, etc.)             │ │
│  │ List planets occupying nakshatra/sub of any planet                   │ │
│  │ All planets + house cusps analyzed                                   │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Panchanga ─────────────────────────────────────────────────────────┐ │
│  │ Daily: tithi end times, yoga end times, karana end times            │ │
│  │        24 horas, Rahu/Gulika/Yama kalam, sunrise/sunset             │ │
│  │        Moon sign change time, moonrise/moonset                      │ │
│  │ Monthly: full month calendar                                        │ │
│  │ Ephemeris: monthly planet positions                                 │ │
│  │ Gouri Panchanga / Choghadiya                                        │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Special Points ────────────────────────────────────────────────────┐ │
│  │ Upagrahas: Gulika, Maandi, Kala, Mrityu, Arthaprahara, Yama,       │ │
│  │            Dhuma, Vyatipata, Parivesha, Indrachaapa, Upaketu        │ │
│  │ Arudhas: AL + 11 bhava, Chandra/Surya arudhas, Graha arudhas        │ │
│  │ Special: Kunda, Yogi/Sahayogi/Avayogi, Trisphuta, 64th Navamsa      │ │
│  │          22nd Drekkana, Bhrigu Bindu, Mrityu Bhaga, Pushkara Bhaga  │ │
│  │ Tithis: Janma, Dhana, Bhratri, Matri etc. (special tithis)          │ │
│  │ Taras: Navatara, Kshema, Utpanna, Adhana, Karma, Samudayika, etc.   │ │
│  │ Nakshatra aspects of planets, Latta (kick) on nakshatras             │ │
│  │ Chara karakas: 8 + 7 schemes, Brahma/Rudra/Maheswara                │ │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Learning Aids ─────────────────────────────────────────────────────┐ │
│  │ Marana Karaka Sthana: planets in death-inflicting houses             │ │
│  │ Planetary relationships: permanent + temporary + compound            │ │
│  │ Pachakadi relationships: planet-sign 5-fold analysis                 │ │
│  │ Graha drishti + Rasi drishti highlighting                            │ │
│  │ Argala + Virodha Argala highlighting                                 │ │
│  │ Highlighted: own signs, exaltation, debilitation, moolatrikona      │ │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘


================================================================================
                       MENU BAR STRUCTURE
================================================================================

  File ─────────────────────────────────────────────────────────────────────
    New         — Create new chart
    Open        — Load .jhd file
    Save        — Save .jhd file
    Save As     — Save with new name
    Print       — Print current chart
    Exit        — Quit application
  ─────────────────────────────────────────────────────────────────────────
  Edit ─────────────────────────────────────────────────────────────────────
    Undo / Redo / Copy / Paste
  ─────────────────────────────────────────────────────────────────────────
  Modes ────────────────────────────────────────────────────────────────────
    Chart display mode toggles, overlay options
  ─────────────────────────────────────────────────────────────────────────
  View ────────────────────────────────────────────────────────────────────
    Zoom level, chart style (S/N/E Indian), language selection
  ─────────────────────────────────────────────────────────────────────────
  Preferences ──────────────────────────────────────────────────────────────
    Ayanamsa: Lahiri, Raman, Deva-datta, Krishnamurti, Usha-Shashi,
              Fagan, Tropical, Custom (user-defined value)
    Year type: 365.2425 solar, 360-day, tithi-based, user-defined
    Sunrise definition: true center, true tip, apparent tip
    Geocentric / Topocentric toggle
    True / Apparent positions toggle
    Mean / True nodes toggle
    Chart colors: fully customizable for every element
    Font size: adjustable
    Header text for printouts (name, address, phone)
    Language: 10 Indian languages for planet/sign names
    Planet/sign naming: English (Sun, Ar) or Sanskrit (Surya, Mesha)
    Note saving: per-chart notes
  ─────────────────────────────────────────────────────────────────────────
  Websites ─────────────────────────────────────────────────────────────────
    Links to Vedic astrology online resources
  ─────────────────────────────────────────────────────────────────────────
  MoreMenus ────────────────────────────────────────────────────────────────
    Additional specialized command groups
  ─────────────────────────────────────────────────────────────────────────
  Help ────────────────────────────────────────────────────────────────────
    About, textbook reference, help topics
  ─────────────────────────────────────────────────────────────────────────


================================================================================
                       COVERAGE GAP ANALYSIS
================================================================================

  FEATURE                                JHORA   OURS   GAP
  ─────────────────────────────────────  ─────   ────   ───────────────────
  MAIN VIEW
  ──────────────────────────────────────────────────────────────────────────
  Three-column consolidated view         ✓       ✓      Special lagna labels
  Planet table with DMS format           ✓       ✓      —     
  Karaka suffixes (DK, AK, etc.)         ✓       ✓      —
  Navamsa column in planet table         ✓       ✓      —
  Complete natal data panel              ✓       ✓      Lunar year, hora lord, 
                                                       sidereal time missing
  Ashtakavarga SAV + BAV all at once     ✓       ✓      —
  ──────────────────────────────────────────────────────────────────────────
  DASAS — we have 12 systems, JHora has ~30
  ──────────────────────────────────────────────────────────────────────────
  Nakshatra dasas (11 total)             ✓       7      Dwisaptati, Shattrimsama,
                                                       Chaturaseeti, Sataabdika
  Rasi dasas (~15 total)                 ✓       7      Lagnamsaka, Padanadamsa,
                                                       Drigdasa, Shoola, Trikona,
                                                       Brahma, Navamsa, Varnada
  Other dasas                            6       3      Sudarsana Chakra,
                                                       Rasi-Bhukta Vimsottari,
                                                       Tithi Ashtottari/Yogini
  ──────────────────────────────────────────────────────────────────────────
  CHAKRAS — we have 2, JHora has 9
  ──────────────────────────────────────────────────────────────────────────
  Kalachakra                            ✓       ✗
  Sarvatobhadra                         ✓       ✓
  Kota Chakra                           ✓       ✓
  Surya Kalanala                        ✓       ✗
  Chandra Kalanala                      ✓       ✗
  Sudarsana Chakra                      ✓       ✗
  Shoola Chakra                         ✓       ✗
  Tripataki Chakra                      ✓       ✗
  ──────────────────────────────────────────────────────────────────────────
  SPECIAL POINTS — partial coverage
  ──────────────────────────────────────────────────────────────────────────
  Upagrahas (11 total)                  ✓       7      Kala, Mrityu, Arthaprahara,
                                                       Yama missing
  Arudhas (bhava + Chandra + Surya      ✓       Bhava  Chandra/Surya arudhas 
   + graha + dual graha)                        only   missing
  Kunda                                 ✓       ✗
  Yogi / Avayogi / Sahayogi             ✓       ✗
  Trisphuta (Deha/Prana/Mrityu)         ✓       ✗
  64th Navamsa, 22nd Drekkana           ✓       ✗
  Bhrigu Bindu                          ✓       ✓
  Mrityu Bhaga / Pushkara Bhaga         ✓       ✗
  ──────────────────────────────────────────────────────────────────────────
  OTHER
  ──────────────────────────────────────────────────────────────────────────
  Progressions (D-n based)              ✓       Partial Secondary only
  KP system (5 sub-lord levels)          ✓       ✓
  Learning aids (relationships,         ✓       Partial Marana + KP done,
   argala, marana karaka)                               rest missing
  Monthly panchanga                     ✓       ✓
  Gouri Panchanga / Choghadiya          ✓       Partial Day only
  Custom divisional D-m×D-n             ✓       ✗
  Chart superimposition                 ✓       ✗
  Dasa Pravesh charts                   ✓       ✗
  Transit search (exact degree)         ✓       ✗
  Graphical transit calendar            ✓       ✗
  Ayanamsa: 20 modes                    ✓       ✓
  Custom ayanamsa                       ✓       ✗
  3 sunrise definitions                 ✓       ✗
  Geocentric/Topocentric toggle         ✓       ✗
  True/Apparent positions toggle        ✓       ✗
  10 Indian languages                   ✓       ✗
  Customizable colors                   ✓       ✗
  Mix&Match chart styles (two at once)  ✓       ✗
  Per-chart notes                       ✓       ✓ (DB)
  ──────────────────────────────────────────────────────────────────────────
  ESTIMATED COVERAGE: ~82% of original JHora 8.0

================================================================================
               RIGHT-CLICK CONTEXT MENUS & CLIPBOARD
================================================================================

Right-click on chart or table → "Copy chart calculations into the clipboard"
Format: plain text with all computed data
Messages:
  "Copied basic chart calculations into the clipboard as text."
  "Copied chart calculations into the clipboard as text. 
   You can paste it into other programs that accept text."
  "Successfully copied the required text to the clipboard"
  "Successfully Copied!"
  "Copied in plain text format!"


================================================================================
               CHART DISPLAY TOGGLES (Show/Hide)
================================================================================

All items can be toggled on/off in the chart display:
  ShowALInCharts          — Arudha Lagna
  ShowBBInCharts          — Bhrigu Bindu  
  ShowGLInCharts          — Ghati Lagna
  ShowHLInCharts          — Hora Lagna
  ShowSLInCharts          — Sree Lagna
  ShowPPInCharts          — Pranapada Lagna
  ShowGulikaInCharts      — Gulika upagraha
  ShowMandiInCharts       — Maandi upagraha
  ShowNodesInCharts       — Rahu/Ketu nodes
  ShowOtherArudhasInCharts — Other arudha padas
  ShowOuterPlanetsInCharts — Uranus/Neptune/Pluto
  ShowUserPointsInCharts  — User-defined custom points


================================================================================
               PREFERENCES DIALOG — COLOR CUSTOMIZATION
================================================================================

Every element color is configurable (~110 individual color settings):

  CHART VIEW:               DASA VIEW:               KOTA CHAKRA VIEW:
  - CartBackground          - Background             - Outer/Wall/Inner/Pillar
  - ChartLine               - Header                 - Frame
  - Frame                   - Date                   - StarName
  - Planet                  - DasaOwner              - BeneficPlanetName
  - Lagna                   - Time                   - MaleficPlanetName
  - AL (Arudha Lagna)       - Year                   - PaalaName (fort guard)
  - SpecialLagna            - Focus (current period)  - SwamiName (fort lord)
  - Upagraha                - Hint                   - AreaName
  - CharaKaraka             - Hyphen                  
  - Varnada                                           
  - OuterPlanets             STRENGTHS VIEW:           KALACHAKRA VIEW:
  - SpecialPoint             - Background             - BodyName
  - BhavaArudha              - GraphBackground        - StarName
  - GrahaArudha              - Bar                    - DikpalaName
  - StartRasi                - Outline                - Frame/Line
  - HighlightedRasi          - ItemName
  - SelectedPlanet           - Title                  SARVATOBHADRA VIEW:
  - SelectedRasi             - Value                  - Frame, Nakshatra
  - Hint                                                - Planet, Rasi
  PLANT RELATIONSHIPS:       TRANSIT SEARCH:           - Consonant, Vowel
  - Mitra (friend)           - Background Good/Bad     - Tithi, Vaara
  - Adhimitra (best friend)  - Date, Frame             - HighlightFrom/To
  - Sama (neutral)           - Planet                  - SpecialPoint
  - Satru (enemy)            - Moon
  - Adhisatru (worst enemy)  - Swarna/Gold, Rajata/Silver
                              - Taamra/Copper, Loha/Iron
  AV (ASHTAKAVARGA) VIEW:    - Vedha (obstruction)      
  - CartBackground           - LegendText, Title
  - ChartLine/Text/Title     
  - Frame/Header             LIST VIEWS:
  - Help                     - Background (odd/even)
  - Highlight                - Highlight
  - StarRasiNorthIndian       - Item/Title/Description

  PANCHANGA VIEW:            CORE VIEW (natal data):
  - Background               - Background
  - Frame                    - Header
  - Text                     - ItemDescription
  - Wait                     - ItemValue

Additional preferences:
  - ChartStyle (0=S Indian regular, 1=S Indian irregular, 2=North, 3=East)
  - ChartStyle2 (secondary chart style for dual display)
  - Font size adjustable
  - Header text for printouts
  - Language: 10 Indian languages
  - Planet/sign naming: English or Sanskrit
  - Preferences can be exported/imported via .ini files


================================================================================
               DASA CONFIGURATION DIALOG OPTIONS
================================================================================

Dasa Start Options (for each dasa system):
  From Moon's nakshatra (default)
  From Lagna's nakshatra
  From Kshema tara (4th star)
  From Utpanna tara (5th star)
  From Adhana tara
  From Maandi's star
  From Gulika's star
  From Trisphuta's star
  From Sun's star
  From Bhrigu Bindu's star
  From Pranapada Lagna's star
  From planets occupying various stars

Year Types:
  365.2425-day solar year
  360-day year
  User-defined custom year (e.g., 327-day)
  Solar longitude-based year (Sun angle measure)
  360-tithi year (Sun-Moon angle progress)

Dasa Levels to Display:
  Mahadasa (MD)         — always shown
  Antardasa (AD)
  Pratyantardasa (PD)  
  Sookshma-Antardasa (SD)
  Prana-Antardasa (PAD)
  Deha-Antardasa (DAD)  — maximum 6 levels

Antardasa Order Options (for Kalachakra):
  F, G, H, A, B, C, D, E (start from dasa lord, forward)
  F, E, D, C, B, A, H, G (start from dasa lord, backward)
  E, F, G, H, A, B, C, D (start from previous lord, forward)
  E, D, C, B, A, H, G, F (start from previous lord, backward)
  G, F, E, D, C, B, A, H (start from next lord sign, backward)

Kalachakra Dasa Sesham Options (5 methods):
  1. Apply sesham to first dasa in cycle. ADs from MD by iteration.
  2. Sesham to full cycle. MDs jump to next cycle. ADs from 9 signs.
  3. Sesham to full cycle. At end, go back to start (leaps per Pararsara).
  4. Sesham to full cycle. ADs from MD (not from cycle).
  5. Sesham to first dasa. ADs can jump to next cycle for continuity.

Tribhagi Variation: Available in Vimsottari and most nakshatra dasas
  Each dasa divided into 3 equal parts for finer timing


================================================================================
               AVASHTA (PLANETARY STATE) SYSTEM
================================================================================

Basic (Age-based):                Sayanadi (Activity-based):
  Baala  — infant                 Sayana — lying down
  Yuva   — young                  Upavesana — sitting
  Vriddha — old                   Nidra — sleeping
  Mrita  — dead                   (others: standing, fighting etc.)

Alertness-based:                  Mood-based:
  (awake, drowsy, asleep...)      (cheerful, gloomy, angry...)

Transit Murthis (golden forms):
  Swarna  — golden (best)
  Rajata  — silver
  Taamra  — copper
  Loha    — iron (worst)


================================================================================
               PROGRESSION TYPES
================================================================================

Three progression systems available:
  1. Bhrigu Pada Progression — Sun progressed by one division per varga
  2. Kalachakra Dasa Based Progression — uses dasa cycle for progression
  3. Sudarsana Chakra Dasa Based Progression — lagna/Moon/Sun at 1 sign/yr

For each progression, the chart is displayed as a standard chart with all
standard calculations (planets, houses, strengths, etc.) but only the
physical and divisional longitudes of the progressed bodies are accurate.


================================================================================
               TAJAKA SUB-TABS DETAIL
================================================================================

┌──────────────────────────────────────────────────────────────────────────┐
│ [Annual] [Monthly] [2.5-day] [5-hr] [25-min] [2-min]                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ Options per sub-tab:                                                     │
│   - True solar motion vs Mean solar motion for Sun return               │
│   - TropicalTajaka: use tropical zodiac for return calculation           │
│   - TrueTajaka: use true planetary positions                             │
│   - Dasa compression from lagna/Moon star OR progressed                  │
│   - Sunrise chart variant available                                      │
│   - Muntha display: from each varga OR rasi only, ADs from dasa         │
│     lord OR dasa sign                                                    │
│   - Patyayini Dasa: compressed dasa with lagna as a dasa lord            │
│   - Mudda/Vimsottari Dasa: compressed Vimsottari for the period          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘


================================================================================
               MUNDANE — DASA COMPRESSION MODES
================================================================================

"Swearing-in" mode: compress dasas to any number of years or days.
Used for country charts, organization charts, etc.

Dasa compression steps:
  1. Solar New Year (Aries/Capricorn ingress) — compress to 1 year
  2. Solar New Month — compress to 1 month
  3. Annual Full Moon — compress to 1 year  
  4. Monthly Full Moon — compress to 1 month
  5. Lunar New Year/Month/Day — compress accordingly
  6. Conjunction-to-conjunction — compress to period between
  7. Planet-in-sign period — compress to planet's stay in sign
  8. Custom: any number of years or days

Time addition: add user-defined years to go to "next lifecycle"
for mundane charts (e.g., USA chart + 144 years)

SpecialYearForTajaka / SpecialYearForTP options available


================================================================================
               PREFERENCES FULL LIST
================================================================================

Main Categories:
  ┌─────────────────────────────────────────────────────────────────────┐
  │ Ayanamsa:                                                           │
  │   Lahiri (True/Chitrapaksha)   Raman        Krishnamoorthy (KP)     │
  │   Fagan-Bradley               Usha-Shashi  Deva-datta (De Luce)     │
  │   Yukteshwar                  JN Bhasin                            │
  │   SSS (True Citra)            True Pushya  True Revati              │
  │   Aldebaran 15Tau             Surya Siddhanta                       │
  │   Aryabhata (2 variants)      Hipparchos                            │
  │   Sassanian                   Galactic Center (4 variants)          │
  │   Tropical (Sayana)           Custom (user-defined value)           │
  │                                                                    │
  │ Positions:                                                          │
  │   Geocentric vs Topocentric                                         │
  │   True vs Apparent positions                                        │
  │   Mean vs True nodes                                                │
  │   ApparentRefraction on/off                                         │
  │                                                                    │
  │ Sunrise Definition:                                                 │
  │   1. True rise of center                                            │
  │   2. True rise of tip                                               │
  │   3. Apparent rise of tip                                           │
  │                                                                    │
  │ Year Definition:                                                    │
  │   365.2425 solar year | 360-day | custom | tithi-based | Sun-angle │
  │                                                                    │
  │ Chart Style:                                                        │
  │   South Indian Regular | South Indian Irregular                     │
  │   North Indian (diamond) | East Indian (Sun chart) + framed variant │
  │                                                                    │
  │ Dual Display (ChartStyle2):                                         │
  │   Show two chart styles simultaneously (e.g., N Indian + S Indian) │
  │                                                                    │
  │ Languages:                                                          │
  │   10 Indian languages for planet/sign names                         │
  │   English (Sun, Ar) or Sanskrit (Surya, Mesha)                      │
  │                                                                    │
  │ Varga Amsa Rulers:                                                  │
  │   Shodasa varga amsa rulers as per Parasara                         │
  │   Compound vs Permanent relationships toggle                        │
  │   Rasi chart relationships vs divisional chart relationships        │
  │                                                                    │
  │ Special Year Settings:                                              │
  │   SpecialYearForTajaka — override Tajaka year                       │
  │   SpecialYearForTP — override Tithi Pravesha year                   │
  │                                                                    │
  │ Miscellaneous:                                                      │
  │   Show chart based on houses from: Lagna/Moon/Sun                   │
  │   CharaKarakaDefinition — 7 or 8 karaka scheme                     │
  │   LunarYrDef / LunarYrSign / SolarYrSign — year starting definitions│
  │   HoraPreference — sunrise or 6am LMT for horas                     │
  │   Start of day: sunrise or 6am LMT for weekdays/horas               │
  └─────────────────────────────────────────────────────────────────────┘


================================================================================
               FINAL GAP SUMMARY
================================================================================

COVERED (~82%):
  ✓ Rasi chart + all 23 varga charts
  ✓ 12 dasa systems (of ~30)
  ✓ 7-planet Shadbala + Bhava Bala + Vimsopaka Bala  
  ✓ 200+ yogas, Ashtakavarga, Arudha (bhava + graha)
  ✓ Chara karakas (8+7 schemes), 36 sahamas
  ✓ Transits with Ashtakavarga + Tara
  ✓ Tajaka (annual/monthly/2.5-day/5-hr/25-min/2-min)
  ✓ Tithi Pravesha (annual + monthly)
  ✓ Mundane (Aries/Capricorn ingress, eclipses, conjunctions)
  ✓ Prasna (108/249/1800 modes), Muhurta (11 tasks)
  ✓ KP sub-lords (5 levels)
  ✓ Progressions (secondary), Sarvatobhadra + Kota chakras
  ✓ Special lagnas (5), Upagrahas (7 solar + Gulika/Mandi)
  ✓ Matchmaking (10 Porutham + Ashta Koota)
  ✓ Panchanga (daily + monthly), Ephemeris
  ✓ HTML export, Atlas (34K cities), Chart browser (SQLite)
  ✓ AI interpretation + AI Teacher + Knowledge base (FTS5)
  ✓ 20 ayanamsas, 3 chart styles, 3-column consolidated view

NOT YET COVERED (~18%):
  ✗ Kalachakra / Sudarsana / Shoola / Tripataki / Surya-Kalanala / 
    Chandra-Kalanala chakras
  ✗ ~18 additional dasa systems (Lagnamsaka, Padanadamsa, Drigdasa,
    Trikona, Brahma, Navamsa, Varnada, Moola, Tara, Sudarsana Chakra,
    Rasi-Bhukta Vimsottari, Tithi Ashtottari/Yogini, etc.)
  ✗ Dasa Pravesh charts (period commencement charts)
  ✗ Chart superimposition (two charts overlaid)
  ✗ Custom divisional charts (D-m×D-n, D-N for any N)
  ✗ Special points: Chandra/Surya arudhas, Kunda, Trisphuta, 
    Yogi/Avayogi/Sahayogi, 64th Navamsa, 22nd Drekkana
  ✗ Upagrahas: Kala, Mrityu, Arthaprahara, Yama (time-based)
  ✗ Special lagnas: Varnada×12, Indu Lagna (financial)
  ✗ Ishta/Kashta Phala with full dignity weighting
  ✗ Avasthas: Sayanadi, Alertness, Mood, Age-based states
  ✗ Learning aids: Argala/Virodha Argala, Pachakadi relationships,
    permanent/temporary/compound relationships display
  ✗ Graphical transit calendar (colored month grid)
  ✗ Transit exact-degree search engine
  ✗ Taras: special taras (Karma, Samudayika, etc.), Nakshatra aspects,
    Latta (planetary kick)
  ✗ Tithis: special tithis (Janma, Dhana, Bhratri, Matri, etc.)
  ✗ Bhava/Chalit for all 23 varga charts (currently D-1 + D-9 only)
  ✗ Progression types: Bhrigu Pada, Kalachakra-based, Sudarsana-based
  ✗ South Indian Irregular chart style
  ✗ Mixed 2-Vargas (two varga charts overlaid)
  ✗ Customizable colors (110 individual settings)
  ✗ Language support (10 Indian languages)
  ✗ Custom ayanamsa (user-defined)
  ✗ 3 sunrise definitions (currently 1)
  ✗ Geocentric/Topocentric toggle, True/Apparent toggle
  ✗ Gouri Panchanga/Choghadiya full implementation
