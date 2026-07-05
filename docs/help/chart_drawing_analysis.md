# Reverse Engineering Analysis: JHora Chart Drawing Engine

## 1. Introduction

**Purpose:** Reverse engineer the original `jhora.exe` binary's chart drawing logic to guide our PyQt6 reimplementation.

**Binary:** `jhora.exe` — PE32 GUI, C++ MFC (VC++ 6.0), statically linked MFC, x86, 3,150 functions.

**Key sections:**

| Section  | VMA          | Size     | File offset | Contents                  |
|----------|--------------|----------|-------------|---------------------------|
| `.text`  | `0x00401000` | 1,325,454 B | `0x1000`    | Executable code (3,150 fns) |
| `.rdata` | `0x00546000` | 186,234 B  | `0x146000`  | Read-only data (strings, vtables, import thunks) |
| `.data`  | `0x00574000` | 147,456 B  | `0x174000`  | Read-write data (INI keys, language strings, yoga texts) |
| `.rsrc`  | `0x008a9000` | 702,344 B  | `0x198000`  | Resources (icons, dialogs, help) |

---

## 2. Correction: Function `0x004CB240` Is NOT Chart Rendering

### 2.1 What the function_map Says

From `docs/function_map.md`:

| Address | Size  | Locals | Description (guessed) |
|---------|-------|--------|----------------------|
| `0x004CB240` | 15,614 B | 202 | **Main chart rendering** — largest function, draws all chart graphics |

### 2.2 What Analysis Shows

This function is actually a **yoga description text builder**. Evidence:

1. **String references:** The function contains **478 `push imm32` instructions** targeting the `.data` section (file offset `0x174000`–`0x198000`). Of these, **406 are unique addresses** that resolve to readable ASCII strings.

2. **String content:** The referenced strings include:
   - **Yoga names:** `Sunaphaa`, `Anaphaa`, `Duradhara`, `Gadaa`, `Kamala`, `Musala`, `Sarpa`, `Sankha`, `Kaahala`, `Parvata`, `Vajra`, `Sringaataka`, `Sakata`, `Soola`, `Rajju`, `Kemadruma`, `Nigadaa`, `Kunthala`, `Gadaaharaa`, etc.
   - **Yoga descriptions:** `"Intelligent, wealthy and famous"`, `"Enjoys comforts, king or an equal"`, `"Planets other than Sun in 2nd from Moon"`, `"An ascetic who attains emancipation"`, `"Very rich"`, `"Poverty"`, `"Becomes a minister at an old age"`, etc.
   - **Planet/house conditions:** `"Lagna lord with 5th lord in a kendra or a kona"`, `"Atma karaka in 5th, 7th, 9th or 10th with a benefic"`, `"Malefics in 3rd/6th from lagna, arudha lagna and atma karaka"`, etc.
   - **Result prefixes:** `" in "`, `"  lagna, conjoined or aspected by "`, `"  in 11th for "`, `"  in 5th, "`

3. **Function size:** At 15,614 B with 202 locals, this is a massive switch-case or decision tree that evaluates astrological conditions and concatenates description strings. The yoga engine in our Python port (`src/jhora/calc/yogas.py` at 488 lines) implements similar logic.

4. **String concatenation:** The function repeatedly calls a **string-append helper** (identified at `0x00513C3E`) — approximately 310 call sites within this function. This is the mechanism for building multi-sentence yoga descriptions.

5. **No GDI calls:** The function contains zero direct GDI32 drawing calls (no `TextOutA`, `MoveToEx`, `LineTo`, `Rectangle`, `CreatePen`, `CreateSolidBrush`, etc.).

### 2.3 Implication

The `function_map.md` entry for `0x004CB240` is **incorrect**. The actual chart rendering function(s) are elsewhere in the binary. The yoga description builder has been successfully reimplemented in `src/jhora/calc/yogas.py`.

---

## 3. Search for the Actual Chart Drawing Function

### 3.1 GDI32 Import Analysis

JHora imports **91 GDI32 functions** (listed at `0x0054604c`–`0x005461b4` in the import table). Key drawing-related imports:

