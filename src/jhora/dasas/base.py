"""
DasaBase — abstract base class for all dasa systems.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from jhora.types.dasa import DasaPeriod, PeriodLevel


@dataclass
class DasaOptions:
    """Configuration options for dasa computation."""
    year_definition: str = "solar"           # solar (365.2425d), savana (360d), tithi (354.367d)
    start_variation: str = "moon"            # moon, kshema, utpanna, adhana, lagna
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

    def get_active_period(self, periods: List[DasaPeriod], target_jd: float) -> Optional[DasaPeriod]:
        """Find the active period at a given date."""
        for md in periods:
            if md.start_jd <= target_jd < md.end_jd:
                if md.sub_periods:
                    return self.get_active_period(md.sub_periods, target_jd)
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
    ) -> List[DasaPeriod]:
        """Build hierarchical period tree from lord sequence.
        
        Args:
            lords: List of (lord_index, lord_years) tuples
            start_jd: JD when first period begins
            cycle_total_years: Total cycle length in years
            sub_ratios: Proportional ratios for sub-period lords
            y_per_d: Days per year (solar=365.2425, savana=360)
            max_level: How deep to subdivide
        """
        periods = []
        current_jd = start_jd
        for lord_idx, lord_yrs in lords:
            dur_days = lord_yrs * y_per_d
            end_jd = current_jd + dur_days
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
                    md, sub_ratios, y_per_d, 1, max_level
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
) -> List[DasaPeriod]:
    """Create subdivision periods for a parent period."""
    if depth > max_depth.value:
        return None
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
    for i, ratio in enumerate(ratios):
        dur = parent_duration * (ratio / total_ratio)
        end_jd = current_jd + dur
        sub = DasaPeriod(
            lord_index=i,
            lord_name=str(i),
            start_jd=current_jd,
            end_jd=end_jd,
            duration_years=dur / y_per_d,
            level=level,
        )
        if depth < max_depth.value:
            sub.sub_periods = _subdivide(sub, ratios, y_per_d, depth + 1, max_depth)
        periods.append(sub)
        current_jd = end_jd
    return periods
