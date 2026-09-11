"""Ashtakavarga — eight-sourced strength (Brihat Parasara Hora Sastra).

Components:
  BAV (Bhinna Ashtakavarga)   — per-planet 12-house bindu count
  SAV (Sarva Ashtakavarga)    — sum of all 7 BAVs (12 houses)
  PAV (Prastara Ashtakavarga) — 8-reference × 12-house per-planet grid
  Trikona Shodhana            — triangular reduction
  Ekadhipatya Shodhana        — lordship reduction
  Sodhya Pinda                — final reduced product

References:
  - Brihat Parasara Hora Sastra, Ashtakavarga adhyaya
  - "Ashtakavarga System of Prediction" by Dr. B.V. Raman
  - Classical Vedic 9.0 binary (function 0x00460bd0)
"""

from typing import Dict, List, Optional, Tuple

from jhora.charts.chart import ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

# ── Benefic houses per (subject, contributor) — Parasara school ──
# Outer key: the planet whose BAV is built. Inner key: the contributing
# reference (Graha, or "LAGNA"). Houses are 1-based from the contributor.
# Source: BPHS Ashtakavarga adhyaya; B.V. Raman. Row sums are the fixed
# BAV totals: Sun 48, Moon 49, Mars 39, Mercury 54, Jupiter 56,
# Venus 52, Saturn 39 (SAV 337 in every chart).

