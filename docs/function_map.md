# Function Map — Jagannatha Hora 8.0 Lite

## Overview

- **Total functions detected**: 3,150
  - `fcn.*` (auto-named): 2,484
  - `method.*` (C++ methods from vtables): 650
  - `sub.*` (thunks to DLL imports): 14
  - Named entry points: `entry0`, `main`
- **External DLL imports**: ~250+ across 13+ DLLs
- **Build**: MSVC++ 6.0, statically linked MFC, no debug symbols, no RTTI

## Named Entry Points

| Address | Name | Size | Description |
|---------|------|------|-------------|
| `0x00502c6b` | `entry0` | 253 B | Program entry point (calls `main`) |
| `0x00511107` | `main` | 24 B | `WinMain` — MFC application entry |

## JHora Class Names Found in Data

| Address | String | Section | Notes |
|---------|--------|---------|-------|
| `0x005743d8` | `CJHoraDoc` | `.data` | Document class (MFC `CDocument`) |
| `0x0058d33c` | `CJHoraView` | `.data` | View class (MFC `CView`/`CScrollView`) |

> These are the only two application-specific class name strings. No other debug symbols or RTTI are present.

## MFC Framework Classes Identified via Vtable Analysis

### Application Architecture
| Vtable Address | Class | Description |
|---------------|-------|-------------|
| `0x0055a724` | `CWinApp` | Application object (vtable slot 16) |
| `0x0055a724` | `CWinThread` | Thread base (vtable slot 40) |
| `0x0055a724` | `COleTemplateServer` | OLE server registration |
| `0x0055a724` | `COleObjectFactory` | OLE object factory |
| — | `CSingleDocTemplate` | SDI document template (vtable at `0x0055a7f8`) |
| — | `CDocManager` | Document template manager (vtable at `0x0055c3a0`) |
| — | `CMirrorFile` | File mirroring base (many vtables use slot 8) |

### Document/View
| Class | Description |
|-------|-------------|
| `CJHoraDoc` | JHora document class (string only, no identified vtable) |
| `CJHoraView` | JHora view class (string only, no identified vtable) |

### Frame Windows
| Vtable Address | Class | Description |
|---------------|-------|-------------|
| `0x0055b7cc` | `CMDIChildWnd` | MDI child frame |
| `0x0055b294` | `CMiniDockFrameWnd` | Mini docking frame |
| `0x0055ce9c` | `CMiniFrameWnd` | Mini frame window |
| `0x0055b294` | `CFrameWnd` | Frame window base (slot 12, 120, 136, 140, 144, etc.) |

### Controls
| Vtable Address | Class | Description |
|---------------|-------|-------------|
| `0x0055ab2c` | `CToolBar` | Toolbar control |
| `0x0055af1c` | `CStatusBar` | Status bar |
| `0x0055b1ac` | `CDockBar` | Docking bar |
| `0x0055bc14` | `CDialogBar` | Dialog bar |
| `0x0055b56c` | `CSplitterWnd` | Splitter window |
| `0x0055cc04` | `CToolTipCtrl` | Tooltip control |

### Dialogs
| Vtable Address | Class | Description |
|---------------|-------|-------------|
| (ubiquitous) | `CDialog` | Base dialog (most vtables inherit from this) |
| `0x0055ba9c` | `CPrintDialog` | Print dialog |
| (in `CPrintDialog` vtable) | `CFileDialog` | File open/save dialog |
| `0x0055c408` | `CNewTypeDlg` | New document type dialog |
| `0x0055d0f8` | `COleBusyDialog` | OLE busy dialog |

### GDI
| Vtable Address | Class | Description |
|---------------|-------|-------------|
| `0x0055bd20` | `CPreviewDC` | Print preview DC |
| `0x0055bd20` | `CDC` | Device context base |
| `0x0055c65c` | `CFont` | Font GDI object |

