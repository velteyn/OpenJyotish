"""Naabhasa yogas — classified celestial combinations (PVR ch. 11.5, BPHS).

- **Asraya (3)**: all planets in movable (Rajju), fixed (Musala) or dual
  (Nala) signs. Seven grahas; nodes excluded (as for Sankhya/Akriti).
- **Dala (2)**: three quadrants held by benefics (Maalaa) or malefics
  (Sarpa). Nodes count here. A quadrant needs just one of the kind;
  mixed quadrants weaken but keep the yoga.
- **Akriti (20)**: shape patterns of all seven planets by house from
  lagna (Gadaa … Samudra).
- **Sankhya (7)**: fallback by distinct-sign count (Veenaa … Gola),
  reported only when no other Naabhasa yoga applies.

Natural benefics: Moon, Mercury, Jupiter, Venus; malefics: Sun, Mars,
Saturn, Rahu, Ketu.
"""

from typing import Dict, List, Optional, Set, Tuple

from jhora.charts.chart import ChartData
from jhora.calc.yogas import YogaResult
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

GRAHAS = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
          Graha.JUPITER, Graha.VENUS, Graha.SATURN]

BENEFICS = {Graha.MOON, Graha.MERCURY, Graha.JUPITER, Graha.VENUS}
MALEFICS = {Graha.SUN, Graha.MARS, Graha.SATURN, Graha.RAHU, Graha.KETU}


