# Reverse Engineering Tools

| Tool | Path | Usage |
|------|------|-------|
| **Reko** | `/home/velteyn/.local/bin/reko` | Runs on `jhora.exe` → outputs to `jhora.reko/` (`.dis` pseudo-C + `.asm` disassembly). |
| **Retdec** | `/home/velteyn/projects/retdec/bin/retdec-decompiler` | Full decompiler (LLVM-based). Run `retdec-decompiler jhora.exe` → outputs to `retdec_out/`: |
| | | `jhora.exe.c` — 371K lines decompiled C (10,407 functions) |
| | | `jhora.exe.dsm` — annotated disassembly (function labels + string comments) |
| | | `jhora.exe.ll` — LLVM IR |
| | | `jhora.exe.bc` — LLVM bitcode |
| | | `jhora.exe.config.json` — function metadata (names, addresses, sizes, 12,690 globals) |
| **Capstone** | Python `pip install capstone` | Used programmatically to disassemble specific ranges; integrated into RE scripts. |

## Retdec Caveats

Retdec produces **optimized** decompiled C — functions may be inlined, merged, or transformed extensively. Small functions often collapse to just 1-2 lines of code, losing the original algorithm. It is not a 1:1 reconstruction but provides excellent high-level understanding and string/API references.

## Matchmaking Discovery

### Ashta Koota (not 10 Porutham)

JHora uses the **Ashta Koota** system (8 factors, **36 points**), NOT the 10 Porutham (19-point) system. Confirmed by the format string at `0x591a3c`:

```
"Gunanka score after matching ashta koota (group of eight factors) = %d (out of 36)."
```

The Ashta Koota 8 factors are:
1. Varna (1 pt) — spiritual/caste compatibility
2. Vashya (2 pt) — mutual control
3. Tara (3 pt) — birth star compatibility
4. Yoni (4 pt) — sexual compatibility
5. Graha Maitri (5 pt) — planetary friendship
6. Gana (6 pt) — temperament
7. Bhakoota/Rasi (7 pt) — rasi compatibility
8. Nadi (8 pt) — health/heredity

Total: **36 points**. String also references 5 levels: below average / average / fair / good / excellent.

### Key Function: `function_4b3b10` (0x4b3b10, 12,048 B)

This is the **Ashta Koota score table lookup**. It:
1. Takes 5 params: `(sex_flag, girl_param1, girl_param2, boy_param1, boy_param2)`
2. Calls `function_4b37a0` for girl and boy to compute indices into a 36×36 table
3. Returns the pre-computed Gunanka score from the table (swaps axes based on `sex_flag`)

### Key Function: `function_4b37a0` (0x4b37a0, 865 B)

Computes an index (0-35) from two integer parameters — likely derived from nakshatra + pada or similar. The 36-value range maps to the 27 nakshatras × 4 padas = 108 possible values, reduced via some mapping.

### Result Display: `function_4e8db0` (0x4e8db0, 619 B)

The matchmaking view handler. Calls `function_4b3b10` with computed parameters, formats the result with the Gunanka string, and shows it in a message box titled "Result of Horoscope Matching for Marriage".

### Corrected Function Map Entry

| Map address | Map label | Actual |
|-------------|-----------|--------|
| `0x0044c170` | Matchmaking/Kuta (5,590 B) | **Small thunk** (136 B, `0x44c170-0x44c1f8`) calling `function_44d670` (UI dialog plumbing). The map is **wrong** — this is actually the chart-drawing-style dispatcher (accesses `[0x8a4b58]` jump table with 23 entries). |

The actual matchmaking logic is at `0x4b3b10` (12,048 B) and `0x4b37a0` (865 B), neither of which are in the current function map.

## Using Retdec with function_map.md

To find the decompiled C for any function at address `0x00XXXXXX`:

```
rg "Address range: 0xXXXXXX" retdec_out/jhora.exe.c
```

Then read the function body starting a few lines after the match.

To see string references in the annotated disassembly:

```
rg "0xXXXXXX" retdec_out/jhora.exe.dsm
```

To find functions by size range:

```
python3 -c "
import json
with open('retdec_out/jhora.exe.config.json') as f:
    cfg = json.load(f)
for fn in cfg['functions']:
    s = int(fn['startAddr'], 16); e = int(fn['endAddr'], 16)
    if 4000 < e-s < 6000:
        print(f'{fn[\"name\"]}: {fn[\"startAddr\"]}-{fn[\"endAddr\"]} ({e-s} B)')
"
```
