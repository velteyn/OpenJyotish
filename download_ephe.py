#!/usr/bin/env python3
"""Download required Swiss Ephemeris data files from astro.com."""
import os, sys, urllib.request

DEST = "jhcore/ephe"
os.makedirs(DEST, exist_ok=True)
BASE = "https://www.astro.com/ftp/swisseph/ephe"

FILES = [
    f"sepl_{n:02d}.se1" for n in [18,24,30,36,42,48,54,60,66,72,78,84,90,96,102,108,114,120,126,132]
] + [
    f"semo_{n:02d}.se1" for n in [18,24,30,36,42,48,54,60,66,72,78,84,90,96,102,108,114,120,126,132]
]

print(f"Downloading {len(FILES)} ephemeris files to {DEST}/...")
downloaded = 0
for f in FILES:
    path = os.path.join(DEST, f)
    if os.path.exists(path):
        continue
    try:
        url = f"{BASE}/{f}"
        urllib.request.urlretrieve(url, path)
        downloaded += 1
        if downloaded % 5 == 0:
            print(f"  {downloaded}/{len(FILES)}...")
    except Exception as e:
        print(f"  WARNING: Could not download {f}: {e}")

print(f"Done: {downloaded} files downloaded, "
      f"{len(os.listdir(DEST))} total in {DEST}/")