### Collections
| Vtable Address | Class | Description |
|---------------|-------|-------------|
| `0x0055b9c8` | `CPtrList` | Pointer list |
| `0x0055cfd0` | `CPtrArray` | Pointer array |
| `0x0055bba4` | `CMapPtrToPtr` | Pointer-to-pointer map |
| `0x0055cb4c` | `CMapStringToPtr` | String-to-pointer map |
| `0x0055bb74` | `CHandleMap` | Handle-to-object map |

### Exceptions
| Vtable Address | Class | Description |
|---------------|-------|-------------|
| `0x0055b950` | `CMemoryException` | Out-of-memory exception |
| `0x0055b968` | `CNotSupportedException` | Unsupported operation |
| `0x0055d00c` | `COleException` | OLE exception |
| (in `CMemoryException`) | `CResourceException` | Resource failure |
| (in `CMemoryException`) | `CFileException` | File I/O error |

### OLE/COM
| Vtable Address | Class | Description |
|---------------|-------|-------------|
| `0x0055c56c` | `COleControlContainer` | OLE control container |
| `0x0055c78c` | `COleControlSite` | OLE control site |
| `0x0055c998` | `CDataSourceControl` | Data source control |
| `0x0055ca98` | `COleMessageFilter` | OLE message filter |
| `0x0055bd9c` | `CArchiveStream` | COM stream wrapper for `CArchive` |
| `0x0055d024` | `CEnumArray` | COM enumerator |

### Other MFC
| Vtable Address | Class | Description |
|---------------|-------|-------------|
| `0x0055b98c` | `CThreadData` | Thread-local data |
| `0x0055be98` | `CRecentFileList` | MRU file list |
| `0x0055ccd8` | `CDockContext` | Docking context |
| `0x0055c9d8` | `CMemFile` | Memory file |
| `0x0055a894` | `COccManager` | OLE control container manager |
| — | `_AFX_WIN_STATE` | MFC Windows state |
| — | `_AFX_THREAD_STATE` | MFC thread state |
| — | `_AFX_SOCK_STATE` | MFC socket state |
| — | `_AFX_OLE_STATE` | MFC OLE state |
| — | `_AFX_MAIL_STATE` | MFC mail state |
| `0x0055d210` | `type_info` | C++ RTTI type info |

## Key Vtable Function Addresses

Notable overridden virtual methods identified in vtables (JHora-specific or significant overrides):

| Address | Name | Notes |
|---------|------|-------|
| `0x0051c2d5` | fcn (in CDialog vtable) | Possibly JHora dialog's `OnCmdMsg` |
| `0x0051b43d` | fcn (in CDialog vtable) | Possibly `OnUpdate` handler |
| `0x005141dc` | fcn (multiple vtables) | `CControlBar` onCreate or similar |
| `0x0051f1c9` | fcn (in CSingleDocTemplate vtable) | Doc template override |
| `0x00515a8f` | fcn (many vtables) | Possibly `OnUpdateCmdUI` |
| `0x00521856` | fcn (CToolBar, CStatusBar) | Toolbar/status bar override |
| `0x0052ee94` | fcn (CToolBar, CDialogBar) | Control bar override |
| `0x00517129` | fcn (many vtables) | Common message handler |
| `0x005168e3` | fcn (CToolBar, CStatusBar) | Paint/draw override |
| `0x0051696f` | fcn (CToolBar, CStatusBar) | Paint/draw override |
| `0x00516347` | fcn (many) | Window proc override |
| `0x00517329` | fcn (many) | Layout/calc override |
| `0x0052aa11` | fcn (CMDIChildWnd) | MDI child override |
| `0x0052ac50` | fcn (CMiniDockFrameWnd) | Docking frame override |
| `0x00511d0a` | fcn (CPrintDialog) | Print dialog handler |
| `0x00514b4d` | fcn (CNewTypeDlg) | New dialog handler |
| `0x00514e50` | fcn (CNewTypeDlg) | New dialog handler |
| `0x00514dd2` | fcn (CPrintDialog) | Print dialog handler |
| `0x00515c98` | fcn (multiple) | Common handler |
| `0x00515a6f` | fcn (CSplitterWnd) | Splitter override |
| `0x00515d30` | fcn (CSplitterWnd) | Splitter override |
| `0x00516303` | fcn (multiple) | Common handler |
| `0x00515da6` | fcn (multiple) | Common handler |
| `0x0052ee94` | fcn (CDialogBar) | Dialog bar override |
| `0x005311ae` | fcn (COleBusyDialog) | Busy dialog override |
| `0x0053181a` | fcn (CEnumArray) | Enum override |
| `0x0053100a` | fcn (COleException) | Exception override |
| `0x004fd898` | fcn (COleControlSite) | Control site override |
| `0x004fdbfd` | fcn (COleControlSite) | Control site override |
| `0x005188a2` | fcn (CMemFile) | File read override |
| `0x005272da` | fcn (CMemFile) | File operation override |

