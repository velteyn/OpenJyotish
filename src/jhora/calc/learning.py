"""Ishta Phala, Kashta Phala, Vaiseshikamsas, and Learning Aids.

Ishta/Kashta Phala: measures how beneficial a planet is for the native.
Vaiseshikamsas: dignity ranks (Parijata, Uttama, Gopura, etc.) from Vimsopaka.
Learning aids: argala, marana karaka sthana, planetary relationships.
"""

from dataclasses import dataclass
from typing import Dict, List

from jhora.charts.chart import ChartData
from jhora.calc.shadbala import ShadbalaComputer
from jhora.calc.vimsopaka import VimsopakaComputer, VimsopakaScheme
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


# ── Marana Karaka Sthana — houses where planets are "dead" (weak) ─────────────
_MARANA_KARAKA: Dict[Graha, int] = {
    Graha.SUN: 12,      # Sun dies in 12th
    Graha.MOON: 8,      # Moon dies in 8th
    Graha.MARS: 7,      # Mars dies in 7th
    Graha.MERCURY: 7,   # Mercury dies in 7th
    Graha.JUPITER: 3,   # Jupiter dies in 3rd
    Graha.VENUS: 6,     # Venus dies in 6th
    Graha.SATURN: 1,    # Saturn dies in 1st
    Graha.RAHU: 9,      # Rahu dies in 9th
    Graha.KETU: 9,      # Ketu dies in 9th
}


# ── Vaiseshikamsa thresholds (Vimsopaka score → rank) ────────────────────────
_VAISESHIKAMSA_RANKS = [
    (0, "None"),
    (5, "Parijata"),
    (8, "Uttama"),
    (10, "Gopura"),
    (12, "Simhasana"),
    (15, "Paravata"),
    (18, "Devaloka"),
    (20, "Brahmaloka"),
]


@dataclass
class LearningReport:
    marana_karaka: list
    vaiseshikamsas: list
    relationships: list


def _house_from_lagna(lon: float, lagna: float) -> int:
    return (int((lon - lagna) / 30) % 12) + 1


def marana_karaka_sthana(cd: ChartData) -> List[dict]:
    """Find planets in their marana karaka sthana (death-inflicting house)."""
    results = []
    for g, death_house in _MARANA_KARAKA.items():
        if g not in cd.planets:
            continue
        h = _house_from_lagna(cd.planet(g).longitude, cd.ascendant)
        if h == death_house:
            r = Rasi.from_longitude(cd.planet(g).longitude)
            results.append({
                "graha": g.full_name,
                "house": h,
                "sign": r.short_name,
                "longitude": cd.planet(g).longitude,
            })
    return results


def vaiseshikamsas(cd: ChartData) -> List[dict]:
    """Compute Vaiseshikamsa rank for each planet from Shadvarga Vimsopaka."""
    vc = VimsopakaComputer(cd)
    results = []
    for r in vc.compute_all(VimsopakaScheme.SHADVARGA):
        rank = "None"
        for threshold, name in _VAISESHIKAMSA_RANKS:
            if r.total >= threshold:
                rank = name
        results.append({
            "graha": r.graha.full_name,
            "score": r.total,
            "rank": rank,
        })
    return sorted(results, key=lambda x: x["score"], reverse=True)


def ishta_kashta_phala(cd: ChartData) -> List[dict]:
    """Ishta/Kashta Phala — beneficence vs maleficence of each planet.

    Based on the planet's Shadbala and its natural benefic/malefic nature.
    Ishta = how much the planet WANTS to help.
    Kashta = how much difficulty it causes.
    """
    sb = ShadbalaComputer(cd)
    results = []
    benefics = {Graha.MOON, Graha.MERCURY, Graha.JUPITER, Graha.VENUS}
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
        r = sb.compute_one(g)
        is_natural_benefic = g in benefics
        # Ishta: higher for strong benefics, low for strong malefics
        if is_natural_benefic:
            ishta = r.total_virupa / 500.0 * 60.0
            kashta = 60.0 - ishta
        else:
            kashta = r.total_virupa / 500.0 * 60.0
            ishta = 60.0 - kashta
        results.append({
            "graha": g.full_name,
            "ishta": min(60, max(0, ishta)),
            "kashta": min(60, max(0, kashta)),
            "benefic": is_natural_benefic,
        })
    return sorted(results, key=lambda x: x["ishta"], reverse=True)


def planetary_relationships(cd: ChartData) -> List[dict]:
    """Show temporary and permanent relationships between planets."""
    results = []
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
        if g not in cd.planets:
            continue
        p = cd.planet(g)
        p_rasi = int(p.longitude / 30)
        friends = []
        enemies = []
        for other in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                      Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
            if other == g or other not in cd.planets:
                continue
            op = cd.planet(other)
            o_rasi = int(op.longitude / 30)
            # Temporary: planets in 2,3,4,10,11,12 from a planet are friends
            diff = (o_rasi - p_rasi) % 12
            if diff in [1, 2, 3, 10, 11]:
                friends.append(other.short_name)
            else:
                enemies.append(other.short_name)
        results.append({
            "graha": g.full_name,
            "sign": Rasi(p_rasi).short_name,
            "temp_friends": friends,
            "temp_enemies": enemies,
        })
    return results
