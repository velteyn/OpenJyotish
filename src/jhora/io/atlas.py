"""City atlas — SQLite-backed search using GeoNames.org data (CC BY 4.0)."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass
class AtlasCity:
    name: str
    latitude: float
    longitude: float
    tz_offset: float
    country: str = ""


class AtlasReader:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def _db(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def search(self, query: str, max_results: int = 20) -> List[AtlasCity]:
        q = query.strip()
        if len(q) < 2:
            return []
        sql = """
            SELECT c.name, c.ascii_name, c.country,
                   c.latitude, c.longitude, c.tz_offset
            FROM cities c
            JOIN cities_fts f ON c.id = f.rowid
            WHERE cities_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        results = []
        for row in self._db.execute(sql, (q, max_results)):
            results.append(AtlasCity(
                name=row["name"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                tz_offset=row["tz_offset"],
                country=row["country"],
            ))
        return results

    def load_all(self) -> List[AtlasCity]:
        results = []
        for row in self._db.execute(
            "SELECT name, latitude, longitude, tz_offset, country "
            "FROM cities ORDER BY name"
        ):
            results.append(AtlasCity(
                name=row["name"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                tz_offset=row["tz_offset"],
                country=row["country"],
            ))
        return results

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
