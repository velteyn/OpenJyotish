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

    def test_prompt_asks_for_direct_answer(self):
        """The prompt must tell reasoning models not to spill planning as output.
        Without this, a reasoning model burns its token budget on a monologue and
        returns no reading (the 'ask' regression)."""
        cd = _sample_chart()
        for prompt in (interpret_prompt(cd, "detailed"),
                       question_prompt(cd, "What is my career?")):
            assert "do not plan it out loud" in prompt
            assert "Begin the reading immediately" in prompt

    def test_system_prompt_asks_for_direct_answer(self):
        from jhora.ai.prompts import SYSTEM_PROMPT
        assert "Answer the question directly" in SYSTEM_PROMPT
        assert "Do NOT print your" in SYSTEM_PROMPT

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

    def test_stream_reasoning_model(self):
        """Reasoning is never surfaced — only the visible answer is streamed."""
        import json

        class _FakeResp:
            def iter_lines(self, decode_unicode=False):
                def _chunk(delta):
                    data = json.dumps({"choices": [{"delta": delta}]})
                    return ("data: " + data + "\n").encode("utf-8")

                return [
                    _chunk({"reasoning_content": "Let me "}),
                    _chunk({"reasoning_content": "think"}),
                    _chunk({"content": "The Moon "}),
                    _chunk({"content": "in Aries"}),
                    b"data: [DONE]\n",
                ]

        engine = AiEngine(AiConfig(provider="custom", base_url="http://localhost:1/v1", model="x"))
        tokens = []
        text = engine._stream_response(_FakeResp(), on_token=tokens.append)
        assert text == "The Moon in Aries"
        assert "Let me think" not in "".join(tokens)
        assert "The Moon in Aries" in "".join(tokens)

    def test_stream_reasoning_only_fallback(self):
        """If the model produced only thinking, emit a notice — not the thoughts."""
        import json

        class _FakeResp:
            def iter_lines(self, decode_unicode=False):
                data = json.dumps({"choices": [{"delta": {"reasoning_content": "deep thinking.."}}]})
                return [(("data: " + data + "\n").encode("utf-8")),
                        b"data: [DONE]\n"]

        engine = AiEngine(AiConfig(provider="custom", base_url="http://localhost:1/v1", model="x"))
        tokens = []
        text = engine._stream_response(_FakeResp(), on_token=tokens.append)
        assert "no visible answer" in text
        assert "deep thinking" not in text
        assert "no visible answer" in "".join(tokens)


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


