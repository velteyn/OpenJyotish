"""Tests for chart interpretation engine and reference texts."""

from jhora.interpreter.engine import ChartInterpreter
from jhora.interpreter.texts import (
    PLANET_MEANINGS, HOUSE_MEANINGS, DIGNITY_DESC,
    RASI_MEANINGS, NAKSHATRA_MEANINGS,
)
from jhora.interpreter.knowledge_base import KnowledgeBase
from jhora.types.graha import Graha


class TestReferenceTexts:
    def test_planet_meanings_all_members(self):
        assert len(PLANET_MEANINGS) == 9
        assert "Sun" in PLANET_MEANINGS
        assert "Ketu" in PLANET_MEANINGS

    def test_house_meanings_all(self):
        assert len(HOUSE_MEANINGS) == 12

    def test_dignity_descriptions(self):
        assert "exalted" in DIGNITY_DESC
        assert "debilitated" in DIGNITY_DESC

    def test_rasi_meanings_all(self):
        assert len(RASI_MEANINGS) == 12
        assert "Aries" in RASI_MEANINGS

    def test_nakshatra_meanings_all(self):
        assert len(NAKSHATRA_MEANINGS) == 27


class TestChartInterpreter:
    def test_overview(self, ref_chart):
        interp = ChartInterpreter()
        result = interp.interpret(ref_chart)
        assert "overview" in result
        assert result["overview"]["ascendant_rasi"] == "Sagittarius"

    def test_planet_placements(self, ref_chart):
        interp = ChartInterpreter()
        result = interp.interpret(ref_chart)
        assert "planets" in result
        assert len(result["planets"]) == 9  # 7 planets + 2 nodes

    def test_planet_strengths(self, ref_chart):
        interp = ChartInterpreter()
        result = interp.interpret(ref_chart)
        assert "strengths" in result
        assert result["strengths"]["Sun"] == "neutral"
        assert result["strengths"]["Mars"] == "moolatrikona"

    def test_house_lords(self, ref_chart):
        interp = ChartInterpreter()
        result = interp.interpret(ref_chart)
        assert "house_lords" in result
        assert len(result["house_lords"]) == 12
        # House 1 lord depends on ascendant (Sagittarius → Jupiter)
        assert result["house_lords"][0]["rasi"] == "Sagittarius"
        assert result["house_lords"][0]["lord"] == "Jupiter"

    def test_yogas_detected(self, ref_chart):
        interp = ChartInterpreter()
        result = interp.interpret(ref_chart)
        assert "yogas" in result
        assert isinstance(result["yogas"], list)

    def test_interpret_text_output(self, ref_chart):
        interp = ChartInterpreter()
        text = interp.interpret_text(ref_chart)
        assert isinstance(text, str)
        assert len(text) > 100
        assert "Sun" in text
        assert "Sagittarius" in text

    def test_lagna_text(self, ref_chart):
        interp = ChartInterpreter()
        text = interp.interpret_text(ref_chart)
        assert "Ascendant" in text
        assert "Sagittarius" in text

    def test_lagna_analysis(self, ref_chart):
        interp = ChartInterpreter()
        result = interp.interpret(ref_chart)
        assert "lagna" in result
        assert "text" in result["lagna"]


class TestKnowledgeBase:
    def test_kb_initialized(self):
        kb = KnowledgeBase()
        assert kb.loaded >= 0

    def test_kb_search_basic(self, ref_chart):
        interp = ChartInterpreter()
        results = interp.search_knowledge("yoga")
        assert isinstance(results, list)

    def test_kb_search_no_results(self):
        kb = KnowledgeBase()
        results = kb.search("xyznonexistent12345")
        assert results == []
