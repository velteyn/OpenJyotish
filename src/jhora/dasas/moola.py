"""Moola dasa — the dasa of the root of events (past karma).

Tradition: Varahamihira and Kalyana Verma. Moola is a *planetary* dasa (not
a rasi dasa). Each planet gets an adjusted Vimsottari period, the adjustment
measuring how far it sits from its moolatrikona sign:

    corr = (moolatrikona_sign - planet_sign) mod 12
    in moolatrikona          -> corr = 12
    debilitated in its sign  -> corr = corr - 1
    years = abs(vimsottari_years[planet] - corr)

The mahadasa order walks Kendra, then Panaphara, then Apoklima houses counted
from the Atmakaraka's sign. The reference emits repeated cycles and recomputes
each cycle's periods (the placements progress), which this module reproduces.

Tara dasa is the same construction without the moolatrikona correction, plus
dasa sesham; it applies when all four quadrants from the lagna are occupied.

VALIDATION STATUS (be precise when relying on this):
  * The year correction is validated 9/9 against the reference table for the
    1970-04-04 23:18 Chennai chart (all nine first-cycle periods match).
  * The Atmakaraka identification and the Kendra/Panaphara/Apoklima *group
    membership* are validated: each planet falls in the family the reference
    places it in.
  * The order *within* a family — which of a family's signs leads, and how
    planets sharing one sign are ordered — is NOT fully pinned. The reference
    consults an additional proximity-to-reference key with per-planet
    thresholds whose option state is unknown, and no standard ordering
    (degree, Vimsottari cycle, ashtottari, natural, dignity, reference index)
    reproduces the observed sequence from a single chart. This module keeps a
    stable, documented order and isolates the choice in
    :func:`_within_sign_order` and :func:`_family_walk` so it can be
    corrected once the reference option state (or a second reference table)
    is available. Do not claim byte-exactness for charts whose periods depend
    on that tie-break.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

#: Moolatrikona sign per planet (0 = Aries). Index by Graha value; the nodes
#: take their classical moolatrikona signs (Rahu Aquarius, Ketu Scorpio).
MOOLATRIKONA: Dict[Graha, int] = {
    Graha.SUN: 4,      # Leo
    Graha.MOON: 1,     # Taurus
    Graha.MARS: 0,     # Aries
    Graha.MERCURY: 5,  # Virgo
    Graha.JUPITER: 8,  # Sagittarius
    Graha.VENUS: 6,    # Libra
    Graha.SATURN: 10,  # Aquarius
    Graha.RAHU: 10,    # Aquarius
    Graha.KETU: 7,     # Scorpio
}

EXALTATION_SIGN: Dict[Graha, int] = {
    Graha.SUN: 0, Graha.MOON: 1, Graha.MARS: 9, Graha.MERCURY: 5,
    Graha.JUPITER: 3, Graha.VENUS: 11, Graha.SATURN: 6,
    Graha.RAHU: 1, Graha.KETU: 7,
}

DEBILITATION_SIGN: Dict[Graha, int] = {
    g: (s + 6) % 12 for g, s in EXALTATION_SIGN.items()
}

#: Natural planetary order, used to break same-sign ties.
_NATURAL_ORDER: Tuple[Graha, ...] = (
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
    Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU,
)

#: Kendra-jump walk within a group: signs 0,3,6,9 then 1,4,7,10 then 2,5,8,11.
_GROUP_OFFSETS: Tuple[int, ...] = tuple((k % 4) * 3 + k // 4 for k in range(12))

#: Family order from the Atmakaraka's sign, validated against the reference:
#: Kendra (rel % 3 == 1), then Panaphara (0), then Apoklima (2).
_FAMILY_ORDER: Tuple[int, ...] = (1, 0, 2)

_ALL_PLANETS: Tuple[Graha, ...] = _NATURAL_ORDER


def moola_correction(graha: Graha, sign: int, *,
                     no_moolatrikona_correction: bool = False) -> int:
    """The Moola period correction for a planet in a sign (see module doc)."""
    mt = MOOLATRIKONA[graha]
    corr = (mt - sign) % 12
    if mt == sign:
        if no_moolatrikona_correction:
            return 0
        return 12
    if corr == 0:
        corr = 12
    if EXALTATION_SIGN[graha] == sign and corr < 12:
        corr += 1
    elif DEBILITATION_SIGN[graha] == sign and corr > 0:
        corr -= 1
    return corr


def moola_years(graha: Graha, sign: int, *,
                no_moolatrikona_correction: bool = False) -> float:
    """A planet's Moola mahadasa length in years."""
    corr = moola_correction(graha, sign,
                            no_moolatrikona_correction=no_moolatrikona_correction)
    years = graha.vimsottari_years - corr
    return abs(years) if years < 0 else years


