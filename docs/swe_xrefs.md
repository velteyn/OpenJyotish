# Swiss Ephemeris Cross-References

## Full Import Table

| # | Address | Function |
|---|---------|----------|
| 1 | 0x005467a4 | `_swe_set_sid_mode@20` |
| 2 | 0x005467a8 | `_swe_fixstar@24` |
| 3 | 0x005467ac | `_swe_deltat@8` |
| 4 | 0x005467b0 | `_swe_julday@24` |
| 5 | 0x005467b4 | `_swe_azalt_rev@24` |
| 6 | 0x005467b8 | `_swe_refrac@28` |
| 7 | 0x005467bc | `_swe_azalt@40` |
| 8 | 0x005467c0 | `_swe_get_ayanamsa@8` |
| 9 | 0x005467c4 | `_swe_set_topo@24` |
| 10 | 0x005467c8 | `_swe_sol_eclipse_when_loc@32` |
| 11 | 0x005467cc | `_swe_sol_eclipse_when_glob@28` |
| 12 | 0x005467d0 | `_swe_lun_eclipse_when@28` |
| 13 | 0x005467d4 | `_swe_houses@36` |
| 14 | 0x005467d8 | `_swe_revjul@28` |
| 15 | 0x005467dc | `_swe_set_ephe_path@4` |
| 16 | 0x005467e0 | `_swe_calc@24` |
| 17 | 0x005467e4 | `_swe_close@0` |
| 18 | 0x005467e8 | `_swe_rise_trans@52` |

## Call Graph

### fcn.0049aaa0 — CORE CHART CALCULATION
**Likely purpose**: Main astronomical computation engine (planet positions, houses, etc.)

Calls:
- `_swe_calc` (planet longitudes)
- `_swe_houses` (house cusps)
- `_swe_julday` (date→JD, 3 calls)
- `_swe_fixstar` (fixed stars, 5 calls)
- `_swe_deltat` (time correction)
- `_swe_azalt_rev` (reverse azimuth/altitude)
- `_swe_refrac` (atmospheric refraction)
- `_swe_azalt` (azimuth/altitude)
- `_swe_revjul` (JD→date)

### fcn.0040b2a0 — ECLIPSE CALCULATIONS
Calls:
- `_swe_set_topo`
- `_swe_sol_eclipse_when_loc` (2×)
- `_swe_sol_eclipse_when_glob` (2×)
- `_swe_lun_eclipse_when` (2×)

### fcn.0049a370 — AYANAMSA GETTER
Calls: `_swe_get_ayanamsa`

### fcn.0049a3a0 — AYANAMSA MODE SETTER
Calls: `_swe_set_sid_mode` (16+ times, one per ayanamsa mode)

### fcn.0049a930 — FIXED STAR / DATE ROUTINE
Calls: `_swe_julday`, `_swe_fixstar`, `_swe_deltat`

### fcn.0049bb00 — PLANET COMPUTATION
Calls: `_swe_calc` (2×), `_swe_deltat`

### fcn.0049bcf0 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049bd80 — DATE CONVERSION
Calls: `_swe_julday` (3×)

### fcn.0049c130 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049c930 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049cb50 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049d210 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049d250 — JD ⇄ DATE
Calls: `_swe_julday`, `_swe_revjul`

### fcn.0049d3e0 — DATE CONVERSION
Calls: `_swe_revjul`

### fcn.0049d500 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049d660 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049dae0 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049dc20 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049de30 — DATE CONVERSION
Calls: `_swe_julday` (2×)

### fcn.0049e1b0 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049e3f0 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049e630 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049e690 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049e870 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.0049eae0 — DATE CONVERSION
Calls: `_swe_julday`

### fcn.004aaa10 — DATE CONVERSION
Calls: `_swe_julday` (2×)

### fcn.004a1350 — RISE/TRANSIT
Calls: `_swe_rise_trans` (reference load)

### fcn.004ba830 — DATE CONVERSION
Calls: `_swe_julday`, `_swe_revjul`

### fcn.004b8d70 — SECONDARY CALC ENGINE
Calls: `_swe_set_sid_mode`, `_swe_fixstar`, `_swe_deltat`

### fcn.004b9390 — TOPOCENTRIC SETUP
Calls: `_swe_set_topo`

### fcn.004db700 — EPHEMERIS PATH
Calls: `_swe_set_ephe_path`

### fcn.004dbf60 — CLEANUP
Calls: `_swe_close`

### (nofunc) 0x43f014 — CLEANUP
Calls: `_swe_close`

### (nofunc) 0x4dc188 — CLEANUP
Calls: `_swe_close`

## Summary

- **1 core engine** (fcn.0049aaa0) does all major calculation: planets, houses, stars, rise/set
- **1 secondary engine** (fcn.004b8d70) handles sidereal mode + star positions
- **1 eclipse calculator** (fcn.0040b2a0) handles all eclipse types
- **~20+ date conversion helpers** wrap _swe_julday / _swe_revjul
- **Ayanamsa setter** (fcn.0049a3a0) has explicit switch for all supported modes
