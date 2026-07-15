#!/usr/bin/env python3
"""Build the Jhora database from source data.

Downloads cities15000.zip from geonames.org (CC BY 4.0) and imports
book extracts from docs/books/extracted/. Writes everything into the
unified database at data/jhora.db.

Usage:
    python3 build_atlas.py              # download + build
    python3 build_atlas.py --local TXT  # build cities from local file
    python3 build_atlas.py --force      # re-download even if cached
    python3 build_atlas.py --knowledge  # only rebuild knowledge base
    python3 build_atlas.py --cities     # only rebuild cities
"""

import csv
import sqlite3
import sys
import urllib.request
import zipfile
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

GEONAMES_URL = "https://download.geonames.org/export/dump/cities15000.zip"
DB_PATH = Path("data/jhora.db")
SRC_TXT = Path("data/cities15000.txt")
SRC_ZIP = Path("data/cities15000.zip")
BOOKS_DIR = Path("docs/books/extracted")


def tz_offset(tzname: str) -> float:
    try:
        return datetime.now(ZoneInfo(tzname)).utcoffset().total_seconds() / 3600
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


def build_cities(db: sqlite3.Connection, src: Path):
    print("Building cities table ...")
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

    with open(src, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        batch = []
        for row in reader:
            if len(row) < 19:
                continue
            try:
                geoid, name, ascii_name = int(row[0]), row[1], row[2]
                lat, lon = float(row[4]), float(row[5])
                country = row[8]
                tzname = row[17]
            except (ValueError, IndexError):
                continue
            if not tzname:
                continue
            if tzname not in tz_cache:
                tz_cache[tzname] = tz_offset(tzname)
            batch.append((geoid, name, ascii_name, country, lat, lon, tz_cache[tzname]))
            count += 1
            if len(batch) >= 5000:
                db.executemany("INSERT OR IGNORE INTO cities VALUES (?,?,?,?,?,?,?)", batch)
                batch = []
                print(f"  {count:,} ...", end="\r")
        if batch:
            db.executemany("INSERT OR IGNORE INTO cities VALUES (?,?,?,?,?,?,?)", batch)

    print(f"\n  {count:,} cities inserted")
    db.execute("""
        CREATE VIRTUAL TABLE cities_fts USING fts5(
            name, ascii_name, country,
            content='cities', content_rowid='id'
        )
    """)
    db.execute("INSERT INTO cities_fts(cities_fts) VALUES('rebuild')")
    db.execute("CREATE INDEX IF NOT EXISTS idx_cities_name ON cities(name)")
    db.commit()


def build_knowledge(db: sqlite3.Connection):
    if not BOOKS_DIR.exists():
        print(f"Books dir not found: {BOOKS_DIR} — skipping knowledge base")
        return
    print("Building knowledge base ...")
    db.execute("DELETE FROM knowledge_fts")
    db.execute("DELETE FROM knowledge_texts")
    count = 0
    for f in sorted(BOOKS_DIR.glob("*.txt")):
        name = f.stem.replace("_", " ").replace(".pdf", "").title()
        content = f.read_text(encoding="utf-8", errors="replace")
        db.execute(
            "INSERT INTO knowledge_texts (source_name, content, char_count) VALUES (?,?,?)",
            (name, content, len(content)),
        )
        count += 1
        print(f"  {name}: {len(content):,} chars")
    db.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
    db.commit()
    print(f"\n  {count} texts loaded, {db.execute('SELECT SUM(char_count) FROM knowledge_texts').fetchone()[0]:,} total chars")


def ensure_schema(db: sqlite3.Connection):
    cur = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cities'")
    if cur.fetchone() is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "jhora.core.database",
            Path("src/jhora/core/database.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        db.executescript("""
            CREATE TABLE IF NOT EXISTS schema_version (version INTEGER);
            CREATE TABLE IF NOT EXISTS knowledge_texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                char_count INTEGER NOT NULL DEFAULT 0,
                loaded_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                source_name, content, content='knowledge_texts', content_rowid='id'
            );
        """)


def verify(db: sqlite3.Connection):
    total = db.execute("SELECT COUNT(*) FROM cities").fetchone()[0]
    kt = db.execute("SELECT COUNT(*) FROM knowledge_texts").fetchone()[0]
    print(f"\nVerification: {total:,} cities, {kt} knowledge texts")
    for q in ["mumbai", "london", "new york", "tokyo"]:
        rows = db.execute(
            "SELECT c.name, c.country, c.latitude, c.longitude, c.tz_offset "
            "FROM cities c JOIN cities_fts f ON c.id = f.rowid "
            "WHERE cities_fts MATCH ? ORDER BY rank LIMIT 1",
            (q,),
        ).fetchall()
        if rows:
            r = rows[0]
            print(f"  {q:12s} → {r[0]:25s} {r[1]} ({r[2]:.2f}, {r[3]:.2f}) UTC{r[4]:+.1f}")


if __name__ == "__main__":
    p = ArgumentParser(description="Build Jhora database from source data")
    p.add_argument("--local", metavar="TXT", help="Build cities from local geonames file")
    p.add_argument("--force", action="store_true", help="Re-download even if cached")
    p.add_argument("--cities", action="store_true", help="Only rebuild cities")
    p.add_argument("--knowledge", action="store_true", help="Only rebuild knowledge base")
    args = p.parse_args()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB_PATH))
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=OFF")
    ensure_schema(db)

    do_all = not args.cities and not args.knowledge

    if do_all or args.cities:
        if args.local:
            src = Path(args.local)
            if not src.exists():
                print(f"ERROR: {src} not found", file=sys.stderr)
                sys.exit(1)
        else:
            src = download(force=args.force)
        build_cities(db, src)

    if do_all or args.knowledge:
        build_knowledge(db)

    verify(db)
    db.close()

    size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    print(f"\nBuilt {DB_PATH} ({size_mb:.1f} MB)")
