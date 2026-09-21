"""Pravesha-chart dasas keyed on tithi, karana and yoga indices.

Companions to the return-chart finders (``tithi_pravesha.py``,
``pravesha.py``). Each engine derives its index from the chart itself,
so it runs on any chart — natal (janma tithi) or pravesha — through
the standard ``compute`` interface:

- Tithi Ashtottari (108): tithi index → lord/duration table below.
  Prescribed for Tithi Pravesha charts.
- Tithi Yogini (36): Yogini lords by tithi instead of nakshatra.
- Karana Chaturaseeti (84): karana serial → lord (nodes excluded),
  12 years each. Prescribed for Tithi/Karana Pravesha charts. No
  standalone Karana Pravesha finder ships (no canonical definition
  found in the mainstream sources) — the engine works wherever the
  tradition places it, starting with Tithi Pravesha charts.
- Yoga Vimsottari (120): yoga index → lord with standard Vimsottari
  years. Prescribed for Yoga Pravesha charts.

Tables: mirrored-implementation method cross-check; tithi/karana
groupings trace to the cited tutorial tradition. Balance in every
system is the elapsed fraction of the current index span times the
MD years. Mahadashas only (no antardasas), matching the conditional
suite scope.
"""

from typing import Dict, List, Optional, Tuple

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha

# tithi numbers are 1-based (1..30); karana serials 1-based (1..60);
# yoga numbers 1-based (1..27).

_TITHI_ASHTOTTARI: List[Tuple[Graha, List[int], float]] = [
    (Graha.SUN, [1, 9, 16, 24], 6.0),
    (Graha.MOON, [2, 10, 17, 25], 15.0),
    (Graha.MARS, [3, 11, 18, 26], 8.0),
    (Graha.MERCURY, [4, 12, 19, 27], 17.0),
    (Graha.SATURN, [7, 15, 22], 10.0),
    (Graha.JUPITER, [5, 13, 20, 28], 19.0),
    (Graha.RAHU, [8, 23, 30], 12.0),
    (Graha.VENUS, [6, 14, 21, 29], 21.0),
]

_TITHI_YOGINI: List[Tuple[Graha, List[int], float]] = [
    (Graha.SUN, [1, 9, 16, 24], 2.0),
    (Graha.MOON, [2, 10, 17, 25], 1.0),
    (Graha.MARS, [3, 11, 18, 26], 4.0),
    (Graha.MERCURY, [4, 12, 19, 27], 5.0),
    (Graha.SATURN, [7, 15, 22], 6.0),
    (Graha.JUPITER, [5, 13, 20, 28], 3.0),
    (Graha.RAHU, [8, 23, 30], 8.0),
    (Graha.VENUS, [6, 14, 21, 29], 7.0),
]

_KARANA_84: List[Tuple[Graha, List[int], float]] = [
    (Graha.SUN, [2, 9, 16, 23, 30, 37, 44, 51, 58], 12.0),
    (Graha.MOON, [3, 10, 17, 24, 31, 38, 45, 52, 59], 12.0),
    (Graha.MARS, [4, 11, 18, 25, 32, 39, 46, 53, 60], 12.0),
    (Graha.MERCURY, [5, 12, 19, 26, 33, 40, 47, 54, 1], 12.0),
    (Graha.JUPITER, [6, 13, 20, 27, 34, 41, 48, 55], 12.0),
    (Graha.VENUS, [7, 14, 21, 28, 35, 42, 49, 56], 12.0),
    (Graha.SATURN, [8, 15, 22, 29, 36, 43, 50, 57], 12.0),
]

_YOGA_VIMSOTTARI: List[Tuple[Graha, List[int], float]] = [
    (Graha.KETU, [3, 12, 21], 7.0),
    (Graha.VENUS, [4, 13, 22], 20.0),
    (Graha.SUN, [5, 14, 23], 6.0),
    (Graha.MOON, [6, 15, 24], 10.0),
    (Graha.MARS, [7, 16, 25], 7.0),
    (Graha.RAHU, [8, 17, 26], 18.0),
    (Graha.JUPITER, [9, 18, 27], 16.0),
    (Graha.MERCURY, [1, 10, 19], 17.0),
    (Graha.SATURN, [2, 11, 20], 19.0),
]


