"""Rule-based Vedic remedy engine.

Deterministic, source-cited remedies derived from the chart — Ishta/Palana
devata (Jaimini), gemstone, planetary mantra, charity/fasting, and dosha
remedies. No LLM in the loop: every recommendation is a pure function of the
chart (and, for Sade Sati, the date), and names its classical authority.

Mainstream sources (see ``openspec/changes/add-remedy-engine/design.md``):
B.V. Raman (*Gems and Astrology*, *Hindu Predictive Astrology*), Sanjay Rath
(*Jaimini Maharishi's Upadesa Sutras*), *Brihat Parashara Hora Sastra* and
Phaladeepika, *Prasna Marga*.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from jhora.charts.chart import ChartData
from jhora.calc.karaka import get_atma_karaka
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

_NAVAMSA = 30.0 / 9.0

#: Planet -> (gemstone, metal, finger, day).
GEMSTONE: Dict[Graha, tuple] = {
    Graha.SUN: ("Ruby (Manikya)", "copper or gold", "ring finger", "Sunday"),
    Graha.MOON: ("Pearl (Moti)", "silver", "little finger", "Monday"),
    Graha.MARS: ("Red Coral (Moonga)", "copper", "ring finger", "Tuesday"),
    Graha.MERCURY: ("Emerald (Panna)", "gold or bronze", "little finger",
                    "Wednesday"),
    Graha.JUPITER: ("Yellow Sapphire (Pukhraj)", "gold", "index finger",
                    "Thursday"),
    Graha.VENUS: ("Diamond (Hira)", "silver or platinum", "middle finger",
                  "Friday"),
    Graha.SATURN: ("Blue Sapphire (Neelam)", "iron or silver", "middle finger",
                   "Saturday"),
    Graha.RAHU: ("Hessonite (Gomed)", "ashtadhatu", "middle finger",
                 "Saturday"),
    Graha.KETU: ("Cat's Eye (Lehsunia)", "ashtadhatu", "ring finger",
                 "Tuesday"),
}

#: Planet -> (beeja mantra, classical japa count).
MANTRA: Dict[Graha, tuple] = {
    Graha.SUN: ("Om Hraam Hreem Hraum Sah Suryaya Namah", 7000),
    Graha.MOON: ("Om Shraam Shreem Shraum Sah Chandraya Namah", 11000),
    Graha.MARS: ("Om Kraam Kreem Kraum Sah Bhaumaya Namah", 10000),
    Graha.MERCURY: ("Om Braam Breem Braum Sah Budhaya Namah", 9000),
    Graha.JUPITER: ("Om Graam Greem Graum Sah Gurave Namah", 19000),
    Graha.VENUS: ("Om Draam Dreem Draum Sah Shukraya Namah", 16000),
    Graha.SATURN: ("Om Praam Preem Praum Sah Shanaischaraya Namah", 23000),
    Graha.RAHU: ("Om Bhraam Bhreem Bhraum Sah Rahave Namah", 18000),
    Graha.KETU: ("Om Sraam Sreem Sraum Sah Ketave Namah", 17000),
}

#: Planet -> (charity items, direction, fast day).
CHARITY: Dict[Graha, tuple] = {
    Graha.SUN: ("wheat, jaggery, copper, ruby", "East", "Sunday"),
    Graha.MOON: ("rice, milk, silver, white cloth", "North-West", "Monday"),
    Graha.MARS: ("red lentils, copper, red coral", "South", "Tuesday"),
    Graha.MERCURY: ("green gram, green cloth, emerald", "North", "Wednesday"),
    Graha.JUPITER: ("chana dal, turmeric, yellow cloth, ghee", "North-East",
                    "Thursday"),
    Graha.VENUS: ("white rice, silver, curd, diamond", "South-East", "Friday"),
    Graha.SATURN: ("black sesame, iron, black cloth, oil", "West", "Saturday"),
    Graha.RAHU: ("black gram, blue/black cloth, gomed", "South-West",
                 "Saturday"),
    Graha.KETU: ("multi-coloured cloth, blankets, sesame", "South-West",
                 "Tuesday"),
}

#: Planet -> Ishta/Palana deity (Jaimini; Rath).
DEITY: Dict[Graha, str] = {
    Graha.SUN: "Sri Rama / Surya Narayana",
    Graha.MOON: "Parvati / Gauri",
    Graha.MARS: "Subrahmanya (Skanda)",
    Graha.MERCURY: "Vishnu",
    Graha.JUPITER: "Dattatreya / Vamana",
    Graha.VENUS: "Lakshmi",
    Graha.SATURN: "Brahma / Kurma",
    Graha.RAHU: "Varaha / Durga",
    Graha.KETU: "Ganesha",
}

_LORD_NAME_TO_GRAHA = {
    "Sun": Graha.SUN, "Moon": Graha.MOON, "Mars": Graha.MARS,
    "Mercury": Graha.MERCURY, "Jupiter": Graha.JUPITER,
    "Venus": Graha.VENUS, "Saturn": Graha.SATURN,
}

#: Functional benefics per lagna (B.V. Raman, Hindu Predictive Astrology —
#: mainstream Parashari). Includes the lagna lord where it rules good houses.
_BENEFICS: Dict[int, set] = {
    0: {Graha.JUPITER, Graha.SUN, Graha.MOON, Graha.MARS},
    1: {Graha.SATURN, Graha.SUN, Graha.MERCURY},
    2: {Graha.VENUS, Graha.MERCURY, Graha.SATURN},
    3: {Graha.JUPITER, Graha.MOON, Graha.MARS},
    4: {Graha.MARS, Graha.JUPITER, Graha.SUN},
    5: {Graha.VENUS, Graha.MERCURY},
    6: {Graha.SATURN, Graha.VENUS, Graha.MERCURY},
    7: {Graha.JUPITER, Graha.MOON, Graha.SUN, Graha.MARS},
    8: {Graha.JUPITER, Graha.SUN, Graha.MARS},
    9: {Graha.VENUS, Graha.MERCURY, Graha.SATURN},
    10: {Graha.VENUS, Graha.MERCURY, Graha.SATURN},
    11: {Graha.JUPITER, Graha.MOON, Graha.MARS},
}

#: Yogakaraka (single-planet) per lagna.
_YOGAKARAKA: Dict[int, Optional[Graha]] = {
    1: Graha.SATURN, 6: Graha.SATURN,      # Taurus, Libra
    3: Graha.MARS, 4: Graha.MARS,          # Cancer, Leo
    9: Graha.VENUS, 10: Graha.VENUS,       # Capricorn, Aquarius
}

_SRC_GEM = "B.V. Raman, Gems and Astrology; SJC gemstone rule"
_SRC_MANTRA = "Brihat Parashara Hora Sastra (remedial chapters)"
_SRC_DEITY = "Jaimini Sutras (Sanjay Rath, Jaimini Maharishi's Upadesa Sutras)"
_SRC_CHARITY = "Brihat Parashara Hora Sastra; Phaladeepika"
_SRC_DOSHA = "Prasna Marga; Saravali; standard Parashari practice"


@dataclass
class RemedyItem:
    category: str
    title: str
    detail: str
    source: str
    planet: Optional[Graha] = None


@dataclass
class RemedyReport:
    ishta_devata: RemedyItem
    palana_devata: RemedyItem
    items: List[RemedyItem] = field(default_factory=list)


def _navamsa_sign(lon: float) -> int:
    return int(lon / _NAVAMSA) % 12


def _lord_graha(rasi_index: int) -> Graha:
    return _LORD_NAME_TO_GRAHA[Rasi(rasi_index).lord]


def _rasi_of(cd: ChartData, g: Graha) -> int:
    return int(cd.planets[g].longitude // 30) % 12


def _house_from_lagna(cd: ChartData, g: Graha) -> int:
    return (_rasi_of(cd, g) - int(cd.ascendant // 30) % 12) % 12 + 1


def _karakamsa(cd: ChartData) -> int:
    planets = {g: {"longitude": p.longitude} for g, p in cd.planets.items()}
    return _navamsa_sign(get_atma_karaka(planets).longitude)


def _devata_for_house(cd: ChartData, house_offset: int) -> RemedyItem:
    """Ishta (12th from Karakamsa) / Palana (9th) deity."""
    kk = _karakamsa(cd)
    target = (kk + house_offset) % 12
    occupants = [g for g in cd.planets if _rasi_of(cd, g) == target]
    if occupants:
        planet = occupants[0]
        basis = f"{planet.full_name} occupies {Rasi(target).full_name} " \
                f"from the Karakamsa"
    else:
        planet = _lord_graha(target)
        basis = f"lord {planet.full_name} of {Rasi(target).full_name} " \
                f"from the Karakamsa"
    return RemedyItem(
        category="deity",
        planet=planet,
        title=f"{DEITY[planet]}",
        detail=basis,
        source=_SRC_DEITY,
    )


def _shadbala(cd: ChartData) -> Dict[Graha, float]:
    from jhora.calc.shadbala import ShadbalaComputer
    return {g: r.total_rupa for g, r in ShadbalaComputer(cd).compute().items()}


def _gemstone_items(cd: ChartData, bal: Dict[Graha, float]) -> List[RemedyItem]:
    lagna = int(cd.ascendant // 30) % 12
    benefics = _BENEFICS[lagna]
    lord = _lord_graha(lagna)
    yk = _YOGAKARAKA.get(lagna)
    malefic = [g for g in GEMSTONE if g not in benefics]

    items: List[RemedyItem] = []
    candidates = [g for g in (lord, yk) if g is not None]
    safe = [g for g in candidates if g in benefics]
    if safe:
        pick = max(safe, key=lambda g: bal.get(g, 0.0))
        gem, metal, finger, day = GEMSTONE[pick]
        items.append(RemedyItem(
            category="gemstone",
            planet=pick,
            title=f"Wear {gem}",
            detail=(f"{pick.full_name} is a functional benefic for the lagna "
                    f"({Rasi(lagna).full_name}); set in {metal}, worn on the "
                    f"{finger}, first on a {day}. Shadbala {bal.get(pick, 0):.1f}R."),
            source=_SRC_GEM,
        ))
    else:
        items.append(RemedyItem(
            category="gemstone",
            title="No primary gemstone",
            detail=("The lagna lord / yogakaraka is a functional malefic for "
                    "this lagna; no gemstone is advised."),
            source=_SRC_GEM,
        ))

    avoid = sorted(set(malefic) | {Graha.RAHU, Graha.KETU})
    items.append(RemedyItem(
        category="avoid",
        title="Avoid these gemstones",
        detail=", ".join(GEMSTONE[g][0] for g in avoid)
        + " (functional malefics and the nodes).",
        source=_SRC_GEM,
    ))
    return items


def _mantra_target(bal: Dict[Graha, float], benefics: set) -> Graha:
    lowest = min(bal, key=lambda g: bal[g])
    benefic_below = [g for g in bal
                     if g in benefics and bal[g] <= bal[lowest] * 1.10]
    return benefic_below[0] if benefic_below else lowest


def _mantra_items(target: Graha) -> List[RemedyItem]:
    mantra, japa = MANTRA[target]
    return [RemedyItem(
        category="mantra",
        planet=target,
        title=f"Japa of {target.full_name} mantra",
        detail=f"{mantra} — {japa:,} repetitions (or 108 daily).",
        source=_SRC_MANTRA,
    )]


def _charity_items(target: Graha, md_lord: Optional[Graha]) -> List[RemedyItem]:
    items: List[RemedyItem] = []
    seen = set()
    for g in (target, md_lord):
        if g is None or g in seen:
            continue
        seen.add(g)
        stuff, direction, day = CHARITY[g]
        items.append(RemedyItem(
            category="charity",
            planet=g,
            title=f"Charity & fast for {g.full_name}",
            detail=f"Give {stuff} on {day}, facing {direction}; observe a "
                   f"{day} fast.",
            source=_SRC_CHARITY,
        ))
    return items


def _kuja(cd: ChartData) -> Optional[RemedyItem]:
    house = _house_from_lagna(cd, Graha.MARS)
    if house in (1, 2, 4, 7, 8, 12):
        return RemedyItem(
            category="dosha", planet=Graha.MARS, title="Kuja (Mangal) dosha",
            detail=f"Mars in house {house} from the lagna. Worship "
                   "Subrahmanya / Hanuman; japa the Mars beeja; red coral only "
                   "if Mars is a functional benefic.",
            source=_SRC_DOSHA,
        )
    return None


def _kaala_sarpa(cd: ChartData) -> Optional[RemedyItem]:
    rahu = _rasi_of(cd, Graha.RAHU)
    ketu = _rasi_of(cd, Graha.KETU)
    seven = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
             Graha.JUPITER, Graha.VENUS, Graha.SATURN]
    # Arc from Rahu forward to Ketu (exclusive) must hold all seven.
    def _in_arc(rasi: int) -> bool:
        return (rasi - rahu) % 12 <= (ketu - rahu) % 12
    if all(_in_arc(_rasi_of(cd, g)) for g in seven):
        return RemedyItem(
            category="dosha", title="Kaala Sarpa dosha",
            detail="All seven planets lie within the Rahu-Ketu arc. Propitiate "
                   "Rahu and Ketu; Naga/Shiva worship; Kaala Sarpa nivarana.",
            source=_SRC_DOSHA,
        )
    return None


def _sade_sati(cd: ChartData, when: Optional[datetime]) -> Optional[RemedyItem]:
    if when is None:
        return None
    from jhora.calc.gochara import compute_transits, sade_sati_status
    from jhora.ephemeris.swe import SweEngine
    se = SweEngine()
    jd = se.julday(when.year, when.month, when.day,
                   when.hour + when.minute / 60.0)
    tr = compute_transits(cd, jd)
    sat = next(e for e in tr.entries if e.graha == Graha.SATURN)
    natal_moon = cd.planets[Graha.MOON].rasi.value
    phase = sade_sati_status(natal_moon, sat.transit_rasi)
    if phase:
        return RemedyItem(
            category="dosha", planet=Graha.SATURN, title="Sade Sati",
            detail=f"Transit Saturn is in the {phase}. Saturn seva, Shani "
                   "mantra, Saturday charity (sesame/oil).",
            source=_SRC_DOSHA,
        )
    return None


def _grahana(cd: ChartData) -> Optional[RemedyItem]:
    for lum in (Graha.SUN, Graha.MOON):
        ll = cd.planets[lum].longitude
        for node in (Graha.RAHU, Graha.KETU):
            d = abs((cd.planets[node].longitude - ll + 180) % 360 - 180)
            if d <= 12:
                return RemedyItem(
                    category="dosha", planet=lum, title="Grahana dosha",
                    detail=f"{lum.full_name} is within {d:.0f}° of "
                           f"{node.full_name}. Propitiate the luminary and the "
                           "node (japa, charity).",
                    source=_SRC_DOSHA,
                )
    return None


def _pitru(cd: ChartData) -> Optional[RemedyItem]:
    ninth_lord = _lord_graha((int(cd.ascendant // 30) % 12 + 8) % 12)
    afflicters = {Graha.RAHU, Graha.KETU, Graha.SATURN, Graha.MARS}
    house9 = (int(cd.ascendant // 30) % 12 + 8) % 12
    hit = [g for g in afflicters
           if _rasi_of(cd, g) == house9 or _rasi_of(cd, g) == _rasi_of(cd, ninth_lord)]
    if hit or _rasi_of(cd, Graha.SUN) == house9:
        names = ", ".join(g.full_name for g in hit) or "Sun"
        return RemedyItem(
            category="dosha", title="Pitru dosha",
            detail=f"9th house/lord afflicted by {names}. Pitru tarpan, "
                   "Shraddha, Vishnu/Sun worship.",
            source=_SRC_DOSHA,
        )
    return None


def compute_remedies(cd: ChartData,
                     when: Optional[datetime] = None) -> RemedyReport:
    """Deterministic, source-cited remedies for a chart."""
    lagna = int(cd.ascendant // 30) % 12
    bal = _shadbala(cd)
    benefics = _BENEFICS[lagna]

    ishta = _devata_for_house(cd, 12)
    palana = _devata_for_house(cd, 9)
    target = _mantra_target(bal, benefics)

    items: List[RemedyItem] = _gemstone_items(cd, bal)
    items += _mantra_items(target)
    items += _charity_items(target, None)
    for dosha in (_kuja(cd), _kaala_sarpa(cd), _sade_sati(cd, when),
                  _grahana(cd), _pitru(cd)):
        if dosha is not None:
            items.append(dosha)
    return RemedyReport(ishta_devata=ishta, palana_devata=palana, items=items)
