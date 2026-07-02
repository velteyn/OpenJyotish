"""Chart interpretation engine - generates Vedic astrology readings."""

from typing import Dict, List, Optional

from typing import Any, List

from jhora.charts.chart import ChartData, PlanetChartData
from jhora.calc.yogas import detect_all, YogaResult
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.interpreter.texts import (
    PLANET_MEANINGS, HOUSE_MEANINGS, DIGNITY_DESC,
    RASI_MEANINGS, NAKSHATRA_MEANINGS, YOGA_DESCRIPTIONS,
)
from jhora.interpreter.knowledge_base import KnowledgeBase


class ChartInterpreter:
    """Generate chart readings from computed ChartData."""

    def __init__(self):
        self.kb = KnowledgeBase()

    def interpret(self, cd: ChartData, style: str = "concise") -> Dict:
        """Generate a full chart interpretation."""
        return {
            "overview": self._overview(cd),
            "planets": self._planet_placements(cd),
            "house_lords": self._house_lords(cd),
            "lagna": self._lagna_analysis(cd),
            "strengths": self._planet_strengths(cd),
            "yogas": self._detect_yogas(cd),
        }

    def interpret_text(self, cd: ChartData, style: str = "concise") -> str:
        """Generate a plain text reading."""
        parts = [self._overview_text(cd)]
        parts.append("\n=== Planetary Placements ===")
        for g in Graha:
            if g in cd.planets:
                parts.append(self._planet_text(cd, g))

        parts.append("\n=== House Lords ===")
        parts.append(self._house_lords_text(cd))

        parts.append("\n=== Yogas Detected ===")
        yogas = self._detect_yogas(cd)
        if yogas:
            for y in yogas:
                parts.append(f"  {y.format()}")
        else:
            parts.append("  No major yogas detected")

        parts.append("\n=== Lagna Analysis ===")
        parts.append(self._lagna_text(cd))

        return "\n".join(parts)

    def _overview(self, cd: ChartData) -> Dict:
        asc_rasi = Rasi.from_longitude(cd.ascendant)
        return {
            "ascendant_rasi": asc_rasi.full_name,
            "ascendant_longitude": f"{cd.ascendant:.2f}°",
            "ayanamsa": cd.ayanamsa_name,
            "ayanamsa_value": f"{cd.ayanamsa_value:.4f}°",
        }

    def _overview_text(self, cd: ChartData) -> str:
        asc_rasi = Rasi.from_longitude(cd.ascendant)
        asc_naks = cd.lagna.nakshatra_name
        asc_pada = cd.lagna.nakshatra_pada
        return (
            f"Birth Data: {cd.birth_date.strftime('%Y-%m-%d')} at "
            f"Lat {cd.latitude} Lon {cd.longitude}\n"
            f"Ayanamsa: {cd.ayanamsa_name.title()} ({cd.ayanamsa_value:.4f}°)\n"
            f"Ascendant: {asc_rasi.full_name} at {cd.ascendant:.2f}° "
            f"({asc_naks} Pada {asc_pada})\n"
            f"Moon: {cd.moon.rasi_name} at {cd.moon.longitude:.2f}°"
        )

    def _planet_placements(self, cd: ChartData) -> Dict[str, Any]:
        result = {}
        for g in Graha:
            if g in cd.planets:
                p = cd.planets[g]
                result[g.full_name] = {
                    "longitude": p.longitude,
                    "rasi": p.rasi_name,
                    "degrees_in_rasi": p.degrees_in_rasi,
                    "nakshatra": p.nakshatra_name,
                    "pada": p.nakshatra_pada,
                    "dignity": p.dignity,
                    "retrograde": p.is_retrograde,
                }
        return result

    def _planet_text(self, cd: ChartData, g: Graha) -> str:
        p = cd.planets[g]
        lines = [
            f"  {g.full_name} in {p.rasi_name} at {p.longitude:.2f}° "
            f"({p.degrees_in_rasi:.1f}° in sign)",
            f"    Nakshatra: {p.nakshatra_name} Pada {p.nakshatra_pada}",
            f"    Dignity: {p.dignity.title()}",
        ]
        if p.is_retrograde:
            lines.append("    ** Retrograde — internalized/reflective expression")
        return "\n".join(lines)

    def _planet_strengths(self, cd: ChartData) -> Dict[str, str]:
        result = {}
        for g in Graha:
            if g in cd.planets:
                result[g.full_name] = cd.planets[g].dignity
        return result

    def _house_lords_text(self, cd: ChartData) -> str:
        lines = []
        for i in range(12):
            cusp = cd.house_cusps[i]
            ras = Rasi.from_longitude(cusp)
            lines.append(f"  House {i+1}: {ras.full_name} (Lord: {ras.lord})")
        return "\n".join(lines)

    def _lagna_text(self, cd: ChartData) -> str:
        asc_rasi = Rasi.from_longitude(cd.ascendant)
        ruler = asc_rasi.lord
        asc_naks = cd.lagna.nakshatra_name
        return (
            f"Ascendant in {asc_rasi.full_name}, ruled by {ruler}.\n"
            f"Nakshatra: {asc_naks} (Pada {cd.lagna.nakshatra_pada}).\n"
            f"{RASI_MEANINGS.get(asc_rasi.full_name, '')}"
        )

    def _detect_yogas(self, cd: ChartData) -> List[YogaResult]:
        return detect_all(cd)

    def _lagna_analysis(self, cd: ChartData) -> Dict:
        return {"text": self._lagna_text(cd)}

    def _house_lords(self, cd: ChartData) -> List[Dict]:
        result = []
        for i in range(12):
            cusp = cd.house_cusps[i]
            ras = Rasi.from_longitude(cusp)
            result.append({"house": i + 1, "rasi": ras.full_name, "lord": ras.lord})
        return result

    def search_knowledge(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search the book/PDF knowledge base."""
        return self.kb.search(query, max_results=max_results)