def _sun_moon(chart: Dict) -> Tuple[float, float]:
    planets = chart["planets"]
    return (planets[Graha.SUN]["longitude"],
            planets[Graha.MOON]["longitude"])


def tithi_index(chart: Dict) -> int:
    """0-based tithi (0-29) from Sun-Moon elongation."""
    sun, moon = _sun_moon(chart)
    return int((moon - sun) % 360.0 // 12.0) % 30


def karana_serial(chart: Dict) -> int:
    """1-based karana serial (1-60): half-tithi index + 1."""
    sun, moon = _sun_moon(chart)
    return int((moon - sun) % 360.0 // 6.0) % 60 + 1


def yoga_index(chart: Dict) -> int:
    """1-based yoga number (1-27) from the (Sun + Moon) point."""
    sun, moon = _sun_moon(chart)
    return int((sun + moon) % 360.0 // (360.0 / 27.0)) % 27 + 1


class _IndexDasa(DasaBase):
    """Mahadashas from a 1-based index table with span balance."""

    table: List[Tuple[Graha, List[int], float]] = []
    system_name = "index"

    def _index(self, chart: Dict) -> int:
        raise NotImplementedError

    def _span(self) -> float:
        raise NotImplementedError

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        idx = self._index(chart)
        start_pos = next(i for i, (_, members, _) in enumerate(self.table)
                         if idx in members)
        sun, moon = _sun_moon(chart)
        if self._span() == 12.0:
            frac = ((moon - sun) % 360.0 % 12.0) / 12.0
        elif self._span() == 6.0:
            frac = ((moon - sun) % 360.0 % 6.0) / 6.0
        else:
            frac = (((sun + moon) % 360.0) % (360.0 / 27.0)) / (360.0 / 27.0)
        periods = []
        cursor = birth_jd
        for i in range(len(self.table)):
            lord, _, yrs = self.table[(start_pos + i) % len(self.table)]
            if i == 0:
                cursor = birth_jd - frac * yrs * y_per_d
            dur_days = yrs * y_per_d
            periods.append(DasaPeriod(
                lord_index=lord.value,
                lord_name=lord.full_name,
                start_jd=cursor,
                end_jd=cursor + dur_days,
                duration_years=yrs,
                level=PeriodLevel.MAHADASA,
                sub_periods=None,
            ))
            cursor += dur_days
        return periods


class TithiAshtottariDasa(_IndexDasa):
    """Tithi Ashtottari (108) from janma tithi."""

    table = _TITHI_ASHTOTTARI
    system_name = "tithi-ashtottari"

    def _index(self, chart: Dict) -> int:
        return tithi_index(chart) + 1

    def _span(self) -> float:
        return 12.0


class TithiYoginiDasa(_IndexDasa):
    """Tithi Yogini (36): Yogini lords by tithi."""

    table = _TITHI_YOGINI
    system_name = "tithi-yogini"

    def _index(self, chart: Dict) -> int:
        return tithi_index(chart) + 1

    def _span(self) -> float:
        return 12.0


class KaranaChaturaaseetiDasa(_IndexDasa):
    """Karana Chaturaseeti (84) from karana serial."""

    table = _KARANA_84
    system_name = "karana-chaturaaseeti"

    def _index(self, chart: Dict) -> int:
        return karana_serial(chart)

    def _span(self) -> float:
        return 6.0


class YogaVimsottariDasa(_IndexDasa):
    """Yoga Vimsottari (120) from the yoga point."""

    table = _YOGA_VIMSOTTARI
    system_name = "yoga-vimsottari"

    def _index(self, chart: Dict) -> int:
        return yoga_index(chart)

    def _span(self) -> float:
        return 360.0 / 27.0
