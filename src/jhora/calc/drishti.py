"""Graha Drishti — the classical aspect (drishti) API.

Parasara's scheme: every planet aspects the 7th house from itself in full;
Mars additionally aspects the 4th and 8th, Jupiter the 5th and 9th, Saturn
the 3rd and 10th. In the Jaimini/SJC reading followed here, Rahu and Ketu
aspect the 5th, 7th and 9th (the nodes' aspects are given the trine quality
of Jupiter).

The module answers the two questions a reading asks: what a planet aspects
("give"), and which planets aspect a point ("receive"). Sign-based aspects
are counted from the planet's sign, the mainstream whole-sign convention.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

#: Houses (1-based, from the planet's own position) it aspects in full.
_BASE_ASPECTS: Tuple[int, ...] = (7,)

#: Extra aspect houses by planet. Nodes take Jupiter's trines plus the 7th.
_SPECIAL_ASPECTS: Dict[Graha, Tuple[int, ...]] = {
    Graha.MARS: (4, 8),
    Graha.JUPITER: (5, 9),
    Graha.SATURN: (3, 10),
    Graha.RAHU: (5, 9),
    Graha.KETU: (5, 9),
}

#: The seven planets plus the nodes, in the order readings list them.
ALL_GRAHAS: Tuple[Graha, ...] = (
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
    Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU,
)


def aspect_houses(graha: Graha) -> Tuple[int, ...]:
    """The houses a planet aspects in full, counted from itself.

    Always includes the 7th; adds the planet's special aspects.
    """
    return tuple(sorted(set(_BASE_ASPECTS + _SPECIAL_ASPECTS.get(graha, ()))))


@dataclass(frozen=True)
class Aspect:
    """One planet aspecting one target sign."""

    graha: Graha
    house: int
    target_sign: Rasi

    @property
    def target_sign_index(self) -> int:
        return int(self.target_sign)


def aspects_from(graha: Graha, from_sign: int) -> List[Aspect]:
    """The signs a planet aspects, given the sign it occupies (0 = Aries)."""
    return [
        Aspect(graha, house, Rasi((from_sign + house - 1) % 12))
        for house in aspect_houses(graha)
    ]


def drishti(cd) -> Dict[Graha, List[Aspect]]:
    """Give view: what each planet in a chart aspects."""
    out: Dict[Graha, List[Aspect]] = {}
    for g in ALL_GRAHAS:
        if g not in cd.planets:
            continue
        from_sign = int(cd.planets[g].longitude // 30) % 12
        out[g] = aspects_from(g, from_sign)
    return out


def receives(cd) -> Dict[Graha, List[Graha]]:
    """Receive view: which planets aspect each planet in a chart.

    Consistent with :func:`drishti` — A appears here for B exactly when A
    lists B's sign among its aspects.
    """
    give = drishti(cd)
    recv: Dict[Graha, List[Graha]] = {g: [] for g in give}
    for giver, aspects in give.items():
        for aspect in aspects:
            for target in give:
                if target == giver:
                    continue
                target_sign = int(cd.planets[target].longitude // 30) % 12
                if aspect.target_sign_index == target_sign:
                    recv[target].append(giver)
    return recv


def aspects_point(cd, longitude: float) -> List[Graha]:
    """Which planets aspect a zodiac longitude (their sign)."""
    target_sign = int(longitude // 30) % 12
    return [
        g for g, aspects in drishti(cd).items()
        if any(a.target_sign_index == target_sign for a in aspects)
    ]
