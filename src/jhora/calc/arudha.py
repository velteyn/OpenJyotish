from typing import Dict, List, Optional
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.calc.dignities import MOOLATRIKONA

"""Arudha padas (risen images) for the 12 bhavas and the 9 grahas.

Classical naming follows "Vedic Astrology: An Integrated Approach", ch. 9
(section "Specific names of arudha padas"): A1 Arudha/Pada lagna, A2 Dhana
(Vitta) pada, A3 Bhratri (Vikrama) pada, A4 Matri (Vahana/Sukha) pada,
A5 Mantra (Putra/Buddhi) pada, A6 Roga (Satru) pada, A7 Dara pada,
A8 Mrityu (Kashta/Randhra) pada, A9 Bhagya (Pitri/Dharma/Guru) pada,
A10 Karma (Swarga/Rajya) pada, A11 Labha pada, A12 Upapada (Gauna/Vyaya/
Moksha) pada.

Arudhas are defined for every divisional chart (ch. 9.5): the sign in the
varga of interest is used, so ``varga_arudhas()`` recomputes them on any
varga. Graha arudhas (arudhas of the nine planets) show how the native
perceives matters; bhava arudhas show how the world perceives him.
"""

#: Primary classical name per bhava arudha (A1..A12).
BHAVA_PADA_NAMES: Dict[int, str] = {
    1: "Arudha Lagna", 2: "Dhana pada", 3: "Bhratri pada",
    4: "Matri pada", 5: "Mantra pada", 6: "Roga pada",
    7: "Dara pada", 8: "Mrityu pada", 9: "Bhagya pada",
    10: "Karma pada", 11: "Labha pada", 12: "Upapada",
}

#: Full synonym sets as listed in the classical table.
BHAVA_PADA_ALIASES: Dict[int, List[str]] = {
    1: ["Arudha lagna", "Pada lagna", "Arudha", "Pada"],
    2: ["Dhanarudha", "Vittarudha", "Dhana pada", "Vitta pada"],
    3: ["Bhatrarudha", "Bhratri pada", "Vikramarudha", "Vikrama pada"],
    4: ["Matri pada", "Vahana pada", "Sukha pada", "Matrarudha",
        "Vahanarudha", "Sukharudha"],
    5: ["Mantra pada", "Mantrarudha", "Putrarudha", "Putra pada",
        "Buddhi pada"],
    6: ["Roga pada", "Satru pada", "Rogarudha", "Satrarudha"],
    7: ["Dara pada", "Dararudha"],
    8: ["Mrityu pada", "Kashta pada", "Kashtarudha", "Randhrarudha"],
    9: ["Bhagya pada", "Bhagyarudha", "Pitri pada", "Pitrarudha",
        "Dharma pada", "Guru pada"],
    10: ["Karma pada", "Karmarudha", "Swarga pada", "Swargarudha",
         "Rajya pada"],
    11: ["Labha pada", "Labharudha"],
    12: ["Upapada lagna", "Upapada", "Gaunapada", "Vyayarudha",
         "Moksha pada"],
}

_SANSKRIT = {
    Graha.SUN: "Surya", Graha.MOON: "Chandra", Graha.MARS: "Mangala",
    Graha.MERCURY: "Budha", Graha.JUPITER: "Guru", Graha.VENUS: "Shukra",
    Graha.SATURN: "Shani", Graha.RAHU: "Rahu", Graha.KETU: "Ketu",
}


def bhava_pada_name(house_num: int) -> str:
    """Primary classical pada name for a bhava arudha (A1..A12)."""
    return BHAVA_PADA_NAMES[house_num]


def graha_pada_name(graha: Graha) -> str:
    """Classical nama-pada for a graha arudha (e.g. Budha pada)."""
    return f"{_SANSKRIT.get(graha, graha.full_name)} pada"


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


def upapada(lagna_lon: float, planets: Dict) -> Rasi:
    """Upapada (A12, the 12th bhava arudha) as a first-class output.

    Classical use: marriage/spouse and the nature of relationships.
    """
    return bhava_arudha(12, lagna_lon, planets)


def darapada(lagna_lon: float, planets: Dict) -> Rasi:
    """Darapada (A7, the 7th bhava arudha) as a first-class output."""
    return bhava_arudha(7, lagna_lon, planets)


def varga_arudhas(cd, varga_level, variant=None):
    """Bhava and graha arudhas computed on a divisional chart (ch. 9.5).

    Returns ``(bhava_arudhas, graha_arudhas)`` for the requested varga,
    using the varga longitudes of the planets and of the lagna. The rasi
    chart is the default when the level is D-1.
    """
    from jhora.charts.varga import VargaChartComputer
    from jhora.types.varga import VargaLevel, VargaVariant

    level = varga_level if isinstance(varga_level, VargaLevel) \
        else VargaLevel[varga_level]
    var = variant or VargaVariant.DEFAULT
    if level == VargaLevel.D_1:
        planets = {g: {"longitude": p.longitude}
                   for g, p in cd.planets.items()}
        lagna = cd.ascendant
    else:
        chart = VargaChartComputer().compute(cd, level, var)
        planets = {g: {"longitude": vp.longitude}
                   for g, vp in chart.positions.items()}
        lagna = chart.lagna_position.longitude
    return (all_bhava_arudhas(lagna, planets),
            all_graha_arudhas(planets))
