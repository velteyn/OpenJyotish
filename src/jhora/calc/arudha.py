from typing import Dict, List, Optional
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.calc.dignities import MOOLATRIKONA


_RASI_TO_LORD: Dict[int, List[Graha]] = {
    0: [Graha.MARS], 1: [Graha.VENUS], 2: [Graha.MERCURY],
    3: [Graha.MOON], 4: [Graha.SUN], 5: [Graha.MERCURY],
    6: [Graha.VENUS], 7: [Graha.MARS, Graha.KETU],
    8: [Graha.JUPITER], 9: [Graha.SATURN],
    10: [Graha.SATURN, Graha.RAHU], 11: [Graha.JUPITER],
}

_SINGLE_LORD = {k: v[0] for k, v in _RASI_TO_LORD.items() if len(v) == 1}


def _lord_of_rasi(rasi_index: int) -> Graha:
    if rasi_index in _SINGLE_LORD:
        return _SINGLE_LORD[rasi_index]
    if rasi_index == 7:
        return Graha.MARS
    if rasi_index == 10:
        return Graha.SATURN
    return _RASI_TO_LORD[rasi_index][0]


def _owned_sign(graha: Graha) -> int:
    if graha == Graha.RAHU:
        return 1
    if graha == Graha.KETU:
        return 7
    if graha in MOOLATRIKONA:
        return MOOLATRIKONA[graha][0]
    signs = graha.lordship_signs
    return signs[0] - 1 if signs else 0


def bhava_arudha(house_num: int, lagna_lon: float, planets: Dict) -> Rasi:
    lagna_rasi = int(lagna_lon // 30) % 12
    house_rasi = (lagna_rasi + house_num - 1) % 12

    lord = _lord_of_rasi(house_rasi)
    lord_lon = planets[lord]["longitude"]
    lord_rasi = int(lord_lon // 30) % 12

    diff = (lord_rasi - house_rasi) % 12
    result = (lord_rasi + diff) % 12

    seventh = (house_rasi + 6) % 12
    if result == house_rasi or result == seventh:
        result = (result + 9) % 12

    return Rasi(result)


def all_bhava_arudhas(lagna_lon: float, planets: Dict) -> Dict[int, Rasi]:
    return {n: bhava_arudha(n, lagna_lon, planets) for n in range(1, 13)}


def graha_arudha(graha: Graha, planets: Dict) -> Rasi:
    planet_lon = planets[graha]["longitude"]
    planet_rasi = int(planet_lon // 30) % 12
    owned = _owned_sign(graha)

    diff = (owned - planet_rasi) % 12
    result = (owned + diff) % 12

    seventh = (planet_rasi + 6) % 12
    if result == planet_rasi or result == seventh:
        result = (result + 9) % 12

    return Rasi(result)


def all_graha_arudhas(planets: Dict) -> Dict[Graha, Rasi]:
    return {g: graha_arudha(g, planets) for g in Graha if g in planets}
