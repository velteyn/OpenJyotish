# Reverse Engineering Analysis: JHora Chart Drawing Engine

## 1. Introduction

**Purpose:** Reverse engineer the original `jhora.exe` binary's chart drawing logic to guide our PyQt6 reimplementation.

**Binary:** `jhora.exe` — PE32 GUI, C++ MFC (VC++ 6.0), statically linked MFC, x86, 3,150 functions.

**Key sections:**

| Section  | VMA          | Size     | File offset | Contents                  |
|----------|--------------|----------|-------------|---------------------------|
| `.text`  | `0x00401000` | 1,324,942 B | `0x1000`    | Executable code (3,150 fns) |
| `.rdata` | `0x00546000` | 473,466 B  | `0x146000`  | Read-only data (strings, vtables, import thunks) |
| `.data`  | `0x00574000` | 868,232 B  | `0x174000`  | Read-write data (INI keys, language strings, yoga texts) |
| `.rsrc`  | `0x008A9000` | 702,344 B  | `0x198000`  | Resources (icons, dialogs, help) |

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

## 3. Complete IAT Map (493 entries, 15 DLLs)

### 3.1 Import List

| DLL | Functions | IAT Start |
|-----|-----------|-----------|
| ADVAPI32.dll | 14 | `0x00546000` |
| COMCTL32.dll | 3 | `0x0054603c` |
| GDI32.dll | 91 | `0x0054604c` |
| KERNEL32.dll | 134 | `0x005461bc` |
| OLEAUT32.dll | 11 | `0x005463d8` |
| OLEPRO32.DLL | 1 | `0x00546408` |
| SHELL32.dll | 6 | `0x00546410` |
| USER32.dll | 180 | `0x0054642c` |
| WININET.dll | 6 | `0x00546700` |
| WINSPOOL.DRV | 3 | `0x0054671c` |
| WSOCK32.dll | 2 | `0x0054672c` |
| comdlg32.dll | 5 | `0x00546738` |
| ole32.dll | 18 | `0x00546750` |
| oledlg.dll | 1 | `0x0054679c` |
| swedll32.dll | 18 | `0x005467a4` |

### 3.2 Key GDI32 Drawing Functions

| IAT Address | Function | Calls in .text | Role |
|-------------|----------|-----------------|------|
| `0x0054607c` | `SetTextColor` | 8 | Text color per planet |
| `0x00546080` | `SetBkColor` | 8 | Background color |
| `0x00546084` | `SaveDC` | - | DC state save |
| `0x00546088` | `RestoreDC` | - | DC state restore |
| `0x0054608c` | `SelectObject` | 30 | Pen/brush/font selection |
| `0x00546090` | `SetBkMode` | 2 | Transparent/opaque text bg |
| `0x005460cc` | `MoveToEx` | 3 | Line start (North Indian diamond) |
| `0x005460d0` | `LineTo` | 1 | Line end (North Indian diamond) |
| `0x005460dc` | `CreateFontA` | 3 | Font creation |
| `0x005460e0` | `DeleteObject` | 6 | GDI cleanup |
| `0x005460fc` | `TextOutA` | 1 | Text output (via CDC wrapper only!) |
| `0x00546100` | `ExtTextOutA` | 9 | Text with clipping (direct calls) |
| `0x00546174` | `CreateFontIndirectA` | 5 | Full LOGFONT creation |
| `0x00546180` | `GetTextExtentPoint32A` | 5 | Text measurement |
| `0x0054619c` | `CreatePen` | 14 | Border pen creation |
| `0x005461a0` | `Rectangle` | 3 | Cell drawing (South Indian) |
| `0x005461a4` | `Polygon` | 3 | Polygon shapes |
| `0x005461a8` | `Ellipse` | 7 | Circle chart (East Indian) |
| `0x005461ac` | `GetTextExtentPointA` | 1 | Legacy text measurement |
| `0x005461b4` | `CreateSolidBrush` | - | Solid brush creation |