class TestModelResolution:
    """Auto model resolution: pick a chat model regardless of server state."""

    def _lm(self, monkeypatch, items, load_ok=True):
        import jhora.ai.engine as eng
        monkeypatch.setattr(eng, "_lmstudio_catalog", lambda base_url, timeout=5.0: items)
        monkeypatch.setattr(eng, "_lmstudio_load",
                            lambda base_url, model_id, timeout=15.0: load_ok)
        monkeypatch.setattr(eng, "_ollama_catalog",
                            lambda base_url, timeout=5.0: [])
        return AiEngine(AiConfig(provider="lmstudio"))

    def test_prefers_loaded_chat_over_embedding(self, monkeypatch):
        items = [
            {"id": "hf.co/x/text-embedding-nomic-embed-text-v1.5",
             "loaded": True, "type": "embeddings"},
            {"id": "hf.co/x/qwen3.5-9b", "loaded": True, "type": "vlm"},
        ]
        engine = self._lm(monkeypatch, items)
        r = engine.resolve_model()
        assert r["status"] == "ok"
        assert r["model"] == "hf.co/x/qwen3.5-9b"
        assert engine.config.model == "hf.co/x/qwen3.5-9b"

    def test_autoloads_best_available_chat(self, monkeypatch):
        items = [
            {"id": "hf.co/x/text-embedding-nomic-embed-text-v1.5",
             "loaded": True, "type": "embeddings"},
            {"id": "hf.co/x/qwen3-8b", "loaded": False, "type": "chat"},
        ]
        engine = self._lm(monkeypatch, items)
        r = engine.resolve_model()
        assert r["status"] == "ok"
        assert r["model"] == "hf.co/x/qwen3-8b"
        assert "automatically" in r["message"] or "Loaded" in r["message"]

    def test_no_chat_model_suggests_under_9gb(self, monkeypatch):
        items = [{"id": "hf.co/x/text-embedding-nomic-embed-text-v1.5",
                  "loaded": True, "type": "embeddings"}]
        engine = self._lm(monkeypatch, items)
        r = engine.resolve_model()
        assert r["status"] == "no_model"
        assert r["model"] == ""
        assert "9GB" in r["message"]

    def test_no_chat_model_load_failed_suggests(self, monkeypatch):
        items = [{"id": "hf.co/x/qwen3-8b", "loaded": False, "type": "chat"}]
        engine = self._lm(monkeypatch, items, load_ok=False)
        r = engine.resolve_model()
        assert r["status"] == "no_model"
        assert "9GB" in r["message"]

    def test_offline_server(self, monkeypatch):
        import requests
        import jhora.ai.engine as eng

        def _boom(base_url, timeout=5.0):
            raise requests.exceptions.ConnectionError("refused")
        monkeypatch.setattr(eng, "_lmstudio_catalog", _boom)
        engine = AiEngine(AiConfig(provider="lmstudio"))
        r = engine.resolve_model()
        assert r["status"] == "offline"

    def test_keeps_concrete_user_model(self, monkeypatch):
        import jhora.ai.engine as eng
        monkeypatch.setattr(eng, "_generic_catalog", lambda base_url, timeout=5.0: [
            {"id": "gpt4", "type": "chat"},
        ])
        cfg = AiConfig(provider="custom", base_url="http://x:9999/v1", model="gpt4")
        engine = AiEngine(cfg)
        r = engine.resolve_model()
        assert r["status"] == "ok"
        assert r["model"] == "gpt4"

    def test_ollama_names_best_installed_model(self, monkeypatch):
        import jhora.ai.engine as eng
        monkeypatch.setattr(eng, "_ollama_catalog", lambda base_url, timeout=5.0: [
            {"id": "deepseek-r1:7b", "loaded": False, "type": "chat"},
            {"id": "qwen3:8b", "loaded": False, "type": "chat"},
        ])
        engine = AiEngine(AiConfig(provider="ollama"))  # default model llama3.2
        r = engine.resolve_model()
        assert r["status"] == "ok"
        assert r["model"] == "qwen3:8b"  # qwen preferred, ≤9GB

    def test_embedding_config_model_is_replaced(self, monkeypatch):
        items = [{"id": "hf.co/x/qwen3-8b", "loaded": False, "type": "chat"}]
        import jhora.ai.engine as eng
        monkeypatch.setattr(eng, "_lmstudio_catalog",
                            lambda base_url, timeout=5.0: items)
        monkeypatch.setattr(eng, "_lmstudio_load",
                            lambda base_url, model_id, timeout=15.0: True)
        engine = AiEngine(AiConfig(provider="lmstudio",
                                   model="text-embedding-nomic-embed-text-v1.5"))
        assert engine._ensure_chat_model() is None
        assert engine.config.model == "hf.co/x/qwen3-8b"

    def test_ensure_chat_model_blocks_with_suggestion(self, monkeypatch):
        items = [{"id": "hf.co/x/nomic-embed-text-v1.5", "loaded": True,
                  "type": "embeddings"}]
        engine = self._lm(monkeypatch, items)
        out = engine._ensure_chat_model()
        assert out is not None
        assert "9GB" in out

    def test_chat_completion_retries_once_on_model_error(self, monkeypatch):
        import requests
        import jhora.ai.engine as eng
        monkeypatch.setattr(eng, "_ollama_catalog", lambda base_url, timeout=5.0: [
            {"id": "qwen3:8b", "loaded": False, "type": "chat"},
        ])
        engine = AiEngine(AiConfig(provider="ollama"))  # placeholder llama3.2
        calls = {"n": 0}

        def fake_call(messages, stream=False):
            calls["n"] += 1
            if calls["n"] == 1:
                raise requests.exceptions.HTTPError("HTTP 404: model not found")
            return {"dummy": True}

        monkeypatch.setattr(engine, "_call", fake_call)
        monkeypatch.setattr(engine, "_stream_response",
                            lambda resp, on_token=None: "ok reply")
        text = engine._chat_completion([{"role": "user", "content": "hi"}])
        assert calls["n"] == 2
        assert text == "ok reply"
        assert engine.config.model == "qwen3:8b"

    def test_download_suggestion_is_under_9gb(self):
        from jhora.ai.engine import _download_suggestion
        for prov in ("ollama", "lmstudio", "unsloth", "custom"):
            msg = _download_suggestion(prov)
            assert "9GB" in msg, prov
            assert prov in msg or "chat" in msg


class TestThinkingCapGating:
    """LM Studio must cap reasoning thinking tokens; other providers must not
    receive the LM Studio-only key (Ollama rejects unknown request fields)."""

    def _post(self, monkeypatch):
        captured = {}

        def fake_post(url, json=None, timeout=None, stream=None):
            captured["payload"] = json
            captured["url"] = url
            import types
            resp = types.SimpleNamespace()
            resp.json = lambda: {"choices": []}
            resp.raise_for_status = lambda: None
            return resp

        import requests as _requests
        monkeypatch.setattr(_requests, "post", fake_post)
        return captured

    def test_lmstudio_sends_thinking_cap(self, monkeypatch):
        captured = self._post(monkeypatch)
        engine = AiEngine(AiConfig(provider="lmstudio",
                                   base_url="http://x:1234/v1", model="m"))
        engine._call([{"role": "user", "content": "hi"}], stream=False)
        assert captured["payload"]["max_thinking_tokens"] == 1024

    def test_ollama_omits_thinking_cap(self, monkeypatch):
        captured = self._post(monkeypatch)
        engine = AiEngine(AiConfig(provider="ollama",
                                   base_url="http://x:11434/v1", model="m"))
        engine._call([{"role": "user", "content": "hi"}], stream=False)
        assert "max_thinking_tokens" not in captured["payload"]


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