| Function              | Thunk Address  | Calls in `.text` | Purpose                      |
|-----------------------|----------------|------------------|------------------------------|
| `CreatePen`           | `0x0054619c`   | 23               | Pen creation for borders     |
| `CreateSolidBrush`    | `0x005461b4`   | 30               | Brush creation for fills     |
| `Rectangle`           | `0x005461a0`   | 12               | Filled rectangle drawing     |
| `Ellipse`             | `0x005461a8`   | 7                | Circle/ellipse drawing       |
| `SelectObject`        | `0x0054608c`   | 60+              | Object selection into DC     |
| `SetTextColor`        | `0x0054607c`   | 8                | Text color setting           |
| `SetBkMode`           | `0x00546090`   | ~5               | Background mode              |
| `PatBlt`              | `0x00546108`   | 14               | Pattern fill                 |
| `MoveToEx`            | `0x005460cc`   | 3                | Line start                   |
| `LineTo`              | `0x005460d0`   | 1                | Line end                     |
| `TextOutA`            | `0x005460fc`   | 1                | Direct text output (rare)    |
| `GetTextExtentPointA` | `0x005461ac`   | 1                | Text measurement             |
| `GetTextExtentPoint32A`| `0x00546180`   | 5                | Text measurement             |
| `Polygon`             | `0x005461a4`   | 2                | Polygon drawing              |
| `RoundRect`           | `0x00546178`   | 1                | Rounded rectangle            |
| `CreateFontA`         | `0x005460dc`   | (call count unavailable) | Font creation |
| `DeleteObject`        | `0x005460e0`   | ~10              | GDI object cleanup           |

### 3.2 MFC CDC Wrapper Architecture

The direct GDI call counts are low because MFC's `CDC` class wraps GDI functions through **virtual function calls**. For example:
- `pDC->TextOut(...)` → `call [ecx+<vtable_offset_for_TextOut>]`
- `pDC->Rectangle(...)` → `call [ecx+<vtable_offset_for_Rectangle>]`

These indirect calls go through the vtable of the `CDC`-derived object (`CPreviewDC` vtable at `0x0055bd20`), not through the import thunks. The direct GDI32 thunks are in small MFC wrapper functions, not in the application's drawing code.

This means the chart drawing function cannot be identified simply by counting direct GDI calls. We must instead identify it through:
- Function size and structure
- Analysis of the `CJHoraView::OnDraw` vtable slot
- Reference patterns to chart-related data structures

### 3.3 Candidate Drawing Functions (via GDI Call Density)

Despite the MFC indirection, some functions show unusually high direct GDI use (likely because they bypass CDC for performance, or are utility functions):

| Address    | Drawing Ops | Key Operations                              | Likely Purpose                           |
|------------|-------------|---------------------------------------------|------------------------------------------|
| `0x0050D683` | 31          | `SelectObject`(12), `PatBlt`(11), `SetTextColor`(5) | Text/print rendering utility |
| `0x00488C80` | 12          | `CreateSolidBrush`(4), `CreatePen`(4), `Rectangle`, `RoundRect`, `Ellipse`, `Polygon` | **Chart cell drawing** — creates pens/brushes, draws grid cells |
| `0x004553C0` | 9           | `Rectangle`(6), `CreateSolidBrush`, `CreatePen`, `Ellipse` | **Grid/rectangle rendering** |
| `0x00481670` | 9           | `CreateSolidBrush`(5), `Ellipse`(3), `CreatePen` | **Circular chart drawing** (East Indian) |
| `0x00427470` | 6           | `CreateSolidBrush`(3), `CreatePen`, `Polygon`, `Ellipse` | **Polygon-based drawing** (North Indian diamond?) |
| `0x004492C0` | 6           | `CreatePen`(3), `Rectangle`(3)              | **Grid border drawing** |
| `0x004E8880` | 6           | `GetTextExtentPoint32A`(4), `CreateSolidBrush`(2) | **Text measurement/rendering** |

Functions `0x004553C0` and `0x00488C80` are the most promising candidates for the core chart grid drawing logic (creating multiple pens/brushes and drawing 6+ rectangles matches the 4×4 grid + center box pattern).

