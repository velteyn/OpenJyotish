# Agent Instructions

## Reverse Engineering & Original Code (TOP PRIORITY)
When implementing calculations, functions, or algorithms:
1. **ALWAYS look at the original `jhora.exe` binary first** — it contains 3,150 functions with known addresses mapped in `docs/function_map.md`
2. Use `reko` (at `/home/velteyn/.local/bin/reko`) to decompile specific functions to pseudocode:
   ```
   reko jhora.exe
   ```
   Output goes to `jhora.reko/` — contains `.dis` files (Reko pseudocode) and `.asm` files (x86 disassembly)
3. `docs/function_map.md` catalogs all known functions with sizes, guessed purposes, and MFC vtable entries
4. `docs/swe_xrefs.md` maps all 18 Swiss Ephemeris API calls to their calling functions
5. **Only if the original function is unrecoverable or provably wrong**, fall back to writing your own implementation based on:
   - The original JHora help file (`docs/help/jhora_help_complete.md`)
   - Reference textbooks (`docs/books/`)
   - Vedic astrology standard formulas

## GUI Design
- The GUI must always be **harmonic, proportional, and stylish** — matching the existing dark theme (PyQt6, Fusion style)
- Consistent spacing: use 10px grid, consistent margins, proportional splitter ratios
- Colors from the established palette; no突兀 colors

## Documentation
- Keep CONTEXT.md up-to-date — add new features, update "Done" section, remove stale "In Progress" entries
- Update PLAN.md if roadmap changes

## Commit Discipline
- After any code change, run `python3 -m pytest tests/ -q` and confirm 0 failures
- Stage all changes, commit with a descriptive message, and push to `origin/main`
- Never leave failing tests in the committed code
