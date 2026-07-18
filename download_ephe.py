#!/usr/bin/env python3
"""Download required Swiss Ephemeris data — planet + moon files only (1900-2100).

Source: github.com/aloistr/swisseph (GPL)
"""
import sys

# Print immediately so batch scripts see something even if imports crash
print("download_ephe.py: starting...", flush=True)

import os, ssl

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

DEST = "jhcore/ephe"
BASE = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe"
TIMEOUT = 30

# We only need the 600-year block covering 1800-2399 for birth charts 1900-2100
# sepl_XX.se1 = planet data, semo_XX.se1 = moon data, XX = block number
FILES = ["sepl_18.se1", "semo_18.se1"]


def download_file(url: str, path: str) -> bool:
    try:
        data = urlopen(url, timeout=TIMEOUT).read()
        with open(path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"  FAILED: {os.path.basename(path)} — {e}", flush=True)
        return False


def download():
    os.makedirs(DEST, exist_ok=True)
    existing = os.listdir(DEST)
    needed = set(FILES)

    extras = [f for f in existing if f.endswith(".se1") and f not in needed]
    for f in extras:
        os.remove(os.path.join(DEST, f))
    if extras:
        print(f"Removed {len(extras)} unneeded files", flush=True)

    print(f"Downloading {len(FILES)} ephemeris files...", flush=True)

    done, skipped, failed = 0, 0, 0
    for f in FILES:
        path = os.path.join(DEST, f)
        if f in existing and f not in extras:
            skipped += 1
            continue
        if download_file(f"{BASE}/{f}", path):
            done += 1
        else:
            failed += 1

    total = len(os.listdir(DEST))
    print(f"\nDone: {done} downloaded, {skipped} existing, {failed} failed, "
          f"{total} files in {DEST}/", flush=True)
    if failed:
        print("Some files failed. Check your internet connection.", flush=True)
        print(f"Manual: {BASE}/", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    download()
