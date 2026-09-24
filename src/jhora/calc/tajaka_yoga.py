"""Tajaka yogas — Ithasala, Eesarpha, Nakta, Yamaya and friends.

Planetary combinations for annual (Tajaka) and horary charts, following
P.V.R. Rao ch. 29.2 (Tajaka Neelakanthi doctrine):

- **Ithasala**: aspect + mutual deeptamsa + approaching (faster behind),
  typed Vartamaana / Poorna / Bhavishya. Retrograde-aware by the velocity
  rule (approaching = the faster planet's advancement gap is closing),
  which reproduces every stated case including the retrograde adaptations.
- **Eesarpha**: aspect + deeptamsa + separating. Failures, disappointments.
- **Nakta / Yamaya**: unaspected pair (no yoga either way) fulfilled with
  the help of a faster (Nakta) or slower (Yamaya) mediator in ithasala
  with both.
- **Manahoo**: Saturn/Mars conjunct the faster planet within its orb —
  cancels the ithasala (conjunction only, per PVR's advice).
- **Kamboola**: Moon in ithasala with a pair member — empowers it.
- **Radda**: ithasala involving a debilitated or retrograde planet —
  negates it (combustion not modeled).
- **Ishkavala / Induvara**: all planets in kendra+panaphara (fortunate)
  or all in apoklima (difficult).
- **Khallasara**: lagna lord zodiacally between Moon and a planet, with
  ithasala to neither — destroys that planet's signification.

Gairi-Kamboola (needs hadda + station prediction) is not implemented.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from jhora.charts.chart import ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

#: Mean-motion order, slowest first (PVR ch. 29.2.3 note 83; nodes omitted —
#: node pairs never form yogas).
_SPEED_ORDER = [Graha.SATURN, Graha.JUPITER, Graha.MARS, Graha.SUN,
                Graha.VENUS, Graha.MERCURY, Graha.MOON]

#: Deeptamsa (orb of aspect) per planet (PVR ch. 28.2).
_DEEPTAMSA = {Graha.SUN: 15.0, Graha.MOON: 12.0, Graha.MARS: 8.0,
              Graha.MERCURY: 7.0, Graha.JUPITER: 9.0, Graha.VENUS: 7.0,
              Graha.SATURN: 9.0}

#: Sign-distance aspect sets (0-based): benefic trinal/sextile, malefic
#: square/conjunction/opposition, neutral semi-sextile.
_BENEFIC = {2, 4, 8, 10}
_MALEFIC = {0, 3, 6, 9}
_NEUTRAL = {1, 11}

GRAHAS = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
          Graha.JUPITER, Graha.VENUS, Graha.SATURN]


def aspect_kind(rasi1: int, rasi2: int) -> Optional[str]:
    """Tajaka aspect kind by sign distance, or None (6th/8th apart)."""
    d = (rasi2 - rasi1) % 12
    if d in _BENEFIC:
        return "benefic"
    if d in _MALEFIC:
        return "malefic"
    if d in _NEUTRAL:
        return "neutral"
    return None


def _faster(g1: Graha, g2: Graha) -> Graha:
    order = {_g: _i for _i, _g in enumerate(_SPEED_ORDER)}
    return g1 if order[g1] > order[g2] else g2


def deeptamsa_check(lon1: float, lon2: float, g1: Graha, g2: Graha
                    ) -> Tuple[bool, Optional[str]]:
    """Mutual deeptamsa containment and its type.

    Returns (in_orb, type) with type Vartamaana (both inside), Poorna
    (advancements within 1°) or Bhavishya (one side within 1° of an edge).
    """
    a1, a2 = lon1 % 30, lon2 % 30
    o1, o2 = _DEEPTAMSA[g1], _DEEPTAMSA[g2]
    in1 = (a2 >= a1 - o1) and (a2 <= a1 + o1)
    in2 = (a1 >= a2 - o2) and (a1 <= a2 + o2)
    if abs(a1 - a2) <= 1.0:
        return True, "Poorna"
    if in1 and in2:
        return True, "Vartamaana"
    edge1 = abs(a2 - (a1 - o1)) <= 1.0 or abs(a2 - (a1 + o1)) <= 1.0
    edge2 = abs(a1 - (a2 - o2)) <= 1.0 or abs(a1 - (a2 + o2)) <= 1.0
    if (in1 and edge2) or (in2 and edge1):
        return True, "Bhavishya"
    return False, None


def approaching(lon1: float, lon2: float, v1: float, v2: float,
                g1: Graha, g2: Graha) -> bool:
    """Whether the faster planet's advancement gap is closing.

    With actual speeds this reproduces every stated case: direct pair
    (faster behind), faster retrograde ahead (moving back toward),
    faster retrograde behind (moving away), slower retrograde (faster
    realization). Station prediction is not modeled.
    """
    f = _faster(g1, g2)
    vf, vs = (v1, v2) if f == g1 else (v2, v1)
    af, as_ = (lon1 % 30, lon2 % 30) if f == g1 else (lon2 % 30, lon1 % 30)
    gap = as_ - af
    if gap == 0:
        return True
    return (vf - vs) * gap > 0


@dataclass(frozen=True)
class YogaResult:
    kind: str  # Ithasala, Eesarpha
    g1: Graha
    g2: Graha
    itype: Optional[str] = None  # Vartamaana / Poorna / Bhavishya
    manahoo_by: Optional[Graha] = None
    radda: bool = False
    kamboola: bool = False


def ithasala(lon1: float, lon2: float, v1: float, v2: float,
             g1: Graha, g2: Graha) -> Optional[str]:
    """Ithasala type if the pair forms it, else None."""
    r1, r2 = int(lon1 // 30) % 12, int(lon2 // 30) % 12
    if aspect_kind(r1, r2) is None:
        return None
    ok, itype = deeptamsa_check(lon1, lon2, g1, g2)
    if not ok:
        return None
    if not approaching(lon1, lon2, v1, v2, g1, g2):
        return None
    return itype


def eesarpha(lon1: float, lon2: float, v1: float, v2: float,
             g1: Graha, g2: Graha) -> bool:
    """Eesarpha: aspect + deeptamsa + separating."""
    r1, r2 = int(lon1 // 30) % 12, int(lon2 // 30) % 12
    if aspect_kind(r1, r2) is None:
        return False
    ok, _ = deeptamsa_check(lon1, lon2, g1, g2)
    if not ok:
        return False
    return not approaching(lon1, lon2, v1, v2, g1, g2)


def _house_yogas(houses) -> Tuple[bool, bool]:
    """Ishkavala (nothing in apoklima) / Induvara (all in apoklima)."""
    houses = set(houses)
    if not houses:
        return False, False
    return (all(h not in (3, 6, 9, 12) for h in houses),
            all(h in (3, 6, 9, 12) for h in houses))


def _manahoo(lons: Dict[Graha, float], g1: Graha, g2: Graha
             ) -> Optional[Graha]:
    """Saturn/Mars conjunct the faster planet within its deeptamsa."""
    f = _faster(g1, g2)
    fr, fa = int(lons[f] // 30) % 12, lons[f] % 30
    for m in (Graha.SATURN, Graha.MARS):
        if m in (g1, g2):
            continue
        if int(lons[m] // 30) % 12 == fr and \
                abs(lons[m] % 30 - fa) <= _DEEPTAMSA[f]:
            return m
    return None


def _radda(dignities: Dict[Graha, str], retros: Dict[Graha, bool],
           g1: Graha, g2: Graha) -> bool:
    return any(dignities.get(g) == "debilitated" or retros.get(g, False)
               for g in (g1, g2))


@dataclass
class TajakaYogas:
    ithasalas: List[YogaResult] = field(default_factory=list)
    eesarphas: List[Tuple[Graha, Graha]] = field(default_factory=list)
    naktas: List[Tuple[Graha, Graha, Graha]] = field(default_factory=list)
    yamayas: List[Tuple[Graha, Graha, Graha]] = field(default_factory=list)
    ishkavala: bool = False
    induvara: bool = False
    khallasaras: List[Tuple[Graha, Graha]] = field(default_factory=list)


def tajaka_yogas(cd: ChartData) -> TajakaYogas:
    """All Tajaka yogas for a chart (annual or horary)."""
    lons = {g: cd.planet(g).longitude for g in GRAHAS}
    vels = {g: cd.planet(g).speed for g in GRAHAS}
    out = TajakaYogas()
    pairs = [(a, b) for i, a in enumerate(GRAHAS) for b in GRAHAS[i + 1:]]

    itha: Dict[Tuple[Graha, Graha], str] = {}
    for a, b in pairs:
        t = ithasala(lons[a], lons[b], vels[a], vels[b], a, b)
        if t is not None:
            itha[(a, b)] = t
    ees = {(a, b) for a, b in pairs
           if (a, b) not in itha and (b, a) not in itha
           and eesarpha(lons[a], lons[b], vels[a], vels[b], a, b)}

    dignities = {g: cd.planet(g).dignity for g in GRAHAS}
    retros = {g: cd.planet(g).is_retrograde for g in GRAHAS}
    moon_pairs = {frozenset(k) for k in itha if Graha.MOON in k}
    for (a, b), t in itha.items():
        third = Graha.MOON not in (a, b) and (
            frozenset((Graha.MOON, a)) in moon_pairs or
            frozenset((Graha.MOON, b)) in moon_pairs)
        out.ithasalas.append(YogaResult(
            kind="Ithasala", g1=a, g2=b, itype=t,
            manahoo_by=_manahoo(lons, a, b),
            radda=_radda(dignities, retros, a, b),
            kamboola=third,
        ))
    out.eesarphas = sorted(ees, key=lambda p: (p[0].value, p[1].value))

    # Nakta / Yamaya: pair without yoga either way + mediator in
    # ithasala with both (faster mediator → Nakta, slower → Yamaya).
    order = {_g: _i for _i, _g in enumerate(_SPEED_ORDER)}
    for a, b in pairs:
        if (a, b) in itha or (a, b) in ees:
            continue
        for m in GRAHAS:
            if m in (a, b):
                continue
            im = ithasala(lons[m], lons[a], vels[m], vels[a], m, a)
            jm = ithasala(lons[m], lons[b], vels[m], vels[b], m, b)
            if im is None or jm is None:
                continue
            if order[m] > order[a] and order[m] > order[b]:
                out.naktas.append((a, b, m))
            elif order[m] < order[a] and order[m] < order[b]:
                out.yamayas.append((a, b, m))

    # Ishkavala / Induvara from houses counted from lagna.
    lagna_rasi = int(cd.ascendant // 30) % 12
    houses = {(int(lons[g] // 30) - lagna_rasi) % 12 + 1 for g in GRAHAS}
    out.ishkavala, out.induvara = _house_yogas(houses)

    # Khallasara: lagna lord zodiacally between Moon and X, ithasala
    # with neither.
    lagna_rasi = int(cd.ascendant // 30) % 12
    try:
        lagna_lord = Graha[Rasi(lagna_rasi).lord.upper()]
    except Exception:
        lagna_lord = None
    if lagna_lord is not None:
        moon_r = int(lons[Graha.MOON] // 30) % 12
        ll_r = int(lons[lagna_lord] // 30) % 12
        for x in GRAHAS:
            if x in (lagna_lord, Graha.MOON):
                continue
            xr = int(lons[x] // 30) % 12
            dist = (xr - moon_r) % 12
            between = dist > 0 and (ll_r - moon_r) % 12 in range(1, dist)
            if between and \
                    ithasala(lons[lagna_lord], lons[Graha.MOON],
                             vels[lagna_lord], vels[Graha.MOON],
                             lagna_lord, Graha.MOON) is None and \
                    ithasala(lons[lagna_lord], lons[x],
                             vels[lagna_lord], vels[x],
                             lagna_lord, x) is None:
                out.khallasaras.append((lagna_lord, x))
    return out
