# Varga Charts — Jagannatha Hora 8.0

All divisional charts (vargas) found in the `jhora.exe` binary, with their variants. Extracted via string analysis.

## Varga Group Systems

Jhora references four classical varga grouping systems:

| Group | Charts | String Found |
|-------|--------|-------------|
| Shad Varga (6) | D-1, D-2, D-3, D-4, D-5, D-9 | `Shad Varga (6)` |
| Sapta Varga (7) | D-1 through D-7 | `Sapta Varga (7)` |
| Dasa Varga (10) | D-1 through D-10 | `Dasa Varga (10)` |
| Shodasa Varga (16) | D-1 through D-16 | `Shodasa Varga (16)` |

Additional strength systems: `Pancha Vargeeya Bala`, `Dwadasa Vargeeya Bala`, `Saptavargaja`.

## Chart Variant Suffixes

| Suffix | Meaning |
|--------|---------|
| (none) | Default/base computation |
| (Trd) | Tridirectional (3 counting methods) |
| (Rev) | Reverse sign assignment |
| (Rev2) | Reverse variant 2 |
| (Pv) | Parivritti (cyclical) |
| (B) | Bhava-based |
| (K) | Kalachakra method |
| (KM) | Krishna Mishra |
| (UKM) | Uniform Krishna Mishra |
| (Jn) | Jagannatha |
| (Sn) | Somanatha |
| (US) | Uma-Shambhu |
| (Sh) | Shashyamsa-like (D-30) |
| (Ar) | From Aries |
| (RvAr) | Reversal from Aries |
| (Ra) | Raman's |
| (Rm) | Raman |
| (RmM) | Raman Modified (SJC) |
| (Ni) | Niranjan |
| (NiM) | Niranjan Modified (SJC) |
| (Md) | Mandooka |
| (Lm) | Lagna (Moon-based) |
| (CnL) | Chandralagna |
| (SN) | Niranjan variant |
| (KN) | K.N. Rao |

## Bhava/Chalit Chakra Support

The following 23 charts have Bhava/chalit chakra computation:

D-1, D-2, D-3, D-4, D-5, D-6, D-7, D-8, D-9, D-10, D-11, D-12, D-16, D-20, D-24, D-27, D-30, D-40, D-45, D-60, D-81, D-108, D-144

---

## Full Chart Listing

### D-1 — Rasi (Rasis)

| Variant | String |
|---------|--------|
| Default | `D-1 (` |
| Bhava | `D-1 (B)` |

- Also referred to as `Rasi (D-1)`.
- Bhava/chalit chakra supported.

---

### D-2 — Hora (Divisions of a sign into 2)

| Variant | String |
|---------|--------|
| Default | `D-2 (` |
| Chandralagna | `D-2 (CnL)` |
| Jagannatha | `D-2 (Jn)` |
| K.N. Rao | `D-2 (KN)` |
| Lagna (Moon-based) | `D-2 (Lm)` |
| Mandooka | `D-2 (Md)` |
| Niranjan | `D-2 (Ni)` |
| Niranjan Modified | `D-2 (NiM)` |
| Parivritti | `D-2 (Pv)` |
| Raman | `D-2 (Rm)` |
| Raman Modified (SJC) | `D-2 (RmM)` |
| Niranjan variant | `D-2 (SN)` |
| Uma-Shambhu | `D-2 (US)` |

Named variants found:
- `Hora (D-2)`
- `Parasara hora (D-2)`
- `Jagannatha hora (D-2)`
- `Kashinatha hora (D-2)`
- `Raman hora (D-2)`
- `Raman hora - SJC modified (D-2)`
- `Niranjan hora (D-2)`
- `Niranjan hora - SJC modified (D-2)`
- `Parivritti-dwaya hora (D-2)` — also described as `Parivritti-dwaya (bi-cyclical) Hora`
- `Samasaptaka hora (D-2)` — also `Samasaptaka Hora (based on 1st & 7th)`
- `Mandooka hora (D-2)`
- `Labha mandooka hora (D-2)`
- `Re-interpreted Parasara Hora [Uma-Shambhu] (D-2)`

---

### D-3 — Drekkana (Divisions of a sign into 3)

| Variant | String |
|---------|--------|
| Default | `D-3 (` |
| Jagannatha | `D-3 (Jn)` |
| Parivritti | `D-3 (Pv)` |
| Somanatha | `D-3 (Sn)` |
| Tridirectional | `D-3 (Trd)` |
| Uma-Shambhu | `D-3 (US)` |

