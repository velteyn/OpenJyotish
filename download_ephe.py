#!/usr/bin/env python3
"""Download or copy Swiss Ephemeris data files.

Primary source: copy from an existing JHora installation.
The astro.com server blocks direct downloads (HTTP 404).

If you have the original JHora installed, point to its ephe directory.
Otherwise, download from https://www.astro.com/swisseph/ (requires browser).
"""
import os, sys, shutil, urllib.request

DEST = "jhcore/ephe"

def copy_from(source_dir):
    """Copy .se1 files from an existing ephemeris directory."""
    count = 0
    for f in os.listdir(source_dir):
        if f.endswith('.se1'):
            src = os.path.join(source_dir, f)
            dst = os.path.join(DEST, f)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                count += 1
    return count

def main():
    os.makedirs(DEST, exist_ok=True)
    existing = [f for f in os.listdir(DEST) if f.endswith('.se1')] if os.path.exists(DEST) else []

    if existing:
        print(f"Already have {len(existing)} ephemeris files in {DEST}/")
        return

    # Try common JHora install locations
    locations = [
        "C:/Program Files/JHora/jhcore/ephe",
        "C:/Projects/jhora/jhcore/ephe",
        os.path.expanduser("~/jhora/jhcore/ephe"),
        "/home/velteyn/projects/Reversing/Jhora/jhcore/ephe",
    ]

    for loc in locations:
        if os.path.isdir(loc):
            count = copy_from(loc)
            if count > 0:
                print(f"Copied {count} files from {loc}")
                return

    print("Ephemeris data not found.")
    print("Options:")
    print("  1. Copy from original JHora: jhora/download_ephe.py /path/to/jhora/jhcore/ephe")
    print("  2. Download from: https://www.astro.com/swisseph/")
    print("     Place .se1 files in jhcore/ephe/")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        source = sys.argv[1]
        count = copy_from(source)
        print(f"Copied {count} files from {source}")
    else:
        main()

