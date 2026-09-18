"""Deterministic birth-chart sampler for training-data generation.

Produces diverse birth-data dicts (suitable for ``ChartBuilder().build``)
covering lagna signs, Moon signs, dasa lords and hemispheres. Train/eval
splits use disjoint seed streams so the held-out eval set is excluded from
training output by construction (spec task 1.6).
"""

import calendar
import random
from typing import Dict, List

DEFAULT_N = 2000
DEFAULT_SEED = 42
EVAL_SEED_OFFSET = 1_000_000

_SPLITS = ("train", "eval")


def _tz_for_lon(lon: float) -> str:
    """Nearest half-hour zone label for a longitude (synthetic charts)."""
    half = round(lon / 7.5) * 0.5
    sign = "+" if half >= 0 else "-"
    h, m = divmod(int(abs(half) * 60), 60)
    return f"{sign}{h:02d}{m:02d}"


def sample_charts(n: int = DEFAULT_N, seed: int = DEFAULT_SEED,
                  split: str = "train") -> List[Dict]:
    """Sample ``n`` birth-data dicts deterministically.

    Args:
        n: number of charts.
        seed: RNG seed (eval split adds a fixed offset for disjointness).
        split: "train" or "eval".
    """
    if split not in _SPLITS:
        raise ValueError(f"split must be one of {_SPLITS}")
    rng = random.Random(seed + (EVAL_SEED_OFFSET if split == "eval" else 0))
    out = []
    for _ in range(n):
        year = rng.randint(1940, 2010)
        month = rng.randint(1, 12)
        day = rng.randint(1, calendar.monthrange(year, month)[1])
        hour = round(rng.uniform(0, 24), 4) % 24
        lat = round(rng.uniform(-60, 60), 4)
        if lat == 0:
            lat = 0.5
        lon = round(rng.uniform(-180, 180), 4)
        out.append({
            "year": year, "month": month, "day": day, "hour": hour,
            "lat": lat, "lon": lon, "tz": _tz_for_lon(lon),
        })
    return out


def coverage(charts: List[Dict]) -> Dict[str, Dict]:
    """Count train charts per lagna sign / Moon sign / current MD lord.

    Computes real charts (slower); used by tests and dataset reports.
    Reference epoch for 'current' MD: 2026-01-01.
    """
    import datetime
    from jhora.charts.chart import ChartBuilder
    from jhora.dasas.vimsottari import VimsottariDasa
    from jhora.types.graha import Graha
    from jhora.types.rasi import Rasi

    lagna, moons, mds = {}, {}, {}
    ref_jd = _jd(2026, 1, 1)
    for bd in charts:
        cd = ChartBuilder().build(**bd)
        lag = Rasi.from_longitude(cd.ascendant).full_name
        lagna[lag] = lagna.get(lag, 0) + 1
        mon = Rasi.from_longitude(cd.planet(Graha.MOON).longitude).full_name
        moons[mon] = moons.get(mon, 0) + 1
        chart_dict = {"planets": {g: {"longitude": p.longitude}
                                  for g, p in cd.planets.items()},
                      "lagna_lon": cd.ascendant}
        for md in VimsottariDasa().compute(cd.julian_day, chart_dict):
            s = getattr(md, "start_jd", None)
            e = getattr(md, "end_jd", None)
            if s is not None and e is not None and s <= ref_jd < e:
                mds[md.lord_name] = mds.get(md.lord_name, 0) + 1
                break
    return {"lagna": lagna, "moon": moons, "md_lord": mds}


def _jd(year: int, month: int, day: int) -> float:
    import datetime
    dt = datetime.datetime(year, month, day, tzinfo=datetime.timezone.utc)
    return dt.timestamp() / 86400.0 + 2440587.5
