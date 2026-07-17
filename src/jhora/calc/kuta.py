"""Kuta Porutham — Vedic marriage compatibility matching.

Supports two scoring systems:
  1. 10 Porutham (19 points) — standard South Indian matchmaking
  2. Ashta Koota (36 points, 8 factors) — classical Vedic binary system

References:
  - "Vedic Astrology: An Integrated Approach" by P.V.R. Narasimha Rao
  - Original Vedic astrology binary (Ashta Koota: format string at 0x591a3c,
    score table lookup at function_4b3b10)
  - "The 10 Poruthams" — standard South Indian matchmaking
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple

from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra
from jhora.types.rasi import Rasi


# ── Scoring system enum ──────────────────────────────────────────────────────

class ScoringSystem(Enum):
    PORUTHAM = "porutham"      # 10 Porutham, 19 points
    ASHTA_KOOTA = "ashta_koota"  # Ashta Koota, 36 points


# ── Result types ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Porutham:
    """Result of a single porutham/ashta-koota factor check."""
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


_GUNANKA_LEVELS: List[Tuple[int, int, str]] = [
    (30, 36, "Excellent"),
    (24, 30, "Good"),
    (18, 24, "Fair"),
    (12, 18, "Average"),
    (0, 12, "Below average"),
]


def gunanka_level(score: float) -> str:
    """Categorize Ashta Koota Gunanka score into qualitative level.

    Matches the classical Vedic binary format string:
    'Gunanka score after matching ashta koota (group of eight factors)
     = %d (out of 36).'
    """
    for lo, hi, label in _GUNANKA_LEVELS:
        if lo <= score < hi:
            return label
    if score == 36:
        return "Excellent"
    return "Below average"


@dataclass(frozen=True)
class KutaResult:
    """Full matchmaking result for a pair of horoscopes."""
    girl_nakshatra: Nakshatra
    boy_nakshatra: Nakshatra
    girl_rasi: Rasi
    boy_rasi: Rasi
    poruthams: List[Porutham]
    system: ScoringSystem = ScoringSystem.PORUTHAM

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

    @property
    def system_name(self) -> str:
        if self.system == ScoringSystem.ASHTA_KOOTA:
            return "Ashta Koota"
        return "10 Porutham"

    @property
    def gunanka_level(self) -> str:
        """Only meaningful for Ashta Koota; returns level label."""
        return gunanka_level(self.total_score)


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


# ── Ashta Koota: Varna — rasi lord caste ──────────────────────────────────────

# Varna hierarchy (higher number = lower varna per traditional texts)
_VARNA: Dict[str, int] = {
    "Jupiter": 1,  # Brahmin (guru)
    "Venus": 1,    # Brahmin (teacher of asuras)
    "Sun": 2,      # Kshatriya (king)
    "Mars": 2,     # Kshatriya (commander)
    "Mercury": 3,  # Vaishya (trader)
    "Saturn": 3,   # Vaishya (worker)
    "Moon": 4,     # Shudra (common people)
}


# ── Ashta Koota: Graha Maitri — planetary friendship table (explicit) ────────

# Friendship relations for Graha Maitri (5 pts in Ashta Koota)
# Key: planet name, Value: (friends, neutrals, enemies)
_GRAHA_MAITRI: Dict[str, Tuple[List[str], List[str], List[str]]] = {
    "Sun":     (["Moon", "Mars", "Jupiter"],  ["Mercury"],               ["Venus", "Saturn"]),
    "Moon":    (["Sun", "Mercury"],            ["Jupiter", "Venus", "Saturn"], ["Mars"]),
    "Mars":    (["Sun", "Moon", "Jupiter"],    ["Venus", "Saturn"],      ["Mercury"]),
    "Mercury": (["Sun", "Venus", "Saturn"],    ["Mars", "Jupiter", "Moon"], []),
    "Jupiter": (["Sun", "Moon", "Mars"],       ["Saturn"],               ["Mercury", "Venus"]),
    "Venus":   (["Mercury", "Saturn"],         ["Mars", "Jupiter"],      ["Sun", "Moon"]),
    "Saturn":  (["Mercury", "Venus"],          ["Jupiter"],              ["Sun", "Moon", "Mars"]),
}


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


# ═══════════════════════════════════════════════════════════════════════════════
# Ashta Koota (8 factors, 36 points) — used by classical Vedic binary
# ═══════════════════════════════════════════════════════════════════════════════

def _ak_check_varna(girl_rasi: Rasi, boy_rasi: Rasi) -> Porutham:
    """Varna (1 pt) — caste/spiritual compatibility of rasi lords.

    Assigns varna hierarchy to rasi lords. Same varna → 1 pt.
    """
    gl = _rasi_lord_str(girl_rasi)
    bl = _rasi_lord_str(boy_rasi)
    gv = _VARNA.get(gl, 0)
    bv = _VARNA.get(bl, 0)
    if gv == bv:
        return Porutham("Varna", 1.0, 1.0, f"Both {gl} ({bv}) — same varna")
    return Porutham("Varna", 0.0, 1.0,
                    f"{gl} (varna {gv}) vs {bl} (varna {bv}) — different")


def _ak_check_vashya(girl_rasi: Rasi, boy_rasi: Rasi) -> Porutham:
    """Vashya (2 pts) — mutual control/attraction based on sign nature.

    Same nature group (chara/sthira/dwisvabhava) → 2 pts.
    6/8 opposition → 0 pts.
    Otherwise → 1 pt.
    """
    gg = _RASI_VASHA_GROUP[girl_rasi]
    bg = _RASI_VASHA_GROUP[boy_rasi]
    if gg == bg:
        return Porutham("Vashya", 2.0, 2.0, f"Both {gg} — compatible")
    diff = (boy_rasi.value - girl_rasi.value) % 12
    if diff in (5, 7):
        return Porutham("Vashya", 0.0, 2.0, "6/8 opposition — not good")
    return Porutham("Vashya", 1.0, 2.0, f"{gg} ↔ {bg} — partial")


def _ak_check_tara(girl_nak: Nakshatra, boy_nak: Nakshatra) -> Porutham:
    """Tara/Dina (3 pts) — birth star compatibility.

    Count from girl's nakshatra to boy's (forward, 1-indexed).
    Check mod 9:
      - 3, 6, 7, 0/9 → Uttama (3 pts)
      - 2, 4, 8     → Madhyama (2 pts)
      - 1, 5        → Adhama (0 pts)
    This matches the standard Ashta Koota Tara scoring.
    """
    count = (boy_nak.value - girl_nak.value) % 27 + 1
    r = count % 9
    if r in (3, 6, 7, 0):
        return Porutham("Tara/Dina", 3.0, 3.0,
                        f"Count {count}, rem {r} — Uttama")
    if r in (2, 4, 8):
        return Porutham("Tara/Dina", 2.0, 3.0,
                        f"Count {count}, rem {r} — Madhyama")
    return Porutham("Tara/Dina", 0.0, 3.0,
                    f"Count {count}, rem {r} — Adhama")


def _ak_check_yoni(girl_nak: Nakshatra, boy_nak: Nakshatra) -> Porutham:
    """Yoni (4 pts) — sexual compatibility via animal symbols.

    Same animal, opposite sex → 4 pts (best)
    Same animal, same sex → 3 pts
    Friend animals → 2 pts
    Neutral → 1 pt
    Enemy → 0 pts
    """
    gy = _YONI[girl_nak]
    by = _YONI[boy_nak]
    if gy.animal == by.animal:
        if gy.is_male != by.is_male:
            return Porutham("Yoni", 4.0, 4.0, f"{gy.animal} opposite sex — best")
        return Porutham("Yoni", 3.0, 4.0, f"{gy.animal} same sex — good")
    if _is_friend(gy.animal, by.animal) or _is_friend(by.animal, gy.animal):
        return Porutham("Yoni", 2.0, 4.0, f"{gy.animal} ↔ {by.animal} — friends")
    if _is_enemy(gy.animal, by.animal) or _is_enemy(by.animal, gy.animal):
        return Porutham("Yoni", 0.0, 4.0, f"{gy.animal} ↔ {by.animal} — enemies")
    return Porutham("Yoni", 1.0, 4.0, f"{gy.animal} ↔ {by.animal} — neutral")


_YONI_ENEMIES: Dict[str, List[str]] = {
    "Serpent": ["Mongoose"],
    "Mongoose": ["Serpent"],
    "Cat": ["Mouse", "Dog"],
    "Mouse": ["Cat"],
    "Dog": ["Cat"],
    "Tiger": ["Deer"],
    "Deer": ["Tiger"],
}


def _is_enemy(a: str, b: str) -> bool:
    """Check if two animals (yoni) are natural enemies.

    Explicit enemy pairs are defined in _YONI_ENEMIES.
    Animals that are not friends and not enemies are neutral.
    """
    if a == b:
        return False
    return b in _YONI_ENEMIES.get(a, [])


def _ak_check_graha_maitri(girl_rasi: Rasi, boy_rasi: Rasi) -> Porutham:
    """Graha Maitri (5 pts) — rasi lord friendship.

    Same lord → 5 pts
    Friend lords → 3 pts
    Neutral lords → 1 pt
    Enemy lords → 0 pts
    """
    gl = _rasi_lord_str(girl_rasi)
    bl = _rasi_lord_str(boy_rasi)
    if gl == bl:
        return Porutham("Graha Maitri", 5.0, 5.0, f"Both {gl} — same lord")
    friends, neutrals, enemies = _GRAHA_MAITRI.get(gl, ([], [], []))
    if bl in friends:
        return Porutham("Graha Maitri", 3.0, 5.0, f"{gl} ↔ {bl} — friends")
    if bl in enemies:
        return Porutham("Graha Maitri", 0.0, 5.0, f"{gl} ↔ {bl} — enemies")
    return Porutham("Graha Maitri", 1.0, 5.0, f"{gl} ↔ {bl} — neutral")


def _ak_check_gana(girl_nak: Nakshatra, boy_nak: Nakshatra) -> Porutham:
    """Gana (6 pts) — temperament compatibility.

    Same gana → 6 pts.
    Deva → Rakshasa (or vice versa) → 0 pts (opposite extremes).
    Other mismatch → 3 pts.
    """
    gg = _GANA[girl_nak]
    bg = _GANA[boy_nak]
    if gg == bg:
        return Porutham("Gana", 6.0, 6.0, f"Both {gg}")
    if set([gg, bg]) == {"Deva", "Rakshasa"}:
        return Porutham("Gana", 0.0, 6.0,
                        f"Girl: {gg}, Boy: {bg} — opposite extremes")
    return Porutham("Gana", 3.0, 6.0,
                    f"Girl: {gg}, Boy: {bg} — partial")


def _ak_check_bhakoota(girl_rasi: Rasi, boy_rasi: Rasi) -> Porutham:
    """Bhakoota/Rasi (7 pts) — rasi position compatibility.

    If signs are 2, 6, 8, or 12 from each other → 0 pts (maraka/enemy).
    Same sign → 0 pts.
    3rd/11th → 5 pts.
    4th/10th → 3 pts.
    7th → 1 pt.
    5th/9th → 7 pts (best — trinal).
    """
    diff = (boy_rasi.value - girl_rasi.value) % 12
    # diff: 0=same, 1=2nd, 2=3rd, 3=4th, 4=5th, 5=6th,
    #       6=7th, 7=8th, 8=9th, 9=10th, 10=11th, 11=12th
    if diff in (0, 1, 5, 7, 11):
        label = {0: "same", 1: "2nd", 5: "6th", 7: "8th", 11: "12th"}.get(diff, str(diff))
        return Porutham("Bhakoota", 0.0, 7.0, f"{label} house — not good")
    if diff == 2 or diff == 10:
        return Porutham("Bhakoota", 5.0, 7.0, "3rd/11th — good")
    if diff == 3 or diff == 9:
        return Porutham("Bhakoota", 3.0, 7.0, "4th/10th — fair")
    if diff == 6:
        return Porutham("Bhakoota", 1.0, 7.0, "7th — neutral")
    # diff == 4 or 8 → 5th/9th
    return Porutham("Bhakoota", 7.0, 7.0, "5th/9th — excellent (trinal)")


def _ak_check_nadi(girl_nak: Nakshatra, boy_nak: Nakshatra) -> Porutham:
    """Nadi (8 pts) — health/heredity compatibility.

    Different nadi → 8 pts (best).
    Same nadi → 0 pts (worst — genetic incompatibility).
    """
    gn = _NADI[girl_nak]
    bn = _NADI[boy_nak]
    if gn != bn:
        return Porutham("Nadi", 8.0, 8.0, f"Girl: {gn}, Boy: {bn} — different")
    return Porutham("Nadi", 0.0, 8.0, f"Both {gn} — same nadi")


def _compute_ashta_koota(
    girl_nak: Nakshatra,
    boy_nak: Nakshatra,
    girl_rasi: Rasi,
    boy_rasi: Rasi,
) -> KutaResult:
    """Compute Ashta Koota (8 factors, 36 points) matchmaking."""
    factors = [
        _ak_check_varna(girl_rasi, boy_rasi),           # 1 pt
        _ak_check_vashya(girl_rasi, boy_rasi),          # 2 pts
        _ak_check_tara(girl_nak, boy_nak),              # 3 pts
        _ak_check_yoni(girl_nak, boy_nak),              # 4 pts
        _ak_check_graha_maitri(girl_rasi, boy_rasi),    # 5 pts
        _ak_check_gana(girl_nak, boy_nak),              # 6 pts
        _ak_check_bhakoota(girl_rasi, boy_rasi),        # 7 pts
        _ak_check_nadi(girl_nak, boy_nak),              # 8 pts
    ]
    return KutaResult(
        girl_nakshatra=girl_nak,
        boy_nakshatra=boy_nak,
        girl_rasi=girl_rasi,
        boy_rasi=boy_rasi,
        poruthams=factors,
        system=ScoringSystem.ASHTA_KOOTA,
    )


# ── Main entry point ─────────────────────────────────────────────────────────

def compute_kuta(
    girl_moon_longitude: float,
    boy_moon_longitude: float,
    system: ScoringSystem = ScoringSystem.PORUTHAM,
) -> KutaResult:
    """Compute marriage compatibility between two horoscopes.

    Args:
        girl_moon_longitude: Moon's sidereal longitude for the girl (0-360).
        boy_moon_longitude: Moon's sidereal longitude for the boy (0-360).
        system: Scoring system to use (PORUTHAM or ASHTA_KOOTA).

    Returns:
        KutaResult with poruthams/factors and totals.
    """
    girl_nak, _ = Nakshatra.from_longitude(girl_moon_longitude)
    boy_nak, _ = Nakshatra.from_longitude(boy_moon_longitude)
    girl_rasi = Rasi.from_longitude(girl_moon_longitude)
    boy_rasi = Rasi.from_longitude(boy_moon_longitude)

    if system == ScoringSystem.ASHTA_KOOTA:
        return _compute_ashta_koota(girl_nak, boy_nak, girl_rasi, boy_rasi)

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
