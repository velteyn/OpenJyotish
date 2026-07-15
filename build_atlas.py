#!/usr/bin/env python3
"""Build the Jhora city atlas database from GeoNames data.

Downloads cities15000.zip from geonames.org, parses it,
and creates a SQLite database with FTS5 full-text search.

Data source: https://download.geonames.org/export/dump/
License: Creative Commons Attribution 4.0 (CC BY 4.0)

Usage:
    python3 build_atlas.py              # download + build to data/cities.db
    python3 build_atlas.py --local TXT  # build from local file
    python3 build_atlas.py --force      # re-download even if cached
"""

import csv
import sqlite3
import sys
import urllib.request
import zipfile
from argparse import ArgumentParser
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime


GEONAMES_URL = "https://download.geonames.org/export/dump/cities15000.zip"
OUTPUT_DB = Path("data/cities.db")
SRC_TXT = Path("data/cities15000.txt")
SRC_ZIP = Path("data/cities15000.zip")


def tz_offset(tzname: str) -> float:
    try:
        tz = ZoneInfo(tzname)
        now = datetime.now(tz)
        return now.utcoffset().total_seconds() / 3600
    except Exception:
        return 0.0


def download(force: bool = False) -> Path:
    if SRC_TXT.exists() and not force:
        print(f"Using cached {SRC_TXT}")
        return SRC_TXT

    if not SRC_ZIP.exists() or force:
        print(f"Downloading {GEONAMES_URL} ...")
        urllib.request.urlretrieve(GEONAMES_URL, SRC_ZIP)

    print(f"Extracting {SRC_ZIP} ...")
    with zipfile.ZipFile(SRC_ZIP, "r") as zf:
        zf.extractall("data/")
    return SRC_TXT


def build(src: Path) -> Path:
    print("Creating database...")
    db = sqlite3.connect(str(OUTPUT_DB))
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=OFF")

    db.execute("DROP TABLE IF EXISTS cities")
    db.execute("DROP TABLE IF EXISTS cities_fts")
    db.execute("""
        CREATE TABLE cities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            ascii_name TEXT NOT NULL,
            country TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            tz_offset REAL NOT NULL
        )
    """)

    tz_cache: dict[str, float] = {}
    count = 0
    errors = 0

    with open(src, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        batch = []
        for row in reader:
            if len(row) < 19:
                continue
            try:
                geoid = int(row[0])
                name = row[1]
                ascii_name = row[2]
                lat = float(row[4])
                lon = float(row[5])
                country = row[8]
                tzname = row[17]
            except (ValueError, IndexError):
                continue
            if not tzname:
                errors += 1
                continue
            if tzname not in tz_cache:
                tz_cache[tzname] = tz_offset(tzname)
            offset = tz_cache[tzname]
            batch.append((geoid, name, ascii_name, country, lat, lon, offset))
            count += 1
            if len(batch) >= 5000:
                db.executemany(
                    "INSERT OR IGNORE INTO cities VALUES (?,?,?,?,?,?,?)", batch
                )
                batch = []
                print(f"  {count:,} ...", end="\r")
        if batch:
            db.executemany(
                "INSERT OR IGNORE INTO cities VALUES (?,?,?,?,?,?,?)", batch
            )
    print(f"\n  {count:,} cities inserted ({errors} tz errors)")

    print("Building FTS5 index ...")
    db.execute("""
        CREATE VIRTUAL TABLE cities_fts USING fts5(
            name, ascii_name, country,
            content='cities', content_rowid='id'
        )
    """)
    db.execute("INSERT INTO cities_fts(cities_fts) VALUES('rebuild')")
    db.execute("CREATE INDEX IF NOT EXISTS idx_cities_name ON cities(name)")

    db.commit()
    db.close()

    size_mb = OUTPUT_DB.stat().st_size / (1024 * 1024)
    print(f"\nBuilt {OUTPUT_DB} ({size_mb:.1f} MB, {count:,} cities)")
    return OUTPUT_DB


def verify():
    db = sqlite3.connect(str(OUTPUT_DB))
    total = db.execute("SELECT COUNT(*) FROM cities").fetchone()[0]
    tz_count = db.execute("SELECT COUNT(DISTINCT tz_offset) FROM cities").fetchone()[0]
    print(f"\nVerification: {total:,} cities, {tz_count} unique offsets")
    for q in ["mumbai", "london", "new york", "tokyo", "berlin", "sydney"]:
        rows = db.execute(
            "SELECT c.name, c.country, c.latitude, c.longitude, c.tz_offset "
            "FROM cities c JOIN cities_fts f ON c.id = f.rowid "
            "WHERE cities_fts MATCH ? ORDER BY rank LIMIT 2",
            (q,)
        ).fetchall()
        if rows:
            r = rows[0]
            print(f"  {q:12s} → {r[0]:25s} {r[1]} ({r[2]:.2f}, {r[3]:.2f}) UTC{r[4]:+.1f}")
    db.close()


if __name__ == "__main__":
    p = ArgumentParser(description="Build Jhora atlas from GeoNames")
    p.add_argument("--local", metavar="TXT", help="Build from local geonames text file")
    p.add_argument("--force", action="store_true", help="Re-download even if cached")
    args = p.parse_args()

    if args.local:
        src = Path(args.local)
        if not src.exists():
            print(f"ERROR: {src} not found", file=sys.stderr)
            sys.exit(1)
    else:
        src = download(force=args.force)

    build(src)
    verify()
