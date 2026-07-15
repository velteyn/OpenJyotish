"""Tests for AI engine — offline-only (no LLM server required)."""

from jhora.ai.engine import AiEngine, AiConfig, PROVIDERS
from jhora.ai.prompts import chart_to_text, interpret_prompt, question_prompt, remedy_prompt
from jhora.charts.chart import ChartBuilder


def _sample_chart():
    b = ChartBuilder()
    return b.build(year=2026, month=7, day=7, hour=10.5, lat=13.08, lon=80.27, tz="+0530")


class TestPrompts:
    def test_chart_to_text(self):
        cd = _sample_chart()
        text = chart_to_text(cd)
        assert "Birth:" in text
        assert "Virgo" in text
        assert "Sun:" in text
        assert "House 1:" in text
        assert "House 12:" in text

    def test_interpret_prompt(self):
        cd = _sample_chart()
        prompt = interpret_prompt(cd, "concise")
        assert "concise" not in prompt.lower().split()[:10]  # style hint is internal
        assert "Please interpret" in prompt

    def test_question_prompt(self):
        cd = _sample_chart()
        prompt = question_prompt(cd, "What is my career?")
        assert "What is my career?" in prompt

    def test_remedy_prompt(self):
        cd = _sample_chart()
        prompt = remedy_prompt(cd)
        assert "remedial" in prompt.lower()


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