## Swiss Ephemeris Imports (18 functions)

| # | Address | Function | Called By |
|---|---------|----------|-----------|
| 1 | `0x005467a4` | `_swe_set_sid_mode@20` | `fcn.0049a3a0` (+16 calls), `fcn.004b8d70` |
| 2 | `0x005467a8` | `_swe_fixstar@24` | `fcn.0049aaa0`, `fcn.004b8d70` |
| 3 | `0x005467ac` | `_swe_deltat@8` | `fcn.0049aaa0`, `fcn.004b8d70`, `fcn.0049bb00`, `fcn.0049a930` |
| 4 | `0x005467b0` | `_swe_julday@24` | `fcn.0049aaa0` (+3), ~20 date conversion helpers |
| 5 | `0x005467b4` | `_swe_azalt_rev@24` | `fcn.0049aaa0` |
| 6 | `0x005467b8` | `_swe_refrac@28` | `fcn.0049aaa0` |
| 7 | `0x005467bc` | `_swe_azalt@40` | `fcn.0049aaa0` |
| 8 | `0x005467c0` | `_swe_get_ayanamsa@8` | `fcn.0049a370` |
| 9 | `0x005467c4` | `_swe_set_topo@24` | `fcn.0040b2a0`, `fcn.004b9390` |
| 10 | `0x005467c8` | `_swe_sol_eclipse_when_loc@32` | `fcn.0040b2a0` |
| 11 | `0x005467cc` | `_swe_sol_eclipse_when_glob@28` | `fcn.0040b2a0` |
| 12 | `0x005467d0` | `_swe_lun_eclipse_when@28` | `fcn.0040b2a0` |
| 13 | `0x005467d4` | `_swe_houses@36` | `fcn.0049aaa0` |
| 14 | `0x005467d8` | `_swe_revjul@28` | `fcn.0049aaa0`, `fcn.0049d250`, `fcn.004ba830`, `fcn.0049d3e0` |
| 15 | `0x005467dc` | `_swe_set_ephe_path@4` | `fcn.004db700` |
| 16 | `0x005467e0` | `_swe_calc@24` | `fcn.0049aaa0`, `fcn.0049bb00` |
| 17 | `0x005467e4` | `_swe_close@0` | `fcn.004dbf60`, `(nofunc) 0x43f014`, `(nofunc) 0x4dc188` |
| 18 | `0x005467e8` | `_swe_rise_trans@52` | `fcn.004a1350` |

## Core Calculation Functions (by size, descending)

