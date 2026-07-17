"""Shadbala — six-fold planetary strength (Brihat Parasara Hora Sastra).

Components:
  Sthana Bala (positional)   — Uchcha, Saptavargaja, Ojayugma, Kendra, Drekkana
  Dig Bala    (directional)  — Kendra bhava strength
  Kala Bala   (temporal)     — Nathonnata, Paksha, Tribhaga, Abda, Masa, Vara, Hora, Ayana
  Chesta Bala (motional)     — Retrogression + elongation + speed
  Naisargika  (natural)      — Fixed per BPHS
  Drik Bala   (aspectual)    — Aspect contribution from other planets

References:
  - Brihat Parasara Hora Sastra, Chapters 9-10
  - "Graha and Bhava Balas" by Dr. B.V. Raman
  - Original Vedic astrology binary (function 0x0045d1e0)
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from jhora.charts.chart import ChartData
from jhora.charts.varga import VargaChartComputer, VargaLevel, VargaVariant
from jhora.calc.angles import diff as angle_diff
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

_RUPA = 60.0

_SAPTAVARGA_LEVELS = [
    VargaLevel.D_1, VargaLevel.D_2, VargaLevel.D_3,
    VargaLevel.D_7, VargaLevel.D_9, VargaLevel.D_12, VargaLevel.D_30,
]

_EXALTATION_SIGN_DEG: Dict[Graha, float] = {
    Graha.SUN: 10.0, Graha.MOON: 33.0, Graha.MARS: 298.0,
    Graha.MERCURY: 165.0, Graha.JUPITER: 95.0, Graha.VENUS: 357.0,
    Graha.SATURN: 200.0,
}

_DEBILITATION_DEG: Dict[Graha, float] = {
    Graha.SUN: 190.0, Graha.MOON: 213.0, Graha.MARS: 118.0,
    Graha.MERCURY: 345.0, Graha.JUPITER: 275.0, Graha.VENUS: 177.0,
    Graha.SATURN: 20.0,
}

_NAISARGIKA_BALA: Dict[Graha, float] = {
    Graha.SUN: 60.0, Graha.MOON: 51.43, Graha.MARS: 17.14,
    Graha.MERCURY: 25.71, Graha.JUPITER: 34.29, Graha.VENUS: 42.86,
    Graha.SATURN: 8.57,
}

_DIG_BALA_HOUSE: Dict[Graha, int] = {
    Graha.SUN: 9, Graha.MOON: 3, Graha.MARS: 9,
    Graha.MERCURY: 0, Graha.JUPITER: 0, Graha.VENUS: 3,
    Graha.SATURN: 6,
}

_MEAN_SPEEDS: Dict[Graha, float] = {
    Graha.SUN: 0.9856, Graha.MOON: 13.176, Graha.MARS: 0.524,
    Graha.MERCURY: 1.383, Graha.JUPITER: 0.083, Graha.VENUS: 1.200,
    Graha.SATURN: 0.033,
}

_SAPTAVARGA_POINTS: Dict[str, float] = {
    "own": 30.0, "moolatrikona": 45.0, "friend": 22.5,
    "neutral": 15.0, "enemy": 7.5, "exalted": 45.0,
}

_FRIEND_RELATIONS: Dict[Graha, Dict[str, list]] = {
    Graha.SUN:     {"friend": [Graha.MOON, Graha.MARS, Graha.JUPITER],
                     "enemy": [Graha.VENUS, Graha.SATURN]},
    Graha.MOON:    {"friend": [Graha.SUN, Graha.MERCURY],
                     "enemy": []},
    Graha.MARS:    {"friend": [Graha.SUN, Graha.MOON, Graha.JUPITER],
                     "enemy": [Graha.MERCURY]},
    Graha.MERCURY: {"friend": [Graha.SUN, Graha.VENUS],
                     "enemy": [Graha.MOON]},
    Graha.JUPITER: {"friend": [Graha.SUN, Graha.MOON, Graha.MARS],
                     "enemy": [Graha.MERCURY, Graha.VENUS]},
    Graha.VENUS:   {"friend": [Graha.MERCURY, Graha.SATURN],
                     "enemy": [Graha.SUN, Graha.MOON]},
    Graha.SATURN:  {"friend": [Graha.MERCURY, Graha.VENUS],
                     "enemy": [Graha.SUN, Graha.MOON, Graha.MARS]},
}

_PLANET_SIGN_OWNERSHIP: Dict[Graha, list] = {
    Graha.SUN: [5], Graha.MOON: [4], Graha.MARS: [1, 8],
    Graha.MERCURY: [3, 6], Graha.JUPITER: [9, 12],
    Graha.VENUS: [2, 7], Graha.SATURN: [10, 11],
}

_SIGN_OWNER: Dict[int, Graha] = {}
for g, signs in _PLANET_SIGN_OWNERSHIP.items():
    for s in signs:
        _SIGN_OWNER[s] = g

_MOOLATRIKONA_SIGN: Dict[Graha, int] = {
    Graha.SUN: 4, Graha.MOON: 1, Graha.MARS: 0,
    Graha.MERCURY: 5, Graha.JUPITER: 8, Graha.VENUS: 6,
    Graha.SATURN: 10,
}


@dataclass
class ShadbalaComponent:
    name: str
    virupa: float
    max_virupa: float

    @property
    def rupa(self) -> float:
        return self.virupa / _RUPA

    @property
    def pct(self) -> float:
        return (self.virupa / self.max_virupa * 100) if self.max_virupa > 0 else 0.0


@dataclass
class ShadbalaResult:
    graha: Graha
    sthana: Dict[str, ShadbalaComponent]
    dig: Dict[str, ShadbalaComponent]
    kala: Dict[str, ShadbalaComponent]
    chesta: Dict[str, ShadbalaComponent]
    naisargika: ShadbalaComponent
    drik: ShadbalaComponent

    @property
    def sthana_total(self) -> float:
        return sum(c.virupa for c in self.sthana.values())

    @property
    def dig_total(self) -> float:
        return sum(c.virupa for c in self.dig.values())

    @property
    def kala_total(self) -> float:
        return sum(c.virupa for c in self.kala.values())

    @property
    def chesta_total(self) -> float:
        return sum(c.virupa for c in self.chesta.values())

    @property
    def total_virupa(self) -> float:
        return (
            self.sthana_total + self.dig_total + self.kala_total
            + self.chesta_total + self.naisargika.virupa + self.drik.virupa
        )

    @property
    def total_rupa(self) -> float:
        return self.total_virupa / _RUPA

    def summary(self) -> str:
        return (
            f"{self.graha.full_name:8s}  "
            f"S={self.sthana_total/60:.2f}  D={self.dig_total/60:.2f}  "
            f"K={self.kala_total/60:.2f}  C={self.chesta_total/60:.2f}  "
            f"N={self.naisargika.rupa:.2f}  Dr={self.drik.rupa:.2f}  "
            f"Tot={self.total_rupa:.2f}R"
        )


class ShadbalaComputer:
    def __init__(self, cd: ChartData):
        self.cd = cd
        self._house_of: Dict[Graha, int] = {}
        self._asc_rasi = int(cd.ascendant // 30) % 12
        for g, p in cd.planets.items():
            self._house_of[g] = (int(p.longitude // 30) % 12 - self._asc_rasi) % 12
        self._varga_computer = VargaChartComputer()
        self._varga_cache: Dict[VargaLevel, dict] = {}
        self._init_vargas()

    def _init_vargas(self):
        for vl in _SAPTAVARGA_LEVELS:
            try:
                vcd = self._varga_computer.compute(self.cd, vl, VargaVariant.DEFAULT)
                self._varga_cache[vl] = {
                    g: vp.rasi.value for g, vp in vcd.positions.items()
                }
            except Exception:
                self._varga_cache[vl] = {}

    def compute(self) -> Dict[Graha, ShadbalaResult]:
        results = {}
        for g in self.cd.planets:
            results[g] = ShadbalaResult(
                graha=g,
                sthana=self._sthana_bala(g),
                dig=self._dig_bala(g),
                kala=self._kala_bala(g),
                chesta=self._chesta_bala(g),
                naisargika=self._naisargika_bala(g),
                drik=self._drik_bala(g),
            )
        return results

    def compute_one(self, g: Graha) -> ShadbalaResult:
        return ShadbalaResult(
            graha=g,
            sthana=self._sthana_bala(g),
            dig=self._dig_bala(g),
            kala=self._kala_bala(g),
            chesta=self._chesta_bala(g),
            naisargika=self._naisargika_bala(g),
            drik=self._drik_bala(g),
        )

    def _sthana_bala(self, g: Graha) -> Dict[str, ShadbalaComponent]:
        return {
            "uchcha": self._uchcha_bala(g),
            "saptavargaja": self._saptavargaja_bala(g),
            "ojhayugma": self._ojhayugma_bala(g),
            "kendra": self._kendra_bala(g),
            "drekkana": self._drekkana_bala(g),
        }

    def _uchcha_bala(self, g: Graha) -> ShadbalaComponent:
        if g not in self.cd.planets or g not in _DEBILITATION_DEG:
            return ShadbalaComponent("uchcha", 0, 60)
        planet_lon = self.cd.planets[g].longitude
        deb_deg = _DEBILITATION_DEG[g]
        dist = min(abs(planet_lon - deb_deg), 360 - abs(planet_lon - deb_deg))
        virupa = dist / 3.0
        return ShadbalaComponent("uchcha", virupa, 60)

    def _saptavargaja_bala(self, g: Graha) -> ShadbalaComponent:
        total = 0.0
        for vl in _SAPTAVARGA_LEVELS:
            varga_data = self._varga_cache.get(vl, {})
            if g not in varga_data:
                continue
            sign_idx = varga_data[g]
            pts = self._varga_points_for_sign(g, sign_idx)
            total += pts
        virupa = min(total, 315.0)
        return ShadbalaComponent("saptavargaja", virupa, 315)

    def _varga_points_for_sign(self, g: Graha, sign_idx: int) -> float:
        owner = _SIGN_OWNER.get(sign_idx)
        if g in _MOOLATRIKONA_SIGN and _MOOLATRIKONA_SIGN[g] == sign_idx:
            return _SAPTAVARGA_POINTS["moolatrikona"]
        if owner == g:
            return _SAPTAVARGA_POINTS["own"]
        relations = _FRIEND_RELATIONS.get(g, {})
        friends = relations.get("friend", [])
        enemies = relations.get("enemy", [])
        if owner in friends:
            return _SAPTAVARGA_POINTS["friend"]
        elif owner in enemies:
            return _SAPTAVARGA_POINTS["enemy"]
        else:
            return _SAPTAVARGA_POINTS["neutral"]

    def _ojhayugma_bala(self, g: Graha) -> ShadbalaComponent:
        if g not in self.cd.planets:
            return ShadbalaComponent("ojhayugma", 0, 15)
        p = self.cd.planets[g]
        is_odd = p.rasi.is_odd
        male = (Graha.SUN, Graha.MARS, Graha.JUPITER)
        female = (Graha.MOON, Graha.VENUS)
        if g in male and is_odd:
            return ShadbalaComponent("ojhayugma", 15, 15)
        if g in female and not is_odd:
            return ShadbalaComponent("ojhayugma", 15, 15)
        if g == Graha.MERCURY:
            return ShadbalaComponent("ojhayugma", 15, 15)
        return ShadbalaComponent("ojhayugma", 0, 15)

    def _kendra_bala(self, g: Graha) -> ShadbalaComponent:
        if g not in self._house_of:
            return ShadbalaComponent("kendra", 0, 60)
        house = self._house_of[g]
        if house in (0, 3, 6, 9):
            return ShadbalaComponent("kendra", 60, 60)
        elif house in (1, 4, 7, 10):
            return ShadbalaComponent("kendra", 30, 60)
        else:
            return ShadbalaComponent("kendra", 15, 60)

    def _drekkana_bala(self, g: Graha) -> ShadbalaComponent:
        if g not in self.cd.planets:
            return ShadbalaComponent("drekkana", 0, 15)
        p = self.cd.planets[g]
        drek = int(p.degrees_in_rasi // 10)
        male_planets = (Graha.SUN, Graha.MARS, Graha.JUPITER)
        female_planets = (Graha.MOON, Graha.VENUS)
        drek_lords = [Graha.MARS, Graha.SUN, Graha.JUPITER]
        drek_is_male = drek_lords[drek % 3] in male_planets
        planet_is_male = g in male_planets
        if drek_is_male == planet_is_male:
            return ShadbalaComponent("drekkana", 15, 15)
        if g in (Graha.MERCURY, Graha.SATURN):
            return ShadbalaComponent("drekkana", 15, 15)
        return ShadbalaComponent("drekkana", 0, 15)

    def _dig_bala(self, g: Graha) -> Dict[str, ShadbalaComponent]:
        if g not in self._house_of or g not in _DIG_BALA_HOUSE:
            return {}
        house = self._house_of[g]
        best = _DIG_BALA_HOUSE[g]
        sep = abs(house - best)
        if sep > 6:
            sep = 12 - sep
        virupa = max(0, 60 - sep * 10)
        return {"dig": ShadbalaComponent("dig", virupa, 60)}

    def _kala_bala(self, g: Graha) -> Dict[str, ShadbalaComponent]:
        return {
            "nathonnatha": self._nathonnatha_bala(g),
            "paksha": self._paksha_bala(g),
            "tribhaga": self._tribhaga_bala(g),
            "abda": self._abda_bala(g),
            "masa": self._masa_bala(g),
            "vara": self._vara_bala(g),
            "hora": self._hora_bala(g),
            "ayana": self._ayana_bala(g),
        }

    def _nathonnatha_bala(self, g: Graha) -> ShadbalaComponent:
        jd = self.cd.julian_day
        lat = self.cd.latitude
        frac = (jd + 0.5) % 1.0
        hour_of_day = frac * 24
        is_day = 6 <= hour_of_day < 18
        if g in (Graha.SUN, Graha.JUPITER, Graha.VENUS):
            base = 60 if is_day else 0
        elif g in (Graha.MOON, Graha.MARS, Graha.SATURN):
            base = 0 if is_day else 60
        elif g == Graha.MERCURY:
            base = 60
        else:
            base = 0
        mid_day = 12.0
        mid_night = 0.0
        if base > 0:
            center = mid_day if is_day else mid_night
            dist = abs(hour_of_day - center)
            if dist > 6:
                dist = 12 - dist
            base = max(0, 60 - dist * 10)
        return ShadbalaComponent("nathonnatha", base, 60)

    def _paksha_bala(self, g: Graha) -> ShadbalaComponent:
        if Graha.SUN not in self.cd.planets or Graha.MOON not in self.cd.planets:
            return ShadbalaComponent("paksha", 0, 60)
        sun_lon = self.cd.planets[Graha.SUN].longitude
        moon_lon = self.cd.planets[Graha.MOON].longitude
        diff = (moon_lon - sun_lon) % 360
        is_shukla = diff < 180
        if is_shukla:
            benefics = (Graha.JUPITER, Graha.VENUS, Graha.MERCURY, Graha.MOON)
            virupa = 60 if g in benefics else 0
        else:
            malefics = (Graha.SUN, Graha.MARS, Graha.SATURN)
            virupa = 60 if g in malefics else 0
        return ShadbalaComponent("paksha", virupa, 60)

    def _tribhaga_bala(self, g: Graha) -> ShadbalaComponent:
        jd = self.cd.julian_day
        frac = (jd + 0.5) % 1.0
        hour_of_day = frac * 24
        period = min(int(hour_of_day / 6), 3)
        is_day = 6 <= hour_of_day < 18
        day_lords = [Graha.MOON, Graha.SUN, Graha.SATURN, Graha.JUPITER]
        night_lords = [Graha.SUN, Graha.MOON, Graha.JUPITER, Graha.SATURN]
        lord = (day_lords if is_day else night_lords)[period]
        return ShadbalaComponent("tribhaga", 60 if lord == g else 0, 60)

    def _abda_bala(self, g: Graha) -> ShadbalaComponent:
        year = self.cd.birth_date.year
        lord_seq = [
            Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
            Graha.JUPITER, Graha.VENUS, Graha.SATURN,
        ]
        lord = lord_seq[year % 7]
        return ShadbalaComponent("abda", 15 if lord == g else 0, 15)

    def _masa_bala(self, g: Graha) -> ShadbalaComponent:
        month = self.cd.birth_date.month
        lord_seq = [
            Graha.SATURN, Graha.JUPITER, Graha.MARS, Graha.SUN,
            Graha.VENUS, Graha.MERCURY, Graha.MOON,
            Graha.SATURN, Graha.JUPITER, Graha.MARS, Graha.SUN, Graha.VENUS,
        ]
        lord = lord_seq[month - 1]
        return ShadbalaComponent("masa", 30 if lord == g else 0, 30)

    def _vara_bala(self, g: Graha) -> ShadbalaComponent:
        weekday_seq = [
            Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
            Graha.JUPITER, Graha.VENUS, Graha.SATURN,
        ]
        weekday = self.cd.birth_date.weekday()
        lord = weekday_seq[weekday % 7]
        return ShadbalaComponent("vara", 45 if lord == g else 0, 45)

    def _hora_bala(self, g: Graha) -> ShadbalaComponent:
        jd = self.cd.julian_day
        frac = (jd + 0.5) % 1.0
        hour_of_day = frac * 24
        sunrise = 6.0
        sunset = 18.0
        is_day = sunrise <= hour_of_day < sunset
        day_lords = [
            Graha.SUN, Graha.VENUS, Graha.MERCURY, Graha.MOON,
            Graha.SATURN, Graha.JUPITER, Graha.MARS,
        ]
        night_lords = [
            Graha.MOON, Graha.SATURN, Graha.JUPITER, Graha.MARS,
            Graha.SUN, Graha.VENUS, Graha.MERCURY,
        ]
        hours_passed = hour_of_day - (sunrise if is_day else sunset)
        if hours_passed < 0:
            hours_passed += 12
        hora_idx = int(hours_passed) % 7
        lords = day_lords if is_day else night_lords
        lord = lords[hora_idx]
        return ShadbalaComponent("hora", 60 if lord == g else 0, 60)

    def _ayana_bala(self, g: Graha) -> ShadbalaComponent:
        if g not in self.cd.planets or Graha.SUN not in self.cd.planets:
            return ShadbalaComponent("ayana", 0, 60)
        p = self.cd.planets[g]
        sun = self.cd.planets[Graha.SUN]
        planet_lon = math.radians(p.longitude)
        obliquity = math.radians(23.44)
        declination = math.asin(math.sin(planet_lon) * math.sin(obliquity))
        decl_deg = abs(math.degrees(declination))
        max_decl = 23.44
        if g in (Graha.MOON, Graha.SATURN):
            virupa = (decl_deg / max_decl) * 60
        else:
            virupa = ((max_decl - decl_deg) / max_decl) * 60
        sun_north = sun.longitude < 180
        planet_north = p.longitude < 180
        if sun_north != planet_north:
            virupa = max(0, virupa)
        else:
            virupa = virupa
        return ShadbalaComponent("ayana", min(virupa, 60), 60)

    def _chesta_bala(self, g: Graha) -> Dict[str, ShadbalaComponent]:
        if g not in self.cd.planets:
            return {}
        p = self.cd.planets[g]
        if g == Graha.SUN or g == Graha.MOON:
            return self._chesta_sun_moon(g)
        retro = p.is_retrograde
        speed = abs(p.speed)
        mean = _MEAN_SPEEDS.get(g, 1.0)
        if retro:
            ratio = speed / mean
            virupa = min(ratio * 30 + 30, 60)
        else:
            sun_lon = self.cd.planets[Graha.SUN].longitude if Graha.SUN in self.cd.planets else 0
            elongation = min(abs(p.longitude - sun_lon) % 360, 360 - abs(p.longitude - sun_lon) % 360)
            if elongation <= 180:
                ratio = elongation / 180.0
                virupa = ratio * 30
            else:
                virupa = 0
        return {"chesta": ShadbalaComponent("chesta", min(virupa, 60), 60)}

    def _chesta_sun_moon(self, g: Graha) -> Dict[str, ShadbalaComponent]:
        virupa = self._naisargika_bala(g).virupa * 0.5
        return {"chesta": ShadbalaComponent("chesta", virupa, 60)}

    def _naisargika_bala(self, g: Graha) -> ShadbalaComponent:
        val = _NAISARGIKA_BALA.get(g, 0)
        return ShadbalaComponent("naisargika", val, val)

    def _drik_bala(self, g: Graha) -> ShadbalaComponent:
        if g not in self.cd.planets:
            return ShadbalaComponent("drik", 0, 60)
        total = 0.0
        g_lon = self.cd.planets[g].longitude
        for other, op in self.cd.planets.items():
            if other == g or other.is_node:
                continue
            sep = angle_diff(g_lon, op.longitude)
            if 60 <= sep <= 120 or 240 <= sep <= 300:
                if other.is_benefic:
                    total += 15
                elif other.is_malefic:
                    total -= 15
        return ShadbalaComponent("drik", max(0, total), 60)
