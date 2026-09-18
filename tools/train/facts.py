"""Fact emitter: engine ground truth per chart in a fixed schema.

The drafter (spec task 1.3) MUST use only these facts; the verifier filter
(spec task 1.4) checks every drafted claim against the same chart. All
periods carry full dates (no "current" relative to run time) so dataset
output is deterministic.
"""

from typing import Dict, List

from jhora.calc.shadbala import ShadbalaComputer
from jhora.calc.yogas import detect_all
from jhora.charts.chart import ChartData
from jhora.dasas.vimsottari import VimsottariDasa
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra

_PLANETS = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
            Graha.JUPITER, Graha.VENUS, Graha.SATURN,
            Graha.RAHU, Graha.KETU]


def _house(cd: ChartData, lon: float) -> int:
    asc = int(cd.ascendant // 30) % 12
    return (int(lon // 30) % 12 - asc) % 12 + 1


def chart_facts(cd: ChartData) -> Dict:
    """Emit the fixed fact schema for one computed chart."""
    lagna_rasi = Rasi.from_longitude(cd.ascendant)
    placements = []
    for g in _PLANETS:
        p = cd.planet(g)
        r = Rasi.from_longitude(p.longitude)
        n, pada = Nakshatra.from_longitude(p.longitude)
        placements.append({
            "planet": g.full_name,
            "sign": r.full_name,
            "deg_in_sign": round(p.longitude % 30.0, 4),
            "nakshatra": n.name.replace("_", " ").title(),
            "pada": pada,
            "house": _house(cd, p.longitude),
            "retrograde": bool(p.is_retrograde),
        })
    house_lords = {}
    for h in range(1, 13):
        idx = (int(cd.ascendant // 30) + h - 1) % 12
        lord = Rasi(idx).lord
        house_lords[h] = (lord.name.capitalize()
                          if hasattr(lord, "name") else str(lord).capitalize())
    strengths = {}
    sbc = ShadbalaComputer(cd)
    for g in _PLANETS[:7]:
        try:
            strengths[g.full_name] = round(
                sbc.compute_one(g).total_virupa, 1)
        except Exception:
            pass
    chart_dict = {"planets": {g: {"longitude": p.longitude}
                              for g, p in cd.planets.items()},
                  "lagna_lon": cd.ascendant}
    dasa = []
    for md in VimsottariDasa().compute(cd.julian_day, chart_dict):
        entry = {
            "lord": md.lord_name,
            "start": md.start_date.strftime("%Y-%m-%d"),
            "end": md.end_date.strftime("%Y-%m-%d"),
            "antardashas": [
                {"lord": sp.lord_name,
                 "start": sp.start_date.strftime("%Y-%m-%d"),
                 "end": sp.end_date.strftime("%Y-%m-%d")}
                for sp in (md.sub_periods or [])
            ],
        }
        dasa.append(entry)
    yogas = []
    try:
        for y in detect_all(cd):
            yogas.append({
                "name": y.name,
                "planets": [p.short_name for p in (y.planets or [])],
            })
    except Exception:
        pass
    bd = cd.birth_date
    return {
        "birth": {"date": bd.strftime("%Y-%m-%d"),
                  "time": bd.strftime("%H:%M"),
                  "lat": cd.latitude, "lon": cd.longitude},
        "lagna": {"sign": lagna_rasi.full_name,
                  "lon": round(cd.ascendant, 4)},
        "placements": placements,
        "house_lords": house_lords,
        "shadbala": strengths,
        "vimsottari": dasa,
        "yogas": yogas,
    }


def facts_schema() -> List[str]:
    """Top-level keys the drafter may rely on (contract)."""
    return ["birth", "lagna", "placements", "house_lords",
            "shadbala", "vimsottari", "yogas"]
