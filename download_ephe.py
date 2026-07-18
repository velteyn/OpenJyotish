#!/usr/bin/env python3
"""Download Swiss Ephemeris data from GitHub.

Source: https://github.com/aloistr/swisseph
License: GPL — freely redistributable
"""
import os, sys, urllib.request

DEST = "jhcore/ephe"
BASE = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe"

# Files needed for 1900-2100 (every 6 months)
MONTHS = list(range(0, 162, 6))  # 0, 6, 12, ..., 156
FILES = [f"sepl_{m:02d}.se1" for m in MONTHS] + \
        [f"semo_{m:02d}.se1" for m in MONTHS] + \
        ["seas_18.se1", "seas_24.se1", "sefx_18.se1", "sefx_24.se1"]

def download():
    os.makedirs(DEST, exist_ok=True)
    existing = os.listdir(DEST)

    print(f"Ephemeris data ({len(FILES)} files) → {DEST}/")
    downloaded, skipped = 0, 0

    for f in FILES:
        path = os.path.join(DEST, f)
        if f in existing:
            skipped += 1
            continue
        try:
            url = f"{BASE}/{f}"
            urllib.request.urlretrieve(url, path)
            downloaded += 1
            if downloaded % 10 == 0:
                print(f"  {downloaded} downloaded...", end="\r")
        except Exception as e:
            print(f"  skip {f}: {e}")

    total = len(os.listdir(DEST))
    print(f"\nDone: {downloaded} new, {skipped} existing, {total} total")
    return total >= 40

if __name__ == "__main__":
    download()