_BAV_MATRIX = {
    Graha.SUN: {
        Graha.SUN: [1, 2, 4, 7, 8, 9, 10, 11],
        Graha.MOON: [3, 6, 10, 11],
        Graha.MARS: [1, 2, 4, 7, 8, 9, 10, 11],
        Graha.MERCURY: [3, 5, 6, 9, 10, 11, 12],
        Graha.JUPITER: [5, 6, 9, 11],
        Graha.VENUS: [6, 7, 12],
        Graha.SATURN: [1, 2, 4, 7, 8, 9, 10, 11],
        "LAGNA": [3, 4, 6, 10, 11, 12],
    },
    Graha.MOON: {
        Graha.SUN: [3, 6, 7, 8, 10, 11],
        Graha.MOON: [1, 3, 6, 7, 10, 11],
        Graha.MARS: [2, 3, 5, 6, 9, 10, 11],
        Graha.MERCURY: [1, 3, 4, 5, 7, 8, 10, 11],
        Graha.JUPITER: [1, 4, 7, 8, 10, 11, 12],
        Graha.VENUS: [3, 4, 5, 7, 9, 10, 11],
        Graha.SATURN: [3, 5, 6, 11],
        "LAGNA": [3, 6, 10, 11],
    },
    Graha.MARS: {
        Graha.SUN: [3, 5, 6, 10, 11],
        Graha.MOON: [3, 6, 11],
        Graha.MARS: [1, 2, 4, 7, 8, 10, 11],
        Graha.MERCURY: [3, 5, 6, 11],
        Graha.JUPITER: [6, 10, 11, 12],
        Graha.VENUS: [6, 8, 11, 12],
        Graha.SATURN: [1, 4, 7, 8, 9, 10, 11],
        "LAGNA": [1, 3, 6, 10, 11],
    },
    Graha.MERCURY: {
        Graha.SUN: [5, 6, 9, 11, 12],
        Graha.MOON: [2, 4, 6, 8, 10, 11],
        Graha.MARS: [1, 2, 4, 7, 8, 9, 10, 11],
        Graha.MERCURY: [1, 3, 5, 6, 9, 10, 11, 12],
        Graha.JUPITER: [6, 8, 11, 12],
        Graha.VENUS: [1, 2, 3, 4, 5, 8, 9, 11],
        Graha.SATURN: [1, 2, 4, 7, 8, 9, 10, 11],
        "LAGNA": [1, 2, 4, 6, 8, 10, 11],
    },
    Graha.JUPITER: {
        Graha.SUN: [1, 2, 3, 4, 7, 8, 9, 10, 11],
        Graha.MOON: [2, 5, 7, 9, 11],
        Graha.MARS: [1, 2, 4, 7, 8, 10, 11],
        Graha.MERCURY: [1, 2, 4, 5, 6, 9, 10, 11],
        Graha.JUPITER: [1, 2, 3, 4, 7, 8, 10, 11],
        Graha.VENUS: [2, 5, 6, 9, 10, 11],
        Graha.SATURN: [3, 5, 6, 12],
        "LAGNA": [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    Graha.VENUS: {
        Graha.SUN: [8, 11, 12],
        Graha.MOON: [1, 2, 3, 4, 5, 8, 9, 11, 12],
        Graha.MARS: [3, 5, 6, 9, 11, 12],
        Graha.MERCURY: [3, 5, 6, 9, 11],
        Graha.JUPITER: [5, 8, 9, 10, 11],
        Graha.VENUS: [1, 2, 3, 4, 5, 8, 9, 10, 11],
        Graha.SATURN: [3, 4, 5, 8, 9, 10, 11],
        "LAGNA": [1, 2, 3, 4, 5, 8, 9, 11],
    },
    Graha.SATURN: {
        Graha.SUN: [1, 2, 4, 7, 8, 10, 11],
        Graha.MOON: [3, 6, 11],
        Graha.MARS: [3, 5, 6, 10, 11, 12],
        Graha.MERCURY: [6, 8, 9, 10, 11, 12],
        Graha.JUPITER: [5, 6, 11, 12],
        Graha.VENUS: [6, 11, 12],
        Graha.SATURN: [3, 5, 6, 11],
        "LAGNA": [1, 3, 4, 6, 10, 11],
    },
}

# Fixed BAV totals (sum of each subject's matrix rows) — chart-invariant.
_BAV_TOTALS = {
    Graha.SUN: 48, Graha.MOON: 49, Graha.MARS: 39, Graha.MERCURY: 54,
    Graha.JUPITER: 56, Graha.VENUS: 52, Graha.SATURN: 39,
}

# The 7 grahas used as occupants in Ashtakavarga (Sun through Saturn).
_OCCUPANT_GRAHAS = [Graha.SUN, Graha.MOON, Graha.MARS,
                    Graha.MERCURY, Graha.JUPITER, Graha.VENUS, Graha.SATURN]

# The 8 reference points (7 grahas + Lagna).
_REFERENCES = _OCCUPANT_GRAHAS + ["LAGNA"]


# ── Helpers ──

def _rasi_of(graha: Graha, chart: ChartData) -> int:
    """Return the rasi index (0-11) for a graha, or lagna."""
    return chart.planets[graha].rasi.value


def _lagna_rasi(chart: ChartData) -> int:
    return chart.lagna.rasi.value


def _dist(from_rasi: int, to_rasi: int) -> int:
    """Return 1-based distance from_rasi → to_rasi (1 = same sign)."""
    return (to_rasi - from_rasi) % 12 + 1


# ── Benefic-house lookup ──

def _require_parasara(parasara_moon: bool, parasara_venus: bool) -> None:
    """Only the Parasara school matrix is implemented.

    The old single-table code path never produced valid output, so no
    working behavior is lost; the Varahamihira variant needs its own
    attested matrix before it can be offered honestly.
    """
    if not parasara_moon or not parasara_venus:
        raise NotImplementedError(
            "Only the Parasara Ashtakavarga school is implemented; "
            "the Varahamihira variant has no validated matrix yet."
        )


def _contrib_sign(contrib, planet_rasi: Dict[Graha, int], lagna_rasi: int) -> int:
    if isinstance(contrib, Graha):
        return planet_rasi[contrib]
    return lagna_rasi  # "LAGNA"


def _is_benefic(subject: Graha, contrib, contrib_sign: int,
                target_rasi: int) -> bool:
    d = _dist(contrib_sign, target_rasi)
    return d in _BAV_MATRIX[subject][contrib]


# ── Core BAV computation ──

def bhinna_ashtakavarga(
    chart: ChartData,
    subject: Graha,
    parasara_moon: bool = True,
    parasara_venus: bool = True,
) -> List[int]:
    """Compute Bhinna Ashtakavarga (BAV) for a given subject planet.

    Returns a 12-element list (one per rasi, Ar=0..Pi=11) of bindu counts.

    Algorithm (BPHS): each contributor C (Sun … Saturn, Lagna) drops one
    bindu into every house that is benefic from C's own position per the
    (subject, C) matrix row. Pure geometry — no occupancy condition, so
    each subject's total is chart-invariant (48/49/39/54/56/52/39).
    """
    _require_parasara(parasara_moon, parasara_venus)
    bav = [0] * 12
    planet_rasi = {g: _rasi_of(g, chart) for g in _OCCUPANT_GRAHAS}
    lagna_r = _lagna_rasi(chart)

    for contrib in list(_OCCUPANT_GRAHAS) + ["LAGNA"]:
        contrib_r = _contrib_sign(contrib, planet_rasi, lagna_r)
        for house_num in _BAV_MATRIX[subject][contrib]:
            bav[(contrib_r + house_num - 1) % 12] += 1

    return bav


def all_bhinna_ashtakavarga(
    chart: ChartData,
    parasara_moon: bool = True,
    parasara_venus: bool = True,
) -> Dict[Graha, List[int]]:
    """Compute BAV for all 7 planets.

    Returns {Graha: [12 bindus]}.
    """
    return {
        g: bhinna_ashtakavarga(chart, g, parasara_moon, parasara_venus)
        for g in _OCCUPANT_GRAHAS
    }


# ── SAV ──

def sarva_ashtakavarga(
    chart: ChartData,
    parasara_moon: bool = True,
    parasara_venus: bool = True,
) -> List[int]:
    """Sarva Ashtakavarga = sum of all 7 BAVs (12 houses)."""
    bavs = all_bhinna_ashtakavarga(chart, parasara_moon, parasara_venus)
    sav = [0] * 12
    for h in range(12):
        total = 0
        for g in _OCCUPANT_GRAHAS:
            total += bavs[g][h]
        sav[h] = total
    return sav


# ── PAV (Prastara Ashtakavarga) ──

def prastara_ashtakavarga(
    chart: ChartData,
    subject: Graha,
    parasara_moon: bool = True,
    parasara_venus: bool = True,
) -> Dict[str, Dict[int, int]]:
    """Prastara Ashtakavarga — 8 contributor rows × 12 houses for one subject.

    Returns {contributor_name: {house_index: 0/1}}.
    Row C has a 1 in every house benefic from C per the (subject, C)
    matrix row — the column sums equal the subject's BAV.
    """
    _require_parasara(parasara_moon, parasara_venus)
    _require_parasara(parasara_moon, parasara_venus)
    planet_rasi = {g: _rasi_of(g, chart) for g in _OCCUPANT_GRAHAS}
    lagna_r = _lagna_rasi(chart)
    pav: Dict[str, Dict[int, int]] = {}

    for contrib in list(_OCCUPANT_GRAHAS) + ["LAGNA"]:
        contrib_r = _contrib_sign(contrib, planet_rasi, lagna_r)
        row = {h: 0 for h in range(12)}
        for house_num in _BAV_MATRIX[subject][contrib]:
            row[(contrib_r + house_num - 1) % 12] = 1
        name = contrib.name if isinstance(contrib, Graha) else contrib
        pav[name] = row

    return pav


# ── Trikona Shodhana (Triangular Reduction) ──

def trikona_shodhana(
    bav: List[int],
) -> List[int]:
    """Trikona Shodhana — triangular reduction on one planet's BAV.

    Groups (1,5,9), (2,6,10), (3,7,11), (4,8,12).
    Within each group, the lowest value becomes 0, remaining two get
    adjusted by subtracting the lowest. This is done for each group.
    """
    working = list(bav)
    groups = [(0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)]
    for a, b, c in groups:
        mn = min(working[a], working[b], working[c])
        working[a] -= mn
        working[b] -= mn
        working[c] -= mn
    return working


def trikona_shodhana_all(
    bavs: Dict[Graha, List[int]],
) -> Dict[Graha, List[int]]:
    """Apply Trikona Shodhana to all 7 BAVs."""
    return {g: trikona_shodhana(bavs[g]) for g in _OCCUPANT_GRAHAS}


# ── Ekadhipatya Shodhana (Lordship Reduction) ──

def _lord_of(rasi_idx: int) -> Optional[Graha]:
    """Return the graha that owns a given rasi index (0-11)."""
    lordship = {
        0: Graha.MARS, 1: Graha.VENUS, 2: Graha.MERCURY,
        3: Graha.MOON, 4: Graha.SUN, 5: Graha.MERCURY,
        6: Graha.VENUS, 7: Graha.MARS, 8: Graha.JUPITER,
        9: Graha.SATURN, 10: Graha.SATURN, 11: Graha.JUPITER,
    }
    return lordship[rasi_idx]


def _rasi_of_graha(g: Graha) -> List[int]:
    return [i for i in range(12) if _lord_of(i) == g]


def ekadhipatya_shodhana(
    bavs: Dict[Graha, List[int]],
) -> Dict[Graha, List[int]]:
    """Ekadhipatya Shodhana — lordship reduction across all planets.

    For planets owning two signs (Mars, Mercury, Jupiter, Venus, Saturn):
      If the bindus in the two owned houses are both > 0 and unequal,
      the higher-value house retains only the difference;
      the lower-value house keeps its original value.
      If both equal, both retain their values.

    For Sun and Moon (single-sign owners): no reduction, pass through.
    """
    result = {g: list(bavs[g]) for g in _OCCUPANT_GRAHAS}
    dual_lords = [Graha.MARS, Graha.MERCURY, Graha.JUPITER,
                  Graha.VENUS, Graha.SATURN]
    for g in dual_lords:
        houses = g.lordship_signs  # e.g., Mars -> [1, 8] (1-based)
        h0, h1 = houses[0] - 1, houses[1] - 1  # convert to 0-based
        v0, v1 = result[g][h0], result[g][h1]
        if v0 > 0 and v1 > 0 and v0 != v1:
            if v0 > v1:
                result[g][h0] = v0 - v1
            else:
                result[g][h1] = v1 - v0
    return result


# ── Full Sodhana (Trikona + Ekadhipatya) ──

def sodhya_pinda(
    chart: ChartData,
    parasara_moon: bool = True,
    parasara_venus: bool = True,
) -> Dict[Graha, int]:
    """Compute Sodhya Pinda (Yoga Pinda) for each planet.

    1. Compute all BAVs
    2. Apply Trikona Shodhana
    3. Apply Ekadhipatya Shodhana
    4. Sum bindus per planet across all 12 houses → Sodhya Pinda
    """
    bavs = all_bhinna_ashtakavarga(chart, parasara_moon, parasara_venus)
    trikona = trikona_shodhana_all(bavs)
    ekadhi = ekadhipatya_shodhana(trikona)
    return {g: sum(ekadhi[g]) for g in _OCCUPANT_GRAHAS}


# ── Kakshya (sub-divisional bindus) ──

_KAKSHYA_REFERENCES = [
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
    Graha.JUPITER, Graha.VENUS, Graha.SATURN, "LAGNA",
]

KAKSHYA_SIZE = 3.75  # 30° / 8 = 3.75° per kakshya


def kakshya_index_from_degree(deg_in_rasi: float) -> int:
    """Return the kakshya index (0-7) for a given degree within a rasi."""
    idx = int(deg_in_rasi // KAKSHYA_SIZE)
    return min(idx, 7)  # clamp 30.0° → index 7


def kakshya_lord(kakshya_idx: int):
    """Return the reference (Graha or 'LAGNA') that rules the given kakshya (0-7)."""
    return _KAKSHYA_REFERENCES[kakshya_idx]


def _ref_contributes(
    house_rasi: int, ref, subject: Graha,
    planet_rasi: Dict[Graha, int], lagna_rasi: int,
) -> bool:
    """Does contributor R put a bindu into house H of the subject's BAV?"""
    contrib_r = _contrib_sign(ref, planet_rasi, lagna_rasi)
    return _is_benefic(subject, ref, contrib_r, house_rasi)


def kakshya_bindu_table(
    subject: Graha,
    chart: ChartData,
    parasara_moon: bool = True,
    parasara_venus: bool = True,
) -> List[List[int]]:
    """12×8 Kakshya table for a given subject planet.

    For each house H (0-11) and each Kakshya K (0-7), the cell shows 1
    if the contributor ruling Kakshya K puts a bindu into house H of the
    subject's BAV. Row sums equal the BAV.
    Returns List[12 houses][8 kakshyas].
    """
    _require_parasara(parasara_moon, parasara_venus)
    _require_parasara(parasara_moon, parasara_venus)
    planet_rasi = {g: _rasi_of(g, chart) for g in _OCCUPANT_GRAHAS}
    lagna_r = _lagna_rasi(chart)
    table = [[0] * 8 for _ in range(12)]

    for h in range(12):
        for k, ref in enumerate(_KAKSHYA_REFERENCES):
            if _ref_contributes(h, ref, subject, planet_rasi, lagna_r):
                table[h][k] = 1
    return table


def all_kakshya_tables(
    chart: ChartData,
    parasara_moon: bool = True,
    parasara_venus: bool = True,
) -> Dict[Graha, List[List[int]]]:
    """Compute Kakshya tables for all 7 planets.

    Returns {Graha: 12×8 table}.
    """
    return {
        g: kakshya_bindu_table(g, chart, parasara_moon, parasara_venus)
        for g in _OCCUPANT_GRAHAS
    }


def kakshya_totals(
    chart: ChartData,
    parasara_moon: bool = True,
    parasara_venus: bool = True,
) -> Dict[str, List[int]]:
    """Per-reference totals across all houses and all subjects.

    Sums the contribution of each reference across all 7 subject BAVs.
    Returns {reference_name: [12 bindu counts]} — i.e., total bindus
    contributed by each reference to each house.
    """
    totals = {str(r): [0] * 12 if isinstance(r, Graha) else [0] * 12
              for r in _KAKSHYA_REFERENCES}
    # Actually just use string keys
    totals = {ref_to_str(r): [0] * 12 for r in _KAKSHYA_REFERENCES}

    for subject in _OCCUPANT_GRAHAS:
        table = kakshya_bindu_table(subject, chart, parasara_moon, parasara_venus)
        for h in range(12):
            for k, ref in enumerate(_KAKSHYA_REFERENCES):
                totals[ref_to_str(ref)][h] += table[h][k]
    return totals


def ref_to_str(r) -> str:
    """Convert a Graha or 'LAGNA' to a string key."""
    if isinstance(r, Graha):
        return r.name
    return r