## 4. KEY DISCOVERY: Direct GDI32 IAT Calls from Application Code

### 4.1 The Real Architecture

Previously we believed JHora's chart drawing went through MFC CDC virtual functions (vtable dispatch). **This is WRONG.** The actual architecture:

1. JHora's application code makes **direct `call [IAT]` calls** to GDI32 functions
2. MFC CDC wrapper thunks exist at `0x004FA249`–`0x004FA2FF` but are **never called from .text** — they're only referenced in `.rdata` (vtables)
3. The 0 refs in .text for CDC thunks proves JHora bypasses CDC for chart drawing

**Evidence:** 
- Zero `E8 rel32` (direct relative call) instructions in .text target any of the CDC wrapper addresses
- All 3 Rectangle calls (at `0x44BBF0`, `0x44BC60`, `0x44BD50`) are direct `call [GDI32.Rectangle]`
- The CDC wrappers at `0x4FAxxx` are only referenced in `.rdata` vtables (5-6 refs each)

### 4.2 Why This Matters

JHora's OnDraw function calls GDI32 directly with `pDC->m_hDC` as the first parameter (ECX contains `this` = the CView, and it extracts the HDC from the CDC parameter). This means:
- **No MFC wrapper overhead** — the compiler inlined CDC member function calls
- **Direct GDI calls in the binary** — easier to identify by searching for `FF 15` (call [IAT]) instructions
- **All chart styles use the same pattern** — direct GDI calls for drawing primitives

## 5. Identified Chart Rendering Functions

### 5.1 Function Map (Actual Chart Drawing Code)

| Function | VA Range | GDI Calls | Purpose | Evidence |
|----------|----------|-----------|---------|----------|
| `fn44B9B6` | `0x44B9B6`–`0x44BDF0` | Rectangle×3, CreatePen×3, CreateBrushIndirect×2 | **South Indian chart grid** (rect angular grid) | 3 pens with 3 rectangles = border + cell lines; has EqualRect check for rect comparison |
| `fn00481670` | `0x481670`–`0x481A50` | Ellipse×3, CreateSolidBrush×5, CreatePen | **East Indian circular chart** (concentric rings) | 3 Ellipse calls = outer ring, inner ring, center circle; 5 brushes for ring fills |
| `fn0051E3B0` | `0x51E3B0`–`0x51E470` | MoveToEx×1, LineTo×1 | **North Indian diamond lines** | MoveToEx+LineTo pair draws one diamond side; called in loop for 12 sides |
| `fn00453220` (or 0x44C170) | `0x44C170`–`0x44C590` | GetWindowRect×1, switch table | **Chart type dispatcher** | 23-entry jump table based on global `0x8A4B58`; dispatches to different drawing functions |

### 5.2 Key Observations

1. **fn44B9B6** (0x44B9B6-0x44BDF0, SEH prologue, `ret 0Ch`):
   - `this` in EBP (`8B E9` = `mov ebp, ecx`)
   - Checks global `[0x8A4B58]` against `0x44` (68 = 'D')
   - Sets global `[0x71FBB0]` to 2 or 5 based on check
   - Calls vtable method at `[this+0x108]` (likely `GetDocument()` or similar)
   - Loads data starting at `[ebp+size]` (object member at some offset)
   - Draws 3 rectangles with 3 distinct pen styles and 2 brushes
   - Has loop iterating 16-byte data structures (planet data for chart cells?)
   - **This is NOT a simple cell renderer** — the 3 rectangles with different pens are likely:
     - Rectangle 1: Outer chart border (thick pen)
     - Rectangle 2: Inner grid lines (thin pen) — or lagna highlight 
     - Rectangle 3: Supplementary highlight (e.g., current Dasha highlight)
   - The actual 12 cells may be drawn by FillRect/PatBlt calls or through a bitmap approach

2. **fn00481670** (0x481670, likely has ellipse drawing):
   - Uses 3× Ellipse, 5× CreateSolidBrush, CreatePen
   - Pattern matches East Indian chart which needs:
     - Outer concentric circle
     - Inner circle (rasi name ring boundary)  
     - Center circle (for ayanamsa text)
   - The 5 brushes likely fill: background, ring areas, center area