### 3.4 Why We Cannot Yet Identify the Main OnDraw

The `CJHoraView` class (string at `0x0058D33C`) inherits from `CView`/`CScrollView`. Its `OnDraw` virtual function would be the main chart rendering entry point. However:
- No vtable for `CJHoraView` has been conclusively identified
- MFC's `CView` vtable has `OnDraw` at a well-known slot index, but without knowing which vtable belongs to `CJHoraView`, we cannot locate it
- The `CScrollView` vtable at `0x0055B7CC` (labeled `CMDIChildWnd` in function_map.md) may actually be related — further analysis needed

---

## 4. Chart Style Analysis (from Help File + Reimplementation)

### 4.1 South Indian (Jupiter-ruled, rasi-based)

**Characteristics:**
- 12 rasis at **fixed positions** in a 4×4 grid (center 2×2 empty)
- Rasis progress **counterclockwise** from Aries at bottom-left
- Ar→Ta→Ge→Cn→Le→Vi→Li→Sc→Sg→Cp→Aq→Pi (moving up then right then down then left)
- Center box displays ayanamsa information
- This is a **rasi-based** format: same rasi always in the same box

**Grid layout (reversed-engineered from `chart_widget.py`):**

```
        Col 0      Col 1      Col 2      Col 3
Row 0:  CANCER     LEO        VIRGO      LIBRA
Row 1:  GEMINI     [center]   [center]   SCORPIO
Row 2:  TAURUS     [center]   [center]   SAGITTARIUS
Row 3:  ARIES      PISCES     AQUARIUS   CAPRICORN
```

**Coordinate mapping** (from `_SOUTH_INDIAN_GRID` in `chart_widget.py:43`):
```python
(3,0,Aries), (3,1,Pisces), (3,2,Aquarius), (3,3,Capricorn),
(2,3,Sagittarius), (1,3,Scorpio),
(0,3,Libra), (0,2,Virgo), (0,1,Leo), (0,0,Cancer),
(1,0,Gemini), (2,0,Taurus)
```

**Planet placement:** Longitude-sorted within each cell. If >2 planets in a rasi, a 2-column sub-grid is used; otherwise 1 column. Planets placed below the rasi header label.

### 4.2 North Indian (Venus-ruled, bhava-based)

**Characteristics:**
- 12 **houses at fixed positions**, not rasis
- House 1 (lagna/Asc) always at **top-right corner**
- House numbers increase **counterclockwise**
- 4×4 grid with house number labeling:

```
        Col 0      Col 1      Col 2      Col 3
Row 0:  10         11         12          1   (Asc)
Row 1:   9       [center]   [center]     2
Row 2:   8       [center]   [center]     3
Row 3:   7          6          5          4
```

**House-to-rasi mapping:** `rasi = (asc_rasi + house_num - 1) % 12`

- The rasi number (1–12) is shown in each house box
- Center box shows ascendant info (e.g., "Asc: Cn")
- This is a **bhava-based** format: same house number always in the same box

**Grid mapping** (from `_draw_north_indian` in `chart_widget.py:159`):
```python
(0,0,10), (0,1,11), (0,2,12), (0,3,1),      # Row 0
(1,3,2),  (2,3,3),  (3,3,4),  (3,2,5),      # Right side down
(3,1,6),  (3,0,7),  (2,0,8),  (1,0,9),      # Bottom row + left side up
```

**Note:** The original JHora draws the North Indian chart with a distinctive **diamond border** connecting house corners, rather than simple rectangles. This "kite" or "diamond" border style is generated by drawing polygons (`Polygon` GDI call at `0x00427470` may be this).

### 4.3 East Indian (Sun-ruled, rasi-based)

**Characteristics:**
- **Circular layout** with 12 wedges (30° each)
- Rasis at fixed positions: Ar at top-right, going **counterclockwise**
- Outer ring (boundary circle), inner circle, and 12 spoke lines
- Wedges labeled with rasi name or "Asc" for lagna rasi
- Planets placed **along spoke lines** between inner and outer rings
- Center displays ayanamsa + lagna info

**Layout parameters:**

