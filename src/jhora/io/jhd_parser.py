from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple


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
    def datetime_utc(self) -> datetime:
        local = datetime(self.year, self.month, self.day,
                        int(self.time_hours),
                        int((self.time_hours % 1) * 60),
                        int(((self.time_hours * 60) % 1) * 60))
        offset = timedelta(hours=self.tz_offset)
        tz = timezone(offset)
        return local.replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)

    @property
    def name(self) -> str:
        return self.filename.removesuffix(".jhd").strip()


_PLANET_ORDER = [
    "Sun", "Moon", "Mars", "Mercury",
    "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]


def _parse_float(val: str) -> float:
    return float(val.strip())


def save_jhd(path: str, data: JhdData) -> None:
    lines = [
        str(data.day),
        str(data.month),
        str(data.year),
        f"{data.time_hours:.6f}",
        f"{data.tz_offset:.6f}",
        f"{data.longitude:.6f}",
        f"{data.latitude:.6f}",
        f"{data.ayanamsa_override:.6f}",
        f"{data.ayanamsa_override:.6f}",
        f"{data.ayanamsa_override:.6f}",
        "0",
        "0",
        data.city or "Unknown",
        data.country or "",
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

    # All variants share first 7 fields
    day = int(lines[0])
    month = int(lines[1])
    year = int(lines[2])
    time_hours = _parse_float(lines[3])
    tz_offset = _parse_float(lines[4])
    longitude = _parse_float(lines[5])
    latitude = _parse_float(lines[6])

    ayanamsa_override = 0.0

    if n <= 8:
        # BIRTH_ONLY — just birth data
        if n == 8:
            ayanamsa_override = _parse_float(lines[7])
        return JhdData(
            filename=filename, format=JhdFormat.BIRTH_ONLY,
            day=day, month=month, year=year,
            time_hours=time_hours, tz_offset=tz_offset,
            longitude=longitude, latitude=latitude,
            ayanamsa_override=ayanamsa_override,
        )

    # n >= 14 — check if line 12 is a city name (non-numeric)
    is_city = n > 12 and not lines[12].replace(".", "").replace("-", "").replace(" ", "").isdigit()

    if is_city:
        # BIRTH_CITY variant
        ayanamsa_override = _parse_float(lines[7])
        city = lines[12].strip()
        country = lines[13].strip() if n > 13 else ""
        planet_longitudes = None

        if n >= 18 and lines[14].replace(".","").replace("-","").isdigit():
            fmt = JhdFormat.BIRTH_CITY_EXTRA
            # lines[14-17] = extra computed fields
        else:
            fmt = JhdFormat.BIRTH_CITY

        return JhdData(
            filename=filename, format=fmt,
            day=day, month=month, year=year,
            time_hours=time_hours, tz_offset=tz_offset,
            longitude=longitude, latitude=latitude,
            ayanamsa_override=ayanamsa_override,
            city=city, country=country,
            planet_longitudes=planet_longitudes,
        )

    # No city — check if we have planet positions (lines 8-16 are large longitudes)
    if n >= 17 and all(c.isdigit() or c in '.-' for c in lines[8]) and float(lines[8]) > 100:
        ayanamsa_override = _parse_float(lines[7])
        planet_longitudes = [_parse_float(lines[i]) for i in range(8, min(17, n))]
        return JhdData(
            filename=filename, format=JhdFormat.PLANET_POSITIONS,
            day=day, month=month, year=year,
            time_hours=time_hours, tz_offset=tz_offset,
            longitude=longitude, latitude=latitude,
            ayanamsa_override=ayanamsa_override,
            planet_longitudes=planet_longitudes,
        )

    ayanamsa_override = _parse_float(lines[7])
    return JhdData(
        filename=filename, format=JhdFormat.BIRTH_ONLY,
        day=day, month=month, year=year,
        time_hours=time_hours, tz_offset=tz_offset,
        longitude=longitude, latitude=latitude,
        ayanamsa_override=ayanamsa_override,
    )