3. **fn0051E3B0** (0x51E3B0):
   - MoveToEx + LineTo pair
   - Draws a single line segment
   - Used in loop for North Indian diamond chart (12 line segments = diamond border)

4. **Dispatcher at 0x44C170**:
   - Switch on `[0x8A4B58]` with values 0-0x48 (72)
   - 23 entries in jump table = likely 23 chart types (16 varga + 7 special)
   - Each entry dispatches to a specific drawing function

### 5.3 Text Rendering Calls

| Function | ExtTextOutA | DrawTextA | SetTextColor | Purpose |
|----------|-------------|-----------|--------------|---------|
| `fn0050DD04` area | 4 | 0 | 1 | Planet glyph text + rasi labels |
| `fn00510AD0` | 0 | 1 | 2 | Header/table text rendering |
| `fn00528533`/`fn005288D4` | 2 | 0 | 0 | ExtText with SetBkColor |
| `fn005366A7` | 1 | 0 | 0 | Text + MoveToEx (chart annotations) |
| `fn00536B57` | 0 | 1 | 0 | Text + MoveToEx |

The **9 ExtTextOutA** calls handle most chart text (planet names, rasi labels, degrees). The **single TextOutA** call at `0x4FA280` is inside the CDC wrapper (never called directly).

## 6. Function Structure of Chart Drawing Functions

### 6.1 Structure of fn44B9B6 (0x44B9B6–0x44BDF0)

**Prologue (0x44B9B6–0x44B9E3):**
- SEH setup: `push -1; push handler 0x53BDE8; push eax; mov eax, fs:[0]; mov fs:[0], esp`
- `sub esp, 0x58` = 88 bytes of locals
- `mov ebp, ecx` — `ecx` = `this` (CView*)
- Check global `[0x8A4B58]`:
  - If `== 0x44` (68): set `[0x71FBB0] = 2`
  - Else: set `[0x71FBB0] = 5`

**Document access (0x44B9F3–0x44BA10):**
- `mov eax, [ebp]` — get vtable pointer
- `call [eax + 0x108]` — **vtable slot 66** = `CView::GetDocument()` returns `CDocument*`
- `mov ebx, eax` — `ebx = pDoc`
- `mov ecx, [ebx + 0xA12E8]` — `pDoc->member` at offset **0xA12E8** (660,200 = some count)

**Data arrays from `this` (CView):**
- `[ebp + 0x298]` — array of 0x10-byte records (RECT structs: left, top, right, bottom)
- `[ebp + 0x2F8]` — second parallel array of 0x10-byte records
- Loop bounds: `ecx = [ebx + 0x9F118]` (second count) and `[ebx + 0x9F120]` (third count)

**Processing loop (0x44BA3F–0x44BA9D):**
```c
// First loop — bounds checking
for (eax = 0; eax < ecx; eax++) {
    RECT* pRect = &view->rects[eax];  // each 0x10 bytes
    if (dx >= pRect->left && dx < pRect->right
        && dy >= pRect->top && dy < pRect->bottom) {
        found = true;
        // Copy RECT: [esp+0x44..0x50] = *pRect
        break;
    }
}
```

**Rectangle drawing (3×):**
```
CreatePen(color=[0x897700], width=1, style=PS_SOLID)  → 0x44BBAF
SelectObject(old_pen)                                    → 0x44BB6E
Rectangle(hdc, x1, y1, x2, y2)                          → 0x44BBEF  (call [0x5461A0])
SelectObject(restore)

CreatePen(color=[0x897718], width=1, style=PS_SOLID)  → 0x44BC16
SelectObject(old_pen)                                    → 0x44BC1C
Rectangle(hdc, x1', y1', x2', y2')                     → 0x44BC5D
SelectObject(restore)

CreatePen(color=[0x897700], width=1, style=PS_SOLID)  → 0x44BD11  (reuse color from [0x897700])
SelectObject(old_pen)
Rectangle(hdc, x1'', y1'', x2'', y2'')                  → 0x44BD57
SelectObject(restore)
```

