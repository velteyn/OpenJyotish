"""Moola dasa — the dasa of the root of events (past karma).

Moola is a *planetary* dasa ("root of events / past karma"), associated with
Varahamihira and Kalyana Verma (author of Saravali). Each planet takes a
Vimsottari period adjusted by how far it sits from its moolatrikona sign:

    corr = (moolatrikona_sign - planet_sign) mod 12
    in moolatrikona          -> corr = 12 (0 with the no-correction option)
    exalted in its sign      -> corr = corr + 1
    debilitated in its sign  -> corr = corr - 1
    years = abs(vimsottari_years[planet] - corr)
    years == 0               -> the full vimsottari period

The mahadasa *order* follows the mainstream planetary practice:

* the cycle is anchored at the sign holding the **most bodies among the Lagna,
  Sun and Moon** (the three reference points; the most occupied of the three
  leads, ties resolved by sign strength below). Any of the three can be
  dropped with the ``moola_use_lagna`` / ``moola_use_sun`` / ``moola_use_moon``
  switches, in which case its sign counts as empty for the anchor;
* from that sign the dasa walks the **kendra jumps** — 1st, 4th, 7th, 10th,
  then 2nd, 5th, 8th, 11th, then 3rd, 6th, 9th, 12th — in three four-sign
  groups;
* within each group the signs are ranked by the number of planets they hold,
  then by exaltation/debilitation counts, then by the sign's own/ruled
  strength and modality;
* within a sign, planets are ranked by dignity — exalted, then non-debilitated,
  then own sign, then rulership — and finally by longitude;
* the antardasas rotate the mahadasa order to start at the mahadasa lord.

Tara dasa is a planetary dasa for charts whose four quadrants from the lagna
are all occupied. It has two definitions (selectable): **Parasara's** — the
Vimsottari planetary sequence starting from the lord of the 9th sign from the
lagna — and **Pt Sanjay Rath's** — the Moola sign-family walk anchored at the
lagna. Both use the full Vimsottari years, and both can apply a **dasa
sesham** (the first mahadasa's balance from the Moon's nakshatra fraction,
optionally reversed for apasavya nakshatras). The `TaraDasaDirectionFromStar`
option reckons the walk direction from the nakshatra instead of the sign.

The node exaltations use the Saravali/Parasara reading (Rahu in Gemini, Ketu in
Sagittarius); the nodes' own signs are Rahu in Virgo and Ketu in Pisces.

VALIDATION STATUS (be precise when relying on this):
  * The year correction is validated nine for nine on the 1970-04-04 23:18
    Chennai chart.
  * The mahadasa order is validated against the reference sequence for the
    1970 chart: Sun, Moon, Rahu, Ketu, Mars, Venus, Mercury, Saturn, Jupiter
    (years 1, 8, 6, 4, 5, 14, 12, 10, 14).
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha

#: Moolatrikona sign per planet (0 = Aries).
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
    Graha.RAHU: 2, Graha.KETU: 8,
}

DEBILITATION_SIGN: Dict[Graha, int] = {
    g: (s + 6) % 12 for g, s in EXALTATION_SIGN.items()
}

#: Own sign per planet (nodes: Rahu Virgo, Ketu Pisces).
OWN_SIGN: Dict[Graha, int] = {
    Graha.SUN: 4, Graha.MOON: 1, Graha.MARS: 0, Graha.MERCURY: 5,
    Graha.JUPITER: 8, Graha.VENUS: 6, Graha.SATURN: 10,
    Graha.RAHU: 5, Graha.KETU: 11,
}

#: Ruler of each sign (0 = Aries). Rahu co-rules Aquarius, Ketu co-rules
#: Scorpio; those are added in :func:`_rules`.
_SIGN_LORD: Tuple[Graha, ...] = (
    Graha.MARS, Graha.VENUS, Graha.MERCURY, Graha.MOON, Graha.SUN,
    Graha.MERCURY, Graha.VENUS, Graha.MARS, Graha.JUPITER, Graha.SATURN,
    Graha.SATURN, Graha.JUPITER,
)

_ALL_PLANETS: Tuple[Graha, ...] = (
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
    Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU,
)

_AQUARIUS = 10
_SCORPIO = 7


def moola_correction(graha: Graha, sign: int, *,
                     no_moolatrikona_correction: bool = False) -> int:
    """The Moola period correction for a planet in a sign.

    The starting value is ``(moolatrikona - sign) mod 12``; a planet in its
    moolatrikona sign takes 12 (or 0 with the no-correction option, which
    also short-circuits to the full period in :func:`moola_years`); then
    exaltation adds one and debilitation subtracts one.
    """
    mt = MOOLATRIKONA[graha]
    corr = (mt - sign) % 12
    if mt == sign:
        if no_moolatrikona_correction:
            return 0
        return 12
    if EXALTATION_SIGN[graha] == sign and corr < 12:
        corr += 1
    if DEBILITATION_SIGN[graha] == sign and corr > 0:
        corr -= 1
    return corr


def moola_years(graha: Graha, sign: int, *,
                no_moolatrikona_correction: bool = False) -> float:
    """A planet's Moola mahadasa length in years.

    The correction (see :func:`moola_correction`) is subtracted from the
    planet's Vimsottari period; a negative remainder is taken as its
    magnitude, and a zero remainder falls back to the full Vimsottari period.
    """
    corr = moola_correction(graha, sign,
                            no_moolatrikona_correction=no_moolatrikona_correction)
    years = graha.vimsottari_years - corr
    if years < 0:
        years = -years
    if years == 0:
        years = graha.vimsottari_years
    return years


# ---------------------------------------------------------------------------
# Ordering — the sign/planet comparison keys behind the mahadasa sequence.
# ---------------------------------------------------------------------------

def _rules(graha: Graha, sign: int) -> bool:
    """Whether ``graha`` rules ``sign`` (nodes co-rule Aquarius / Scorpio)."""
    if _SIGN_LORD[sign] == graha:
        return True
    if graha is Graha.RAHU and sign == _AQUARIUS:
        return True
    if graha is Graha.KETU and sign == _SCORPIO:
        return True
    return False


def _match(a: int, b: int) -> int:
    """Sign-relationship predicate used by the sign-strength score."""
    if a == b:
        return 1
    ra, rb = a % 3, b % 3
    if ra == 0 and rb == 1 and (a + 1) % 12 != b and (b + 1) % 12 != a:
        return 1
    if ra == 1 and rb == 0 and (a + 1) % 12 != b and (b + 1) % 12 != a:
        return 1
    if ra == 2 and rb == 2:
        return 1
    return 0


def _associated_sign(graha: Graha) -> int:
    if graha in (Graha.SATURN, Graha.RAHU):
        return _AQUARIUS
    if graha in (Graha.MARS, Graha.KETU):
        return _SCORPIO
    return 0


def _session_key(graha: Graha, view: "_MoolaChart") -> int:
    sign = view.signs[graha]
    assoc = _associated_sign(graha)
    forward = (assoc // 3) & 1
    delta = (assoc - sign + 12) if forward else (sign - assoc + 12)
    value = delta % 12
    if EXALTATION_SIGN[graha] == sign and value < 12:
        value += 1
    if DEBILITATION_SIGN[graha] == sign and value > 0:
        value -= 1
    return value


def _co_lord_choice(a: Graha, b: Graha, view: "_MoolaChart") -> Graha:
    """Resolve a co-ruled sign's lord between ``a`` and ``b``."""
    sa, sb = view.signs[a], view.signs[b]
    aa, ab = _associated_sign(a), _associated_sign(b)
    if (sa == aa) != (sb == ab):
        return b if sa == aa else a
    ca = sum(1 for g in _ALL_PLANETS if view.signs[g] == sa)
    cb = sum(1 for g in _ALL_PLANETS if view.signs[g] == sb)
    if ca != cb:
        return a if ca > cb else b
    va, vb = _sign_score(sa, view), _sign_score(sb, view)
    if va != vb:
        return a if va > vb else b
    if (EXALTATION_SIGN[a] == sa) != (EXALTATION_SIGN[b] == sb):
        return a if EXALTATION_SIGN[a] == sa else b
    if (DEBILITATION_SIGN[a] == sa) != (DEBILITATION_SIGN[b] == sb):
        return a if DEBILITATION_SIGN[a] != sa else b
    if sa % 3 != sb % 3:
        return a if sa % 3 > sb % 3 else b
    return a if _session_key(a, view) >= _session_key(b, view) else b


