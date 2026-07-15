"""City atlas — SQLite-backed search using GeoNames.org data (CC BY 4.0).

Uses the unified Jhora database (data/jhora.db). The AtlasReader wraps a subset
of queries on the `cities` and `cities_fts` tables.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from jhora.core.database import get_db


@dataclass
class AtlasCity:
    name: str
    latitude: float
    longitude: float
    tz_offset: float
    country: str = ""


class AtlasReader:
    """Query the cities table in the unified database."""

    def __init__(self, path: str | Path | None = None):
        self._db = get_db()

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
        pass


class StaticAtlasReader:
    """Fallback atlas: loads from a JSON file (e.g. jhd_samples.json)."""

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
    """Open the atlas — tries DB first, then JSON fallback in base_dir."""
    if base_dir is None:
        try:
            reader = AtlasReader()
            results = reader.search("lon", max_results=1)
            if results:
                return reader
        except Exception:
            pass

    roots = [Path(base_dir)] if base_dir else [Path.cwd()]
    for root in roots:
        sample_path = (root / "data" / "jhd_samples.json").resolve()
        if sample_path.exists():
            return StaticAtlasReader.from_jhd_samples(sample_path)

    raise FileNotFoundError("No atlas available — cities table empty or missing")