Named variants found:
- `Drekkana (D-3)`
- `Parasara drekkana (D-3)`
- `Jagannatha drekkana (D-3)` — also referred to as `Jagannatha drekkana`
- `Somanatha drekkana (D-3)`
- `Parivritti-traya drekkana (D-3)` — also described as `Parivritti-traya (tri-cyclical) Drekkana`
- `Re-interpreted Parasara drekkana [Uma-Shambhu] (D-3)`

---

### D-4 — Chaturthamsa (Divisions of a sign into 4)

| Variant | String |
|---------|--------|
| Default | `D-4 (` |
| Parivritti | `D-4 (Pv)` |

Named variants:
- `Chaturthamsa (D-4)`
- `Parasara chaturthamsa (D-4)`
- `Parivritti chaturthamsa (D-4)`

---

### D-5 — Panchamsa (Divisions of a sign into 5)

| Variant | String |
|---------|--------|
| Default | `D-5 (` |
| Parivritti | `D-5 (Pv)` |

Named variants:
- `Panchamsa (D-5)`
- `Standard panchamsa (D-5)`
- `Parivritti panchamsa (D-5)`

---

### D-6 — Shashthamsa (Divisions of a sign into 6)

| Variant | String |
|---------|--------|
| Default | `D-6 (` |

Named:
- `Shashthamsa (D-6)`

---

### D-7 — Saptamsa (Divisions of a sign into 7)

| Variant | String |
|---------|--------|
| Default | `D-7 (` |
| 1st-7th reverse | `D-7 (1-7)` |
| 7th-1st reverse | `D-7 (7-1)` |
| Tridirectional | `D-7 (Trd)` |

Named variants:
- `Saptamsa (D-7)`
- `Traditional Parasara saptamsa [even: 7th-1st forward] (D-7)`
- `Re-interpreted Parasara saptamsa [even: 1st-7th reverse] (D-7)` — variant `(1-7)`
- `Re-interpreted Parasara saptamsa [even: 7th-1st reverse] (D-7)` — variant `(7-1)`

---

### D-8 — Ashtamsa (Divisions of a sign into 8)

| Variant | String |
|---------|--------|
| Default | `D-8 (` |
| Raman | `D-8 (Ra)` |

Named variants:
- `Ashtamsa (D-8)`
- `Regular Ashtamsa (D-8)`
- `Raman's Ashtamsa (D-8)`

---

### D-9 — Navamsa (Divisions of a sign into 9)

| Variant | String |
|---------|--------|
| Default | `D-9 (` |
| Kalachakra | `D-9 (K)` |
| Krishna Mishra | `D-9 (KM)` |
| Uniform Krishna Mishra | `D-9 (UKM)` |

Named variants:
- `Navamsa (D-9)`
- `Normal navamsa (D-9)`
- `Kalachakra navamsa (D-9)`
- `Krishna Mishra navamsa (D-9)`
- `Uniform Krishna Mishra navamsa (D-9)`

---

### D-10 — Dasamsa (Divisions of a sign into 10)

| Variant | String |
|---------|--------|
| Default | `D-10 (` |
| Even: 5th-8th | `D-10 (5-8)` |
| Even: 6th-9th | `D-10 (6-9)` |
| Even: 9th-12th | `D-10 (9-12)` |
| Parivritti | `D-10 (Pv)` |
| Tridirectional | `D-10 (Trd)` |

Named variants:
- `Dasamsa (D-10)`
- `Traditional Parasara dasamsa [Even: 9th-6th] (D-10)`
- `Re-interpreted Parasara dasamsa [Even: 5th-8th] (D-10)` — variant `(5-8)`
- `Re-interpreted Parasara dasamsa [Even: 6th-9th] (D-10)` — variant `(6-9)`
- `Re-interpreted Parasara dasamsa [Even: 9th-12th] (D-10)` — variant `(9-12)`
- `Parivritti dasamsa (D-10)` — variant `(Pv)`

---

### D-11 — Ekadasamsa / Rudramsa (Divisions of a sign into 11)

| Variant | String |
|---------|--------|
| Default | `D-11 (` |
| Raman/Rath | `D-11 (Ra)` |

Named variants:
- `Raman's Ekadasamsa (D-11)`
- `Rath's Rudramsa (D-11)`
- `Rudramsa (D-11)`

Description found:
> "Mandooka dasa of Rudramsa (D-11) shows death, wars and destruction. It is an ayur dasa. It is very important in predicting the outcomes of wars."

---

