"""Conditional nakshatra dasas (BPHS): applicability-gated timing systems.

Nine BPHS systems (the PVR unified paper as the mainstream statement;
BPHS verses via the Santhanam translation cross-checked):

- Ashtottari (108) lives in ``ashtottari.py``.
- Eight live here: Shodasottari (116), Dwadasottari (112),
  Panchottari (105), Sataabdika (100), Chaturaaseeti (84),
  Dwisaptati (72), Shashtihayani (60), Shattrimsa (36).

Each system has a seed nakshatra, a lord order with fixed durations,
a counting direction, and a TRUE positional applicability gate
(lagna hora/navamsa/dwadasamsa, planetary placements, paksha and
day/night) — not just the Moon nakshatra. Tithi Ashtottari and
Karana Chaturaseeti are pravesha-chart dasas and stay deferred until
Tithi/Karana Pravesha chart support exists (gap Priority 3 #11);
shipping them for natal charts would invite misuse.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from jhora.charts.chart import ChartData
from jhora.dasas.base import DasaOptions
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha


def hora_lord(lagna_lon: float) -> str:
    """Hora ruler of the lagna: Sun/Moon by half-sign (standard hora)."""
    sign = int(lagna_lon // 30) % 12
    first_half = (lagna_lon % 30.0) < 15.0
    if sign % 2 == 0:  # odd sign: Sun then Moon
        return "Sun" if first_half else "Moon"
    return "Moon" if first_half else "Sun"


def paksha(sun_lon: float, moon_lon: float) -> str:
    """Shukla (waxing) or Krishna (waning) half of the lunar month."""
    return "Shukla" if (moon_lon - sun_lon) % 360.0 < 180.0 else "Krishna"


def navamsa_sign(lon: float) -> int:
    """0-based rasi index of the navamsa position."""
    return int(lon * 9.0 // 30.0) % 12


def dwadasamsa_sign(lon: float) -> int:
    """0-based rasi index of the dwadasamsa position."""
    return int(lon * 12.0 // 30.0) % 12


@dataclass
class ConditionalDasa:
    name: str
    total_years: int
    planets: List[Graha]
    durations: Dict[Graha, float]
    order: List[Graha]
    seed_nak: int = 0          # 0-based birth-nakshatra seed of order[0]
    direction: int = 1         # +1 zodiacal, -1 anti-zodiacal counting
    nak_lords: Optional[Dict[int, Graha]] = None  # explicit map (Shashtihayani)
    condition: str = ""        # human-readable applicability gate

    def lord_for_nak(self, nak: int) -> Graha:
        """Start lord for a birth nakshatra (0-26)."""
        if self.nak_lords is not None:
            if nak in self.nak_lords:
                return self.nak_lords[nak]
            # Chitra (13) has no pada in the BPHS Shashtihayani map;
            # fall back to the universal (Vimsottari) lord, documented.
            from jhora.types.nakshatra import Nakshatra
            return Nakshatra(nak).lord
        k = ((nak - self.seed_nak) * self.direction) % 27
        return self.order[k % len(self.order)]

    def is_applicable(self, ctx: dict) -> bool:
        """Positional gate; overridden per system below."""
        return ctx.get("moon_nak", -1) >= 0

    def compute(self, birth_jd: float, chart: dict,
                opts: Optional[DasaOptions] = None) -> List[DasaPeriod]:
        """Mahadashas from the birth nakshatra with pada balance."""
        from jhora.types.nakshatra import Nakshatra
        o = opts or DasaOptions()
        y_per_d = 365.2425 if o.year_definition == "solar" else 360.0
        moon = chart["planets"][Graha.MOON]["longitude"]
        nak = int(moon / (360.0 / 27.0)) % 27
        span = 360.0 / 27.0
        pada = int(((moon % span) / (span * 0.25)))
        start_lord = self.lord_for_nak(nak)
        start_idx = self.order.index(start_lord)
        periods = []
        current_jd = birth_jd
        for i in range(len(self.order)):
            g = self.order[(start_idx + i) % len(self.order)]
            dur = self.durations[g]
            if i == 0:
                elapsed = pada * 0.25 * dur
                current_jd = birth_jd - elapsed * y_per_d
            end_jd = current_jd + dur * y_per_d
            periods.append(DasaPeriod(
                lord_index=g.value,
                lord_name=g.full_name,
                start_jd=current_jd,
                end_jd=end_jd,
                duration_years=dur,
                level=PeriodLevel.MAHADASA,
                sub_periods=None,
            ))
            current_jd = end_jd
        return periods


def _ctx(chart: ChartData) -> dict:
    """Gate context: positions, vargas, paksha, hora, day/night."""
    from jhora.dasas.jaimini_common import normalize_planets, planet_signs
    planets = normalize_planets(
        {g: {"longitude": p.longitude} for g, p in chart.planets.items()})
    sigs = planet_signs(planets)
    moon_lon = planets[Graha.MOON]
    sun_lon = planets[Graha.SUN]
    lagna = int(chart.ascendant // 30) % 12
    try:
        from jhora.calc.sahama import is_day_birth
        day = is_day_birth(chart)
    except Exception:
        day = True
    return {
        "moon_nak": int(moon_lon / (360.0 / 27.0)) % 27,
        "lagna": lagna,
        "signs": sigs,
        "nav_lagna": navamsa_sign(chart.ascendant),
        "d12_lagna": dwadasamsa_sign(chart.ascendant),
        "paksha": paksha(sun_lon, moon_lon),
        "hora": hora_lord(chart.ascendant),
        "day": day,
    }


def _house_lord(sign: int) -> Graha:
    from jhora.dasas.jaimini_common import _single_lord
    return _single_lord(sign)


@dataclass
class _GatedDasa(ConditionalDasa):
    gate: str = ""

    def is_applicable(self, ctx: dict) -> bool:
        sigs = ctx["signs"]
        lagna = ctx["lagna"]
        if self.gate == "dwisaptati":
            # Lagna lord in 7th, or 7th lord in lagna.
            sev = (lagna + 6) % 12
            return (sigs.get(_house_lord(lagna)) == sev
                    or sigs.get(_house_lord(sev)) == lagna)
        if self.gate == "shodasottari":
            return ((ctx["hora"] == "Sun" and ctx["paksha"] == "Shukla")
                    or (ctx["hora"] == "Moon" and ctx["paksha"] == "Krishna"))
        if self.gate == "dwadasottari":
            return ctx["nav_lagna"] in (1, 6)  # Taurus/Libra navamsa
        if self.gate == "panchottari":
            return lagna == 3 and ctx["d12_lagna"] == 3  # Cancer both
        if self.gate == "shashtihayani":
            return sigs.get(Graha.SUN) == lagna
        if self.gate == "sataabdika":
            return ctx["nav_lagna"] == lagna  # vargottama lagna
        if self.gate == "chaturaaseeti":
            tenth = (lagna + 9) % 12
            return sigs.get(_house_lord(tenth)) == tenth
        if self.gate == "shattrimsa":
            return ((ctx["hora"] == "Sun" and ctx["day"])
                    or (ctx["hora"] == "Moon" and not ctx["day"]))
        return super().is_applicable(ctx)


_C8_NOKETU = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU]

DWISAPTATI = _GatedDasa(
    name="Dwisaptati Sama", total_years=72, planets=_C8_NOKETU,
    durations={g: 9.0 for g in _C8_NOKETU},
    order=list(_C8_NOKETU), seed_nak=18, direction=1, gate="dwisaptati",
    condition="Lagna lord in 7th, or 7th lord in lagna (seed Moola)",
)

SHODASOTTARI = _GatedDasa(
    name="Shodasottari", total_years=116,
    planets=[Graha.SUN, Graha.MARS, Graha.JUPITER, Graha.SATURN,
             Graha.KETU, Graha.MOON, Graha.MERCURY, Graha.VENUS],
    durations={Graha.SUN: 11.0, Graha.MARS: 12.0, Graha.JUPITER: 13.0,
               Graha.SATURN: 14.0, Graha.KETU: 15.0, Graha.MOON: 16.0,
               Graha.MERCURY: 17.0, Graha.VENUS: 18.0},
    order=[Graha.SUN, Graha.MARS, Graha.JUPITER, Graha.SATURN,
           Graha.KETU, Graha.MOON, Graha.MERCURY, Graha.VENUS],
    seed_nak=7, direction=1, gate="shodasottari",
    condition="Lagna in Sun hora + Shukla paksha, or Moon hora + "
              "Krishna paksha (seed Pushya)",
)

DWADASOTTARI = _GatedDasa(
    name="Dwadasottari", total_years=112,
    planets=[Graha.SUN, Graha.JUPITER, Graha.KETU, Graha.MERCURY,
             Graha.RAHU, Graha.MARS, Graha.SATURN, Graha.MOON],
    durations={Graha.SUN: 7.0, Graha.JUPITER: 9.0, Graha.KETU: 11.0,
               Graha.MERCURY: 13.0, Graha.RAHU: 15.0, Graha.MARS: 17.0,
               Graha.SATURN: 19.0, Graha.MOON: 21.0},
    order=[Graha.SUN, Graha.JUPITER, Graha.KETU, Graha.MERCURY,
           Graha.RAHU, Graha.MARS, Graha.SATURN, Graha.MOON],
    seed_nak=26, direction=-1, gate="dwadasottari",
    condition="Lagna in Taurus/Libra navamsa (seed Revati, "
              "anti-zodiacal count)",
)

PANCHOTTARI = _GatedDasa(
    name="Panchottari", total_years=105,
    planets=[Graha.SUN, Graha.MERCURY, Graha.SATURN, Graha.MARS,
             Graha.VENUS, Graha.MOON, Graha.JUPITER],
    durations={Graha.SUN: 12.0, Graha.MERCURY: 13.0, Graha.SATURN: 14.0,
               Graha.MARS: 15.0, Graha.VENUS: 16.0, Graha.MOON: 17.0,
               Graha.JUPITER: 18.0},
    order=[Graha.SUN, Graha.MERCURY, Graha.SATURN, Graha.MARS,
           Graha.VENUS, Graha.MOON, Graha.JUPITER],
    seed_nak=16, direction=1, gate="panchottari",
    condition="Lagna Cancer in rasi and dwadasamsa (seed Anuradha)",
)

SHASHTIHAYANI = _GatedDasa(
    name="Shashtihayani", total_years=60,
    planets=[Graha.JUPITER, Graha.SUN, Graha.MARS, Graha.MOON,
             Graha.MERCURY, Graha.VENUS, Graha.SATURN, Graha.RAHU],
    durations={Graha.JUPITER: 10.0, Graha.SUN: 10.0, Graha.MARS: 10.0,
               Graha.MOON: 6.0, Graha.MERCURY: 6.0, Graha.VENUS: 6.0,
               Graha.SATURN: 6.0, Graha.RAHU: 6.0},
    order=[Graha.JUPITER, Graha.SUN, Graha.MARS, Graha.MOON,
           Graha.MERCURY, Graha.VENUS, Graha.SATURN, Graha.RAHU],
    seed_nak=0, direction=1, gate="shashtihayani",
    condition="Sun in lagna",
    nak_lords={0: Graha.JUPITER, 1: Graha.JUPITER, 2: Graha.JUPITER,
               6: Graha.JUPITER, 3: Graha.SUN, 4: Graha.SUN,
               5: Graha.SUN, 20: Graha.SUN, 7: Graha.MARS,
               8: Graha.MARS, 9: Graha.MARS, 26: Graha.MARS,
               10: Graha.MOON, 11: Graha.MOON, 12: Graha.MOON,
               14: Graha.MERCURY, 15: Graha.MERCURY, 16: Graha.MERCURY,
               17: Graha.VENUS, 18: Graha.VENUS, 19: Graha.VENUS,
               21: Graha.SATURN, 22: Graha.SATURN, 23: Graha.RAHU,
               24: Graha.RAHU, 25: Graha.RAHU},
)

SATAABDIKA = _GatedDasa(
    name="Sataabdika", total_years=100,
    planets=[Graha.SUN, Graha.MOON, Graha.VENUS, Graha.MERCURY,
             Graha.JUPITER, Graha.MARS, Graha.SATURN],
    durations={Graha.SUN: 5.0, Graha.MOON: 5.0, Graha.VENUS: 10.0,
               Graha.MERCURY: 10.0, Graha.JUPITER: 20.0,
               Graha.MARS: 20.0, Graha.SATURN: 30.0},
    order=[Graha.SUN, Graha.MOON, Graha.VENUS, Graha.MERCURY,
           Graha.JUPITER, Graha.MARS, Graha.SATURN],
    seed_nak=26, direction=1, gate="sataabdika",
    condition="Lagna vargottama: same sign in rasi and navamsa "
              "(seed Revati)",
)

CHATURAASEETI = _GatedDasa(
    name="Chaturaaseeti Sama", total_years=84,
    planets=[Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
             Graha.JUPITER, Graha.VENUS, Graha.SATURN],
    durations={g: 12.0 for g in [Graha.SUN, Graha.MOON, Graha.MARS,
                                 Graha.MERCURY, Graha.JUPITER,
                                 Graha.VENUS, Graha.SATURN]},
    order=[Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
           Graha.JUPITER, Graha.VENUS, Graha.SATURN],
    seed_nak=14, direction=1, gate="chaturaaseeti",
    condition="10th lord in 10th (seed Swati)",
)

SHATTRIMSA = _GatedDasa(
    name="Shattrimsa Sama", total_years=36,
    planets=[Graha.MOON, Graha.SUN, Graha.JUPITER, Graha.MARS,
             Graha.MERCURY, Graha.SATURN, Graha.VENUS, Graha.RAHU],
    durations={Graha.MOON: 1.0, Graha.SUN: 2.0, Graha.JUPITER: 3.0,
               Graha.MARS: 4.0, Graha.MERCURY: 5.0, Graha.SATURN: 6.0,
               Graha.VENUS: 7.0, Graha.RAHU: 8.0},
    order=[Graha.MOON, Graha.SUN, Graha.JUPITER, Graha.MARS,
           Graha.MERCURY, Graha.SATURN, Graha.VENUS, Graha.RAHU],
    seed_nak=21, direction=1, gate="shattrimsa",
    condition="Lagna in Sun hora by day, or Moon hora by night "
              "(seed Sravana)",
)

ALL_CONDITIONAL = {
    "dwisaptati": DWISAPTATI,
    "shodasottari": SHODASOTTARI,
    "dwadasottari": DWADASOTTARI,
    "panchottari": PANCHOTTARI,
    "shashtihayani": SHASHTIHAYANI,
    "sataabdika": SATAABDIKA,
    "chaturaaseeti": CHATURAASEETI,
    "shattrimsa": SHATTRIMSA,
}


def list_applicable(chart: ChartData) -> List[dict]:
    """List which conditional dasas apply to a chart (true gates)."""
    ctx = _ctx(chart)
    results = []
    for key, dasa in ALL_CONDITIONAL.items():
        if dasa.is_applicable(ctx):
            results.append({
                "name": key,
                "full_name": dasa.name,
                "total_years": dasa.total_years,
                "condition": dasa.condition,
            })
    return results
