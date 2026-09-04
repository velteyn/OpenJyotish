"""Tests for AI engine — offline-only (no LLM server required)."""

from jhora.ai.engine import AiEngine, AiConfig, PROVIDERS
from jhora.ai.prompts import interpret_prompt, question_prompt, remedy_prompt, _chart_compact, _estimate_tokens
from jhora.ai.json_export import chart_to_json
from jhora.ai.analysis import build_analysis_text
from jhora.charts.chart import ChartBuilder
from jhora.calc.special_lagnas import UserSpecialLagnaConfig
from jhora.types.graha import Graha


def _sample_chart():
    b = ChartBuilder()
    return b.build(year=2026, month=7, day=7, hour=10.5, lat=13.08, lon=80.27, tz="+0530")


class TestPrompts:
    def test_chart_compact(self):
        cd = _sample_chart()
        text = _chart_compact(cd)
        assert "Asc" in text
        assert "Su" in text
        assert "Sun" not in text[:50]  # compact uses short names
        assert "H1:" in text

    def test_interpret_prompt(self):
        cd = _sample_chart()
        prompt = interpret_prompt(cd, "concise")
        assert "CHART" in prompt
        assert "TASK" in prompt
        assert _estimate_tokens(prompt) < 8000  # should fit within budget

    def test_question_prompt(self):
        cd = _sample_chart()
        prompt = question_prompt(cd, "What is my career?")
        assert "What is my career?" in prompt

    def test_remedy_prompt(self):
        cd = _sample_chart()
        prompt = remedy_prompt(cd)
        assert "REMEDIES" in prompt


class TestAiEngine:
    def test_provider_presets(self):
        for name in ["ollama", "lmstudio", "unsloth", "custom"]:
            assert name in PROVIDERS
            p = PROVIDERS[name]
            assert "base_url" in p
            assert "default_model" in p

    def test_engine_defaults(self):
        engine = AiEngine(AiConfig(provider="ollama"))
        assert engine.config.base_url == "http://localhost:11434/v1"
        assert engine.config.model == "llama3.2"

    def test_engine_custom(self):
        config = AiConfig(provider="custom", base_url="http://x:9999/v1", model="gpt4")
        engine = AiEngine(config)
        assert engine.config.base_url == "http://x:9999/v1"
        assert engine.config.model == "gpt4"

    def test_health_check_offline(self):
        config = AiConfig(provider="custom", base_url="http://127.0.0.1:19999/v1", model="x")
        engine = AiEngine(config)
        result = engine.health_check()
        assert result["ok"] is False
        assert "error" in result

    def test_interpret_offline(self):
        cd = _sample_chart()
        config = AiConfig(provider="custom", base_url="http://127.0.0.1:19999/v1", model="x")
        engine = AiEngine(config)
        result = engine.interpret(cd, style="concise")
        assert "Could not reach" in result

    def test_ask_offline(self):
        cd = _sample_chart()
        config = AiConfig(provider="custom", base_url="http://127.0.0.1:19999/v1", model="x")
        engine = AiEngine(config)
        result = engine.ask(cd, "Career?")
        assert "Could not reach" in result

    def test_remedies_offline(self):
        cd = _sample_chart()
        config = AiConfig(provider="custom", base_url="http://127.0.0.1:19999/v1", model="x")
        engine = AiEngine(config)
        result = engine.remedies(cd)
        assert "Could not reach" in result


class TestUslInAI:
    def test_json_export_usl_included(self):
        cd = _sample_chart()
        cfg = UserSpecialLagnaConfig(Graha.JUPITER, 9.0)
        result = chart_to_json(cd, usl_config=cfg)
        names = [s["name"] for s in result["special_lagnas"]]
        assert "Ju9" in names

    def test_json_export_without_usl(self):
        cd = _sample_chart()
        result = chart_to_json(cd)
        names = [s["name"] for s in result["special_lagnas"]]
        assert "Ju9" not in names

    def test_analysis_text_usl(self):
        cd = _sample_chart()
        cfg = UserSpecialLagnaConfig(Graha.RAHU, 3.0, reverse=True)
        text = build_analysis_text(cd, usl_config=cfg)
        assert "Ra3R" in text
        assert "User's Special Lagna" in text


class TestArudhaSahamaExport:
    def test_json_export_arudhas(self):
        cd = _sample_chart()
        result = chart_to_json(cd)
        assert len(result["arudhas"]["bhava"]) == 12
        assert len(result["arudhas"]["graha"]) > 0
        assert result["arudhas"]["bhava"][0]["pada"] == "AL"

    def test_json_export_sahamas(self):
        cd = _sample_chart()
        result = chart_to_json(cd)
        assert len(result["sahamas"]) >= 10
        assert any("sign" in s for s in result["sahamas"])

    def test_json_export_karakas_fixed(self):
        # compute_chara_karakas must receive dict-of-dicts (not ChartData planets)
        cd = _sample_chart()
        result = chart_to_json(cd)
        assert len(result["karakas"]) == 8

    def test_analysis_text_has_arudha_sahama(self):
        cd = _sample_chart()
        text = build_analysis_text(cd)
        assert "Bhava Arudha Padas" in text
        assert "Graha Arudhas" in text
        assert "Sahamas" in text
        assert "Chara Karakas" in text


class TestDasaSystemsPropagation:
    """Cross-surface invariant: AI must be aware of all dasa systems."""

    def test_json_export_dasa_system_and_options(self):
        cd = _sample_chart()
        result = chart_to_json(cd)
        assert result["dasa"]["system"] == "vimsottari"
        assert result["dasa"]["options"] == {"seed": "moon", "sesham": "moon",
                                             "year": "solar"}
        assert len(result["dasa"]["mahadashas"]) > 0

    def test_json_export_other_dasa_systems(self):
        cd = _sample_chart()
        result = chart_to_json(cd)
        systems = result["dasa"]["systems"]
        for sys in ("ashtottari", "yogini", "sudasa", "chara",
                    "narayana", "kalachakra"):
            assert sys in systems, f"{sys} missing from dasa systems"
            assert "current_mahadasha_lord" in systems[sys], \
                f"{sys} has no current mahadasha"

    def test_analysis_text_lists_other_dasa_systems(self):
        cd = _sample_chart()
        text = build_analysis_text(cd)
        assert "Other Dasa Systems" in text
        assert "Ashtottari" in text
        assert "Kalachakra" in text

