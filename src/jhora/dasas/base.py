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
    start_variation: str = "moon"

    #: How the first mahadasa's duration is handled:
    #:   moon  - reduce first MD by the fraction of Moon's nakshatra remaining
    #:   full  - every MD gets its full year count (cycle totals 120 years)
    sesham_method: str = "moon"

    subdivision_level: PeriodLevel = PeriodLevel.PRATYANTARDASA
    include_subperiods: bool = True
    custom_sequence: Optional[List[int]] = None


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
                    sub_order,
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
) -> List[DasaPeriod]:
    """Create subdivision periods for a parent period.

    When sub_order (cycle lord indices parallel to ratios) is given, the
    enumeration rotates to the parent lord's cycle position, so sub-periods
    start from the parent lord at every depth; otherwise legacy input order
    is kept byte-identical.
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
        i = (start + k) % n if order is not None else k
        ratio = ratios[i]
        dur = parent_duration * (ratio / total_ratio)
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
                                         sub_order)
        periods.append(sub)
        current_jd = end_jd
    return periods