def _sign_lord(sign: int, view: "_MoolaChart") -> Graha:
    if sign == _AQUARIUS:
        return _co_lord_choice(Graha.SATURN, Graha.RAHU, view)
    if sign == _SCORPIO:
        return _co_lord_choice(Graha.MARS, Graha.KETU, view)
    return _SIGN_LORD[sign]


def _sign_score(sign: int, view: "_MoolaChart") -> int:
    """A sign's ruled/owned strength score used by the sign comparator.

    Uses the *static* sign-lord table (the co-lord is not resolved here — that
    would recurse through :func:`_co_lord_choice`).
    """
    lord = _SIGN_LORD[sign]
    score = _match(sign, view.signs[Graha.MERCURY])
    score += _match(sign, view.signs[Graha.JUPITER])
    if _match(sign, view.signs[lord]):
        score += 1
    elif sign == _SCORPIO:
        score += _match(sign, view.signs[Graha.KETU])
    elif sign == _AQUARIUS:
        score += _match(sign, view.signs[Graha.RAHU])
    return score


def _sign_key(sign: int, view: "_MoolaChart") -> Tuple:
    """Sort key (higher first) for signs within a four-sign group."""
    occupants = [g for g in _ALL_PLANETS if view.signs[g] == sign]
    lord = _sign_lord(sign, view)
    lord_sign = view.signs[lord]
    lord_lon = view.lon[lord] - lord_sign * 30
    if lord in (Graha.RAHU, Graha.KETU):
        lord_lon = 30 - lord_lon
    return (
        len(occupants),
        sum(1 for g in occupants if EXALTATION_SIGN[g] == sign),
        -sum(1 for g in occupants if DEBILITATION_SIGN[g] == sign),
        _sign_score(sign, view),
        int((sign & 1) != (lord_sign & 1)),
        sign % 3,
        lord_lon,
    )


