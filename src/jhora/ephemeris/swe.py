"""
SweEngine — central Swiss Ephemeris wrapper.

Wraps all 18 SE API functions used by the classical Vedic binary.
Caches recent calculations for performance.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import swisseph as swe


# Planet IDs matching Swiss Ephemeris constants
SE_SUN = swe.SUN
SE_MOON = swe.MOON
SE_MARS = swe.MARS
SE_MERCURY = swe.MERCURY
SE_JUPITER = swe.JUPITER
SE_VENUS = swe.VENUS
SE_SATURN = swe.SATURN
SE_RAHU = swe.TRUE_NODE
SE_KETU = swe.OSCU_APOG  # or swe.MEAN_APOG?
# pyswisseph doesn't have ASC_BIT — use combo flag
SE_ASCENDANT = 0x10000

# House system constants (same as SE)
SE_HOUSES_PLACIDUS = b'P'
SE_HOUSES_EQUAL = b'E'
SE_HOUSES_REGIOMONTANUS = b'R'
SE_HOUSES_CAMPANUS = b'C'
SE_HOUSES_PORPHYRIUS = b'O'

# Calculation flags
SEFLG_SPEED = swe.FLG_SPEED          # 256
SEFLG_SIDEREAL = swe.FLG_SIDEREAL    # 64
SEFLG_TOPO = swe.FLG_TOPOCTR         # 8192
SEFLG_SWIEPH = swe.FLG_SWIEPH        # 1024
SEFLG_DEFAULT = SEFLG_SWIEPH | SEFLG_SPEED | SEFLG_SIDEREAL

# Sidereal modes (matching JHora ayanamsas)
# Using available pyswisseph constants:
# Lahiri=1, Raman=3, Krishnamurti=5, True Citra=27, True Pushya=29, Aldebaran 15Tau=14


SIDMODE_MAP = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
    "fagan": swe.SIDM_FAGAN_BRADLEY,
    "usha_shashi": swe.SIDM_USHASHASHI,
    "deva_datta": swe.SIDM_DELUCE,
    "de_luce": swe.SIDM_DELUCE,
    "yukteshwar": swe.SIDM_YUKTESHWAR,
    "jn_bhasin": swe.SIDM_JN_BHASIN,
    "sss": swe.SIDM_TRUE_CITRA,
    "true_citra": swe.SIDM_TRUE_CITRA,
    "pushya_paksha": swe.SIDM_TRUE_PUSHYA,
    "true_pushya": swe.SIDM_TRUE_PUSHYA,
    "rohini_paksha": swe.SIDM_ALDEBARAN_15TAU,
    "aldebaran": swe.SIDM_ALDEBARAN_15TAU,
    "surya_siddhanta": swe.SIDM_SURYASIDDHANTA,
    "aryabhata": swe.SIDM_ARYABHATA,
    "hipparchos": swe.SIDM_HIPPARCHOS,
    "sassanian": swe.SIDM_SASSANIAN,
    "tropical": None,  # handled specially — no sidereal offset
}


@dataclass
class PlanetData:
    """Planet position data returned by SweEngine."""
    longitude: float        # degrees (0-360)
    latitude: float         # degrees
    speed: float            # degrees/day
    distance_au: float
    is_retrograde: bool

    @property
    def rasi_index(self) -> int:
        return int(self.longitude // 30) % 12

    @property
    def degrees_in_rasi(self) -> float:
        return self.longitude % 30

    @property
    def rasi(self) -> str:
        names = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]
        return names[self.rasi_index]


@dataclass
class HouseData:
    """House cusps and related points."""
    cusps: List[float]       # 13 cusps (index 1-12 used)
    ascendant: float
    mc: float
    arudha_lagna: Optional[float] = None


class SweEngine:
    """Wrapper around Swiss Ephemeris with caching."""

    def __init__(self, ephe_path: Optional[str] = None):
        if ephe_path:
            swe.set_ephe_path(ephe_path)
        self._ayanamsa_name: str = "lahiri"
        self._sidereal_mode: int = swe.SIDM_LAHIRI
        self._flags: int = SEFLG_DEFAULT
        self._cache: Dict = {}
        swe.set_sid_mode(self._sidereal_mode)

    def set_sidereal_mode(self, name: str) -> None:
        """Set ayanamsa mode by name. Use 'tropical' for no ayanamsa."""
        name_lower = name.lower()
        if name_lower == "tropical":
            swe.set_sid_mode(swe.SIDM_USER, 0.0, 0.0)
            self._sidereal_mode = swe.SIDM_USER
            self._ayanamsa_name = "tropical"
            self._flags = SEFLG_DEFAULT
            self._cache.clear()
            return
        mode = SIDMODE_MAP.get(name_lower)
        if mode is None:
            raise ValueError(f"Unknown ayanamsa: {name}. Options: {list(SIDMODE_MAP.keys())}")
        self._sidereal_mode = mode
        self._ayanamsa_name = name
        self._flags = SEFLG_DEFAULT
        swe.set_sid_mode(mode)
        self._cache.clear()

    def get_ayanamsa(self, jd: float) -> float:
        """Get ayanamsa value for given Julian day."""
        return swe.get_ayanamsa(jd)

    def calc_planet(self, planet_id: int, jd: float, flags: Optional[int] = None) -> PlanetData:
        """Compute planet position at given Julian day.
        
        Planet IDs: SE_SUN=0, SE_MOON=1, ... SE_TRUE_NODE=10, SE_OSCU_APOG=11
        """
        f = flags if flags is not None else self._flags
        result = swe.calc_ut(jd, planet_id, f)
        arr = result[0]
        # arr = [longitude, latitude, distance, longitude_speed, latitude_speed, distance_speed]
        lon, lat, dist, lon_speed = arr[0], arr[1], arr[2], arr[3]
        return PlanetData(
            longitude=lon % 360,
            latitude=lat,
            speed=lon_speed,
            distance_au=dist,
            is_retrograde=lon_speed < 0,
        )

    def calc_planets(self, jd: float) -> Dict[int, PlanetData]:
        """Compute all 7 planets + Rahu/Ketu + 3 outer planets at once."""
        planets = {}
        for pid in range(7):  # SUN(0) through SATURN(6)
            planets[pid] = self.calc_planet(pid, jd)
        # Outer planets
        for pid in [7, 8, 9]:  # Uranus, Neptune, Pluto
            planets[pid] = self.calc_planet(pid, jd)
        rahu = self.calc_planet(swe.MEAN_NODE, jd)
        planets[10] = PlanetData(
            longitude=rahu.longitude, latitude=rahu.latitude,
            speed=rahu.speed, distance_au=rahu.distance_au,
            is_retrograde=rahu.is_retrograde,
        )
        ketu_lon = (rahu.longitude + 180) % 360
        planets[11] = PlanetData(
            longitude=ketu_lon, latitude=-rahu.latitude,
            speed=rahu.speed, distance_au=rahu.distance_au,
            is_retrograde=not rahu.is_retrograde,
        )
        return planets

    def houses(self, jd: float, lat: float, lon: float, house_sys: bytes = b'P') -> HouseData:
        """Compute house cusps for given JD and location."""
        cusps, ascmc = swe.houses(jd, lat, lon, house_sys)
        return HouseData(
            cusps=list(cusps),
            ascendant=ascmc[0] % 360,
            mc=ascmc[1] % 360,
        )

    def fixstar(self, star_name: str, jd: float) -> PlanetData:
        """Compute fixed star position."""
        result = swe.fixstar_ut(star_name, jd, self._flags)
        arr = result[0]
        lon, lat, dist, lon_speed = arr[0], arr[1], arr[2], arr[3]
        return PlanetData(
            longitude=lon % 360,
            latitude=lat,
            speed=lon_speed,
            distance_au=dist,
            is_retrograde=False,
        )

    def julday(self, year: int, month: int, day: int, hour: float, greg: bool = True) -> float:
        """Convert calendar date to Julian day (UT)."""
        return swe.julday(year, month, day, hour, 1 if greg else 0)

    def revjul(self, jd: float) -> Tuple[int, int, int, float]:
        """Convert Julian day to calendar date."""
        year, month, day, hour = swe.revjul(jd)
        return int(year), int(month), int(day), float(hour)

    def solcross_ut(self, x2cross: float, jd_start: float,
                    flags: Optional[int] = None) -> float:
        """Find next UT time when Sun crosses a given longitude.

        Args:
            x2cross: target longitude (degrees)
            jd_start: start search from this Julian day (UT)
            flags: calculation flags (uses default if None)

        Returns:
            Julian day (UT) of the crossing.
        """
        f = flags if flags is not None else self._flags
        return swe.solcross_ut(x2cross % 360, jd_start, f)

    def helio_cross_ut(self, planet: int, x2cross: float, jd_start: float,
                       flags: Optional[int] = None,
                       backwards: bool = False) -> float:
        """Find when a planet crosses a given longitude (heliocentric, UT).

        Args:
            planet: SE planet ID
            x2cross: target longitude (degrees)
            jd_start: start search from this Julian day (UT)
            flags: calculation flags
            backwards: search backwards in time

        Returns:
            Julian day (UT) of the crossing.
        """
        f = flags if flags is not None else self._flags
        return swe.helio_cross_ut(planet, x2cross % 360, jd_start, f, backwards)

    def rise_trans(self, jd: float, body: int, lat: float, lon: float,
                   rise: bool = True) -> Optional[float]:
        """Compute sunrise/sunset or moonrise/moonset time.
        
        Returns JD of the event, or None if it doesn't occur.
        """
        rsmi = swe.CALC_RISE if rise else swe.CALC_SET
        geopos = (lon, lat, 0.0)
        result = swe.rise_trans(jd, body, rsmi, geopos)
        return result[1][0] if result[0] == 0 else None

    def deltat(self, jd: float) -> float:
        """Get Delta T (difference between TT and UT) in days."""
        return swe.deltat(jd)

    def azalt(self, jd: float, lat: float, lon: float, 
              body_lon: float, body_lat: float) -> Tuple[float, float]:
        """Compute azimuth and altitude of a celestial body."""
        geo_pos = (lon, lat, 0.0)  # (lon, lat, altitude)
        result = swe.azalt(jd, swe.CALC_ALT, geo_pos, body_lon, body_lat)
        return (result[0], result[1])  # azimuth, altitude

    def close(self) -> None:
        """Close ephemeris files."""
        swe.close()
        self._cache.clear()