### D-12 — Dwadasamsa (Divisions of a sign into 12)

| Variant | String |
|---------|--------|
| Default | `D-12 (` |
| Reverse | `D-12 (Rev)` |
| Tridirectional | `D-12 (Trd)` |

Named variants:
- `Dwadasamsa (D-12)`
- `Traditional Parasara shodasamsa (D-12)`
- `Re-interpreted Parasara shodasamsa [even sign reversal] (D-12)` — variant `(Rev)`

---

### D-16 — Shodasamsa (Divisions of a sign into 16)

| Variant | String |
|---------|--------|
| Default | `D-16 (` |
| Reverse | `D-16 (Rev)` |
| Tridirectional | `D-16 (Trd)` |

Named variants:
- `Shodasamsa (D-16)`
- `Traditional Parasara shodasamsa (D-16)`
- `Re-interpreted Parasara shodasamsa [even sign reversal] (D-16)` — variant `(Rev)`

---

### D-20 — Vimsamsa (Divisions of a sign into 20)

| Variant | String |
|---------|--------|
| Default | `D-20 (` |
| Reverse | `D-20 (Rev)` |
| Tridirectional | `D-20 (Trd)` |

Named variants:
- `Vimsamsa (D-20)`
- `Traditional Parasara shodasamsa (D-20)`
- `Re-interpreted Parasara shodasamsa [even sign reversal] (D-20)` — variant `(Rev)`

---

### D-24 — Siddhamsa (Divisions of a sign into 24)

| Variant | String |
|---------|--------|
| Default | `D-24 (` |
| Reverse | `D-24 (Rev)` |
| Reverse 2 | `D-24 (Rev2)` |
| Tridirectional | `D-24 (Trd)` |

Named variants:
- `Siddhamsa (D-24)`
- `Traditional Parasara siddhamsa [Le->Cn, Cn->Ge] (D-24)`
- `Re-interpreted Parasara siddhamsa [Le->Cn, Cn->Le] (D-24)` — variant `(Rev)`
- `Re-interpreted Parasara siddhamsa [Le->Cn, Le->Cn] (D-24)` — variant `(Rev2)`

---

### D-27 — Nakshatramsa (Divisions of a sign into 27)

| Variant | String |
|---------|--------|
| Default | `D-27 (` |
| Reverse | `D-27 (Rev)` |
| Tridirectional | `D-27 (Trd)` |

Named variants:
- `Nakshatramsa (D-27)`
- `Traditional Parasara shodasamsa (D-27)`
- `Re-interpreted Parasara shodasamsa [even sign reversal] (D-27)` — variant `(Rev)`

---

### D-30 — Trimsamsa (Divisions of a sign into 30)

| Variant | String |
|---------|--------|
| Default | `D-30 (` |
| Parivritti | `D-30 (Pv)` |
| Shashyamsa-like | `D-30 (Sh)` |

Named variants:
- `Trimsamsa (D-30)`
- `Standard Trimsamsa (irregular D-30 with empty Cn and Le)`
- `Shashyamsa like trimsamsa (D-30)`
- `Parasara trimsamsa (D-30)`
- `Parivritti trimsamsa (D-30)`
- `Parivritti Trimsa Trimsamsa (regular and cyclical D-30)`

---

### D-40 — Khavedamsa / Chatvarimsamsa (Divisions of a sign into 40)

| Variant | String |
|---------|--------|
| Default | `D-40 (` |

Named:
- `Khavedamsa (D-40)`

---

### D-45 — Akshavedamsa (Divisions of a sign into 45)

| Variant | String |
|---------|--------|
| Default | `D-45 (` |

Named:
- `Akshavedamsa (D-45)`

---

### D-60 — Shashtyamsa (Divisions of a sign into 60)

| Variant | String |
|---------|--------|
| Default | `D-60 (` |
| From Aries | `D-60 (Ar)` |
| Reverse | `D-60 (Rev)` |
| Reversal from Aries | `D-60 (RvAr)` |
| Tridirectional | `D-60 (Trd)` |

Named variants:
- `Shashtyamsa (D-60)`
- `Traditional Parasara shashtyamsa (D-60)`
- `Re-interpreted Parasara shashtyamsa [even sign reversal] (D-60)`
- `Re-interpreted Parasara shashtyamsa [even sign reversal, from Aries] (D-60)` — variant `(RvAr)`
- `Re-interpreted Parasara shashtyamsa [from Aries] (D-60)` — variant `(Ar)`