def _planet_key(graha: Graha, view: "_MoolaChart") -> Tuple:
    """Sort key (higher first) for planets sharing a sign."""
    sign = view.signs[graha]
    lon = view.lon[graha] - sign * 30
    if graha in (Graha.RAHU, Graha.KETU):
        lon = 30 - lon
    return (
        EXALTATION_SIGN[graha] == sign,
        DEBILITATION_SIGN[graha] != sign,
        OWN_SIGN[graha] == sign,
        _rules(graha, sign),
        lon,
    )


def _insertion_sort(items: Sequence, before: Callable[[object, object], bool]):
    """Insertion sort — mirrors the reference sort, stable and deterministic."""
    out = list(items)
    for i in range(1, len(out)):
        item = out[i]
        j = i
        while j > 0 and before(item, out[j - 1]):
            out[j] = out[j - 1]
            j -= 1
        out[j] = item
    return out


@dataclass
class _MoolaChart:
    """The placements Moola reads: planet -> sign/longitude, and the lagna."""

    signs: Dict[Graha, int]
    lon: Dict[Graha, float]
    lagna_sign: int


def _chart_view(chart: Dict) -> "_MoolaChart":
    planets = chart["planets"]
    signs = {
        g: int(planets[g]["longitude"] // 30) % 12
        for g in _ALL_PLANETS if g in planets
    }
    lon = {g: float(planets[g]["longitude"]) for g in signs}
    lagna = chart.get("lagna_lon")
    if lagna is None:
        lagna = chart.get("ascendant", 0.0)
    lagna_sign = int(lagna // 30) % 12
    return _MoolaChart(signs=signs, lon=lon, lagna_sign=lagna_sign)


def _select_base(view: "_MoolaChart", opts: DasaOptions) -> int:
    """The sign with the most bodies among the enabled Lagna/Moon/Sun signs.

    Disabling a reference treats its sign as empty (value zero), exactly as the
    inclusion switches do.
    """
    occupants: Dict[int, int] = {}
    for g in _ALL_PLANETS:
        occupants[view.signs[g]] = occupants.get(view.signs[g], 0) + 1

    def bodies(sign: int) -> int:
        return occupants.get(sign, 0) + (1 if sign == view.lagna_sign else 0)

    lagna_sign = view.lagna_sign
    moon_sign = view.signs[Graha.MOON]
    sun_sign = view.signs[Graha.SUN]
    values = [
        (lagna_sign, bodies(lagna_sign) if opts.moola_use_lagna else 0),
        (moon_sign, bodies(moon_sign) if opts.moola_use_moon else 0),
        (sun_sign, bodies(sun_sign) if opts.moola_use_sun else 0),
    ]
    best = values[0][1]
    tied = [values[0][0]]
    for sign, value in values[1:]:
        if value > best:
            best = value
            tied = [sign]
        elif value == best:
            tied.append(sign)
    tied = list(dict.fromkeys(tied))
    tied = _insertion_sort(
        tied, lambda a, b: _sign_key(a, view) > _sign_key(b, view))
    return tied[0]


def _group_sequence(view: "_MoolaChart",
                    opts: Optional[DasaOptions] = None) -> List[Graha]:
    """The mahadasa order (the exact reference sequence)."""
    opts = opts or DasaOptions()
    base = _select_base(view, opts)
    jump = lambda k: 3 * (k % 4) + k // 4          # 0,3,6,9,1,4,7,10,2,5,8,11
    step = 1 if base % 2 == 0 else -1

    def before_sign(a, b):
        return _sign_key(a, view) > _sign_key(b, view)

    def before_planet(a, b):
        return _planet_key(a, view) > _planet_key(b, view)

    sequence: List[Graha] = []
    for chunk in range(3):
        group = [(base + step * jump(chunk * 4 + i)) % 12 for i in range(4)]
        for sign in _insertion_sort(group, before_sign):
            planets = [g for g in _ALL_PLANETS if view.signs[g] == sign]
            sequence.extend(_insertion_sort(planets, before_planet))
    return sequence


#: The Vimsottari planetary sequence (the order of the 120-year cycle).
_VIMSOTTARI_SEQUENCE: Tuple[Graha, ...] = (
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.RAHU, Graha.JUPITER,
    Graha.SATURN, Graha.MERCURY, Graha.KETU, Graha.VENUS,
)
_NAKSHATRA_SPAN = 360.0 / 27.0


def _tara_direction(view: "_MoolaChart", opts: DasaOptions) -> int:
    """Direction of the Tara dasa (+1 forward, -1 reverse)."""
    if getattr(opts, "tara_direction_from_star", False):
        nakshatra = int(view.lon[Graha.MOON] // _NAKSHATRA_SPAN) % 27
        return -1 if (nakshatra // 3) % 2 else 1
    return 1 if view.lagna_sign % 2 == 0 else -1


def _tara_sequence(view: "_MoolaChart", opts: DasaOptions) -> List[Graha]:
    """The Tara mahadasa order for the chosen definition.

    * ``parasara``: the Vimsottari sequence starting from the lord of the 9th
      sign from the lagna.
    * ``rath``: the Moola sign-family walk from the lagna (sign/planet
      comparators), the planets of each sign in order.
    """
    step = _tara_direction(view, opts)
    if getattr(opts, "tara_definition", "parasara") == "rath":
        before_sign = lambda a, b: _sign_key(a, view) > _sign_key(b, view)
        before_planet = lambda a, b: _planet_key(a, view) > _planet_key(b, view)
        jump = lambda k: 3 * (k % 4) + k // 4
        sequence: List[Graha] = []
        for chunk in range(3):
            group = [(view.lagna_sign + step * jump(chunk * 4 + i)) % 12
                     for i in range(4)]
            for sign in _insertion_sort(group, before_sign):
                sequence.extend(_insertion_sort(
                    [g for g in _ALL_PLANETS if view.signs[g] == sign],
                    before_planet))
        return sequence
    lord = _SIGN_LORD[(view.lagna_sign + 8) % 12]
    start = _VIMSOTTARI_SEQUENCE.index(lord)
    sequence = list(_VIMSOTTARI_SEQUENCE[start:] + _VIMSOTTARI_SEQUENCE[:start])
    if step < 0:
        sequence = list(reversed(sequence))
    return sequence


class MoolaDasa(DasaBase):
    """Moola dasa — the planetary dasa of past karma."""

    system_name = "moola"

    def compute(self, birth_jd: float, chart: Dict,
                options: Optional[DasaOptions] = None) -> List[DasaPeriod]:
        opts = options or self.options
        view = _chart_view(chart)
        if getattr(opts, "tara_variant", False):
            return self._compute_tara(birth_jd, view, opts)
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0

        sequence = _group_sequence(view, opts)
        periods: List[DasaPeriod] = []
        current = birth_jd
        for g in sequence:
            years = moola_years(g, view.signs[g])
            end = current + years * y_per_d
            md = DasaPeriod(
                lord_index=g.value, lord_name=g.full_name,
                start_jd=current, end_jd=end, duration_years=years,
                level=PeriodLevel.MAHADASA,
            )
            if opts.subdivision_level.value >= PeriodLevel.ANTARDASA.value:
                md.sub_periods = self._antardasas(md, sequence, view, False,
                                                  y_per_d, opts)
            periods.append(md)
            current = end
        return periods

    # -- Tara ---------------------------------------------------------------

    def _compute_tara(self, birth_jd: float, view: "_MoolaChart",
                      opts: DasaOptions) -> List[DasaPeriod]:
        sequence = _tara_sequence(view, opts)
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        years = {g: g.vimsottari_years for g in sequence}

        # Dasa sesham: the first mahadasa's balance is the Moon's nakshatra
        # fraction remaining at birth (optional; reversed for apasavya
        # nakshatras if the option asks).
        start = birth_jd
        if getattr(opts, "tara_use_sesham", True):
            fraction = 1.0 - (view.lon[Graha.MOON] % _NAKSHATRA_SPAN) / _NAKSHATRA_SPAN
            nakshatra = int(view.lon[Graha.MOON] // _NAKSHATRA_SPAN) % 27
            if (getattr(opts, "tara_sesham_rev_apasavya", False)
                    and (nakshatra // 3) % 2 == 1):
                fraction = 1.0 - fraction
            first = sequence[0]
            start = birth_jd - (1.0 - fraction) * years[first] * y_per_d

        periods: List[DasaPeriod] = []
        current = start
        for g in sequence:
            end = current + years[g] * y_per_d
            md = DasaPeriod(
                lord_index=g.value, lord_name=g.full_name,
                start_jd=current, end_jd=end, duration_years=years[g],
                level=PeriodLevel.MAHADASA,
            )
            if opts.subdivision_level.value >= PeriodLevel.ANTARDASA.value:
                md.sub_periods = self._tara_antardasas(md, sequence, years,
                                                       y_per_d)
            periods.append(md)
            current = end
        return periods

    def _tara_antardasas(self, md: DasaPeriod, sequence: List[Graha],
                         years: Dict[Graha, float],
                         y_per_d: float) -> List[DasaPeriod]:
        """Antardasas rotate the Tara order to start at the mahadasa lord."""
        n = len(sequence)
        start = sequence.index(
            next(g for g in _ALL_PLANETS if g.value == md.lord_index))
        total = sum(years.values())
        out: List[DasaPeriod] = []
        cur = md.start_jd
        parent_days = md.end_jd - md.start_jd
        for k in range(n):
            g = sequence[(start + k) % n]
            dur = parent_days * years[g] / total
            end = cur + dur
            out.append(DasaPeriod(
                lord_index=g.value, lord_name=g.full_name,
                start_jd=cur, end_jd=end, duration_years=dur / y_per_d,
                level=PeriodLevel.ANTARDASA,
            ))
            cur = end
        return out


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
