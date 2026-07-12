import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

JAGANNATHA_MAGIC = b"Jagannatha Hora\0\0\0\x01"


@dataclass
class AtlasCity:
    name: str
    latitude: float
    longitude: float
    tz_offset: float


class AtlasReader:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        with open(self.path, "rb") as f:
            self._data = f.read()
        if not self._data.startswith(JAGANNATHA_MAGIC):
            raise ValueError("Not a valid Jagannatha Hora atlas file")
        self._groups: dict[str, int] = {}
        self._parse_index()
        self._cities: Optional[list[AtlasCity]] = None
        self._city_map: Optional[dict[str, list[AtlasCity]]] = None

    def _parse_index(self):
        idx_off = 0x60
        for i in range(10000):
            off = idx_off + i * 4
            if off + 4 > len(self._data):
                break
            val = int.from_bytes(self._data[off:off+4], "big")
            if val == 0x00000864 or val == 0:
                continue
            if val >= len(self._data):
                break
            if self._data[val] != 0xC0:
                break
            meta = self._data[val+1:val+11]
            group_code = meta[4:6].decode("ascii", errors="replace")
            self._groups[group_code] = val

    def _decode_tz(self, raw_tz: int) -> float:
        if raw_tz >= 128:
            raw_tz -= 256
        return raw_tz / 4.0

    @staticmethod
    def _decode_latlon(raw: bytes) -> tuple[float, float]:
        lon_int = raw[0]
        lat_int = raw[3]
        lat_min = raw[4] if raw[4] < 128 else raw[4] - 128
        lon_min = raw[1] if raw[1] < 128 else raw[1] - 128
        lat_sign = 1 if raw[4] >= 128 else -1
        lon_sign = 1 if raw[1] >= 128 else -1
        lat = lat_sign * (lat_int + lat_min / 60.0)
        lon = lon_sign * (lon_int + lon_min / 60.0)
        return lat, lon

    def _parse_group(self, group: str) -> list[AtlasCity]:
        cities = []
        off = self._groups.get(group)
        if off is None:
            return cities
        pos = off + 11
        while pos < len(self._data):
            if self._data[pos] == 0x80:
                pos += 4
                continue
            length = self._data[pos]
            if length < 2 or length > 60:
                break
            ne = pos + 1 + length
            if ne + 12 >= len(self._data):
                break
            if self._data[ne:ne+2] != b"\0\0":
                break
            name = self._data[pos+1:ne].decode("ascii", errors="replace")
            block = self._data[ne+2:ne+12]
            lat, lon = self._decode_latlon(block)
            tz = self._decode_tz(block[8])
            cities.append(AtlasCity(name, lat, lon, tz))
            pos = ne + 12
        return cities

    def load_all(self) -> list[AtlasCity]:
        if self._cities is not None:
            return self._cities
        self._cities = []
        for code in sorted(self._groups):
            self._cities.extend(self._parse_group(code))
        return self._cities

    def search(self, query: str, max_results: int = 20) -> list[AtlasCity]:
        if self._city_map is None:
            self._city_map = {}
            for code in sorted(self._groups):
                for city in self._parse_group(code):
                    key = city.name.lower()
                    self._city_map.setdefault(key, []).append(city)
        q = query.lower()
        results = []
        for key, cities in self._city_map.items():
            if q in key:
                results.extend(cities)
                if len(results) >= max_results:
                    break
        return results[:max_results]


class StaticAtlasReader:
    """Small in-repo fallback city index used when bundled atlas files are absent."""

    def __init__(self, cities: list[AtlasCity]):
        self._cities = cities
        self._city_map: dict[str, list[AtlasCity]] = {}
        for city in cities:
            key = city.name.lower()
            self._city_map.setdefault(key, []).append(city)

    @classmethod
    def from_jhd_samples(cls, path: str | Path) -> "StaticAtlasReader":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        seen: set[tuple[str, float, float, float]] = set()
        cities: list[AtlasCity] = []
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

    def search(self, query: str, max_results: int = 20) -> list[AtlasCity]:
        q = query.lower()
        results: list[AtlasCity] = []
        for key, cities in self._city_map.items():
            if q in key:
                results.extend(cities)
                if len(results) >= max_results:
                    break
        return results[:max_results]


def open_default_atlas(base_dir: str | Path | None = None) -> AtlasReader | StaticAtlasReader:
    """Open the bundled atlas if present, otherwise fall back to sample city data."""
    roots = []
    if base_dir is not None:
        roots.append(Path(base_dir))
    roots.extend([
        Path.cwd(),
        Path(__file__).resolve().parents[3],
    ])

    checked: list[Path] = []
    for root in roots:
        for rel in ("jhcore/atlas/jhworld.adb", "jhcore/atlas/jhlite.adb"):
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

    checked_paths = ", ".join(str(path) for path in checked)
    raise FileNotFoundError(
        f"Could not find bundled atlas files ({checked_paths}) or data/jhd_samples.json"
    )
