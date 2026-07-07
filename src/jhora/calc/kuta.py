"""Kuta Porutham — Vedic marriage compatibility matching (10 Porutham).

References:
  - "Vedic Astrology: An Integrated Approach" by P.V.R. Narasimha Rao
  - "The 10 Poruthams" — standard South Indian matchmaking
  - Original JHora 8.0 binary (function 0x0044c170)
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra
from jhora.types.rasi import Rasi


# ── Result type ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Porutham:
    """Result of a single porutham check."""
    name: str
    score: float
    max_score: float
    description: str

    @property
    def fraction(self) -> str:
        return f"{self.score:.0f}/{self.max_score:.0f}"

    @property
    def is_good(self) -> bool:
        return self.score >= self.max_score / 2


@dataclass(frozen=True)
class KutaResult:
    """Full matchmaking result for a pair of horoscopes."""
    girl_nakshatra: Nakshatra
    boy_nakshatra: Nakshatra
    girl_rasi: Rasi
    boy_rasi: Rasi
    poruthams: List[Porutham]

    @property
    def total_score(self) -> float:
        return sum(p.score for p in self.poruthams)

    @property
    def max_score(self) -> float:
        return sum(p.max_score for p in self.poruthams)

    @property
    def percentage(self) -> float:
        if self.max_score == 0:
            return 0.0
        return self.total_score / self.max_score * 100


# ── Gana ─────────────────────────────────────────────────────────────────────

_GANA: Dict[Nakshatra, str] = {
    Nakshatra.ASVINI: "Deva",
    Nakshatra.BHARANI: "Manushya",
    Nakshatra.KRITTIKA: "Rakshasa",
    Nakshatra.ROHINI: "Manushya",
    Nakshatra.MRIGASHIRA: "Deva",
    Nakshatra.ARDRA: "Manushya",
    Nakshatra.PUNARVASU: "Deva",
    Nakshatra.PUSHYA: "Deva",
    Nakshatra.ASHLESHA: "Rakshasa",
    Nakshatra.MAGHA: "Rakshasa",
    Nakshatra.PURVA_PHALGUNI: "Manushya",
    Nakshatra.UTTARA_PHALGUNI: "Manushya",
    Nakshatra.HASTA: "Deva",
    Nakshatra.CHITRA: "Rakshasa",
    Nakshatra.SWATI: "Deva",
    Nakshatra.VISHAKHA: "Rakshasa",
    Nakshatra.ANURADHA: "Deva",
    Nakshatra.JYESHTHA: "Rakshasa",
    Nakshatra.MULA: "Rakshasa",
    Nakshatra.PURVA_SHADHA: "Manushya",
    Nakshatra.UTTARA_SHADHA: "Manushya",
    Nakshatra.SHRAVANA: "Deva",
    Nakshatra.DHANISHTA: "Rakshasa",
    Nakshatra.SHATABHISHA: "Rakshasa",
    Nakshatra.PURVA_BHADRAPADA: "Manushya",
    Nakshatra.UTTARA_BHADRAPADA: "Manushya",
    Nakshatra.REVATI: "Deva",
}


# ── Yoni ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class _YoniAnimal:
    animal: str
    is_male: bool


_YONI: Dict[Nakshatra, _YoniAnimal] = {
    Nakshatra.ASVINI:             _YoniAnimal("Horse", True),
    Nakshatra.BHARANI:            _YoniAnimal("Elephant", True),
    Nakshatra.KRITTIKA:           _YoniAnimal("Sheep", False),
    Nakshatra.ROHINI:             _YoniAnimal("Serpent", True),
    Nakshatra.MRIGASHIRA:         _YoniAnimal("Serpent", False),
    Nakshatra.ARDRA:              _YoniAnimal("Dog", True),
    Nakshatra.PUNARVASU:          _YoniAnimal("Cat", False),
    Nakshatra.PUSHYA:             _YoniAnimal("Sheep", True),
    Nakshatra.ASHLESHA:           _YoniAnimal("Cat", True),
    Nakshatra.MAGHA:              _YoniAnimal("Mouse", False),
    Nakshatra.PURVA_PHALGUNI:     _YoniAnimal("Mouse", True),
    Nakshatra.UTTARA_PHALGUNI:    _YoniAnimal("Cow", True),
    Nakshatra.HASTA:              _YoniAnimal("Buffalo", False),
    Nakshatra.CHITRA:             _YoniAnimal("Tiger", False),
    Nakshatra.SWATI:              _YoniAnimal("Buffalo", True),
    Nakshatra.VISHAKHA:           _YoniAnimal("Tiger", True),
    Nakshatra.ANURADHA:           _YoniAnimal("Deer", False),
    Nakshatra.JYESHTHA:           _YoniAnimal("Deer", True),
    Nakshatra.MULA:               _YoniAnimal("Dog", False),
    Nakshatra.PURVA_SHADHA:       _YoniAnimal("Monkey", True),
    Nakshatra.UTTARA_SHADHA:      _YoniAnimal("Mongoose", True),
    Nakshatra.SHRAVANA:           _YoniAnimal("Monkey", False),
    Nakshatra.DHANISHTA:          _YoniAnimal("Lion", True),
    Nakshatra.SHATABHISHA:        _YoniAnimal("Horse", False),
    Nakshatra.PURVA_BHADRAPADA:   _YoniAnimal("Lion", False),
    Nakshatra.UTTARA_BHADRAPADA:  _YoniAnimal("Cow", False),
    Nakshatra.REVATI:             _YoniAnimal("Elephant", False),
}

# Natural animal friendships for yoni compatibility
# (symmetric — only one direction listed)
_YONI_FRIENDS: Dict[str, List[str]] = {
    "Horse":     ["Elephant", "Buffalo"],
    "Elephant":  ["Horse", "Lion"],
    "Sheep":     ["Cow"],
    "Serpent":   ["Cat"],
    "Dog":       ["Tiger", "Monkey"],
    "Cat":       ["Serpent", "Mouse"],
    "Mouse":     ["Cat", "Mongoose"],
    "Buffalo":   ["Horse", "Tiger"],
    "Tiger":     ["Dog", "Buffalo", "Deer", "Cow"],
    "Deer":      ["Tiger", "Mongoose"],
    "Monkey":    ["Dog", "Mongoose"],
    "Mongoose":  ["Mouse", "Deer", "Monkey"],
    "Lion":      ["Elephant", "Cow"],
    "Cow":       ["Sheep", "Lion", "Tiger"],
}


# ── Nadi ─────────────────────────────────────────────────────────────────────

_NADI: Dict[Nakshatra, str] = {
    Nakshatra.ASVINI:            "Adya",
    Nakshatra.BHARANI:           "Madhya",
    Nakshatra.KRITTIKA:          "Antya",
    Nakshatra.ROHINI:            "Antya",
    Nakshatra.MRIGASHIRA:        "Madhya",
    Nakshatra.ARDRA:             "Adya",
    Nakshatra.PUNARVASU:         "Adya",
    Nakshatra.PUSHYA:            "Madhya",
    Nakshatra.ASHLESHA:          "Antya",
    Nakshatra.MAGHA:             "Antya",
    Nakshatra.PURVA_PHALGUNI:    "Madhya",
    Nakshatra.UTTARA_PHALGUNI:   "Adya",
    Nakshatra.HASTA:             "Adya",
    Nakshatra.CHITRA:            "Madhya",
    Nakshatra.SWATI:             "Antya",
    Nakshatra.VISHAKHA:          "Antya",
    Nakshatra.ANURADHA:          "Madhya",
    Nakshatra.JYESHTHA:          "Adya",
    Nakshatra.MULA:              "Adya",
    Nakshatra.PURVA_SHADHA:      "Madhya",
    Nakshatra.UTTARA_SHADHA:     "Antya",
    Nakshatra.SHRAVANA:          "Antya",
    Nakshatra.DHANISHTA:         "Madhya",
    Nakshatra.SHATABHISHA:       "Adya",
    Nakshatra.PURVA_BHADRAPADA:  "Adya",
    Nakshatra.UTTARA_BHADRAPADA: "Madhya",
    Nakshatra.REVATI:            "Antya",
}


# ── Rajju ────────────────────────────────────────────────────────────────────

_RAJJU: Dict[Nakshatra, int] = {
    Nakshatra.ASVINI:            1,
    Nakshatra.BHARANI:           2,
    Nakshatra.KRITTIKA:          3,
    Nakshatra.ROHINI:            4,
    Nakshatra.MRIGASHIRA:        5,
    # below: no rajju (Rajju-hina) — mapped to 0
    Nakshatra.ARDRA:              0,
    Nakshatra.PUNARVASU:          0,
    Nakshatra.PUSHYA:             0,
    Nakshatra.ASHLESHA:           0,
    Nakshatra.MAGHA:              1,
    Nakshatra.PURVA_PHALGUNI:     2,
    Nakshatra.UTTARA_PHALGUNI:    3,
    Nakshatra.HASTA:              4,
    Nakshatra.CHITRA:             5,
    Nakshatra.SWATI:              0,
    Nakshatra.VISHAKHA:           0,
    Nakshatra.ANURADHA:           0,
    Nakshatra.JYESHTHA:           0,
    # Second cycle of 3 per group
    Nakshatra.MULA:               1,
    Nakshatra.PURVA_SHADHA:       2,
    Nakshatra.UTTARA_SHADHA:      3,
    Nakshatra.SHRAVANA:           4,
    Nakshatra.DHANISHTA:          5,
    Nakshatra.SHATABHISHA:        0,
    Nakshatra.PURVA_BHADRAPADA:   0,
    Nakshatra.UTTARA_BHADRAPADA:  0,
    Nakshatra.REVATI:             0,
}

_RAJJU_NAMES = {1: "Moola", 2: "Agni", 3: "Dhanu", 4: "Sthira/Hridaya", 5: "Kantha"}


# ── Vedha pairs ──────────────────────────────────────────────────────────────

# Nakshatras opposite in the zodiac (13 nakshatras apart ≈ 180°)
_VEDHA_PAIRS: Dict[Nakshatra, Nakshatra] = {
    Nakshatra.ASVINI:          Nakshatra.JYESHTHA,
    Nakshatra.BHARANI:         Nakshatra.ANURADHA,
    Nakshatra.KRITTIKA:        Nakshatra.VISHAKHA,
    Nakshatra.ROHINI:          Nakshatra.SWATI,
    Nakshatra.MRIGASHIRA:      Nakshatra.CHITRA,
    Nakshatra.ARDRA:           Nakshatra.UTTARA_BHADRAPADA,
    Nakshatra.PUNARVASU:       Nakshatra.PURVA_BHADRAPADA,
    Nakshatra.PUSHYA:          Nakshatra.SHATABHISHA,
    Nakshatra.ASHLESHA:        Nakshatra.DHANISHTA,
    Nakshatra.MAGHA:           Nakshatra.SHRAVANA,
    Nakshatra.PURVA_PHALGUNI:  Nakshatra.UTTARA_SHADHA,
    Nakshatra.UTTARA_PHALGUNI: Nakshatra.PURVA_SHADHA,
    Nakshatra.HASTA:           Nakshatra.MULA,
}


# ── Vashya — sign control groups ──────────────────────────────────────────────

# Signs grouped by nature: same-group signs are naturally compatible
_VASHA_GROUPS: Dict[str, List[Rasi]] = {
    "chara":     [Rasi.ARIES, Rasi.CANCER, Rasi.LIBRA, Rasi.CAPRICORN],
    "sthira":    [Rasi.TAURUS, Rasi.LEO, Rasi.SCORPIO, Rasi.AQUARIUS],
    "dwiswabhava": [Rasi.GEMINI, Rasi.VIRGO, Rasi.SAGITTARIUS, Rasi.PISCES],
}

_RASI_VASHA_GROUP: Dict[Rasi, str] = {}
for _g, _rs in _VASHA_GROUPS.items():
    for _r in _rs:
        _RASI_VASHA_GROUP[_r] = _g


# ── Friendship helper ────────────────────────────────────────────────────────

def _is_friend(a: str, b: str) -> bool:
    """Check if two animals (yoni) are natural friends."""
    if a == b:
        return True
    return b in _YONI_FRIENDS.get(a, [])


def _rasi_lord_str(rasi: Rasi) -> str:
    """Planet name string for the lord of a rasi."""
    return rasi.lord  # returns string like "Mars", "Venus", etc.


def _graha_from_name(name: str) -> Graha:
    """Convert a planet name string to Graha enum."""
    mapping = {
        "Sun": Graha.SUN, "Moon": Graha.MOON, "Mars": Graha.MARS,
        "Mercury": Graha.MERCURY, "Jupiter": Graha.JUPITER,
        "Venus": Graha.VENUS, "Saturn": Graha.SATURN,
        "Rahu": Graha.RAHU, "Ketu": Graha.KETU,
    }
    return mapping.get(name, Graha.SATURN)


def _lord_friendship(lord1: str, lord2: str) -> str:
    """Check friendship between two rasi lords (string names)."""
    from jhora.calc.shadbala import _FRIEND_RELATIONS
    g1 = _graha_from_name(lord1)
    g2 = _graha_from_name(lord2)
    if g1 == g2:
        return "same"
    if g2 in _FRIEND_RELATIONS[g1]["friend"]:
        return "friend"
    if g2 in _FRIEND_RELATIONS[g1]["enemy"]:
        return "enemy"
    return "neutral"


# ── Individual porutham checks ────────────────────────────────────────────────

def _check_dina(girl_nak: Nakshatra, boy_nak: Nakshatra) -> Porutham:
    """Dina Porutham — nakshatra counting (health & longevity).

    Count from girl's nakshatra to boy's (forward, 1-indexed).
    If count mod 9 ∈ {2, 4, 6, 8, 0} → good.
    """
    count = (boy_nak.value - girl_nak.value) % 27 + 1
    r = count % 9
    good = r in (2, 4, 6, 8, 0)
    desc = f"Count {count}/9 rem {r} — {'good' if good else 'not good'}"
    return Porutham("Dina", 1.0 if good else 0.0, 1.0, desc)


def _check_gana(girl_nak: Nakshatra, boy_nak: Nakshatra) -> Porutham:
    """Gana Porutham — temperament.

    Same gana → good (1). Differing → partial (0).
    """
    gg = _GANA[girl_nak]
    bg = _GANA[boy_nak]
    if gg == bg:
        score = 1.0
        desc = f"Both {gg}"
    else:
        score = 0.0
        desc = f"Girl: {gg}, Boy: {bg}"
    return Porutham("Gana", score, 1.0, desc)


def _check_yoni(girl_nak: Nakshatra, boy_nak: Nakshatra) -> Porutham:
    """Yoni Porutham — sexual compatibility.

    Same animal, opposite sex → best (1).
    Same animal, same sex → partial (0.5).
    Friend animals → good (0.75).
    Enemy animals → bad (0).
    Neutral → partial (0.5).
    """
    gy = _YONI[girl_nak]
    by = _YONI[boy_nak]
    if gy.animal == by.animal:
        if gy.is_male != by.is_male:
            return Porutham("Yoni", 1.0, 1.0,
                            f"{gy.animal} opposite sex — best")
        else:
            return Porutham("Yoni", 0.5, 1.0,
                            f"{gy.animal} same sex — partial")
    if _is_friend(gy.animal, by.animal):
        return Porutham("Yoni", 0.75, 1.0,
                        f"{gy.animal} ↔ {by.animal} — friends")
    if _is_friend(by.animal, gy.animal):
        return Porutham("Yoni", 0.75, 1.0,
                        f"{gy.animal} ↔ {by.animal} — friends")
    return Porutham("Yoni", 0.0, 1.0,
                    f"{gy.animal} ↔ {by.animal} — enemies/neutral")


def _check_rasi(girl_rasi: Rasi, boy_rasi: Rasi) -> Porutham:
    """Rasi Porutham — moon sign compatibility.

    Count girl→boy signs (1-12). Good counts: 2, 4, 6, 8, 10, 12.
    Same sign (1) and odd counts → not good.
    """
    count = (boy_rasi.value - girl_rasi.value) % 12 + 1
    if count in (2, 4, 6, 8, 10, 12):
        score = 2.0
        desc = f"Count {count} — good"
    else:
        score = 0.0
        desc = f"Count {count} — not good"
    return Porutham("Rasi", score, 2.0, desc)


def _check_rasyadhipati(girl_rasi: Rasi, boy_rasi: Rasi) -> Porutham:
    """Rasyadhipati Porutham — sign lord friendship.

    Same lord or friendly lords → good.
    Enemy lords → not good.
    """
    gl = _rasi_lord_str(girl_rasi)
    bl = _rasi_lord_str(boy_rasi)
    rel = _lord_friendship(gl, bl)
    if rel in ("same", "friend"):
        score = 1.0
        desc = f"{gl} ↔ {bl}: {rel}"
    else:
        score = 0.0
        desc = f"{gl} ↔ {bl}: {rel}"
    return Porutham("Rasyadhipati", score, 1.0, desc)


def _check_nadi(girl_nak: Nakshatra, boy_nak: Nakshatra) -> Porutham:
    """Nadi Porutham — health/heredity.

    Same nadi → bad (0/8). Different nadi → good (8/8).
    """
    gn = _NADI[girl_nak]
    bn = _NADI[boy_nak]
    if gn != bn:
        return Porutham("Nadi", 8.0, 8.0, f"Girl: {gn}, Boy: {bn}")
    return Porutham("Nadi", 0.0, 8.0, f"Both {gn} — same nadi")


def _check_rajju(girl_nak: Nakshatra, boy_nak: Nakshatra) -> Porutham:
    """Rajju Porutham — longevity.

    Same rajju group → bad. Different or rajju-hina → good.
    """
    gr = _RAJJU.get(girl_nak, 0)
    br = _RAJJU.get(boy_nak, 0)
    if gr != 0 and gr == br:
        desc = f"Both {_RAJJU_NAMES[gr]} Rajju — not good"
        return Porutham("Rajju", 0.0, 1.0, desc)
    if gr == br == 0:
        return Porutham("Rajju", 1.0, 1.0, "Both Rajju-hina")
    if gr == 0:
        return Porutham("Rajju", 1.0, 1.0,
                        f"Girl Rajju-hina, Boy {_RAJJU_NAMES[br]}")
    if br == 0:
        return Porutham("Rajju", 1.0, 1.0,
                        f"Girl {_RAJJU_NAMES[gr]}, Boy Rajju-hina")
    return Porutham("Rajju", 1.0, 1.0,
                    f"Different — Girl {_RAJJU_NAMES[gr]}, Boy {_RAJJU_NAMES[br]}")


def _check_vedha(girl_nak: Nakshatra, boy_nak: Nakshatra) -> Porutham:
    """Vedha Porutham — obstruction.

    If one nakshatra is the vedha counterpart of the other → bad.
    """
    if boy_nak == _VEDHA_PAIRS.get(girl_nak) or girl_nak == _VEDHA_PAIRS.get(boy_nak):
        return Porutham("Vedha", 0.0, 1.0,
                        f"{girl_nak.name} ↔ {boy_nak.name} — vedha")
    return Porutham("Vedha", 1.0, 1.0, "No vedha")


def _check_vashya(girl_rasi: Rasi, boy_rasi: Rasi) -> Porutham:
    """Vashya Porutham — mutual control/attraction.

    Same nature group → good (2).
    Different groups → check if not in 6/8 opposition. If 6/8 → 0.
    """
    gg = _RASI_VASHA_GROUP[girl_rasi]
    bg = _RASI_VASHA_GROUP[boy_rasi]
    if gg == bg:
        return Porutham("Vashya", 2.0, 2.0, f"Both {gg}")
    # Check 6/8 opposition
    diff = (boy_rasi.value - girl_rasi.value) % 12
    if diff in (5, 7):
        return Porutham("Vashya", 0.0, 2.0,
                        f"6/8 opposition — not good")
    return Porutham("Vashya", 0.5, 2.0,
                    f"{gg} ↔ {bg} — partial")


def _check_mahendra(girl_nak: Nakshatra, boy_nak: Nakshatra) -> Porutham:
    """Mahendra Porutham — prosperity.

    Count from girl's nakshatra to boy's.
    Good counts: 4, 7, 9, 13, 22, 26 (or 27 counting total).
    """
    count = (boy_nak.value - girl_nak.value) % 27 + 1
    if count in (4, 7, 9, 13, 22, 27):
        return Porutham("Mahendra", 1.0, 1.0, f"Count {count} — good")
    return Porutham("Mahendra", 0.0, 1.0, f"Count {count} — not good")


# ── Main entry point ─────────────────────────────────────────────────────────

def compute_kuta(
    girl_moon_longitude: float,
    boy_moon_longitude: float,
) -> KutaResult:
    """Compute all 10 Kuta Poruthams between two horoscopes.

    Args:
        girl_moon_longitude: Moon's sidereal longitude for the girl (0-360).
        boy_moon_longitude: Moon's sidereal longitude for the boy (0-360).

    Returns:
        KutaResult with all 10 poruthams and totals.
    """
    girl_nak, _ = Nakshatra.from_longitude(girl_moon_longitude)
    boy_nak, _ = Nakshatra.from_longitude(boy_moon_longitude)
    girl_rasi = Rasi.from_longitude(girl_moon_longitude)
    boy_rasi = Rasi.from_longitude(boy_moon_longitude)

    poruthams = [
        _check_dina(girl_nak, boy_nak),
        _check_gana(girl_nak, boy_nak),
        _check_yoni(girl_nak, boy_nak),
        _check_rasi(girl_rasi, boy_rasi),
        _check_rasyadhipati(girl_rasi, boy_rasi),
        _check_nadi(girl_nak, boy_nak),
        _check_rajju(girl_nak, boy_nak),
        _check_vedha(girl_nak, boy_nak),
        _check_vashya(girl_rasi, boy_rasi),
        _check_mahendra(girl_nak, boy_nak),
    ]

    return KutaResult(
        girl_nakshatra=girl_nak,
        boy_nakshatra=boy_nak,
        girl_rasi=girl_rasi,
        boy_rasi=boy_rasi,
        poruthams=poruthams,
    )
