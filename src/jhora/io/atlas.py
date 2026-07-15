"""City atlas — SQLite-backed search using GeoNames.org data (CC BY 4.0)."""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict


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


class StaticAtlasReader:
    """Fallback atlas: loads from a JSON file of city entries (e.g. jhd_samples.json)."""

    def __init__(self, cities: List[AtlasCity]):
        self._city_map: Dict[str, List[AtlasCity]] = {}
        for city in cities:
            key = city.name.lower()
            self._city_map.setdefault(key, []).append(city)

    @classmethod
    def from_jhd_samples(cls, path: str | Path) -> "StaticAtlasReader":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        seen: set = set()
        cities: List[AtlasCity] = []
        for entry in raw:
            name = str(entry.get("city", "")).strip()
            if not name or name.lower() == "unknown":
                continue
            city = AtlasCity(
                name=name,
                latitude=float(entry["latitude"]),
                longitude=float(entry["longitude"]),
                tz_offset=float(entry["tz_offset"]),
            )
            key = (city.name.lower(), city.latitude, city.longitude, city.tz_offset)
            if key in seen:
                continue
            seen.add(key)
            cities.append(city)
        return cls(cities)

    def search(self, query: str, max_results: int = 20) -> List[AtlasCity]:
        q = query.lower()
        results: List[AtlasCity] = []
        for key, cities in self._city_map.items():
            if q in key:
                results.extend(cities)
                if len(results) >= max_results:
                    break
        return results[:max_results]

    def close(self):
        pass


def open_default_atlas(base_dir: str | Path | None = None) -> AtlasReader | StaticAtlasReader:
    if base_dir is not None:
        roots = [Path(base_dir)]
    else:
        roots = [
            Path.cwd(),
            Path(__file__).resolve().parents[3],
        ]
    checked: List[Path] = []
    for root in roots:
        for rel in ("data/cities.db",):
            candidate = (root / rel).resolve()
            if candidate in checked:
                continue
            checked.append(candidate)
            if candidate.exists():
                return AtlasReader(candidate)
    for root in roots:
        sample_path = (root / "data" / "jhd_samples.json").resolve()
        if sample_path.exists():
            return StaticAtlasReader.from_jhd_samples(sample_path)
    checked_paths = ", ".join(str(p) for p in checked)
    raise FileNotFoundError(
        f"Could not find cities.db or data/jhd_samples.json ({checked_paths})"
    )
