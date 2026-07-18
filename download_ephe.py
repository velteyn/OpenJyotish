#!/usr/bin/env python3
"""Download required Swiss Ephemeris data — planet + moon files only (1900-2100).

Source: github.com/aloistr/swisseph (GPL)
"""
import os, urllib.request

DEST = "jhcore/ephe"
BASE = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe"

# Only planet + moon files needed for birth charts 1900-2100
MONTHS = range(0, 162, 6)  # 0, 6, 12, ..., 156
FILES = [f"sepl_{m:02d}.se1" for m in MONTHS] + \
        [f"semo_{m:02d}.se1" for m in MONTHS]

def download():
    os.makedirs(DEST, exist_ok=True)
    existing = os.listdir(DEST)
    print(f"Downloading {len(FILES)} ephemeris files (planet + moon, 1900-2100)...")
    needed_set = set(FILES)
    extras = [f for f in existing if f.endswith(".se1") and f not in needed_set]
    for f in extras:
        os.remove(os.path.join(DEST, f))
    if extras:
        print(f"Removed {len(extras)} unneeded files (asteroids, fixed stars, etc.)")
    done, skip = 0, 0
    for f in FILES:
        path = os.path.join(DEST, f)
        if f in existing and f not in extras:
            skip += 1; continue
        try:
            urllib.request.urlretrieve(f"{BASE}/{f}", path)
            done += 1
            if done % 10 == 0: print(f"  {done}...", end="\r")
        except Exception as e:
            print(f"  skip {f}: {e}")
    print(f"\nDone: {done} downloaded, {skip} existing, {len(os.listdir(DEST))} total")

if __name__ == "__main__":
    download()