Referenced as "past life" chart in Moola dasa description:
> "Use D-60 (past life) and rasi (this life) with Moola dasa to judge how past life's karma influences this life's events."

---

### D-81 — Nava-Navamsa (Divisions of a sign into 81)

| Variant | String |
|---------|--------|
| Default | `D-81 (` |
| Kalachakra | `D-81 (K)` |

Named variants:
- `Navanavamsa (D-81)`
- `Normal nava-navamsa (D-81)`
- `Kalachakra nava-navamsa (D-81)` — variant `(K)`

---

### D-108 — Ashtottaramsa (Divisions of a sign into 108)

| Variant | String |
|---------|--------|
| Default | `D-108 (` |

Named:
- `Ashtottaramsa (D-108)`

---

### D-144 — Dwadasamsa-Dwadasamsa (Divisions of a sign into 144)

| Variant | String |
|---------|--------|
| Default | `D-144 (` |

Named:
- `Dwadasamsa-Dwadasamsa (D-144)`

---

### D-150 (Divisions of a sign into 150)

| Variant | String |
|---------|--------|
| Default | `D-150` |

No named variant or description found.

---

## Summary: All D-# Charts

| Chart | Sanskrit Name | Variants | Bhava/Chalit |
|-------|---------------|----------|:---:|
| D-1 | Rasi | `B` | Yes |
| D-2 | Hora | `CnL`, `Jn`, `KN`, `Lm`, `Md`, `Ni`, `NiM`, `Pv`, `Rm`, `RmM`, `SN`, `US` | Yes |
| D-3 | Drekkana | `Jn`, `Pv`, `Sn`, `Trd`, `US` | Yes |
| D-4 | Chaturthamsa | `Pv` | Yes |
| D-5 | Panchamsa | `Pv` | Yes |
| D-6 | Shashthamsa | (none) | Yes |
| D-7 | Saptamsa | `1-7`, `7-1`, `Trd` | Yes |
| D-8 | Ashtamsa | `Ra` | Yes |
| D-9 | Navamsa | `K`, `KM`, `UKM` | Yes |
| D-10 | Dasamsa | `5-8`, `6-9`, `9-12`, `Pv`, `Trd` | Yes |
| D-11 | Ekadasamsa / Rudramsa | `Ra` | Yes |
| D-12 | Dwadasamsa | `Rev`, `Trd` | Yes |
| D-16 | Shodasamsa | `Rev`, `Trd` | Yes |
| D-20 | Vimsamsa | `Rev`, `Trd` | Yes |
| D-24 | Siddhamsa | `Rev`, `Rev2`, `Trd` | Yes |
| D-27 | Nakshatramsa | `Rev`, `Trd` | Yes |
| D-30 | Trimsamsa | `Pv`, `Sh` | Yes |
| D-40 | Khavedamsa | (none) | Yes |
| D-45 | Akshavedamsa | (none) | Yes |
| D-60 | Shashtyamsa | `Ar`, `Rev`, `RvAr`, `Trd` | Yes |
| D-81 | Nava-Navamsa | `K` | Yes |
| D-108 | Ashtottaramsa | (none) | Yes |
| D-144 | Dwadasamsa-Dwadasamsa | (none) | Yes |
| D-150 | — | (none) | No |

**Total unique chart levels: 23 (D-1 through D-150)**

**Total charts with Bhava/chalit chakra: 23**

## Additional Varga-Related Strings

### Custom / Sub-divisional charts
- `Custom divisional chart (D-n)` — user-defined division
- `Sub-divisional chart (D-mxn chosen currently)` — nested division (m × n)

### Arudha references
- `Arudha lagna of each divisional chart`
- `Graha arudha of each divisional chart`

### Muntha references
- `Muntha from each varga chart, with antardasas starting from dasa lord`
- `Muntha from each varga chart, with antardasas starting from dasa sign`
- `Muntha of rasi chart shown in all vargas`

### Ashtakavarga
- `Ashtakavarga` (D-1 base chart)
- `Prastara (spread-out) ashtakavarga`
- `BhavaDrivenSarvaAshtakaVarga`
- `Apavargaa`, `Mokshapavarga`
- `Ashtakavarga Bala`

### Deity
- `CVargaDeityView` — a view for varga deities (planet-to-deity mapping per varga)

### Display
- `Natal varga:` and `Transit varga:` — display context labels
- `DisplayVarga=%d %d`
- `BhavaChartVarga=%d`
- `SCDasaVarga=%d`
- `BuddhiGatiDasaVarga=%d`
