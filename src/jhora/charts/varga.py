"""
VargaChartComputer — compute planetary positions in all 23 divisional charts (D-1 through D-150).

Algorithm:
  For a planet at longitude L in a sign S (S = floor(L/30), 0=Aries..11=Pisces),
  and a varga of division count N:
    1. pos_in_sign = L % 30
    2. part_size = 30 / N
    3. part_index = floor(pos_in_sign / part_size)
    4. Map (S, part_index) → target_sign using variant-specific rules
    5. Return target_sign and degrees_within_part = pos_in_sign - part_index * part_size
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.varga import VargaLevel, VargaVariant
from jhora.charts.chart import ChartData, VargaPosition


_VARIANTS_BY_LEVEL: Dict[VargaLevel, List[VargaVariant]] = {
    VargaLevel.D_1: [VargaVariant.DEFAULT, VargaVariant.B],
    VargaLevel.D_2: [
        VargaVariant.DEFAULT, VargaVariant.CNL, VargaVariant.JN,
        VargaVariant.KN, VargaVariant.LM, VargaVariant.MD,
        VargaVariant.NI, VargaVariant.NIM, VargaVariant.PV,
        VargaVariant.RM, VargaVariant.RMM, VargaVariant.SN, VargaVariant.US,
    ],
    VargaLevel.D_3: [
        VargaVariant.DEFAULT, VargaVariant.JN, VargaVariant.PV,
        VargaVariant.SN, VargaVariant.TRD, VargaVariant.US,
    ],
    VargaLevel.D_4: [VargaVariant.DEFAULT, VargaVariant.PV],
    VargaLevel.D_5: [VargaVariant.DEFAULT, VargaVariant.PV],
    VargaLevel.D_6: [VargaVariant.DEFAULT],
    VargaLevel.D_7: [VargaVariant.DEFAULT, VargaVariant.V1_7, VargaVariant.V7_1, VargaVariant.TRD],
    VargaLevel.D_8: [VargaVariant.DEFAULT, VargaVariant.RA],
    VargaLevel.D_9: [VargaVariant.DEFAULT, VargaVariant.K, VargaVariant.KM, VargaVariant.UKM],
    VargaLevel.D_10: [
        VargaVariant.DEFAULT, VargaVariant.V5_8, VargaVariant.V6_9,
        VargaVariant.V9_12, VargaVariant.PV, VargaVariant.TRD,
    ],
    VargaLevel.D_11: [VargaVariant.DEFAULT, VargaVariant.RA],
    VargaLevel.D_12: [VargaVariant.DEFAULT, VargaVariant.REV, VargaVariant.TRD],
    VargaLevel.D_16: [VargaVariant.DEFAULT, VargaVariant.REV, VargaVariant.TRD],
    VargaLevel.D_20: [VargaVariant.DEFAULT, VargaVariant.REV, VargaVariant.TRD],
    VargaLevel.D_24: [VargaVariant.DEFAULT, VargaVariant.REV, VargaVariant.REV2, VargaVariant.TRD],
    VargaLevel.D_27: [VargaVariant.DEFAULT, VargaVariant.REV, VargaVariant.TRD],
    VargaLevel.D_30: [VargaVariant.DEFAULT, VargaVariant.PV, VargaVariant.SH],
    VargaLevel.D_40: [VargaVariant.DEFAULT],
    VargaLevel.D_45: [VargaVariant.DEFAULT],
    VargaLevel.D_60: [
        VargaVariant.DEFAULT, VargaVariant.AR, VargaVariant.REV,
        VargaVariant.RVAR, VargaVariant.TRD,
    ],
    VargaLevel.D_81: [VargaVariant.DEFAULT, VargaVariant.K],
    VargaLevel.D_108: [VargaVariant.DEFAULT],
    VargaLevel.D_144: [VargaVariant.DEFAULT],
    VargaLevel.D_150: [VargaVariant.DEFAULT],
}


@dataclass(frozen=True)
class VargaChartData:
    varga_level: VargaLevel
    variant: VargaVariant
    positions: Dict[Graha, VargaPosition]
    lagna_position: VargaPosition


class VargaChartComputer:
    def __init__(self):
        self._cache: Dict[Tuple[VargaLevel, VargaVariant], VargaChartData] = {}

    def compute(
        self,
        cd: ChartData,
        varga_level: VargaLevel,
        variant: VargaVariant = VargaVariant.DEFAULT,
    ) -> VargaChartData:
        key = (varga_level, variant)
        if key in self._cache:
            return self._cache[key]

        n = varga_level.divisions
        positions = {}
        for g, p in cd.planets.items():
            positions[g] = _compute_one(g, p.longitude, n, variant)

        lagna_pos = _compute_one(Graha.SUN, cd.ascendant, n, variant)
        result = VargaChartData(
            varga_level=varga_level,
            variant=variant,
            positions=positions,
            lagna_position=lagna_pos,
        )
        self._cache[key] = result
        return result

    def compute_all(self, cd: ChartData) -> Dict[Tuple[VargaLevel, VargaVariant], VargaChartData]:
        results = {}
        for vl, variants in _VARIANTS_BY_LEVEL.items():
            if vl == VargaLevel.D_1:
                continue
            for var in variants:
                results[(vl, var)] = self.compute(cd, vl, var)
        return results

    def clear_cache(self):
        self._cache.clear()


def _compute_one(graha: Graha, longitude: float, n: int, variant: VargaVariant) -> VargaPosition:
    sign_idx = int(longitude // 30) % 12
    pos_in_sign = longitude % 30
    part_size = 30.0 / n
    part_index = int(pos_in_sign // part_size)

    target_sign = _map_sign(sign_idx, part_index, n, variant)
    degrees_in_rasi = pos_in_sign - part_index * part_size
    target_longitude = target_sign * 30.0 + degrees_in_rasi

    return VargaPosition(
        graha=graha,
        varga_level=_level_for_divisions(n),
        variant=variant,
        longitude=target_longitude,
        rasi=Rasi(target_sign),
        degrees_in_rasi=degrees_in_rasi,
    )


def _level_for_divisions(n: int) -> VargaLevel:
    for vl in VargaLevel:
        if vl.divisions == n:
            return vl
    return VargaLevel.D_1


def _map_sign(sign: int, part: int, n: int, variant: VargaVariant) -> int:
    if variant == VargaVariant.DEFAULT:
        return _default_map(sign, part, n)
    elif variant == VargaVariant.REV:
        return _reverse_map(sign, part, n)
    elif variant == VargaVariant.REV2:
        return _rev2_map(sign, part, n)
    elif variant == VargaVariant.PV:
        return _parivritti_map(sign, part, n)
    elif variant == VargaVariant.TRD:
        return _tridirectional_map(sign, part, n)
    elif variant == VargaVariant.K:
        return _kalachakra_map(sign, part, n)
    elif variant == VargaVariant.KM:
        return _krishna_mishra_map(sign, part, n)
    elif variant == VargaVariant.UKM:
        return (sign + 4 + part) % 12  # uniform krishna mishra
    elif variant == VargaVariant.AR:
        return part % 12  # from Aries
    elif variant == VargaVariant.RVAR:
        return _rev_from_aries_map(sign, part, n)
    elif variant == VargaVariant.B:
        return sign  # bhava: same as rasi
    elif variant in (VargaVariant.RA, VargaVariant.RM, VargaVariant.RMM):
        return (sign + part) % 12  # Raman variants
    elif variant == VargaVariant.V1_7:
        return _1_7_map(sign, part, n)
    elif variant == VargaVariant.V7_1:
        return _7_1_map(sign, part, n)
    elif variant == VargaVariant.V5_8:
        return _5_8_map(sign, part, n)
    elif variant == VargaVariant.V6_9:
        return _6_9_map(sign, part, n)
    elif variant == VargaVariant.V9_12:
        return _9_12_map(sign, part, n)
    elif variant == VargaVariant.JN:
        return (sign + part) % 12  # Jagannatha
    elif variant == VargaVariant.SN:
        return (sign + part) % 12  # Somanatha
    elif variant == VargaVariant.US:
        return (sign + part) % 12  # Uma-Shambhu
    elif variant == VargaVariant.SH:
        return (sign + part) % 12  # Shashyamsa-like
    elif variant in (VargaVariant.NI, VargaVariant.NIM, VargaVariant.SN2,
                     VargaVariant.CNL, VargaVariant.KN, VargaVariant.LM,
                     VargaVariant.MD, VargaVariant.K_N_RAO):
        return _default_map(sign, part, n)
    else:
        return _default_map(sign, part, n)


def _default_map(sign: int, part: int, n: int) -> int:
    if sign % 2 == 0:
        return (sign + part) % 12
    else:
        offset = n // 2
        return (sign + offset + part) % 12


def _reverse_map(sign: int, part: int, n: int) -> int:
    if sign % 2 == 0:
        return (sign + part) % 12
    else:
        return (sign + n - 1 - part) % 12


def _rev2_map(sign: int, part: int, n: int) -> int:
    base = (sign + part) % 12
    if base == 3:
        return 4
    elif base == 4:
        return 3
    return base


def _parivritti_map(sign: int, part: int, n: int) -> int:
    return (sign + part) % 12


def _tridirectional_map(sign: int, part: int, n: int) -> int:
    third = n // 3
    if part < third:
        return (sign + part) % 12
    elif part < 2 * third:
        offset = n // 2
        return (sign + offset + part) % 12
    else:
        return (sign + n - 1 - part) % 12


def _kalachakra_map(sign: int, part: int, n: int) -> int:
    r = Rasi(sign)
    if r.is_movable:
        return (sign + part) % 12
    elif r.is_fixed:
        return (sign + 5 + part) % 12
    else:
        return (sign + 9 + part) % 12


def _krishna_mishra_map(sign: int, part: int, n: int) -> int:
    grid = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8],
        [1, 2, 3, 4, 5, 6, 7, 8, 0],
        [2, 3, 4, 5, 6, 7, 8, 0, 1],
        [3, 4, 5, 6, 7, 8, 0, 1, 2],
        [4, 5, 6, 7, 8, 0, 1, 2, 3],
        [5, 6, 7, 8, 0, 1, 2, 3, 4],
        [6, 7, 8, 0, 1, 2, 3, 4, 5],
        [7, 8, 0, 1, 2, 3, 4, 5, 6],
        [8, 0, 1, 2, 3, 4, 5, 6, 7],
        [0, 1, 2, 3, 4, 5, 6, 7, 8],
        [1, 2, 3, 4, 5, 6, 7, 8, 0],
        [2, 3, 4, 5, 6, 7, 8, 0, 1],
    ]
    if 0 <= sign < 12 and 0 <= part < min(n, 9):
        return grid[sign][part]
    return (sign + part) % 12


def _rev_from_aries_map(sign: int, part: int, n: int) -> int:
    if sign % 2 == 0:
        return part % 12
    else:
        return (n - 1 - part) % 12


def _1_7_map(sign: int, part: int, n: int) -> int:
    if sign % 2 == 0:
        return (sign + 1 + part) % 12
    else:
        return (sign + part) % 12


def _7_1_map(sign: int, part: int, n: int) -> int:
    if sign % 2 == 0:
        return (sign + 7 - part) % 12
    else:
        return (sign + part) % 12


def _5_8_map(sign: int, part: int, n: int) -> int:
    if sign % 2 == 0:
        return (sign + 5 + part) % 12
    else:
        return (sign + part) % 12


def _6_9_map(sign: int, part: int, n: int) -> int:
    if sign % 2 == 0:
        return (sign + 6 + part) % 12
    else:
        return (sign + part) % 12


def _9_12_map(sign: int, part: int, n: int) -> int:
    if sign % 2 == 0:
        return (sign + 9 + part) % 12
    else:
        return (sign + part) % 12


def get_variants_for_level(vl: VargaLevel) -> List[VargaVariant]:
    return _VARIANTS_BY_LEVEL.get(vl, [VargaVariant.DEFAULT])