| Parameter | Value |
|-----------|-------|
| Outer radius | `min(w,h)/2 - 12` |
| Inner radius | `outer_r * 0.275` (center text area) |
| Mid radius | `(outer_r + inner_r) / 2` (rasi name position) |
| Planet position | Along spokes, evenly spaced between inner and outer |
| Start angle | -90° (top = 0° reference) |
| Wedge angle | 30° per rasi |

**Angle mapping:** Wedge `i` (rasi value `i`, 0=Aries) is centered at `i * 30° - 90° + 15°`.

**Note:** The original JHora draws this chart without the enclosing rectangle mentioned in the help file (though some practitioners add one). The `Ellipse` and `CreateSolidBrush` calls at `0x00481670` likely handle the circular ring rendering.

---

## 5. Planet Positioning Logic (All Styles)

All three styles share a common planet layout algorithm:

### 5.1 Data Structure

Each cell/wedge contains a list of planets occupying that rasi, sorted by longitude:
```python
planets_by_rasi: Dict[Rasi, List[Tuple[Graha, float]]]
```

### 5.2 Layout Within Cell

```python
n = len(planets)
cols = 2 if n > 2 else 1
rows = (n + cols - 1) // cols
```

- **1–2 planets:** single column, vertically stacked
- **3+ planets:** 2-column grid, filled column-first
- Planet glyph rendered at calculated `(col, row)` position within cell
- Retrograde indicator "R" appended after glyph (in red: `#e94560`)
- Navamsa overlay: D-9 sign short name in small green text (`#00ff88`)

### 5.3 Planet Glyph
- Uses `graha.short_name` (e.g., "Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")
- Color-coded per planet:
  | Planet | Color |
  |--------|-------|
  | Sun    | `#FF6B35` (orange) |
  | Moon   | `#C0C0C0` (grey) |
  | Mars   | `#FF4444` (red) |
  | Mercury | `#44CC44` (green) |
  | Jupiter | `#FFB347` (amber) |
  | Venus  | `#FF69B4` (pink) |
  | Saturn | `#4488FF` (blue) |
  | Rahu   | `#8B4513` (brown) |
  | Ketu   | `#FFD700` (gold) |

### 5.4 Lagna Highlighting
- The cell/wedge containing the ascendant rasi is highlighted with a thicker border (`2.5px` vs `1.5px`) in accent color (`#e94560`)
- Center box shows lagna info (rasi short name, ayanamsa value)

---

## 6. Identified Helper Functions in Binary

### 6.1 String/Text Helpers

| Address   | Purpose | Evidence |
|-----------|---------|----------|
| `0x00513C3E` | **String concatenation** | Called ~310 times within `0x004CB240` (yoga builder); used to build description strings |
| `0x00513AB5` | **String/object initialization** | Called 8× |
| `0x00513BEE` | **String utility** | Called 2× |
| `0x00513D4A` | **String utility** | Called 2× |
| `0x00513DBE` | **String utility** | Called 6× |
| `0x00513E91` | **String utility** | Called 1× |
| `0x00513ECD` | **String utility** | Called 8× |

