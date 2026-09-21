"""
DasaBase — abstract base class for all dasa systems.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from jhora.types.dasa import DasaPeriod, PeriodLevel


@dataclass
class DasaOptions:
    """Configuration options for dasa computation.

    Shared across all dasa systems. Nakshatra dasas (Vimsottari, Ashtottari,
    Yogini, etc.) interpret ``start_variation``, ``sesham_method`` and
    ``year_definition``.
    """
    year_definition: str = "solar"           # solar (365.2425d), savana (360d), tithi (354.367d)

    #: Which body/reference seeds the nakshatra dasa cycle:
    #:   moon      - from Moon's nakshatra (standard)
    #:   lagna     - from Lagna's nakshatra
    #:   sun       - from Sun's nakshatra
    #:   kshema    - from the Kshema tara (4th nakshatra) from Moon
    #:   utpanna   - from the Utpanna tara (5th nakshatra) from Moon
    #:   adhana    - from the Aadhaana tara (8th nakshatra) from Moon
    #:   maandi    - from the Maandi (Gulika) position (needs its longitude)
    #:   trisphuta - from the Trisphuta longitude (Lagna + Moon + Gulika)
    #:   devi      - from the 7th nakshatra (Devi tara) from Moon
    #:   brahma    - from the 9th nakshatra (Brahma tara) from Moon
    start_variation: str = "moon"

    #: Antardasa construction method for nakshatra dasas:
    #:   rao_rath    - rotate sub-periods to start at the parent lord (default)
    #:   raman       - Dr. Raman first-fraction (sub-periods from the MD lord,
    #:                 first sub halved at the start of the cycle)
    #:   continuous  - each sub-period starts where the previous ended, in the
    #:                 MD lord's order (no re-anchoring)
    #:   raghavacharya - navamsa progression (sub-periods follow the navamsa
    #:                 order from the seed nakshatra)
    ad_method: str = "rao_rath"

    #: How the first mahadasa's duration is handled:
    #:   moon  - reduce first MD by the fraction of Moon's nakshatra remaining
    #:   full  - every MD gets its full year count (cycle totals 120 years)
    sesham_method: str = "moon"

    subdivision_level: PeriodLevel = PeriodLevel.PRATYANTARDASA
    include_subperiods: bool = True
    custom_sequence: Optional[List[int]] = None

    #: Which chara karaka seeds Karaka Dasa ("Putra", "Matri", "Bhratri",
    #: "Dara"); other systems ignore it.
    karaka_role: str = "Dara"

    #: Narayana-dasa variant: "base" (default), "sama", "paka" or "ayur".
    narayana_variant: str = "base"
    #: Narayana-dasa chart seed: None/"D-1" (default), or a varga label such
    #: as "D-9"/"D-60"/"D-144". The caller supplies the seed chart's lord
    #: longitudes in the chart dict under "seed_varga_positions".
    narayana_chart: Optional[str] = None

    #: Which house seeds Shoola Dasa (1 = self/lagna, 9 = Pitri/father,
    #: 7 = Dara/spouse, 5 = Putra/children); other systems ignore it.
    seed_house: int = 1


class DasaBase(ABC):
    """Abstract base for all dasa system implementations."""

    system_name: str = "base"

    def __init__(self, options: Optional[DasaOptions] = None):
        self.options = options or DasaOptions()

    @abstractmethod
    def compute(self, birth_jd: float, chart: Dict, options: DasaOptions) -> List[DasaPeriod]:
        """Compute the full dasa period tree.
        
        Args:
            birth_jd: Julian day of birth (UT)
            chart: Chart data dict with planet positions, etc.
            options: Dasa computation options
            
        Returns:
            List of DasaPeriod (MDs with nested sub-periods)
        """
        ...

    @staticmethod
    def get_active_period(periods: List[DasaPeriod], target_jd: float) -> Optional[DasaPeriod]:
        """Find the active period at a given date."""
        for md in periods:
            if md.start_jd <= target_jd < md.end_jd:
                if md.sub_periods:
                    return DasaBase.get_active_period(md.sub_periods, target_jd)
                return md
        return None

    @staticmethod
    def compute_fraction_remaining(nakshatra_degrees: float, nakshatra_span: float = 13.333333) -> float:
        """Compute fraction of nakshatra remaining (0 to 1).
        
        Args:
            nakshatra_degrees: Moon's degrees within current nakshatra (0 to 13.333)
            nakshatra_span: Total span of nakshatra (13.333 for Vimsottari)
            
        Returns:
            Fraction remaining (0 = at end, 1 = at start)
        """
        remain = nakshatra_span - nakshatra_degrees
        return remain / nakshatra_span

    @staticmethod
    def build_period_tree(
        lords: List[Tuple[int, float]],
        start_jd: float,
        cycle_total_years: float,
        sub_ratios: List[float],
        y_per_d: float = 365.2425,
        max_level: PeriodLevel = PeriodLevel.PRATYANTARDASA,
        lord_names: Optional[Dict[int, str]] = None,
        sub_lord_names: Optional[Dict[int, str]] = None,
        sub_order: Optional[List[int]] = None,
        ad_method: str = "rao_rath",
    ) -> List[DasaPeriod]:
        """Build hierarchical period tree from lord sequence.
        
        Args:
            lords: List of (lord_index, lord_years) tuples
            start_jd: JD when first period begins
            cycle_total_years: Total cycle length in years
            sub_ratios: Proportional ratios for sub-period lords
            y_per_d: Days per year (solar=365.2425, savana=360)
            max_level: How deep to subdivide
            lord_names: Optional dict mapping lord_index → display name
            sub_lord_names: Optional dict mapping ratio-index → sub-period display name
            sub_order: Optional cycle lord indices parallel to sub_ratios.
                When given, each parent's sub-periods rotate to start from the
                parent lord; when absent, legacy input order is kept.
        """
        lord_names = lord_names or {}
        if sub_lord_names is None:
            sub_lord_names = {}
            for i in range(len(sub_ratios)):
                try:
                    from jhora.types.graha import Graha
                    sub_lord_names[i] = Graha(i).full_name
                except (ValueError, ImportError):
                    sub_lord_names[i] = str(i)
        periods = []
        current_jd = start_jd
        for lord_idx, lord_yrs in lords:
            dur_days = lord_yrs * y_per_d
            end_jd = current_jd + dur_days
            if lord_idx in lord_names:
                lord_str = lord_names[lord_idx]
            else:
                try:
                    from jhora.types.graha import Graha
                    lord_str = Graha(lord_idx).full_name
                except (ValueError, ImportError):
                    lord_str = str(lord_idx)
            md = DasaPeriod(
                lord_index=lord_idx,
                lord_name=lord_str,
                start_jd=current_jd,
                end_jd=end_jd,
                duration_years=lord_yrs,
                level=PeriodLevel.MAHADASA,
            )
            if max_level.value >= PeriodLevel.ANTARDASA.value:
                md.sub_periods = _subdivide(
                    md, sub_ratios, y_per_d, 1, max_level, sub_lord_names,
                    sub_order, ad_method,
                )
            periods.append(md)
            current_jd = end_jd
        return periods


def _subdivide(
    parent: DasaPeriod,
    ratios: List[float],
    y_per_d: float,
    depth: int,
    max_depth: PeriodLevel,
    sub_lord_names: Optional[Dict[int, str]] = None,
    sub_order: Optional[List[int]] = None,
    ad_method: str = "rao_rath",
) -> List[DasaPeriod]:
    """Create subdivision periods for a parent period.

    When sub_order (cycle lord indices parallel to ratios) is given, the
    enumeration rotates to the parent lord's cycle position, so sub-periods
    start from the parent lord at every depth; otherwise legacy input order
    is kept byte-identical.

    ``ad_method`` selects the construction:
      * ``rao_rath``    - the rotation above (default, unchanged)
      * ``raman``       - Dr. Raman's first-fraction: the parent lord runs the
                          first half of the sub-cycle before the proportional
                          rotation (sub-periods keep the rotation order)
      * ``continuous``  - no re-anchoring: each level continues in the parent
                          lord's cyclic order from the start of the parent
      * ``raghavacharya`` - navamsa progression: the sub-order steps by one
                          navamsa per sub-period instead of the Vimsottari order
    """
    if depth > max_depth.value:
        return None
    sub_lord_names = sub_lord_names or {}
    order = list(sub_order) if sub_order is not None else None
    if order is not None:
        try:
            start = order.index(parent.lord_index)
        except ValueError:
            start = 0
    else:
        start = 0

    # ── Antardasa construction method ────────────────────────────────────
    # Only the first level (antardasas) is method-sensitive; deeper levels
    # follow the same rotation so a method choice cannot cascade.
    raman_halved_first = False
    big_step = 1
    if ad_method == "continuous" and order is not None:
        # Each sub-period continues in the parent lord's cyclic order,
        # starting at the parent lord (no re-anchoring beyond the parent).
        pass
    elif ad_method == "raghavacharya" and order is not None:
        # Navamsa progression: step by one navamsa per sub-period, so the
        # order advances by the sign's navamsa count rather than by one.
        big_step = max(1, len(order) // 4) or 1
    elif ad_method == "raman" and depth == 1:
        # Dr. Raman first-fraction: the parent lord opens the cycle and its
        # first sub-period is halved (the remaining half is redistributed by
        # the proportional rotation).
        raman_halved_first = True

    total_ratio = sum(ratios)
    periods = []
    level_map = {
        1: PeriodLevel.ANTARDASA,
        2: PeriodLevel.PRATYANTARDASA,
        3: PeriodLevel.SUKSHMA,
        4: PeriodLevel.PRANA,
        5: PeriodLevel.DEHA,
    }
    level = level_map.get(depth, PeriodLevel.ANTARDASA)
    parent_duration = parent.end_jd - parent.start_jd
    current_jd = parent.start_jd
    n = len(ratios)
    for k in range(n):
        i = (start + k * big_step) % n if order is not None else k
        ratio = ratios[i]
        dur = parent_duration * (ratio / total_ratio)
        if raman_halved_first and k == 0:
            dur = dur / 2.0
        end_jd = current_jd + dur
        sub_name = sub_lord_names.get(i, str(i))
        sub = DasaPeriod(
            lord_index=order[i] if order is not None else i,
            lord_name=sub_name,
            start_jd=current_jd,
            end_jd=end_jd,
            duration_years=dur / y_per_d,
            level=level,
        )
        if depth < max_depth.value:
            sub.sub_periods = _subdivide(sub, ratios, y_per_d, depth + 1, max_depth, sub_lord_names,
                                         sub_order, ad_method)
        periods.append(sub)
        current_jd = end_jd
    return periods
