# Extraction Summary

## Method
- **Tool:** helpdeco 2.1 (rofl0r's 64-bit Linux port, with strlwr() UB fix)
- **Source:** `jhora.hlp` — 3,820,452 bytes, MS Windows 95 Help, title "Jagannatha Hora Help"
- **Bug fix:** `strlwr()` at helpdeco.c:442 had `while(*p) *p = tolower(*(p++))` causing heap overflow on 64-bit. Fixed to `while(*p) { *p = tolower(*p); p++; }`

## Results
- **Topics extracted:** 56
- **Images extracted:** 35 (3 WMF + 32 BMP)
- **RTF source:** 395 KB, 2,789 lines
- **Phrase table:** 2,825 phrases

## Output

All files in `/home/velteyn/projects/Reversing/Jhora/docs/help/`:
- `*.md` — individual topic files (numbered 00–57)
- `00_INDEX.md` — topic index with links
- `jhora_help_complete.md` — all topics concatenated
- `jhora_help_summary.md` — this file
