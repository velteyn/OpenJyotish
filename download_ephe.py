#!/usr/bin/env python3
"""Download required Swiss Ephemeris data — planet + moon files only (1900-2100).

Source: github.com/aloistr/swisseph (GPL)
"""
import os, sys, ssl

# Handle Windows SSL issues (missing CA certificates)
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

try:
    from urllib.request import urlopen, urlretrieve
except ImportError:
    from urllib import urlopen, urlretrieve

DEST = "jhcore/ephe"
BASE = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe"
TIMEOUT = 30

MONTHS = range(0, 162, 6)
FILES = [f"sepl_{m:02d}.se1" for m in MONTHS] + \
        [f"semo_{m:02d}.se1" for m in MONTHS]


def download_file(url: str, path: str) -> bool:
    try:
        data = urlopen(url, timeout=TIMEOUT).read()
        with open(path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"  FAILED: {os.path.basename(path)} — {e}")
        return False


def download():
    os.makedirs(DEST, exist_ok=True)
    existing = os.listdir(DEST)
    needed_set = set(FILES)

    extras = [f for f in existing if f.endswith(".se1") and f not in needed_set]
    for f in extras:
        os.remove(os.path.join(DEST, f))
    if extras:
        print(f"Removed {len(extras)} unneeded files (asteroids, fixed stars, etc.)")

    print(f"Downloading {len(FILES)} ephemeris files (planet + moon)...")
    sys.stdout.flush()

    done, skipped, failed = 0, 0, 0
    for f in FILES:
        path = os.path.join(DEST, f)
        if f in existing and f not in extras:
            skipped += 1
            continue
        if download_file(f"{BASE}/{f}", path):
            done += 1
            print(f"  [{done}/{len(FILES)}] {f}")
        else:
            failed += 1
        sys.stdout.flush()

    total = len(os.listdir(DEST))
    print(f"\nDone: {done} downloaded, {skipped} existing, {failed} failed, {total} total in {DEST}/")
    if failed:
        print("Some files failed. Check your internet connection and try again.")
        print(f"Manual download: {BASE}/")
        sys.exit(1)


if __name__ == "__main__":
    download()