**Return:** `ret 0Ch` — 3 dword arguments (`this` in ECX + 3 stack params = HDC, param2, param3)

**Key addresses:**
| Address | Role |
|---------|------|
| `[0x008A4B58]` | Chart type (0–72, 0x44=68 triggers special mode) |
| `[0x0071FBB0]` | Mode flag (2 or 5) |
| `[0x00897700]` | Pen color 1 (for outer border + third rectangle) |
| `[0x00897718]` | Pen color 2 (for middle rectangle) |
| `[ebp + 0x298]` | RECT array 1 on CView (each entry 16 bytes) |
| `[ebp + 0x2F8]` | RECT array 2 on CView |
| `[ebx + 0xA12E8]` | Count from CDocument |
| `[ebx + 0x9F118]` | Count 2 from CDocument |
| `[ebx + 0x9F120]` | Count 3 from CDocument |

### 6.2 Structure of fn00481670 (0x481670–0x481A50)

**Size:** ~0x3E0 bytes (992 bytes), large stack frame (`sub esp, 0xA34` = 2,612 bytes locals).

**Data access:**
```c
// Accessed from `this` (ecx = CView*):
int cx = this->member_0x88 + 0x2C;
int cy = this->member_0x90 - 0x18;
int dx = this->member_0x84;   // x origin
int dy = this->member_0x8C;   // y origin
int rx = (cx - dx) / 3;       // radius divider (uses 0x2AAAAAAB magic for /3)
int ry = (cy - dy) / 3;       // same division

// Complex division by 3:
//   mov eax, 0x2AAAAAAB
//   imul ebx                  ; signed multiply edx:eax = ebx * 0x2AAAAAAB
//   sar edx, 1                ; shift result
//   mov eax, edx
//   shr eax, 0x1F             ; fix sign
//   add edx, eax              ; final = edx (corrected)
```

**Colors used:**
- `0x00D2D2FF` — light blue (ellipse 1 background via CreateSolidBrush)
- `0x00FFFFFF` — white (ellipse 2 background)
- `0x00D2FFD2` — light green (ellipse 3 background)
- `[0x0089784C]` — pen color from global variable

**3 Ellipse calls with 5 brushes:**
```
// Ring 1 (outermost) — blue fill
CreateSolidBrush(0xD2D2FF)           → 0x481723
SelectObject(brush)
CreatePen(0x89784C, width=2, style=0) → 0x48176E
SelectObject(pen)
Ellipse(hdc, cx-r1, cy-r1, cx+r1, cy+r1)  → 0x4817F0  (call [0x5461A8])
// Complex radius calculation r1:
//   edi = half-width/height of drawing area
//   r1 = edi * (current_step * 21 / 64) — uses fixed-point arithmetic

// Ring 2 (middle) — white fill
CreateSolidBrush(0xFFFFFF)           → 0x481810
SelectObject(brush)
Ellipse(hdc, cx-r2, cy-r2, cx+r2, cy+r2)  → 0x4818CA

// Ring 3 (innermost) — green fill  
CreateSolidBrush(0xD2FFD2)           → 0x4818EA
SelectObject(brush)
Ellipse(hdc, cx-r3, cy-r3, cx+r3, cy+r3)  → followed by more ellipses
```

The radius calculations use fixed-point division by 6 (magic number `0x2AAAAAAB` for /3, and `0x88888889` for /6) to compute proportional ring positions.

**Return:** Not SEH — uses `push ebp; mov ebp, esp; and esp, -8` (stack alignment at -8)

### 6.3 Structure of fn0051E3B0 (0x51E3B0) and fn0051E3FC (0x51E3FC)

