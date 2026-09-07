"""
ChartData — immutable data structure holding all computed chart information.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra
from jhora.types.varga import VargaLevel, VargaVariant
from jhora.ephemeris.swe import SweEngine, PlanetData, HouseData


@dataclass(frozen=True)
class PlanetChartData:
    """Position of a single planet in the chart."""
    graha: Graha
    longitude: float
    latitude: float
    speed: float
    is_retrograde: bool
    rasi: Rasi
    degrees_in_rasi: float
    nakshatra: Nakshatra
    nakshatra_pada: int
    dignity: str

    @property
    def rasi_name(self) -> str:
        return self.rasi.full_name

    @property
    def nakshatra_name(self) -> str:
        return self.nakshatra.name.replace("_", " ").title()


@dataclass(frozen=True)
class VargaPosition:
    """Planet position in a divisional chart."""
    graha: Graha
    varga_level: VargaLevel
    variant: VargaVariant
    longitude: float
    rasi: Rasi
    degrees_in_rasi: float


@dataclass(frozen=True)
class ChartData:
    """Complete chart calculation result — immutable."""
    # Input
    birth_date: datetime
    julian_day: float
    latitude: float
    longitude: float
    timezone: str
    ayanamsa_name: str
    ayanamsa_value: float

    # Planets
    planets: Dict[Graha, PlanetChartData]

    # Lagnas
    lagna: PlanetChartData
    bhava_lagna: Optional[PlanetChartData] = None
    hora_lagna: Optional[PlanetChartData] = None
    ghati_lagna: Optional[PlanetChartData] = None
    sree_lagna: Optional[PlanetChartData] = None

    # Houses
    house_cusps: Tuple[float, ...] = field(default_factory=lambda: tuple(range(12)))
    ascendant: float = 0.0
    mc: float = 0.0

    # Outer planets (computed but not in main planets dict)
    outer_planets: Dict[str, dict] = field(default_factory=dict)

    # Vargas (lazy computed)
    varga_positions: Dict[Tuple[VargaLevel, VargaVariant], Dict[Graha, VargaPosition]] = field(default_factory=dict)

    # Metadata
    sex: str = ""

    def planet(self, graha: Graha) -> PlanetChartData:
        return self.planets[graha]

    @property
    def sun(self) -> PlanetChartData:
        return self.planets[Graha.SUN]

    @property
    def moon(self) -> PlanetChartData:
        return self.planets[Graha.MOON]

    @property
    def time_of_day_hours(self) -> float:
        """Local clock time in decimal hours, derived from JD and timezone."""
        _year, _month, _day, utc_hour = SweEngine().revjul(self.julian_day)
        local_hour = utc_hour - ChartBuilder._parse_tz(self.timezone)
        return local_hour % 24.0


class ChartBuilder:
    """Builds ChartData from birth information."""

    def __init__(self, swe: Optional[SweEngine] = None):
        self.swe = swe or SweEngine()

    @staticmethod
    def _parse_tz(tz: str) -> float:
        """Parse timezone string to signed decimal hours.
        
        Convention: tz_offset is added to local time to get UTC.
        For India (UTC+5:30): UTC = local - 5:30, so tz_offset = -5.5.
        
        Supports:
          "+0530", "+05:30", "+5:30", "+5.5", "+5" → -5.5 (UTC+X means local ahead, so subtrahend)
          "-0500", "-05:00", "-5:00" → +5.0 (UTC-X means local behind, so addend)
          "-5.36", "-5.5" (decimal) → direct JHD format
          "Asia/Kolkata" → IANA timezone lookup
        """
        if not tz or tz in ("UTC", "GMT", "Z"):
            return 0.0
        tz = tz.strip()

        if "/" in tz:
            try:
                from zoneinfo import ZoneInfo
                from datetime import datetime
                zi = ZoneInfo(tz)
                offset_sec = datetime.now(zi).utcoffset().total_seconds()
                return -(offset_sec / 3600.0)
            except Exception:
                pass

        try:
            if tz.startswith("+"):
                rest = tz[1:].strip()
                if ":" in rest:
                    h, m = rest.split(":", 1)
                    return -(float(h) + float(m) / 60.0)
                elif len(rest) == 4 and rest.isdigit():
                    h, m = int(rest[:2]), int(rest[2:])
                    return -(h + m / 60.0)
                else:
                    return -float(rest)
            elif tz.startswith("-"):
                rest = tz[1:].strip()
                if ":" in rest:
                    h, m = rest.split(":", 1)
                    return float(h) + float(m) / 60.0
                elif len(rest) == 4 and rest.isdigit():
                    h, m = int(rest[:2]), int(rest[2:])
                    return float(h) + float(m) / 60.0
                else:
                    return float(tz)
            if ":" in tz:
                h, m = tz.split(":", 1)
                return -(float(h) + float(m) / 60.0)
            elif len(tz) == 4 and tz.isdigit():
                h, m = int(tz[:2]), int(tz[2:])
                return -(h + m / 60.0)
            return float(tz)
        except (ValueError, IndexError):
            return 0.0

    def build(
        self,
        year: int, month: int, day: int,
        hour: float,
        lat: float, lon: float,
        tz: str = "UTC",
        ayanamsa: str = "lahiri",
        house_sys: bytes = b'P',
        sex: str = "",
    ) -> ChartData:
        self.swe.set_sidereal_mode(ayanamsa)
        tz_offset = self._parse_tz(tz)
        utc_hour = hour + tz_offset  # local → UTC via signed offset
        jd = self.swe.julday(year, month, day, utc_hour)
        ayanamsa_val = self.swe.get_ayanamsa(jd)

        # SE→Graha mapping: Graha enum uses Vedic numbering, not SE IDs
        _SE_TO_GRAHA = {
            0: Graha.SUN, 1: Graha.MOON, 2: Graha.MERCURY,
            3: Graha.VENUS, 4: Graha.MARS, 5: Graha.JUPITER,
            6: Graha.SATURN, 10: Graha.RAHU, 11: Graha.KETU,
        }
        _OUTER_PLANETS = {7: "Uranus", 8: "Neptune", 9: "Pluto"}
        raw = self.swe.calc_planets(jd)
        planet_data = {}
        for se_id, g in _SE_TO_GRAHA.items():
            pd = raw[se_id]
            rasi = Rasi.from_longitude(pd.longitude)
            naks, pada = Nakshatra.from_longitude(pd.longitude)
            dignity = self._calc_dignity(g, pd.longitude)
            planet_data[g] = PlanetChartData(
                graha=g, longitude=pd.longitude, latitude=pd.latitude,
                speed=pd.speed, is_retrograde=pd.is_retrograde,
                rasi=rasi, degrees_in_rasi=pd.degrees_in_rasi,
                nakshatra=naks, nakshatra_pada=pada, dignity=dignity,
            )
        outer_data = {}
        for se_id, name in _OUTER_PLANETS.items():
            pd = raw[se_id]
            r = Rasi.from_longitude(pd.longitude)
            outer_data[name] = {
                "longitude": pd.longitude, "sign": r.short_name,
                "sign_full": r.full_name, "is_retrograde": pd.is_retrograde,
                "speed": pd.speed,
            }

        # Houses
        hd = self.swe.houses(jd, lat, lon, house_sys)

        # Lagna
        lagna_rasi = Rasi.from_longitude(hd.ascendant)
        naks_l, pada_l = Nakshatra.from_longitude(hd.ascendant)
        lagna = PlanetChartData(
            graha=Graha.SUN,  # placeholder — lagna is not a planet
            longitude=hd.ascendant, latitude=0, speed=0,
            is_retrograde=False, rasi=lagna_rasi,
            degrees_in_rasi=hd.ascendant % 30,
            nakshatra=naks_l, nakshatra_pada=pada_l,
            dignity="lagna",
        )

        cd = ChartData(
            birth_date=datetime(year, month, day),
            julian_day=jd, latitude=lat, longitude=lon,
            timezone=tz, ayanamsa_name=ayanamsa,
            ayanamsa_value=ayanamsa_val,
            sex=sex,
            planets=planet_data, lagna=lagna,
            house_cusps=tuple(hd.cusps),
            ascendant=hd.ascendant, mc=hd.mc,
            outer_planets=outer_data,
        )

        # Populate sunrise-based special lagnas (Bhava / Hora / Ghati / Sree).
        sl = self._special_lagna_positions(cd)
        if sl:
            from dataclasses import replace as _replace
            cd = _replace(cd, bhava_lagna=sl.get("bhava"),
                          hora_lagna=sl.get("hora"),
                          ghati_lagna=sl.get("ghati"),
                          sree_lagna=sl.get("sree"))
        return cd

    def _special_lagna_positions(self, cd: ChartData) -> Dict:
        """Return PlanetChartData for the sunrise-based special lagnas, if any.

        Returns an empty dict when the ephemeris sunrise cannot be determined
        (e.g. polar day/night), keeping the chart fields None-safe.
        """
        from jhora.calc import special_lagnas as _sl
        lons = _sl.compute_time_lagnas(cd)
        if any(lons.get(k) is None for k in ("bhava", "hora", "ghati", "sree")):
            return {}

        def _mk(lon):
            rasi = Rasi.from_longitude(lon)
            nak, pada = Nakshatra.from_longitude(lon)
            return PlanetChartData(
                graha=Graha.SUN, longitude=lon, latitude=0, speed=0,
                is_retrograde=False, rasi=rasi,
                degrees_in_rasi=lon % 30,
                nakshatra=nak, nakshatra_pada=pada, dignity="lagna",
            )

        return {k: _mk(lons[k]) for k in ("bhava", "hora", "ghati", "sree")}

    @staticmethod
    def _calc_dignity(graha: Graha, lon: float) -> str:
        """Determine basic dignity of a planet."""
        deg_in_sign = lon % 30
        rasi = int(lon // 30) % 12
        from jhora.calc.dignities import DignityChecker
        checker = DignityChecker()
        return checker.get_dignity(graha, rasi, deg_in_sign)
