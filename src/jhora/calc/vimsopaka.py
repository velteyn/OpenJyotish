"""Vimsopaka Bala — varga-weighted planetary strength (BPHS Chapter 27).

Four schemes (weight sets) determine how divisional chart dignities combine
into a 20-point score per planet (Vimsa = 20, upaka = points).

Schemes:
  Shadvarga     (6 vargas): D1, D2, D3, D7, D9, D12
  Saptavarga    (7 vargas): Shadvarga + D30
  Dashavarga   (10 vargas): Shadvarga + D16, D20, D24, D30
  Shodasavarga (16 vargas): Dashavarga + D4, D5, D6, D27, D40, D45, D60
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from jhora.charts.chart import ChartData
from jhora.charts.varga import VargaChartComputer
from jhora.calc.dignities import DignityChecker
from jhora.types.graha import Graha
from jhora.types.varga import VargaLevel


class VimsopakaScheme(Enum):
    SHADVARGA = "shadvarga"
    SAPTAVARGA = "saptavarga"
    DASHAVARGA = "dashavarga"
    SHODASAVARGA = "shodasavarga"


# Varga weights per scheme — how many points each varga contributes to the 20
_WEIGHTS = {
    VimsopakaScheme.SHADVARGA: {
        VargaLevel.D_1: 6.0, VargaLevel.D_2: 2.0, VargaLevel.D_3: 4.0,
        VargaLevel.D_7: 5.0, VargaLevel.D_9: 3.0,
    },
    VimsopakaScheme.SAPTAVARGA: {
        VargaLevel.D_1: 5.0, VargaLevel.D_2: 2.0, VargaLevel.D_3: 3.0,
        VargaLevel.D_7: 2.5, VargaLevel.D_9: 4.5, VargaLevel.D_30: 3.0,
    },
    VimsopakaScheme.DASHAVARGA: {
        VargaLevel.D_1: 3.0, VargaLevel.D_2: 1.5, VargaLevel.D_3: 1.5,
        VargaLevel.D_7: 1.5, VargaLevel.D_9: 1.5, VargaLevel.D_12: 1.5,
        VargaLevel.D_16: 1.0, VargaLevel.D_20: 1.0,
        VargaLevel.D_24: 1.0, VargaLevel.D_30: 1.0,
    },
    VimsopakaScheme.SHODASAVARGA: {
        VargaLevel.D_1: 3.5, VargaLevel.D_2: 1.0, VargaLevel.D_3: 1.0,
        VargaLevel.D_4: 0.5, VargaLevel.D_5: 0.5, VargaLevel.D_6: 0.5,
        VargaLevel.D_7: 1.0, VargaLevel.D_9: 3.0,
        VargaLevel.D_12: 1.0, VargaLevel.D_16: 1.5,
        VargaLevel.D_20: 0.5, VargaLevel.D_24: 1.0,
        VargaLevel.D_27: 1.0, VargaLevel.D_30: 1.0,
        VargaLevel.D_40: 0.5, VargaLevel.D_45: 0.5,
        VargaLevel.D_60: 1.0,
    },
}

# Dignity → fraction of varga weight (0.0 to 1.0)
_DIGNITY_FRACTIONS = {
    "exalted": 1.0,
    "moolatrikona": 1.0,
    "own": 1.0,
    "friend": 0.75,
    "neutral": 0.50,
    "enemy": 0.25,
    "debilitated": 0.0,
}

# Planets that get scored (nodes excluded in Vimsopaka)
_VIMSOPAKA_PLANETS = [
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
    Graha.JUPITER, Graha.VENUS, Graha.SATURN,
]


@dataclass
class VimsopakaComponent:
    varga: str
    weight: float
    dignity: str
    score: float


@dataclass
class VimsopakaResult:
    graha: Graha
    scheme: VimsopakaScheme
    components: List[VimsopakaComponent]
    total: float
    percentage: float  # % of max (20)


class VimsopakaComputer:
    def __init__(self, chart: ChartData):
        self.chart = chart
        self.vcc = VargaChartComputer()
        self.dc = DignityChecker()
        self._varga_cache: Dict[VargaLevel, dict] = {}

    def _varga(self, level: VargaLevel) -> dict:
        if level not in self._varga_cache:
            self._varga_cache[level] = self.vcc.compute(self.chart, level)
        return self._varga_cache[level]

    def compute(self, graha: Graha,
                scheme: VimsopakaScheme = VimsopakaScheme.SHADVARGA,
                ) -> VimsopakaResult:
        weights = _WEIGHTS[scheme]
        components = []
        for vl, weight in weights.items():
            vcd = self._varga(vl)
            vpos = vcd.positions.get(graha)
            if vpos is None:
                continue
            dignity = self.dc.get_dignity(
                graha, vpos.rasi.value, vpos.degrees_in_rasi,
            )
            fraction = _DIGNITY_FRACTIONS.get(dignity, 0.5)
            score = weight * fraction
            components.append(VimsopakaComponent(
                varga=vl.name,
                weight=weight,
                dignity=dignity,
                score=score,
            ))
        total = sum(c.score for c in components)
        return VimsopakaResult(
            graha=graha, scheme=scheme, components=components,
            total=round(total, 1), percentage=round(total / 20.0 * 100, 1),
        )

    def compute_all(self, scheme: VimsopakaScheme = VimsopakaScheme.SHADVARGA,
                    ) -> List[VimsopakaResult]:
        return [self.compute(g, scheme) for g in _VIMSOPAKA_PLANETS]