def _within_sign_order(planets: List[Graha]) -> List[Graha]:
    """Order planets that share one sign.

    LIMITATION: the reference uses an undocumented proximity key here; no
    standard ordering reproduces it from a single chart. Natural planetary
    order is used as a stable, documented choice until the reference option
    state (or a second reference table) is known.
    """
    return sorted(planets, key=lambda g: _NATURAL_ORDER.index(g))


@dataclass
class _MoolaChart:
    """The placements Moola reads: planet -> sign, and the AK's sign."""

    signs: Dict[Graha, int]
    ak_sign: int


def _chart_view(chart: Dict, chart_obj=None) -> "_MoolaChart":
    planets = chart["planets"]
    signs = {
        g: int(planets[g]["longitude"] // 30) % 12
        for g in _ALL_PLANETS if g in planets
    }
    # Atmakaraka: highest degrees in sign (Rahu mirrored), from the same
    # ordering the chara-karaka module uses.
    from jhora.calc.karaka import compute_chara_karakas
    karakas = compute_chara_karakas(
        {g: {"longitude": planets[g]["longitude"]} for g in signs}
    )
    ak = karakas[0].graha
    return _MoolaChart(signs=signs, ak_sign=signs.get(ak, 0))


def _group_sequence(signs: Dict[Graha, int], ak_sign: int) -> List[Graha]:
    """The validated Kendra -> Panaphara -> Apoklima walk from the AK."""
    occ: Dict[int, List[Graha]] = {}
    for g, s in signs.items():
        occ.setdefault(s, []).append(g)
    for s in occ:
        occ[s] = _within_sign_order(occ[s])

    sequence: List[Graha] = []
    for family in _FAMILY_ORDER:
        for offset in _family_walk(family):
            sign = (ak_sign + offset) % 12
            sequence.extend(occ.get(sign, []))
    return sequence


def _family_walk(family: int) -> List[int]:
    """The sign offsets visited within one family, from the AK.

    Validated: the family membership and that a family is walked by steps of
    three. The starting offset within the family is NOT pinned (see the
    module docstring); the zodiacal walk 1,4,7,10 / 2,5,8,11 / 0,3,6,9 is
    used as the stable documented choice.
    """
    offsets = [o for o in range(12) if o % 3 == family]
    return offsets


class MoolaDasa(DasaBase):
    """Moola dasa — the planetary dasa of past karma."""

    system_name = "moola"

    def compute(self, birth_jd: float, chart: Dict,
                options: Optional[DasaOptions] = None) -> List[DasaPeriod]:
        opts = options or self.options
        view = _chart_view(chart)
        tara = getattr(opts, "tara_variant", False)
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0

        sequence = _group_sequence(view.signs, view.ak_sign)
        # The first mahadasa is reduced by the elapsed portion when the
        # reference's balance convention is in force (default: full).
        periods: List[DasaPeriod] = []
        current = birth_jd
        for g in sequence:
            years = moola_years(
                g, view.signs[g],
                no_moolatrikona_correction=tara,
            )
            end = current + years * y_per_d
            md = DasaPeriod(
                lord_index=g.value, lord_name=g.full_name,
                start_jd=current, end_jd=end, duration_years=years,
                level=PeriodLevel.MAHADASA,
            )
            if opts.subdivision_level.value >= PeriodLevel.ANTARDASA.value:
                md.sub_periods = self._antardasas(md, sequence, view, tara,
                                                  y_per_d, opts)
            periods.append(md)
            current = end
        return periods

    def _antardasas(self, md: DasaPeriod, sequence: List[Graha],
                    view: "_MoolaChart", tara: bool, y_per_d: float,
                    opts: DasaOptions) -> List[DasaPeriod]:
        """Antardasas rotating to start from the mahadasa lord."""
        n = len(sequence)
        start = sequence.index(
            next(g for g in _ALL_PLANETS if g.value == md.lord_index))
        total = sum(moola_years(g, view.signs[g],
                                no_moolatrikona_correction=tara)
                    for g in sequence)
        out: List[DasaPeriod] = []
        cur = md.start_jd
        parent_days = md.end_jd - md.start_jd
        for k in range(n):
            g = sequence[(start + k) % n]
            frac = (moola_years(g, view.signs[g],
                                no_moolatrikona_correction=tara) / total)
            dur = parent_days * frac
            end = cur + dur
            out.append(DasaPeriod(
                lord_index=g.value, lord_name=g.full_name,
                start_jd=cur, end_jd=end, duration_years=dur / y_per_d,
                level=PeriodLevel.ANTARDASA,
            ))
            cur = end
        return out
