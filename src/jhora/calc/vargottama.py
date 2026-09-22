"""Vargottama — planets and lagna in the same rasi in a divisional chart.

A body is **vargottama** in a varga when it occupies the same rasi in that
divisional chart as in the rasi chart (D-1). Classically the term refers to
D-9 (navamsa): a vargottama planet is considered strengthened, and the concept
extends to every varga. This module reports, per body, the varga levels in
which it is vargottama.
"""

from dataclasses import dataclass
from typing import Dict, List

from jhora.charts.chart import ChartData
from jhora.charts.varga import VargaChartComputer
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.varga import VargaLevel, VargaVariant


@dataclass(frozen=True)
class VargottamaResult:
    """Per-body varga levels in which the body is vargottama."""

    planets: Dict[Graha, List[VargaLevel]]
    lagna: List[VargaLevel]

    def is_vargottama(self, graha: Graha, level: VargaLevel) -> bool:
        return level in self.planets.get(graha, [])


def compute_vargottama(cd: ChartData, computer: VargaChartComputer = None
                       ) -> VargottamaResult:
    """Compute, for every planet and the lagna, the vargottama vargas."""
    computer = computer or VargaChartComputer()
    d1 = {g: Rasi.from_longitude(p.longitude) for g, p in cd.planets.items()}
    d1_lagna = Rasi.from_longitude(cd.ascendant)

    planets: Dict[Graha, List[VargaLevel]] = {g: [] for g in d1}
    lagna: List[VargaLevel] = []
    for level in VargaLevel:
        if level == VargaLevel.D_1:
            continue
        try:
            chart = computer.compute(cd, level, VargaVariant.DEFAULT)
        except Exception:
            continue
        for g in d1:
            pos = chart.positions.get(g)
            if pos is not None and pos.rasi == d1[g]:
                planets[g].append(level)
        if chart.lagna_position.rasi == d1_lagna:
            lagna.append(level)
    return VargottamaResult(planets=planets, lagna=lagna)