**fn0051E3B0 (linked-list MovetoEx helper, `ret 0Ch`, 3 args):**
```
this[4] = first HDC/coordinate
this[8] = pointer to next node (linked list)
if this[4] != this[8]:            ; if node has content
    MoveToEx(this[4], X, Y, &pt)  ; move to coordinate
this = this[8]                     ; advance to next
if this != NULL:
    MoveToEx(this, X, Y, &pt)      ; move to next coordinate
return pt                          ; return last position
```
This traverses a linked list drawing MoveToEx at each coordinate.

**fn0051E3FC (MoveToEx+LineTo, `ret 8`, 2 args) — the actual line drawer:**
```
this[4] = HDC
this[8] = destination coordinate
if this[8] != NULL && this[4] != this[8]:
    MoveToEx(this[8], X, Y, NULL)  ; only if dest differs from current
LineTo(this[4], X, Y)              ; draw the line
```
Draws one line segment. Called 12× in a loop for the diamond border.

**Key correction:** The reko decompiler incorrectly shows both calls as MoveToEx. In reality:
- `0x51E3B9`: `mov edi, [0x5460CC]` — loads MoveToEx from IAT
- `0x51E3E6`: `call edi` — calls MoveToEx (through the edi register)
- `0x51E427`: `call [0x5460D0]` — **direct** call to LineTo

## 7. Chart Style Dispatch

### 7.1 Global Variables

| Address | Type | Role |
|---------|------|------|
| `[0x008A4B58]` | int32 | **Chart type indicator** — checked by fn44B9B6, fn44C170 dispatcher |
| `[0x0071FBB0]` | int32 | Mode flag — set to 2 or 5 based on chart type |
| `[0x008A4B5C]` | int32 | Related state variable |
| `[0x008A6D60]` | int32 | Font/theme related |

### 7.2 Dispatcher Implementation

The dispatcher at 0x44C170 uses a **two-level dispatch**:

```asm
mov eax, [0x8A4B58]          ; get chart type (0-72)
cmp eax, 0x48                ; max 72
ja  default_handler           ; if > 72, skip to ret
xor edx, edx
mov dl, [eax + 0x44C254]     ; lookup table → index 0-22
jmp [edx*4 + 0x44C1F8]       ; jump table → 23 entries
```

**Lookup table at 0x44C254** (73 bytes, for chart types 0–72):

| Index range | Values | Meaning |
|-------------|--------|---------|
| 0–12 | mostly 0x00 | Types 0–12 → jump table entry 0 → Rasi chart handler |
| 13–25 | 0x16 (22) | Types 13–25 → invalid/fallback (ret) |
| 26 | 0x02 | → entry 2 = 0x44DCA0 |
| 27 | 0x03 | → entry 3 = 0x44DE30 |
| 28 | 0x04 | → entry 4 = 0x44DEF0 |
| 29 | 0x05 | → entry 5 = 0x44DFB0 |
| 30 | 0x06 | → entry 6 = 0x44E070 |
| 31 | 0x07 | → entry 7 = 0x44E1E3 |
| 32 | 0x08 | → entry 8 = 0x44E1E8 |
| 33 | 0x09 | → entry 9 = 0x44E1D9 |
| 34 | 0x0A | → entry 10 = 0x44E1D4 |
| 35 | 0x16 | Invalid |
| 36–41 | 0x09, 0x0C, 0x0D, 0x0B, 0x0B, 0x0B | Mixed |
| 42–57 | 0x16 | Invalid |
| 58–67 | 0x0E..0x15 | Chart types 60–67 have unique handlers |
| 68–70 | 0x16, 0x16, 0x15 | Types 68–70: 68, 69 = invalid, 70 = entry 21 |
| 71–72 | 0x16, 0x15 | 71 = invalid, 72 = entry 21 |

