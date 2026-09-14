"""Build the distributable public data/jhora.db: schema + cities only.

Forward-only hygiene: old commits keep whatever they have; this produces
the content all FUTURE clones receive. Drops everything personal or
copyrighted: book texts, vector embeddings, FTS book index, charts,
threads, preferences. Keeps the 34k-city atlas (factual data).

Usage:
  PYTHONPATH=src python3 tools/build_public_db.py --from data/jhora.db \
      --to /tmp/clean.db
then inspect /tmp/clean.db and copy it over data/jhora.db deliberately.
"""

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default="data/jhora.db")
    ap.add_argument("--to", required=True)
    args = ap.parse_args()

    src, dst = Path(args.src), Path(args.to)
    if not src.is_file():
        sys.exit(f"source DB not found: {src}")
    if dst.exists():
        sys.exit(f"refusing to overwrite: {dst} (delete it first)")

    from jhora.core.database import set_db_path, get_db
    set_db_path(dst)
    get_db()  # creates the current schema (charts, threads, preferences)
    get_db().close()

    con = sqlite3.connect(dst)
    con.execute(f"ATTACH '{src}' AS old")
    con.execute("INSERT INTO cities SELECT * FROM old.cities")
    try:
        con.execute("INSERT INTO cities_fts(cities_fts) VALUES('rebuild')")
    except Exception as e:
        print(f"fts rebuild note: {e}")
    con.commit()

    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("tables:", sorted(tables))
    # NOTE: unqualified names fall through to the ATTACHED old DB, so every
    # check below is qualified with main. explicitly.
    for t, cond in (("knowledge_texts", "1=1"),
                    ("textbook_chunks", "1=1"),
                    ("charts", "1=1"),
                    ("chat_threads", "1=1"),
                    ("guru_threads", "1=1"),
                    ("preferences", "1=1")):
        try:
            n = con.execute(f"SELECT COUNT(*) FROM main.{t}").fetchone()[0]
            print(f"{t}: {n} rows")
            assert n == 0, f"{t} must be empty in the public DB"
        except sqlite3.OperationalError:
            print(f"{t}: (no such table, ok)")
    n = con.execute("SELECT COUNT(*) FROM main.cities").fetchone()[0]
    print(f"cities: {n} rows")
    assert n > 30000, "cities atlas missing!"
    con.execute("VACUUM")
    con.close()
    print(f"wrote {dst} ({dst.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