| Address | Size | Locals | Description (guessed) |
|---------|------|--------|----------------------|
| `0x004cb240` | 15,614 B | 202 | **Main chart rendering** — largest function, draws all chart graphics |
| `0x0046c890` | 9,719 B | 146 | **Dasa computation engine** — handles multiple dasa systems |
| `0x004dd410` | 8,846 B | 307 | **Report/text generator** — builds formatted text output |
| `0x0041d820` | 8,558 B | 219 | **Chart data computation** — processes all chart factors |
| `0x0045ede0` | 7,656 B | 118 | **Varga chart division** — computes all D-n divisional charts |
| `0x0045d1e0` | 7,163 B | 113 | **Planet strength calculation** — Shadbala etc. |
| `0x00437e40` | 7,271 B | 107 | **Tajaka (solar return) engine** |
| `0x00442de0` | 7,400 B | 117 | **Transit calculation** |
| `0x004362d0` | 6,735 B | 108 | **Muhurta/electional** |
| `0x00460bd0` | 6,893 B | 106 | **Ashtakavarga computation** |
| `0x0040c540` | 5,957 B | 139 | **Horary (Prasna) engine** |
| `0x0044c170` | 5,590 B | 134 | **Matchmaking/Kuta** |
| `0x0044a330` | 5,233 B | 91 | **Dasa timing** — sub-period calculations |
| `0x004df940` | 5,224 B | 574 | **Print/display formatting** — many string locals |
| `0x004b6c80` | 4,697 B | 561 | **INI/config file handler** — many config keys |
| `0x0049aaa0` | 4,147 B | 95 | **Core astronomical engine** — planets, houses, stars, rise/set |
| `0x004a3800` | 2,306 B | 94 | **Ayanamsa handler** |
| `0x004c9fe0` | 2,375 B | 102 | **Data file I/O** — `.jhd` file reading |
| `0x004c95a0` | 2,613 B | 105 | **Serialization support** |
| `0x004c2250` | 1,858 B | 129 | **Atlas lookup** — city/coordinate database |
| `0x0049bb00` | — | — | **Planet position** via `_swe_calc` |
| `0x0040b2a0` | — | — | **Eclipse calculator** |
| `0x0049a3a0` | — | — | **Ayanamsa mode setter** (16+ modes) |
| `0x004b8d70` | — | — | **Secondary calc engine** (sidereal + stars) |
| `0x004b9390` | — | — | **Topocentric setup** |
| `0x004a1350` | — | — | **Rise/transit times** |
| `0x004db700` | — | — | **Ephemeris path setup** |
| `0x004dbf60` | — | — | **Cleanup** (`_swe_close`) |

## Dasa Systems (identified from string table in .data)

| String Address | Dasa Name |
|---------------|-----------|
| `0x005743b0` | Rasi-Bhukta Vimsottari Dasa |
| `0x00574b5c` | Niryana Shoola Dasa |
| `0x00575364` | Vimsottari Dasa |
| `0x00575374` | Mudda/Vimsottari Dasa |
| `0x00575510` | Kalachakra Dasa |
| `0x00575714` | Ashtottari Dasa |
| `0x005757ac` | Yogini Dasa |
| `0x00575d98` | Shashti-hayani Dasa |
| `0x00575ff8` | Patyayini Dasa |
| `0x00576128` | Tithi Ashtottari Dasa |
| `0x0057631c` | Moola Dasa |
| `0x00576494` | Tara Dasa |
| `0x00576500` | Kaala Dasa |
| `0x00576550` | Chakra Dasa |
| `0x0057666c` | Rasi-Bhukta Mudda/Vimsottari Dasa |
| `0x00576720` | AK Kendradi Graha Dasa |
| `0x00576828` | Tithi Yogini Dasa |
| `0x005768d0` | Naisargika Dasa |
| `0x00576a30` | Yoga Vimsottari Dasa |
| `0x00576b70` | Sudarsana Chakra Dasa |

## Ayanamsa Modes (from string references in fcn.0049a3a0)

Identified via `fcn.0049a3a0` +16 calls to `_swe_set_sid_mode`:
- Lahiri
- Raman
- Krishnamurti
- SSS (Sri Surya Siddhanta)
- Pushya-paksha
- Rohini-paksha
- Fixed-star custom
- Traditional Lahiri

## Varga Charts (from .rsrc strings)