**Jump table targets (23 entries):**
| Entry | Address | Handler | Purpose |
|-------|---------|---------|---------|
| 0 | 0x44C189 | `jmp 0x44D670` | Rasi (D-1) + D-2, D-3 etc. |
| 1 | 0x44C19D | `jmp 0x44DB40` | D-2 (Hora) |
| 2 | 0x44C1AC | `jmp 0x44DCA0` | Type 26 |
| 3 | 0x44C1B1 | `jmp 0x44DE30` | Type 27 |
| 4 | 0x44C1B6 | `jmp 0x44DEF0` | Type 28 |
| 5 | 0x44C1BB | `jmp 0x44DFB0` | Type 29 |
| 6 | 0x44C1C0 | `jmp 0x44E070` | Type 30 |
| 7–22 | ... | ... | Various varga and special charts |

Value `0x44` (68) in fn44B9B6 corresponds to lookup at index 68 = 0x16 (22 = invalid), so the **fn44B9B6 `0x44` check is a separate special case** before the dispatch, not part of it.

### 7.3 Virtual Function Calls

Both fn44B9B6 and nearby functions call `[this+0x108]` which is a vtable offset in the CView-derived class:
- `0x108` = 264 bytes into vtable = entry number 66 (0-indexed)
- Likely `CView::GetDocument()` which returns a `CDocument*`

The returned document pointer is used to access chart data via member offsets (e.g., `[eax+0x120]`, `[eax-0x0E14]`).

---

## 9. North Indian Chart — Diamond Border

### 9.1 Architecture

Based on RE analysis, the North Indian diamond border is drawn by fn0051E3B0 (MoveToEx + LineTo pair), called 12 times to form the 12-sided diamond shape that connects outer house corners.

The diamond border connects the outer four corners of the 4×3 grid (excluding the center 2×2 area). The shape looks like:

```
    ╱╲╱╲╱╲╱╲
  ╱               ╲
  │               │
  ╲               ╱
    ╲╱╲╱╲╱╲╱
```

Each "side" of the diamond connects adjacent house corners. The Polygon GDI call may also be used for the solid background fill of the diamond shape.

### 9.2 Implementation Plan

In the PyQt6 port, the North Indian diamond can be drawn using QPainterPath:
```python
path = QPainterPath()
path.moveTo(p1)
path.lineTo(p2)  # × 12 for each diamond side
painter.drawPath(path)
```

## 10. Implementation Guidance

### 10.1 How to Match the Original

| Chart Style | RE-Matched Function | Key GDI Pattern | Qt Equivalent |
|-------------|---------------------|-----------------|---------------|
| South Indian | fn44B9B6 | 3× CreatePen + 3× Rectangle | `drawRect` with different `QPen` styles |
| East Indian | fn00481670 | 3× Ellipse + 5× CreateSolidBrush | `drawEllipse` with `QBrush` fills |
| North Indian | fn0051E3B0 (×12 in loop) | MoveToEx + LineTo | `drawLine` or `QPainterPath` with 12 segments |
| Text rendering | fn0050DD04 | 4× ExtTextOutA | `drawText` with `QFont` |
| Chart type dispatch | fn0044C170 | 23-entry switch on `[0x8A4B58]` | Python `if/elif` or dict dispatch |

### 10.2 Key Data Structures

The drawing functions access chart data through:
1. `this` pointer (CView) — ECX/EBP register
2. Virtual function `[this+0x108]` — returns document pointer (CDocument*)
3. Member offsets in the document — house/rasi data at offsets like `[doc+0x120]`, `[doc-0x0E14]`
4. Global variables — `[0x8A4B58]` chart type, `[0x71FBB0]` mode flag

In our Python port, chart data comes from `ChartData` objects (already implemented in `chart_data.py`).

### 10.3 Functions Still Needing Decompilation

These functions likely contain additional chart-drawing details but remain unanalyzed:

| Address | Suspected Role | Contains |
|---------|----------------|----------|
| `0x004553C0` | Grid layout calculator | Rectangle ×6, CreatePen |
| `0x00488C80` | Multi-element drawing | CreateSolidBrush ×4, CreatePen ×4, Rectangle, RoundRect, Ellipse, Polygon |
| `0x00427470` | Polygon shapes (North Indian?) | CreateSolidBrush ×3, CreatePen, Polygon, Ellipse |