def _houses(lons: Dict[Graha, float], lagna_lon: float) -> Dict[Graha, int]:
    lagna = int(lagna_lon // 30) % 12
    return {g: (int(lon // 30) - lagna) % 12 + 1 for g, lon in lons.items()}


def asraya_yogas(signs: Set[int]) -> List[str]:
    """Asraya names when every sign shares one nature (else [])."""
    if not signs:
        return []
    natures = set()
    for s in signs:
        r = Rasi(s % 12)
        natures.add("movable" if r.is_movable else
                    ("fixed" if r.is_fixed else "dual"))
    if len(natures) > 1:
        return []
    return {"movable": ["Rajju Yoga"], "fixed": ["Musala Yoga"],
            "dual": ["Nala Yoga"]}[next(iter(natures))]


def dala_yogas(kendra_occupants: Dict[int, Set[Graha]]) -> List[str]:
    """Dala names when 3+ quadrants hold benefics (Maalaa) / malefics (Sarpa).

    ``kendra_occupants`` maps kendra house (1/4/7/10) to its planets.
    """
    out = []
    ben = sum(1 for h in (1, 4, 7, 10)
              if kendra_occupants.get(h, set()) & BENEFICS)
    mal = sum(1 for h in (1, 4, 7, 10)
              if kendra_occupants.get(h, set()) & MALEFICS)
    if ben >= 3:
        out.append("Maalaa Yoga")
    if mal >= 3:
        out.append("Sarpa Yoga")
    return out


def _all_in(houses: Set[int], allowed: Set[int]) -> bool:
    return bool(houses) and houses <= allowed


def akriti_yogas(houses: Set[int],
                 houses_by_kind: Dict[str, Set[int]]) -> List[str]:
    """Akriti names for the occupied-house shape (houses from lagna)."""
    out = []
    h = houses
    pairs = [{1, 4}, {4, 7}, {7, 10}, {10, 1}]
    if any(h == p for p in pairs):
        out.append("Gadaa Yoga")
    if h == {1, 7}:
        out.append("Sakata Yoga")
    if h == {1, 5, 9}:
        out.append("Sringaataka Yoga")
    if h == {4, 10}:
        out.append("Vihanga Yoga")
    if h in ({2, 6, 10}, {3, 7, 11}, {4, 8, 12}):
        out.append("Hala Yoga")
    ben_houses = houses_by_kind.get("benefic", set())
    mal_houses = houses_by_kind.get("malefic", set())
    if {1, 7} <= ben_houses and {4, 10} <= mal_houses:
        out.append("Vajra Yoga")
    if _all_in(h, {1, 4, 7, 10}):
        out.append("Kamala Yoga")
    if _all_in(h, {2, 3, 5, 6, 8, 9, 11, 12}):
        out.append("Vaapi Yoga")
    if _all_in(h, {1, 2, 3, 4}):
        out.append("Yoopa Yoga")
    if _all_in(h, {4, 5, 6, 7}):
        out.append("Sara Yoga")
    if _all_in(h, {7, 8, 9, 10}):
        out.append("Sakti Yoga")
    if _all_in(h, {10, 11, 12, 1}):
        out.append("Danda Yoga")
    for start, name in ((1, "Naukaa Yoga"), (4, "Koota Yoga"),
                        (7, "Chatra Yoga"), (10, "Chaapa Yoga")):
        span = {(start - 1 + k) % 12 + 1 for k in range(7)}
        if h and h <= span:
            out.append(name)
    for start in (2, 3, 5, 6, 8, 9, 11, 12):
        span = {(start - 1 + k) % 12 + 1 for k in range(7)}
        if h and h <= span:
            out.append("Ardha Chandra Yoga")
            break
    if h and all(x % 2 == 1 for x in h):
        out.append("Chakra Yoga")
    if h and all(x % 2 == 0 for x in h):
        out.append("Samudra Yoga")
    return out


def sankhya_yoga(n_signs: int) -> Optional[str]:
    """Sankhya name by distinct-sign count (fallback only)."""
    return {7: "Veenaa Yoga", 6: "Daama Yoga", 5: "Paasa Yoga",
            4: "Kedaara Yoga", 3: "Soola Yoga", 2: "Yuga Yoga",
            1: "Gola Yoga"}.get(n_signs)


_DESCRIPTIONS = {
    "Rajju Yoga": "all planets in movable signs; travel, foreign rise",
    "Musala Yoga": "all planets in fixed signs; honor, fame, firmness",
    "Nala Yoga": "all planets in dual signs; accumulation, skill",
    "Maalaa Yoga": "benefics in three quadrants; happiness, luxuries",
    "Sarpa Yoga": "malefics in three quadrants; misery, dependence",
    "Gadaa Yoga": "planets in two successive quadrants; wealth, learning",
    "Sakata Yoga": "planets in 1st and 7th only; disease, friendlessness",
    "Sringaataka Yoga": "planets in trines from lagna; royal favor",
    "Vihanga Yoga": "planets in 4th and 10th; wandering, quarrels",
    "Hala Yoga": "planets in mutual non-lagna trines; toil, poverty",
    "Vajra Yoga": "benefics in 1st/7th, malefics in 4th/10th; valour",
    "Yava Yoga": "malefics in 1st/7th, benefics in 4th/10th; dharma, wealth",
    "Kamala Yoga": "planets all in quadrants; kingship, fame",
    "Vaapi Yoga": "planets out of quadrants; amassed wealth",
    "Yoopa Yoga": "planets in 1st–4th; spiritual knowledge",
    "Sara Yoga": "planets in 4th–7th; cruelty, hunting",
    "Sakti Yoga": "planets in 7th–10th; sharp but struggling",
    "Danda Yoga": "planets in 10th–1st; loss, servitude",
    "Naukaa Yoga": "planets within 7 from lagna; water wealth",
    "Koota Yoga": "planets within 7 from 4th; forts, harshness",
    "Chatra Yoga": "planets within 7 from 7th; kindness, kings",
    "Chaapa Yoga": "planets within 7 from 10th; secrets, wandering",
    "Ardha Chandra Yoga": "planets within 7 from panaphara/apoklima; command",
    "Chakra Yoga": "planets in odd houses; emperorship",
    "Samudra Yoga": "planets in even houses; stable wealth",
    "Veenaa Yoga": "seven signs occupied; music, leadership",
    "Daama Yoga": "six signs occupied; riches, fame",
    "Paasa Yoga": "five signs occupied; capable but flawed",
    "Kedaara Yoga": "four signs occupied; agriculture, happiness",
    "Soola Yoga": "three signs occupied; sharp, valiant, poor",
    "Yuga Yoga": "two signs occupied; discarded, unhappy",
    "Gola Yoga": "one sign occupied; strong but sad",
}


def naabhasa_yogas(cd: ChartData) -> List[YogaResult]:
    """All applicable Naabhasa yogas (Sankhya only if nothing else)."""
    lons = {g: cd.planet(g).longitude for g in GRAHAS}
    houses = _houses(lons, cd.ascendant)
    hset = set(houses.values())
    out: List[YogaResult] = []

    def add(names: List[str], planets):
        for name in names:
            out.append(YogaResult(
                name=name, category="Naabhasa",
                description=_DESCRIPTIONS.get(name, name),
                planets=tuple(planets)))

    signs = {int(lon // 30) % 12 for lon in lons.values()}
    add(asraya_yogas(signs), GRAHAS)

    kendra_occ: Dict[int, Set[Graha]] = {}
    for g, h in houses.items():
        if h in (1, 4, 7, 10):
            kendra_occ.setdefault(h, set()).add(g)
    add(dala_yogas(kendra_occ), GRAHAS)

    ben_houses = {h for g, h in houses.items() if g in BENEFICS}
    mal_houses = {h for g, h in houses.items() if g in MALEFICS}
    kinds = {"benefic": ben_houses, "malefic": mal_houses}
    akriti = akriti_yogas(hset, kinds)
    # Yava needs malefics-in-{1,7} + benefics-in-{4,10}: handled inside
    # via explicit check (houses_by_kind lacks the split).
    if {1, 7} <= {h for g, h in houses.items() if g in MALEFICS} and \
            {4, 10} <= ben_houses:
        akriti.append("Yava Yoga")
    add(akriti, GRAHAS)

    if not out:
        name = sankhya_yoga(len(signs))
        if name is not None:
            add([name], GRAHAS)
    return out
