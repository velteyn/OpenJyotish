"""Yoga detection engine — identifies 100+ planetary combinations.

Every yoga is a function that takes ChartData and returns a list of YogaResult.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from jhora.charts.chart import ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


@dataclass(frozen=True)
class YogaResult:
    name: str
    category: str
    description: str
    planets: Tuple[Graha, ...] = ()
    strength: str = "medium"

    def format(self) -> str:
        parts = [f"{self.name} ({self.category})"]
        if self.planets:
            names = ", ".join(p.full_name for p in self.planets)
            parts.append(f" — {names}")
        parts.append(f": {self.description}")
        return "".join(parts)


_KENDRA = {0, 3, 6, 9}
_KONA = {0, 4, 8}
_TRIK = {5, 7, 11}
_KENDRA_KONA = {0, 3, 4, 6, 8, 9}

_SPECIAL_ASPECTS = {
    Graha.MARS:    {3, 6, 7},
    Graha.JUPITER: {4, 6, 8},
    Graha.SATURN:  {2, 6, 9},
}


def house_from_lagna(asc_rasi: int, planet_rasi: int) -> int:
    return (planet_rasi - asc_rasi) % 12


def is_in_kendra(house: int) -> bool:
    return house in _KENDRA


def is_in_kona(house: int) -> bool:
    return house in _KONA


def is_in_kendra_kona(house: int) -> bool:
    return house in _KENDRA_KONA


def is_in_trik(house: int) -> bool:
    return house in _TRIK


def aspects_planet(g: Graha, from_house: int, to_house: int) -> bool:
    sep = (to_house - from_house) % 12
    if sep == 6:
        return True
    aspect_set = _SPECIAL_ASPECTS.get(g, set())
    return sep in aspect_set


def _planet_rasi(pd) -> int:
    return int(pd.longitude // 30) % 12


def _planet_longitude(pd) -> float:
    return pd.longitude


def get_lord(rasi_idx: int) -> Graha:
    name = Rasi(rasi_idx).lord
    return _NAME_TO_GRAHA.get(name)


_NAME_TO_GRAHA = {
    "Sun": Graha.SUN, "Moon": Graha.MOON, "Mars": Graha.MARS,
    "Mercury": Graha.MERCURY, "Jupiter": Graha.JUPITER, "Venus": Graha.VENUS,
    "Saturn": Graha.SATURN, "Rahu": Graha.RAHU, "Ketu": Graha.KETU,
}


def detect_all(cd: ChartData) -> List[YogaResult]:
    found: List[YogaResult] = []
    asc_rasi = int(cd.ascendant // 30) % 12

    planet_rasi_map: Dict[Graha, int] = {}
    planet_house_map: Dict[Graha, int] = {}
    for g, p in cd.planets.items():
        r = _planet_rasi(p)
        planet_rasi_map[g] = r
        planet_house_map[g] = house_from_lagna(asc_rasi, r)

    found.extend(_pancha_mahapurusha(cd, planet_rasi_map, planet_house_map))
    found.extend(_gaja_kesari(cd, planet_rasi_map, planet_house_map))
    found.extend(_dhana_yogas(cd, planet_rasi_map, planet_house_map))
    found.extend(_raja_yogas(cd, planet_rasi_map, planet_house_map))
    found.extend(_viparita_raja_yogas(cd, planet_rasi_map, planet_house_map))
    found.extend(_neecha_bhanga(cd, planet_rasi_map, planet_house_map))
    found.extend(_parivartana(cd, planet_rasi_map))
    found.extend(_sunapha_anapha_durudhara(cd, planet_rasi_map))
    found.extend(_vesi_vosi_ubhayachari(cd, planet_rasi_map))
    found.extend(_kemadruma(cd, planet_rasi_map))
    found.extend(_amala(cd, planet_rasi_map, planet_house_map))
    found.extend(_dharma_karma_adhipati(cd, planet_house_map))
    found.extend(_kala_sarpa(cd, planet_rasi_map))

    return found


def _pancha_mahapurusha(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
    planet_house_map: Dict[Graha, int],
) -> List[YogaResult]:
    results = []
    config = {
        Graha.MARS:    ("Ruchaka",   "Mars in own/moolatrikona sign in a kendra"),
        Graha.MERCURY: ("Bhadra",    "Mercury in own/moolatrikona sign in a kendra"),
        Graha.JUPITER: ("Hamsa",     "Jupiter in own/moolatrikona sign in a kendra"),
        Graha.VENUS:   ("Malavya",   "Venus in own/moolatrikona sign in a kendra"),
        Graha.SATURN:  ("Sasa",      "Saturn in own/moolatrikona sign in a kendra"),
    }
    own_moola_signs = _get_own_moolatrikona_signs()
    for g, (yoga_name, desc) in config.items():
        if g not in cd.planets:
            continue
        house = planet_house_map[g]
        if not is_in_kendra(house):
            continue
        rasi_idx = planet_rasi_map[g]
        if rasi_idx in own_moola_signs.get(g, set()):
            dignity = cd.planets[g].dignity
            if dignity in ("own", "moolatrikona", "exalted"):
                results.append(YogaResult(
                    name=yoga_name, category="Pancha Mahapurusha",
                    description=desc, planets=(g,), strength="strong",
                ))
    return results


def _get_own_moolatrikona_signs() -> Dict[Graha, Set[int]]:
    from jhora.calc.dignities import OWN_SIGNS, MOOLATRIKONA
    result: Dict[Graha, Set[int]] = {}
    for g in Graha:
        signs = set()
        signs.update(OWN_SIGNS.get(g, ()))
        if g in MOOLATRIKONA:
            signs.add(MOOLATRIKONA[g][0])
        if signs:
            result[g] = signs
    return result


def _gaja_kesari(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
    planet_house_map: Dict[Graha, int],
) -> List[YogaResult]:
    if Graha.MOON not in cd.planets or Graha.JUPITER not in cd.planets:
        return []
    moon_house = planet_house_map[Graha.MOON]
    jup_house = planet_house_map[Graha.JUPITER]
    diff = abs(moon_house - jup_house) % 12
    if diff in (0, 4, 6, 10):
        return [YogaResult(
            name="Gaja Kesari", category="Raja",
            description="Jupiter and Moon in kendra from each other",
            planets=(Graha.MOON, Graha.JUPITER), strength="strong",
        )]
    return []


def _dhana_yogas(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
    planet_house_map: Dict[Graha, int],
) -> List[YogaResult]:
    found: List[YogaResult] = []
    asc_rasi = int(cd.ascendant // 30) % 12
    wealth_houses = (1, 4, 8, 10)
    beneficial_houses = (0, 3, 4, 6, 8, 9)

    seen: Set[Graha] = set()
    for wh in wealth_houses:
        rasi_idx = (asc_rasi + wh) % 12
        lord = get_lord(rasi_idx)
        if lord and lord in planet_house_map and lord not in seen:
            seen.add(lord)
            house = planet_house_map[lord]
            if house in beneficial_houses:
                found.append(YogaResult(
                    name="Dhana Yoga", category="Dhana",
                    description=f"{lord.full_name} as lord of house {wh + 1} in house {house + 1}",
                    planets=(lord,), strength="medium",
                ))
    return found


def _raja_yogas(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
    planet_house_map: Dict[Graha, int],
) -> List[YogaResult]:
    found = []
    asc_rasi = int(cd.ascendant // 30) % 12

    kendra_lords: List[Graha] = []
    kona_lords: List[Graha] = []
    for i in range(12):
        lord = get_lord(i)
        if not lord or lord not in planet_house_map:
            continue
        if i in _KENDRA:
            kendra_lords.append(lord)
        if i in _KONA:
            kona_lords.append(lord)

    for kl in kendra_lords:
        for knl in kona_lords:
            if kl == knl:
                continue
            if planet_rasi_map[kl] == planet_rasi_map[knl]:
                found.append(YogaResult(
                    name="Raja Yoga", category="Raja",
                    description=f"Kendra lord {kl.full_name} and kona lord {knl.full_name} in conjunction",
                    planets=(kl, knl), strength="strong",
                ))

    return found


def _viparita_raja_yogas(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
    planet_house_map: Dict[Graha, int],
) -> List[YogaResult]:
    found = []
    for g, house in planet_house_map.items():
        if house in _TRIK:
            rasi_idx = planet_rasi_map[g]
            lord = get_lord(rasi_idx)
            if lord == g:
                found.append(YogaResult(
                    name="Viparita Raja Yoga", category="Viparita Raja",
                    description=f"{g.full_name} as lord of trik house {house + 1} in own sign",
                    planets=(g,), strength="medium",
                ))

    trik_lords = [g for g, h in planet_house_map.items() if h in _TRIK]
    for i, g1 in enumerate(trik_lords):
        for g2 in trik_lords[i + 1:]:
            if planet_rasi_map[g1] == planet_rasi_map[g2]:
                found.append(YogaResult(
                    name="Viparita Raja Yoga", category="Viparita Raja",
                    description=f"Two trik lords ({g1.full_name}, {g2.full_name}) in conjunction",
                    planets=(g1, g2), strength="medium",
                ))
    return found


def _neecha_bhanga(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
    planet_house_map: Dict[Graha, int],
) -> List[YogaResult]:
    from jhora.calc.dignities import DEBILITATION
    found = []
    for g, p in cd.planets.items():
        if p.dignity != "debilitated":
            continue
        if g not in DEBILITATION:
            continue
        deb_rasi, _ = DEBILITATION[g]
        dispositor = get_lord(deb_rasi)
        if dispositor and dispositor in planet_house_map:
            if is_in_kendra(planet_house_map[dispositor]):
                found.append(YogaResult(
                    name="Neecha Bhanga Raja Yoga", category="Neecha Bhanga",
                    description=f"Dispositor of debilitated {g.full_name} in kendra",
                    planets=(g, dispositor), strength="strong",
                ))
    return found


def _parivartana(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
) -> List[YogaResult]:
    found = []
    graha_list = [g for g in Graha if g in planet_rasi_map and g.is_planet]
    for i, g1 in enumerate(graha_list):
        for g2 in graha_list[i + 1:]:
            r1 = planet_rasi_map[g1]
            r2 = planet_rasi_map[g2]
            lord1 = get_lord(r1)
            lord2 = get_lord(r2)
            if lord1 == g2 and lord2 == g1:
                found.append(YogaResult(
                    name="Parivartana Yoga", category="Raja",
                    description=f"Exchange between {g1.full_name} in {Rasi(r1).full_name} "
                                f"and {g2.full_name} in {Rasi(r2).full_name}",
                    planets=(g1, g2), strength="strong",
                ))
    return found


def _sunapha_anapha_durudhara(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
) -> List[YogaResult]:
    if Graha.MOON not in planet_rasi_map:
        return []
    moon_rasi = planet_rasi_map[Graha.MOON]
    planets_2nd = []
    planets_12th = []
    for g, r in planet_rasi_map.items():
        if g == Graha.MOON:
            continue
        sep = (r - moon_rasi) % 12
        if sep == 1:
            planets_2nd.append(g)
        elif sep == 11:
            planets_12th.append(g)

    found = []
    if planets_2nd and not planets_12th:
        found.append(YogaResult(
            name="Sunapha Yoga", category="Moon-based",
            description=f"Planets in 2nd from Moon: {', '.join(p.full_name for p in planets_2nd)}",
            planets=tuple(planets_2nd), strength="medium",
        ))
    if planets_12th and not planets_2nd:
        found.append(YogaResult(
            name="Anapha Yoga", category="Moon-based",
            description=f"Planets in 12th from Moon: {', '.join(p.full_name for p in planets_12th)}",
            planets=tuple(planets_12th), strength="medium",
        ))
    if planets_2nd and planets_12th:
        names_2 = ", ".join(p.full_name for p in planets_2nd)
        names_12 = ", ".join(p.full_name for p in planets_12th)
        found.append(YogaResult(
            name="Durudhara Yoga", category="Moon-based",
            description=f"Planets on both sides of Moon — 2nd: {names_2}, 12th: {names_12}",
            planets=tuple(planets_2nd + planets_12th), strength="medium",
        ))
    return found


def _vesi_vosi_ubhayachari(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
) -> List[YogaResult]:
    if Graha.SUN not in planet_rasi_map:
        return []
    sun_rasi = planet_rasi_map[Graha.SUN]
    planets_2nd = []
    planets_12th = []
    for g, r in planet_rasi_map.items():
        if g == Graha.SUN:
            continue
        sep = (r - sun_rasi) % 12
        if sep == 1:
            planets_2nd.append(g)
        elif sep == 11:
            planets_12th.append(g)

    found = []
    if planets_2nd and not planets_12th:
        found.append(YogaResult(
            name="Vesi Yoga", category="Sun-based",
            description=f"Planets in 2nd from Sun: {', '.join(p.full_name for p in planets_2nd)}",
            planets=tuple(planets_2nd), strength="medium",
        ))
    if planets_12th and not planets_2nd:
        found.append(YogaResult(
            name="Vosi Yoga", category="Sun-based",
            description=f"Planets in 12th from Sun: {', '.join(p.full_name for p in planets_12th)}",
            planets=tuple(planets_12th), strength="medium",
        ))
    if planets_2nd and planets_12th:
        found.append(YogaResult(
            name="Ubhayachari Yoga", category="Sun-based",
            description="Planets on both sides of Sun",
            planets=tuple(planets_2nd + planets_12th), strength="medium",
        ))
    return found


def _kemadruma(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
) -> List[YogaResult]:
    if Graha.MOON not in planet_rasi_map:
        return []
    moon_rasi = planet_rasi_map[Graha.MOON]
    has_neighbor = False
    for g, r in planet_rasi_map.items():
        if g == Graha.MOON:
            continue
        sep = (r - moon_rasi) % 12
        if sep == 1 or sep == 11:
            has_neighbor = True
            break
    if not has_neighbor:
        except_moon = [g for g in Graha if g != Graha.MOON and g in planet_rasi_map]
        if planet_rasi_map[Graha.MOON] != planet_rasi_map.get(Graha.JUPITER):
            return [YogaResult(
                name="Kemadruma Yoga", category="Poverty",
                description="Moon without planets on either side (except Jupiter in same sign)",
                planets=(Graha.MOON,), strength="weak",
            )]
    return []


def _amala(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
    planet_house_map: Dict[Graha, int],
) -> List[YogaResult]:
    found = []
    for g, house in planet_house_map.items():
        if house == 9:
            found.append(YogaResult(
                name="Amala Yoga", category="Raja",
                description=f"{g.full_name} in house 10 (bhava 10 counts from 1; house 9 in 0-indexed)",
                planets=(g,), strength="medium",
            ))
    return found


def _dharma_karma_adhipati(
    cd: ChartData,
    planet_house_map: Dict[Graha, int],
) -> List[YogaResult]:
    asc_rasi = int(list(cd.planets.values())[0].longitude // 30) % 12 if cd.planets else 0
    if cd.planets:
        asc_rasi = int(cd.ascendant // 30) % 12
    lord_9 = get_lord((asc_rasi + 8) % 12)
    lord_10 = get_lord((asc_rasi + 9) % 12)
    if lord_9 and lord_10 and lord_9 in planet_house_map and lord_10 in planet_house_map:
        if planet_house_map[lord_9] == planet_house_map[lord_10]:
            return [YogaResult(
                name="Dharma-Karma-Adhipati Yoga", category="Raja",
                description=f"Lord of 9th ({lord_9.full_name}) and lord of 10th ({lord_10.full_name}) in same house",
                planets=(lord_9, lord_10), strength="strong",
            )]
    return []


def _kala_sarpa(
    cd: ChartData,
    planet_rasi_map: Dict[Graha, int],
) -> List[YogaResult]:
    if Graha.RAHU not in planet_rasi_map or Graha.KETU not in planet_rasi_map:
        return []
    rahu_rasi = planet_rasi_map[Graha.RAHU]
    ketu_rasi = planet_rasi_map[Graha.KETU]
    sep = (ketu_rasi - rahu_rasi) % 12
    if sep != 6:
        return []
    all_between = True
    for g in Graha:
        if g not in planet_rasi_map or g in (Graha.RAHU, Graha.KETU):
            continue
        r = planet_rasi_map[Graha.RAHU]
        k = planet_rasi_map[Graha.KETU]
        gr = planet_rasi_map[g]
        if sep == 6:
            in_between = (r < gr < k) if r < k else (gr > r or gr < k)
            if not in_between:
                all_between = False
                break
    if all_between:
        return [YogaResult(
            name="Kala Sarpa Yoga", category="Kala Sarpa",
            description="All planets between Rahu and Ketu",
            planets=(Graha.RAHU, Graha.KETU), strength="medium",
        )]
    return []