These helpers are in the `0x00513xxx` range, which appears to be a **string utility library** (MSVC's `CString` or custom string class). The 310× call count from the yoga builder alone confirms `0x004CB240` is text-oriented, not graphical.

### 6.2 Drawing Helpers (GDI Wrappers)

Due to MFC's CDC vtable indirection, the actual drawing functions are hard to identify statically. The functions in §3.3 are the best candidates isolated so far.

---

## 7. GDI32 Capabilities Available for Drawing

The original binary has 91 GDI functions available. The following are most relevant to chart drawing:

### 7.1 Geometry Primitives

| Function    | Purpose for Chart Drawing |
|-------------|---------------------------|
| `Rectangle` | Filled cell backgrounds (4×4 grid cells) |
| `RoundRect` | Rounded cell corners (if used — only 1 call site) |
| `Ellipse`   | Outer/inner rings for East Indian chart |
| `Polygon`   | North Indian diamond/kite border style |
| `MoveToEx`/`LineTo` | Grid lines, spoke lines |
| `PatBlt`    | Pattern fills |

### 7.2 Text Rendering

| Function              | Purpose |
|-----------------------|---------|
| `TextOutA`            | Planet glyphs, rasi labels (via CDC wrapper) |
| `ExtTextOutA`         | Extended text with clipping |
| `SetTextColor`        | Per-planet coloring |
| `SetBkColor`/`SetBkMode` | Transparent text background |
| `SetTextAlign`        | Text alignment |
| `GetTextExtentPointA` / `GetTextExtentPoint32A` | Text measurement for layout |
| `CreateFontA`         | Font creation for labels |
| `CreateFontIndirectA` | Font creation with full LOGFONT |

### 7.3 Graphics State

| Function          | Purpose |
|-------------------|---------|
| `CreatePen`       | Border pens (different widths/colors for cells, lagna highlight) |
| `CreateSolidBrush` | Fill brushes for cells, center box |
| `CreateBrushIndirect` | Hatched/pattern brushes |
| `SelectObject`    | Selecting pens, brushes, fonts into DC |
| `DeleteObject`    | GDI object cleanup |

### 7.4 Coordinate System

| Function                | Purpose |
|-------------------------|---------|
| `SetMapMode`            | Coordinate mapping |
| `SetViewportOrgEx`      | Viewport origin |
| `SetWindowOrgEx`        | Window origin |
| `DPtoLP`/`LPtoDP`      | Coordinate conversion |

### 7.5 Bitmap/Print Support

| Function    | Purpose |
|-------------|---------|
| `BitBlt`    | Bit block transfer (double buffering?) |
| `StartDocA`/`StartPage`/`EndPage`/`EndDoc` | Print support |
| `StretchDIBits` | DIB rendering to printer |

---

## 8. Key Findings

1. **Function `0x004CB240` is NOT the chart rendering function.** It is a **yoga description text builder** that evaluates 406+ astrological conditions and concatenates result strings via a string-append helper (`0x00513C3E`, called ~310×). The `function_map.md` entry for this function is incorrect.

2. **Chart rendering is MFC vtable-based.** The actual drawing goes through `CJHoraView::OnDraw` → `CDC::` virtual methods → GDI32 thunks. Direct GDI calls are only in MFC wrapper functions, not in application code. This makes static identification of the drawing function difficult.

3. **Three chart styles use simple geometry.** All three styles (South Indian 4×4 grid, North Indian 4×4 grid+border, East Indian 12-spoke circle) use only basic GDI primitives — no complex paths, no bitmap fonts, no GDI+.

4. **Planet glyphs are GDI text.** The original uses `TextOutA` (via `CDC::TextOut`) with the small string font to render planet glyphs ("Su", "Mo", etc.) — not custom bitmaps or icon fonts. Colors are set via `SetTextColor` per planet.

5. **North Indian diamond border.** The North Indian style likely uses `Polygon` (calls found at `0x00427470`) to draw the kite/diamond border connecting outer house corners — a distinctive visual feature not yet implemented in our port.

6. **Double buffering.** The `BitBlt` and `PatBlt` calls suggest the chart may be rendered to an offscreen bitmap and then blitted to the window, or printed via standard MFC print architecture.

---

## 9. Reimplementation Status (from `chart_widget.py`)

### 9.1 Completed

| Feature | Status | Location |
|---------|--------|----------|
| South Indian chart | ✅ Full implementation | `chart_widget.py:128` — `_draw_south_indian()` |
| North Indian chart | ✅ Basic implementation | `chart_widget.py:154` — `_draw_north_indian()` |
| East Indian chart | ✅ Basic implementation | `chart_widget.py:188` — `_draw_east_indian()` |
| Planet placement grid | ✅ 1/2 column auto-layout | `chart_widget.py:278` — `_draw_planets()` |
| Planet coloring | ✅ Per-planet distinct colors | `chart_widget.py:31` — `PLANET_COLORS` |
| Retrograde indicator | ✅ "R" suffix in accent color | `chart_widget.py:312` |
| Lagna highlighting | ✅ Thicker border + "Asc" label | `chart_widget.py:251` — `_draw_header()` |
| Navamsa overlay | ✅ D-9 sign label in green | `chart_widget.py:317` |
| Dignity column | ✅ Short dignity codes | via `ChartData` dignity field |

### 9.2 Missing vs Original

| Feature | Original JHora | Our Implementation | Priority |
|---------|---------------|-------------------|----------|
| North Indian diamond border | `Polygon`-based kite border | Simple rectangles only | Medium |
| East Indian planet positioning | Along spokes, may use different spacing | Simple linear spacing | Low |
| Font selection | `CreateFontA` with specific typeface | `QFont("sans-serif")` | Low |
| Print support | Full MFC print architecture | Not implemented | Low |
| Multi-wheel (natal + transit) | Available in original | Not implemented | Future |
| Double buffering | `BitBlt`-based offscreen | Not needed (Qt handles) | None |

---

## 10. Methodology

### 10.1 Tools Used
- **objdump** (binutils) — PE section analysis, import table extraction
- **Python struct analysis** — raw byte-level search for call sites, string references, GDI thunk cross-references
- **strings** — ASCII string extraction from `.rdata` and `.data` sections
- **Reko decompiler** — pseudocode decompilation (partial success; many large functions failed to decompile)
- **function_map.md** — reference for known function addresses and sizes

### 10.2 Key Analysis Techniques
1. **String reference counting:** Counted `push imm32` instructions targeting `.data` section to identify text-processing functions
2. **GDI call site analysis:** Found all `FF 15` (call dword ptr [import]) instructions targeting GDI32 thunks, grouped by function region
3. **Function boundary detection:** MSVC prologue pattern (`55 8B EC` = `push ebp; mov ebp, esp`) to identify function starts
4. **String decoding:** Read ASCII strings at `.data` addresses referenced by the yoga builder function

### 10.3 Limitations
- **No debug symbols:** MSVC 6.0 without COFF symbols, /PDB, or RTTI
- **No xref graph:** Without IDA Pro/Ghidra, all cross-references must be computed manually via raw byte search
- **Partial Reko output:** Many large functions failed to decompile to pseudocode (the `.dis` files only cover ~50% of the 3,150 functions)
- **MFC vtable indirection:** CDC virtual calls cannot be statically resolved to specific GDI calls without runtime tracing

---

## Appendix A: Yoga String Table (Partial)

The 406 strings referenced by function `0x004CB240` include:

```
0x00579584: Brahma            0x0057E178: Jaya
0x0057E180: Bhadra            0x0057F660: Poverty
0x0057FA24: Indra             0x0057FB24: Gadaa
0x0057FD98: Kamala            0x0057FDD4: Musala
0x0057FDF8: Maalaa            0x00580218: Vishnu
0x005802B0: Lakshmi           0x005802C0: Gouri
0x005804A4: Gandharva         0x00580608: Sarpa
0x00580754: Parivraja/Pravrajya  0x00587018: Comforts, good looks and character
0x00587068: Anaphaa           0x005870B8: Sunaphaa
0x0058711C: Duradhara         0x005896E4: Sankha
0x00589838: Kaahala           0x005898A8: Parvata
0x0058A094: Vajra             0x0058A170: Sringaataka
0x0058A200: Sakata            0x0058A3EC: Soola
0x0058A610: Rajju             0x0058A77C: Kemadruma
```

## Appendix B: Segments Not Yet Decompiled

The following large functions in the `.text` segment likely contain chart-drawing logic but were not decompiled by Reko (no `.dis` output was generated):

- `0x004553C0` (9 GDI ops, 6× Rectangle) — grid drawing
- `0x00481670` (9 GDI ops, 5× CreateSolidBrush, 3× Ellipse) — circular chart drawing
- `0x00488C80` (12 GDI ops, 4× CreateSolidBrush, 4× CreatePen) — chart cell drawing
- `0x0050D683` (31 GDI ops, 12× SelectObject, 11× PatBlt) — text/print rendering

These should be targeted for future decompilation (e.g., via Ghidra or IDA Pro) to extract the exact drawing algorithms for the North Indian diamond border and East Indian circle chart.
