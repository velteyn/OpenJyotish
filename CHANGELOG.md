# Changelog — OpenJyotish

All notable changes, newest first. Release tags: `vX.Y.Z`.

## Unreleased

### Added
- Dasa Sandhi (10% rule, most-used reading): junction windows in CLI
  `dasa-sandhi` (55 commands, `--system`), the GUI dasa text and the
  JSON dasa block. Chidra-dasha (final bhukti) rides along: `--chidra`
  flag, GUI lines, `dasa.chidra`.
- Asta-Udaya: Venus/Jupiter combust + rising windows per year (daily
  elongation scan, ±1 day) — CLI `asta-udaya` (54 commands), Mundane
  tab table. Annual data stays out of the natal JSON.
- Avakahada birth identity (108-syllable nama table, gana/yoni/nadi
  off the shared tables): new CLI `avakahada` (53 commands), Points
  tab table, folded into JSON `omens` (still 31 sections).
- Birth omens: Ganda Moola nakshatras (Moon + lagna) and Vishti
  karana — CLI `chart` footer, Points tab table, JSON `omens`
  section (31). Lagna row now carries its Gnd flag in chart/GUI.
- Argala (Jaimini 1-1-5/10): primary/virodha pairs, strict-majority
  rule, trikona secondary, visesha, Ketu mirror — new CLI `argala`
  (52 commands), Points tab table, JSON `argala` section (30).
- Graha Yuddha: five-planet wars inside 1° (Venus exception, then
  northern latitude, disc tiebreak) — CLI `chart` footer, Points tab
  table, new JSON `yuddha` section (29 sections).
- Avasthas (Balaadi set, odd/even bands) in CLI `chart`, the GUI
  planet table and JSON.
- Gandanta: water-fire junction zones flagged in CLI `chart` (Gnd
  column), the GUI planet table and JSON (per planet + lagna).
- Combustion (Asta): per-planet orbs (Mercury/Venus retro-aware),
  flagged in CLI `chart`, the GUI planet table and the JSON planets
  block.
- GUI learning sections on the Points tab: Marana Karaka Sthana
  table and Vaiseshikamsa ranks (scores shown alongside).

### Fixed
- Marana Karaka Sthana drops the Ketu assignment (Jataka Parijata
  17.34-36 lists eight planets; Ketu carries no classical MKS).
- GUI Compare view (Chart & Varga page): second birth-data form with
  Copy-from-A, two charts side by side in a splitter, A side mirroring
  the main chart; Packed toggle and chart style apply to both.
- GUI monthly Calendar tab (Special Topics page): 7x6 panchanga grid
  (tithi + nakshatra per day, today highlighted), prev/next + month/
  year navigation, place fields synced from birth data, click-a-day
  detail (limbs, sunrise/sunset, Rahu/Gulika/Yama, optional
  Durmuhurta/Varjya adjuncts).
- GUI Chakras tab (Transits & Tajaka page): interactive 9x9
  Sarvatobhadra grid with Janma-nakshatra reference, vedha table,
  Kota Chakra summary and a current-transit overlay.
- Buddhi Gati dasa (Agni Purana tradition): chart-read MD order swept
  from the 4th from lagna, descending-longitude planets, count years
  ± dignity, configurable base varga (`dasa ... buddhi-gati
  --buddhi-gati-varga D-9`); CLI/TUI/GUI/JSON wired.
- Naabhasa yogas, all 32 (P.V.R. Rao ch. 11.5): Asraya, Dala, Akriti,
  Sankhya (fallback-only per doctrine) — flowing into detect_all and
  every yoga surface.

## v1.8.1 — 2026-09-24

### Fixed
- Windows installer build: the frozen CLI is built as `openjyotish`
  again (the rename missed the PyInstaller spec, pointing smoke and the
  installer shortcut at an unbuilt file); smoke hardens with a dist
  listing, `--version` probe and timeout. Debian ships both
  `openjyotish` and `jhora` symlinks.

## v1.8.0 — 2026-09-24

### Added
- GUI Points & Maitri tab (Upagrahas, Sphutas, Special Points, Maitri
  matrix) + `upagrahas` CLI + Vargottama column on the Varga tab.
- Graha Maitri (`maitri` CLI): Naisargika (asymmetric BPHS tables),
  Tatkalika and Panchadha compound tables with scores.
- Sripati bhava option for chalit (`chart --chalit --bhava-method
  sripati`, GUI Houses combo); default behavior unchanged. Sripati
  spans now live in `calc/chalit.py` (single source).
- Tajaka yogas (P.V.R. Rao ch. 29.2, worked numbers as tests): Ithasala
  (Vartamaana/Poorna/Bhavishya, retrograde-aware), Eesarpha, Nakta,
  Yamaya, Manahoo, Kamboola, Radda, Ishkavala, Induvara, Khallasara —
  on the `tajaka` CLI and the GUI Tajaka tab.