D-1 through D-150 with multiple variants:
- Standard: D-1 (Rasi), D-2 (Hora), D-3 (Drekkana), D-4 (Chaturthamsa), etc.
- D-9 (Navamsa), D-10 (Dasamsa), D-11 (Rudramsa), D-12 (Dwadasamsa)
- D-16 (Shodasamsa), D-20 (Vimsamsa), D-24 (Siddhamsa)
- D-27 (Nakshatramsa), D-30 (Trimsamsa), D-40 (Khavedamsa)
- D-45 (Akshavedamsa), D-60 (Shashtyamsa), D-81 (Navanavamsa)
- D-108 (Ashtottaramsa), D-144 (Dwadasamsa-Dwadasamsa)
- Custom D-n, Sub-divisional charts

## Largest Functions by Local Variable Count

| Address | Locals | Size | Description |
|---------|--------|------|-------------|
| `0x004df940` | 574 | 5,224 B | **Print/display formatting** |
| `0x004b6c80` | 561 | 4,697 B | **INI/config handler** |
| `0x004dd410` | 307 | 8,846 B | **Report generator** |
| `0x004cb240` | 202 | 15,614 B | **Chart rendering** |
| `0x0041d820` | 219 | 8,558 B | **Chart computation** |
| `0x0040c540` | 139 | 5,957 B | **Prasna (horary)** |

## MFC Static Function Patterns

The following MFC functions are statically linked (identified by their calling convention and vtable slot patterns):

### CWinApp Overrides
- `InitInstance` — likely around `fcn.00508cb4` (48 args, 811 B) or nearby
- `ExitInstance` — cleanup
- `OnIdle` — idle processing

### CDocument Overrides (CJHoraDoc)
- `Serialize` — JHD file save/load
- `OnNewDocument` — new chart
- `DeleteContents` — cleanup

### CView Overrides (CJHoraView)
- `OnDraw` — chart rendering
- `OnUpdate` — view refresh
- `OnPreparePrinting` — print support

### Frame Window Overrides
- `OnCreate` — toolbar/status bar creation at `fcn.005141dc` (referenced in many vtables)

## External DLL Dependencies

| DLL | Count | Key Functions |
|-----|-------|---------------|
| `KERNEL32.dll` | 134 | Heap, file, string, thread, critical section |
| `USER32.dll` | 180 | Window, message, GDI coordinate, menu, clipboard |
| `GDI32.dll` | 91 | Bitmap, font, DC, drawing, text output |
| `ADVAPI32.dll` | 14 | Registry operations |
| `WININET.dll` | 6 | Internet connectivity checks |
| `SHELL32.dll` | 6 | Shell execute, drag-drop, file info |
| `COMCTL32.dll` | 3 | Image list, common controls init |
| `comdlg32.dll` | 5 | Open/save/print common dialogs |
| `WINSPOOL.DRV` | 3 | Printer management |
| `ole32.dll` | 18 | OLE/COM storage, clipboard, class factory |
| `OLEAUT32.dll` | 9 | Variant, string, type library |
| `OLEPRO32.DLL` | 1 | OLE font creation |
| `WSOCK32.dll` | 2 | WSA startup/cleanup |
| `swedll32.dll` | 18 | Swiss Ephemeris API |
| `oledlg.dll` | 1 | OLE busy dialog |

## Analysis Notes

1. **All 3,150 functions are unnamed in the binary** — no COFF symbols, no exports, no debug info, no RTTI names.
2. **MFC statically linked** — all ~650 vtables are MFC internal classes. Only two JHora class name strings exist (`CJHoraDoc`, `CJHoraView`).
3. **Largest function** is `0x004cb240` (15,614 bytes, 202 locals) — almost certainly the main chart drawing routine.
4. **Core astronomy** is `fcn.0049aaa0` (4,147 B) — calls `_swe_calc`, `_swe_houses`, `_swe_fixstar`, `_swe_rise_trans`, etc.
5. **Config/INI** handler at `fcn.004b6c80` has 561 locals — likely reads all `jhora.ini` settings into a table.
6. **Document type** is JHD (Jagannatha Hora Data) with OLE registration as `JHora.Document`.
7. **Multiple Dasa variants** — 20+ named dasa strings in `.data` section.
8. **MDI application** — `CMDIChildWnd` vtable confirms multi-document interface.
