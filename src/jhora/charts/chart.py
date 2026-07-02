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

    # Vargas (lazy computed)
    varga_positions: Dict[Tuple[VargaLevel, VargaVariant], Dict[Graha, VargaPosition]] = field(default_factory=dict)

    def planet(self, graha: Graha) -> PlanetChartData:
        return self.planets[graha]

    @property
    def sun(self) -> PlanetChartData:
        return self.planets[Graha.SUN]

    @property
    def moon(self) -> PlanetChartData:
        return self.planets[Graha.MOON]


class ChartBuilder:
    """Builds ChartData from birth information."""

    def __init__(self, swe: Optional[SweEngine] = None):
        self.swe = swe or SweEngine()

    def build(
        self,
        year: int, month: int, day: int,
        hour: float,
        lat: float, lon: float,
        tz: str = "UTC",
        ayanamsa: str = "lahiri",
        house_sys: bytes = b'P',
    ) -> ChartData:
        self.swe.set_sidereal_mode(ayanamsa)
        jd = self.swe.julday(year, month, day, hour)
        ayanamsa_val = self.swe.get_ayanamsa(jd)

        # Compute planets
        raw = self.swe.calc_planets(jd)
        planet_data = {}
        for se_id in range(7):
            g = Graha(se_id)
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

        # Rahu and Ketu
        pd_rahu = raw[10]
        rasi_r = Rasi.from_longitude(pd_rahu.longitude)
        naks_r, pada_r = Nakshatra.from_longitude(pd_rahu.longitude)
        planet_data[Graha.RAHU] = PlanetChartData(
            graha=Graha.RAHU, longitude=pd_rahu.longitude,
            latitude=pd_rahu.latitude, speed=pd_rahu.speed,
            is_retrograde=pd_rahu.is_retrograde,
            rasi=rasi_r, degrees_in_rasi=pd_rahu.degrees_in_rasi,
            nakshatra=naks_r, nakshatra_pada=pada_r, dignity="node",
        )
        pd_ketu = raw[11]
        rasi_k = Rasi.from_longitude(pd_ketu.longitude)
        naks_k, pada_k = Nakshatra.from_longitude(pd_ketu.longitude)
        planet_data[Graha.KETU] = PlanetChartData(
            graha=Graha.KETU, longitude=pd_ketu.longitude,
            latitude=pd_ketu.latitude, speed=pd_ketu.speed,
            is_retrograde=pd_ketu.is_retrograde,
            rasi=rasi_k, degrees_in_rasi=pd_ketu.degrees_in_rasi,
            nakshatra=naks_k, nakshatra_pada=pada_k, dignity="node",
        )

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

        return ChartData(
            birth_date=datetime(year, month, day),
            julian_day=jd, latitude=lat, longitude=lon,
            timezone=tz, ayanamsa_name=ayanamsa,
            ayanamsa_value=ayanamsa_val,
            planets=planet_data, lagna=lagna,
            house_cusps=tuple(hd.cusps),
            ascendant=hd.ascendant, mc=hd.mc,
        )

    @staticmethod
    def _calc_dignity(graha: Graha, lon: float) -> str:
        """Determine basic dignity of a planet."""
        deg_in_sign = lon % 30
        rasi = int(lon // 30) % 12
        from jhora.calc.dignities import DignityChecker
        checker = DignityChecker()
        return checker.get_dignity(graha, rasi, deg_in_sign)