- D-60 Shashtiamsa start (count forward from the sign, P.V.R. Rao
  ch. 6.2.20, Jupiter-in-Sg worked example).
- Classical varga starts for D-5, D-6, D-8, D-11 (P.V.R. Rao ch. 6.2,
  pinned on his worked examples) plus the Raman anti-zodiacal D-11
  variant. Remaining unsourced levels unchanged.
- Special sensitive points (`special-points` CLI): Baadhaka sthana/lord,
  Pushkara navamsa/bhaga, Mrityu bhaga (with Mandi), 64th navamsa (Khara),
  22nd drekkana.
- Mean/true lunar nodes option (the reference program exposes the same
  preference): `SweEngine.set_use_true_nodes`, `ChartBuilder.build(...,
  nodes=...)`, `chart --nodes`, GUI nodes combo; transit Rahu/Ketu follow
  the chart mode and are now reported on the transit result. Default stays
  mean (all reference vectors were pinned with it).

### Fixed
- Kalachakra Revati grouping (Revati → Savya-2 per the pada tables;
  previously misassigned, affecting Moon-in-Revati charts only).
- Sodhya Pinda now follows BPHS / P.V.R. Rao ch. 12: occupation-aware
  Ekadhipatya Shodhana (rules 1–4) and Rasi Pinda + Graha Pinda with the
  Rasimana/Grahamana multipliers (verified: Mercury 152 = 77 + 75).
  Values change accordingly wherever Sodhya Pinda is shown.

## v1.7.0 — 2026-09-23

### Added
- Sade Sati phase timeline with dates — new `sade-sati` CLI, Transits-tab
  table, dashboard KEY DATES with exact dates, TUI menu entry, HTML report
  section, and `sade_sati` block in the `analyze` JSON; Kantaka/Ashtama Shani
  included, retrograde re-entries as separate intervals.
- Dasa entry chart — new `dasa-entry` CLI (period path like `Jupiter/Saturn`,
  any dasa engine); double-click a period in the GUI dasa-chart table to see
  its entry chart; `dasa_entry` block in the `analyze` JSON; HTML report section.
- Tajaka annual Vimshottari from the return Moon (`tajaka --vimshottari
  sesham|full|none`).
- Ashtakavarga Bala view (`ashtakavarga --bala`): per-planet strength at each
  reduction stage (BAV → Trikona → Ekadhipatya = Sodhya Pinda).
- GUI packed chart mode + per-widget D-1/D-9 styles ("Two styles").
- Yogakaraka reported as a detected yoga (flows to CLI/GUI/JSON).
- Rasi-Bhukta Vimsottari dasa system.
- Rule-based remedy engine (sourced): yantra, dasha-lord, timing, doshas,
  partner-aware marriage remedies; Remedies GUI panel.
- KP Vimsottari presentation (`kp --when`) and bhava significators
  ( CLI table, GUI tab, AI JSON).
- Five classical yogas: Budha-Aditya, Chandra-Mangala, Adhi (graded),
  Lagnaadhi, Vasumati.
- Dasa chart view (running period tree): `dasa-chart` CLI + GUI dasa tab.
- Per-varga Shadbala and Bhava Bala matrices (report + `varga_strength` JSON).
- Gochara vedha (transit obstruction, Raman ch. 34 exemptions).
- `jhora --version` / `-V`.

### Fixed
- Swiss Ephemeris planet mapping order (transits at birth now equal natal).
- Special-lagna SE body map; Tajaka Harsha Bala exaltation scoring.
- Whole-sign house counting in learning/comparison, Kuja dosha, and aspects.
- Classical varga start signs for the default mapping (D-2/3/4/7/9/10/12 and
  D-16/20/24/27/30/40/45); navamsa/vargottama corrected.
- `compute_all_upagrahas` sunrise call (temporal upagrahas were silently dropped).
- `analyze` redaction no longer blanks astrological longitudes.
- Kalachakra rewritten to the Raghavaacharya method (nine mahadasas).
- Rasi-dasa seeds (Lagnamsaka, Narayana) from the stronger of lagna and 7th.

### Changed
- Release packaging never ships `data/jhora.db` (app creates a fresh
  database); `make_release.sh` fails loudly when the version is unknown.
- Varga variant wiring verified; D-7/D-10 offset parity flagged as needing
  published variant tables (no behavior change).
- Traditional one-pager values pinned against their engines (test-only).

## v1.6.3 and earlier

See GitHub Releases and the git history (`git log --oneline v1.6.2..v1.6.3`).
Detailed per-PR notes for the v1.7.0 cycle are the PR bodies (#160–#199).
