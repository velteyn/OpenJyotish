# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller bundle: OpenJyotish GUI (windowed) + CLI (console).

Build on each target OS (binaries are platform-specific):
    pyinstaller packaging/OpenJyotish.spec
"""

import os
import sys

from PyInstaller.utils.hooks import collect_data_files

# Spec-relative paths: bare relative paths resolve against the spec file's
# own directory, so anchor everything at the repo root (SPECPATH is the
# spec file's directory, provided by PyInstaller — __file__ is undefined).
ROOT = os.path.dirname(os.path.abspath(SPECPATH))

block_cipher = None

# tzdata ships zoneinfo on Windows (no system database there).
_wanted_datas = [
    (os.path.join(ROOT, "jhcore", "ephe"), "jhcore/ephe"),
    (os.path.join(ROOT, "data", "jhd_samples.json"), "data"),
]
datas = []
for _src, _dst in _wanted_datas:
    if os.path.exists(_src):
        datas.append((_src, _dst))
    else:
        print(f"WARNING: bundle data missing, skipping: {_src} "
              f"(ephemeris is downloaded in CI; see download_ephe.sh)")
if sys.platform == "win32":
    try:
        datas += collect_data_files("tzdata")
    except Exception:
        pass

binaries = []
hiddenimports = []
excludes = ["tests", "tkinter", "unittest", "pydoc", "doctest"]

gui_analysis = Analysis(
    [os.path.join(ROOT, "packaging", "gui_main.py")],
    pathex=[os.path.join(ROOT, "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    excludes=excludes,
    noarchive=False,
)
cli_analysis = Analysis(
    [os.path.join(ROOT, "src", "jhora", "__main__.py")],
    pathex=[os.path.join(ROOT, "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    excludes=excludes,
    noarchive=False,
)

gui_pyz = PYZ(gui_analysis.pure, gui_analysis.zipped_data, cipher=block_cipher)
cli_pyz = PYZ(cli_analysis.pure, cli_analysis.zipped_data, cipher=block_cipher)

gui_exe = EXE(
    gui_pyz, gui_analysis.scripts, [],
    exclude_binaries=True,
    name="OpenJyotish",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
cli_exe = EXE(
    cli_pyz, cli_analysis.scripts, [],
    exclude_binaries=True,
    name="jhora",
    debug=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    gui_exe, cli_exe,
    gui_analysis.binaries, cli_analysis.binaries,
    gui_analysis.datas, cli_analysis.datas,
    strip=False,
    upx=False,
    name="OpenJyotish",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="OpenJyotish.app",
        icon=None,
        bundle_identifier="com.openjyotish.app",
        info_plist={
            "NSHighResolutionCapable": "True",
            "LSMinimumSystemVersion": "11.0",
        },
    )