---

## 11. Key Findings

1. **Function `0x004CB240` is NOT the chart rendering function.** It is a **yoga description text builder**.

2. **Direct GDI calls, not CDC vtable.** JHora's chart drawing makes direct `call [IAT]` calls to GDI32 functions (CreatePen, Rectangle, Ellipse, ExtTextOutA, etc.) — NOT through MFC CDC wrapper thunks. The CDC wrappers at 0x4FAxxx are only in .rdata vtables, never called from code.

3. **Three separate rendering functions** for the three chart styles:
   - fn44B9B6 (0x44B9B6): South Indian — 3 pens + 3 rectangles + 2 brushes
   - fn00481670 (0x481670): East Indian — 3 ellipses + 5 brushes  
   - fn0051E3B0 (0x51E3B0): North Indian — MoveToEx + LineTo (called ×12)

4. **Chart type dispatch** at fn0044C170 switches on global `[0x8A4B58]` with 23 entries.

5. **Text rendering** uses 9× ExtTextOutA (direct) and 5× DrawTextA (direct) calls, plus the single TextOutA at the CDC wrapper (never called from app code).

6. **Complete IAT** mapped: 493 entries across 15 DLLs, including 91 GDI32 functions.

---

## 12. Reimplementation Status (from `chart_widget.py`)

### 12.1 Completed

| Feature | Status | Location |
|---------|--------|----------|
| South Indian chart | ✅ Full implementation | `chart_widget.py` — `_draw_south_indian()` |
| North Indian chart | ✅ Basic implementation | `chart_widget.py` — `_draw_north_indian()` |
| East Indian chart | ✅ Basic implementation | `chart_widget.py` — `_draw_east_indian()` |
| Planet placement grid | ✅ 1/2 column auto-layout | `chart_widget.py` — `_draw_planets()` |
| Planet coloring | ✅ Per-planet distinct colors | `chart_widget.py` |
| Retrograde indicator | ✅ "R" suffix in accent color | `chart_widget.py` |
| Lagna highlighting | ✅ Thicker border + "Asc" label | `chart_widget.py` |
| Navamsa overlay | ✅ D-9 sign label in green | `chart_widget.py` |
| Dignity column | ✅ Short dignity codes | via `ChartData` |

### 12.2 Missing vs Original

| Feature | Original JHora | Our Implementation | Priority |
|---------|---------------|-------------------|----------|
| North Indian diamond border | MoveToEx+LineTo ×12 | Simple rectangles only | Medium |
| East Indian planet positioning | Along spokes, specific spacing | Simple linear spacing | Low |
| Font selection | CreateFontA with specific typeface | QFont("sans-serif") | Low |
| Print support | Full MFC print architecture | Not implemented | Low |
| Chart type dispatch | 23-entry switch/case | Not implemented | Future |

---

## 13. Methodology

### 13.1 Tools Used
- **Reko decompiler** — x86 disassembly + pseudocode (partial coverage)
- **Python capstone** — x86 instruction decoding (for call site analysis)
- **Python struct analysis** — raw byte-level search for IAT call sites, string references
- **PE header parsing** — section layout, import table extraction

### 13.2 Key Analysis Techniques
1. **IAT call site search:** Find all `FF 15` (call [IAT]) instructions in .text section, resolve via IAT map
2. **Function boundary detection:** SEH prologue (`64 A1 00 00 00 00 6A FF 68 ...`) and standard prologue (`55 8B EC`)
3. **GDI call clustering:** Group IAT calls by function region to identify rendering functions
4. **IAT map construction:** Parse PE import directory to build (IAT_VA → DLL.function) mapping

### 13.3 Limitations
- **No debug symbols:** MSVC 6.0 without COFF symbols, /PDB, or RTTI
- **No xref graph:** All cross-references computed via raw byte search
- **Partial Reko output:** Many large functions failed to decompile
- **Function boundary ambiguity:** SEH-based functions and FPO-optimized functions hard to identify
