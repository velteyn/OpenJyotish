"""Chart data I/O — .jhd file parser + SQLite chart storage.

.. warning::
   .jhd files store birth data (date, time, coordinates) in clear text.
   Treat these files as sensitive. Use the SQLite database for storage
   where possible, and avoid sharing .jhd files publicly.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from jhora.core.database import get_db


class JhdFormat(Enum):
    BIRTH_ONLY = "birth_only"
    BIRTH_CITY = "birth_city"
    PLANET_POSITIONS = "planet_positions"
    BIRTH_CITY_EXTRA = "birth_city_extra"


@dataclass
class JhdData:
    filename: str
    format: JhdFormat
    day: int
    month: int
    year: int
    time_hours: float
    tz_offset: float
    longitude: float
    latitude: float
    ayanamsa_override: float = 0.0
    city: str = ""
    country: str = ""
    planet_longitudes: Optional[List[float]] = None

    @property
    def name(self) -> str:
        return self.filename.removesuffix(".jhd").strip()


_PLANET_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


# ---- .jhd file I/O (kept for compatibility with original format) ----

def _parse_float(val: str) -> float:
    return float(val.strip())


def save_jhd(path: str, data: JhdData) -> None:
    lines = [
        str(data.day), str(data.month), str(data.year),
        f"{data.time_hours:.6f}", f"{data.tz_offset:.6f}",
        f"{data.longitude:.6f}", f"{data.latitude:.6f}",
        f"{data.ayanamsa_override:.6f}", f"{data.ayanamsa_override:.6f}",
        f"{data.ayanamsa_override:.6f}", "0", "0",
        data.city or "Unknown", data.country or "",
    ]
    if data.planet_longitudes and len(data.planet_longitudes) >= 9:
        lines.append("18")
        lines.append("0")
        for pl in data.planet_longitudes:
            lines.append(f"{pl:.6f}")
    text = "\r\n".join(lines) + "\r\n"
    with open(path, "w", newline="") as f:
        f.write(text)


def parse_jhd(path: str) -> JhdData:
    with open(path, "rb") as f:
        raw = f.read()
    lines = raw.decode("ascii", errors="replace").strip().split("\r\n")
    n = len(lines)
    filename = path.split("/")[-1]

    day, month, year = int(lines[0]), int(lines[1]), int(lines[2])
    time_hours = _parse_float(lines[3])
    tz_offset = _parse_float(lines[4])
    longitude = _parse_float(lines[5])
    latitude = _parse_float(lines[6])
    ayanamsa_override = _parse_float(lines[7]) if n > 7 else 0.0

    if n <= 8:
        return JhdData(filename=filename, format=JhdFormat.BIRTH_ONLY,
                       day=day, month=month, year=year, time_hours=time_hours,
                       tz_offset=tz_offset, longitude=longitude, latitude=latitude,
                       ayanamsa_override=ayanamsa_override)

    is_city = n > 12 and not lines[12].replace(".", "").replace("-", "").replace(" ", "").isdigit()
    if is_city:
        city = lines[12].strip()
        country = lines[13].strip() if n > 13 else ""
        planet_longitudes = None
        if n >= 18 and all(c.isdigit() or c in '.-' for c in lines[14]) and float(lines[14]) > 100:
            planet_longitudes = [_parse_float(lines[i]) for i in range(14, min(23, n))]
            fmt = JhdFormat.BIRTH_CITY_EXTRA
        else:
            fmt = JhdFormat.BIRTH_CITY
        return JhdData(filename=filename, format=fmt,
                       day=day, month=month, year=year, time_hours=time_hours,
                       tz_offset=tz_offset, longitude=longitude, latitude=latitude,
                       ayanamsa_override=ayanamsa_override, city=city, country=country,
                       planet_longitudes=planet_longitudes)

    if n >= 17 and float(lines[8]) > 100:
        planet_longitudes = [_parse_float(lines[i]) for i in range(8, min(17, n))]
        return JhdData(filename=filename, format=JhdFormat.PLANET_POSITIONS,
                       day=day, month=month, year=year, time_hours=time_hours,
                       tz_offset=tz_offset, longitude=longitude, latitude=latitude,
                       ayanamsa_override=ayanamsa_override,
                       planet_longitudes=planet_longitudes)

    return JhdData(filename=filename, format=JhdFormat.BIRTH_ONLY,
                   day=day, month=month, year=year, time_hours=time_hours,
                   tz_offset=tz_offset, longitude=longitude, latitude=latitude,
                   ayanamsa_override=ayanamsa_override)


# ---- SQLite chart storage ----

def save_chart_to_db(name: str, day: int, month: int, year: int,
                      time_hours: float, tz_offset: float,
                      latitude: float, longitude: float,
                      ayanamsa: str = "lahiri",
                      city: str = "", country: str = "",
                      notes: str = "",
                      planet_longitudes: Optional[List[float]] = None) -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO charts (name, day, month, year, time_hours, tz_offset, "
        "latitude, longitude, ayanamsa, city, country, notes) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (name, day, month, year, time_hours, tz_offset,
         latitude, longitude, ayanamsa, city, country, notes),
    )
    chart_id = cur.lastrowid
    if planet_longitudes:
        for i, lon in enumerate(planet_longitudes):
            db.execute(
                "INSERT INTO chart_planets (chart_id, graha, longitude) "
                "VALUES (?,?,?)", (chart_id, i, lon),
            )
    db.commit()
    return chart_id


def load_chart_from_db(chart_id: int) -> Optional[dict]:
    db = get_db()
    row = db.execute("SELECT * FROM charts WHERE id = ?", (chart_id,)).fetchone()
    if row is None:
        return None
    result = dict(row)
    planets = db.execute(
        "SELECT graha, longitude, latitude, speed, is_retrograde "
        "FROM chart_planets WHERE chart_id = ? ORDER BY graha",
        (chart_id,),
    ).fetchall()
    result["planet_longitudes"] = {p["graha"]: dict(p) for p in planets}
    return result


def list_charts(search: str = "") -> List[dict]:
    db = get_db()
    if search:
        rows = db.execute(
            "SELECT id, name, created_at, city, country, day, month, year "
            "FROM charts WHERE name LIKE ? ORDER BY created_at DESC LIMIT 50",
            (f"%{search}%",),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT id, name, created_at, city, country, day, month, year "
            "FROM charts ORDER BY created_at DESC LIMIT 50",
        ).fetchall()
    return [dict(r) for r in rows]


def delete_chart(chart_id: int):
    db = get_db()
    db.execute("DELETE FROM charts WHERE id = ?", (chart_id,))
    db.commit()


def import_jhd_to_db(path: str) -> int:
    """Parse a .jhd file and save it to the database."""
    data = parse_jhd(path)
    return save_chart_to_db(
        name=data.name,
        day=data.day, month=data.month, year=data.year,
        time_hours=data.time_hours, tz_offset=data.tz_offset,
        latitude=data.latitude, longitude=data.longitude,
        city=data.city, country=data.country,
        planet_longitudes=data.planet_longitudes,
    )


def export_chart_to_jhd(chart_id: int, path: str):
    """Load a chart from DB and save as .jhd file."""
    data = load_chart_from_db(chart_id)
    if data is None:
        raise ValueError(f"Chart {chart_id} not found")
    jhd = JhdData(
        filename=Path(path).name,
        format=JhdFormat.BIRTH_CITY,
        day=data["day"], month=data["month"], year=data["year"],
        time_hours=data["time_hours"], tz_offset=data["tz_offset"],
        longitude=data["longitude"], latitude=data["latitude"],
        city=data.get("city", ""), country=data.get("country", ""),
        planet_longitudes=list(data.get("planet_longitudes", {}).keys()),
    )
    save_jhd(path, jhd)
