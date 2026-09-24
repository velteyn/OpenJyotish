"""Graha Maitri — planetary friendships (BPHS, Naisargika/Tatkalika/Panchadha).

- **Naisargika** (natural): fixed per-planet tables, asymmetric
  (Mars befriends the Moon; the Moon stays neutral to Mars).
- **Tatkalika** (temporal): planets in 2nd, 3rd, 4th, 10th, 11th or 12th
  from each other are temporal friends, otherwise temporal enemies
  (mutual by construction).
- **Panchadha** (compound, fivefold): natural friend + temporal friend =
  Adhimitra (4); natural neutral + temporal friend = Mitra (3);
  mixed or neutral pairs = Sama (2); natural neutral + temporal enemy =
  Shatru (1); enemy + enemy = Adhishatru (0).

Seven grahas only (nodes have no settled natural friendships).
"""

from typing import Dict, List, Tuple

from jhora.types.graha import Graha

_FRIEND = "friend"
_NEUTRAL = "neutral"
_ENEMY = "enemy"

#: Natural friendships per planet (BPHS; asymmetric).
_NATURAL: Dict[Graha, Dict[str, set]] = {
    Graha.SUN: {_FRIEND: {Graha.MOON, Graha.MARS, Graha.JUPITER},
                _NEUTRAL: {Graha.MERCURY},
                _ENEMY: {Graha.VENUS, Graha.SATURN}},
    Graha.MOON: {_FRIEND: {Graha.SUN, Graha.MERCURY},
                 _NEUTRAL: {Graha.MARS, Graha.JUPITER, Graha.VENUS,
                            Graha.SATURN},
                 _ENEMY: set()},
    Graha.MARS: {_FRIEND: {Graha.SUN, Graha.MOON, Graha.JUPITER},
                 _NEUTRAL: {Graha.VENUS, Graha.SATURN},
                 _ENEMY: {Graha.MERCURY}},
    Graha.MERCURY: {_FRIEND: {Graha.SUN, Graha.VENUS},
                    _NEUTRAL: {Graha.MARS, Graha.JUPITER, Graha.SATURN},
                    _ENEMY: {Graha.MOON}},
    Graha.JUPITER: {_FRIEND: {Graha.SUN, Graha.MOON, Graha.MARS},
                    _NEUTRAL: {Graha.SATURN},
                    _ENEMY: {Graha.MERCURY, Graha.VENUS}},
    Graha.VENUS: {_FRIEND: {Graha.MERCURY, Graha.SATURN},
                  _NEUTRAL: {Graha.MARS, Graha.JUPITER},
                  _ENEMY: {Graha.SUN, Graha.MOON}},
    Graha.SATURN: {_FRIEND: {Graha.MERCURY, Graha.VENUS},
                   _NEUTRAL: {Graha.JUPITER},
                   _ENEMY: {Graha.SUN, Graha.MOON, Graha.MARS}},
}

#: Temporal-friend sign offsets (0-based) from the planet's own sign.
_TEMPORAL_FRIEND = {1, 2, 3, 9, 10, 11}

_SCORES = {(4, "Adhimitra"), (3, "Mitra"), (2, "Sama"),
           (1, "Shatru"), (0, "Adhishatru")}

GRAHAS = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
          Graha.JUPITER, Graha.VENUS, Graha.SATURN]


def naisargika(g1: Graha, g2: Graha) -> str:
    """Natural relationship of g1 toward g2 (asymmetric)."""
    for rel in (_FRIEND, _NEUTRAL, _ENEMY):
        if g2 in _NATURAL[g1][rel]:
            return rel
    raise ValueError(f"No natural relation {g1} -> {g2}")


def tatkalika(rasi1: int, rasi2: int) -> str:
    """Temporal relationship by sign distance (mutual)."""
    return _FRIEND if (rasi2 - rasi1) % 12 in _TEMPORAL_FRIEND else _ENEMY


def panchadha(g1: Graha, g2: Graha, rasi1: int, rasi2: int
              ) -> Tuple[str, int]:
    """Compound (name, score 0-4) relationship of g1 toward g2."""
    nat = naisargika(g1, g2)
    tmp = tatkalika(rasi1, rasi2)
    if nat == _FRIEND and tmp == _FRIEND:
        score = 4
    elif nat == _NEUTRAL and tmp == _FRIEND:
        score = 3
    elif nat == _NEUTRAL and tmp == _ENEMY:
        score = 1
    elif nat == _ENEMY and tmp == _ENEMY:
        score = 0
    else:
        score = 2
    return dict(_SCORES)[score], score


def maitri_table(rasis: Dict[Graha, int]) -> Dict[Tuple[Graha, Graha], str]:
    """Panchadha names for every ordered pair (diagonal: 'Self')."""
    out = {}
    for a in GRAHAS:
        for b in GRAHAS:
            out[(a, b)] = "Self" if a == b else panchadha(
                a, b, rasis[a], rasis[b])[0]
    return out


def score_table(rasis: Dict[Graha, int]) -> List[List[int]]:
    """Panchadha scores as a 7x7 matrix (GRAHAS order; diagonal 4)."""
    return [[4 if a == b else panchadha(a, b, rasis[a], rasis[b])[1]
             for b in GRAHAS] for a in GRAHAS]
