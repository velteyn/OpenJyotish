"""Tests for AI engine — offline-only (no LLM server required)."""

from jhora.ai.engine import AiEngine, AiConfig, PROVIDERS, _generic_catalog
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

    def test_anchor_budget_scales_with_window(self):
        from jhora.ai.prompts import anchor_budget
        assert anchor_budget(2048) == 819
        assert anchor_budget(4096) == 1638
        assert anchor_budget(8192) == 3276
        assert anchor_budget(131072) == 6000

    def test_anchor_sections_survive_small_window(self):
        from jhora.ai.prompts import conversation_anchor, _estimate_tokens
        cd = _sample_chart()
        anchor = conversation_anchor(cd, max_context=8192)
        assert "--- CHART ---" in anchor
        assert _estimate_tokens(anchor) <= 3276 + 2000
        small = conversation_anchor(cd, max_context=2048)
        assert "--- CHART ---" in small
        assert len(small) <= len(anchor)

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

    def test_analysis_text_has_choghadiya(self):
        cd = _sample_chart()
        text = build_analysis_text(cd)
        assert "Choghadiya" in text
        assert "Day " in text and "Night " in text

    def test_analysis_text_has_panchanga(self):
        from jhora.calc.muhurta import compute_panchanga
        cd = _sample_chart()
        text = build_analysis_text(cd)
        assert "Panchanga Info:" in text
        for label in ("Tithi:", "Nakshatra:", "Yoga:", "Karana:",
                      "Weekday:"):
            assert label in text
        # Karana matches the canonical computation (same inputs as the
        # snapshot: birth date at 12:00 UTC).
        info = compute_panchanga(cd.birth_date.replace(hour=12, minute=0),
                                 cd.latitude, cd.longitude, 0.0)
        assert f"Karana: {info.karana_name}" in text

    def test_analysis_text_has_muhurta_adjuncts(self):
        from jhora.ai.analysis import muhurta_adjuncts_snapshot
        from jhora.types.nakshatra import Nakshatra

        cd = _sample_chart()
        janma, _pada = Nakshatra.from_longitude(cd.moon.longitude)
        assert janma is not None
        text = build_analysis_text(cd)
        assert "MUHURTA ADJUNCTS" in text
        snapshot = muhurta_adjuncts_snapshot(cd)
        assert "Durmuhurta avoid" in snapshot
        assert "Varjya avoid" in snapshot
        assert "Panchaka avoid" in snapshot
        assert "Chandra Bala:" in snapshot
        assert "Tara Bala:" in snapshot

    def test_json_export_has_choghadiya(self):
        from jhora.ai.json_export import full_analysis
        cd = _sample_chart()
        result = full_analysis(
            f"{cd.birth_date.strftime('%Y-%m-%d %H:%M:%S')} {cd.timezone} "
            f"{cd.latitude:.4f} {cd.longitude:.4f}"
        )
        ch = result.get("choghadiya", {})
        assert ch, "choghadiya block missing from JSON export"
        assert len(ch.get("day", [])) == 8
        assert len(ch.get("night", [])) == 8
        assert ch["day"][0]["slot"] and ch["day"][0]["rating"]


class TestModelResolution:
    """Auto model resolution: pick a chat model regardless of server state."""

    def _lm(self, monkeypatch, items, load_ok=True):
        import jhora.ai.engine as eng
        monkeypatch.setattr(eng, "_lmstudio_catalog", lambda base_url, timeout=5.0: items)
        monkeypatch.setattr(eng, "_load_with_fallback",
                            lambda base_url, model_key, want_ctx,
                            min_ctx=1024, timeout=120.0: "inst-1" if load_ok else "")
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
        assert r["model"] == "inst-1"  # pinned to the loaded instance
        assert engine.config.model == "inst-1"
        assert "inst-1" in engine._managed_instances
        assert "automatically" in r["message"] or "Loaded" in r["message"]

    def test_no_chat_model_suggests_under_9gb(self, monkeypatch):
        items = [{"id": "hf.co/x/text-embedding-nomic-embed-text-v1.5",
                  "loaded": True, "type": "embeddings"}]
        engine = self._lm(monkeypatch, items)
        r = engine.resolve_model()
        assert r["status"] == "no_model"
        assert r["model"] == ""
        assert "Ministral" in r["message"]

    def test_no_chat_model_load_failed_suggests(self, monkeypatch):
        items = [{"id": "hf.co/x/qwen3-8b", "loaded": False, "type": "chat"}]
        engine = self._lm(monkeypatch, items, load_ok=False)
        r = engine.resolve_model()
        assert r["status"] == "no_model"
        assert "Ministral" in r["message"]

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
        monkeypatch.setattr(eng, "_load_with_fallback",
                            lambda base_url, model_key, want_ctx,
                            min_ctx=1024, timeout=120.0: "inst-9")
        engine = AiEngine(AiConfig(provider="lmstudio",
                                   model="text-embedding-nomic-embed-text-v1.5"))
        assert engine._ensure_chat_model() is None
        assert engine.config.model == "inst-9"

    def test_ensure_chat_model_blocks_with_suggestion(self, monkeypatch):
        items = [{"id": "hf.co/x/nomic-embed-text-v1.5", "loaded": True,
                  "type": "embeddings"}]
        engine = self._lm(monkeypatch, items)
        out = engine._ensure_chat_model()
        assert out is not None
        assert "Ministral" in out

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
        for prov in ("ollama", "unsloth", "custom"):
            msg = _download_suggestion(prov)
            assert "9GB" in msg, prov
            assert prov in msg or "chat" in msg

    def test_is_model_refusal(self):
        import requests
        from jhora.ai.engine import _is_model_refusal

        def err(status, text=""):
            e = requests.exceptions.HTTPError(f"HTTP {status}")
            e.response = type("R", (), {"status_code": status,
                                        "text": text})()
            return e
        assert _is_model_refusal(err(404)) is True
        assert _is_model_refusal(err(400, "not loaded, switch model")) is True
        assert _is_model_refusal(err(500, "boom")) is False
        assert _is_model_refusal(Exception("x")) is False

    def test_404_falls_back_to_loaded_model(self, monkeypatch):
        import requests
        import jhora.ai.engine as eng
        monkeypatch.setattr(eng, "_generic_catalog",
                            lambda base_url, timeout=8.0: [
            {"id": "stale-model", "loaded": False, "type": "llm"},
            {"id": "live-model", "loaded": True, "type": "llm"},
        ])
        engine = AiEngine(AiConfig(provider="unsloth",
                                   base_url="http://x:8888/v1",
                                   model="stale-model"))
        calls = {"n": 0}
        seen = {}

        def fake_call(messages, stream=False):
            calls["n"] += 1
            seen[calls["n"]] = engine.config.model
            if calls["n"] == 1:
                e = requests.exceptions.HTTPError("404 Not Found")
                e.response = type(
                    "R", (), {"status_code": 404,
                              "text": "not loaded, switch model by request"})()
                raise e
            return {"dummy": True}

        monkeypatch.setattr(engine, "_call", fake_call)
        monkeypatch.setattr(engine, "_stream_response",
                            lambda resp, on_token=None: "recovered reply")
        notes = []
        text = engine._chat_completion([{"role": "user", "content": "hi"}],
                                       on_token=notes.append)
        assert calls["n"] == 2
        assert seen[1] == "stale-model"
        assert seen[2] == "live-model"
        assert text == "recovered reply"
        assert any("stale-model" in n and "live-model" in n for n in notes)

    def test_500_does_not_swap_model(self, monkeypatch):
        import requests
        import jhora.ai.engine as eng
        monkeypatch.setattr(eng, "_generic_catalog",
                            lambda base_url, timeout=8.0: [
            {"id": "stale-model", "loaded": False, "type": "llm"},
            {"id": "live-model", "loaded": True, "type": "llm"},
        ])
        engine = AiEngine(AiConfig(provider="unsloth",
                                   base_url="http://x:8888/v1",
                                   model="stale-model"))
        calls = {"n": 0}

        def fake_call(messages, stream=False):
            calls["n"] += 1
            if calls["n"] == 1:
                e = requests.exceptions.HTTPError("500 boom")
                e.response = type("R", (), {"status_code": 500,
                                            "text": "boom"})()
                raise e
            return {"dummy": True}

        monkeypatch.setattr(engine, "_call", fake_call)
        monkeypatch.setattr(engine, "_stream_response",
                            lambda resp, on_token=None: "second try")
        notes = []
        engine._chat_completion([{"role": "user", "content": "hi"}],
                                on_token=notes.append)
        assert calls["n"] == 2
        assert engine.config.model == "stale-model"  # kept, not swapped
        assert not any("instead" in n for n in notes)

    def test_unsloth_ctx_from_catalog(self, monkeypatch):
        import requests as _requests
        import jhora.ai.engine as eng

        class _FakeResp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"object": "list", "data": [
                    {"id": "unsloth/Qwen3.8-27B-GGUF", "loaded": True,
                     "context_length": 8448,
                     "max_context_length": 8448},
                    {"id": "other", "loaded": False,
                     "context_length": 4096},
                ]}
        monkeypatch.setattr(_requests, "get", lambda *a, **k: _FakeResp())
        assert eng._unsloth_context_length("http://x:8888/v1", "whatever") == 0
        assert eng._unsloth_context_length("http://x:8888/v1", "loaded") == 8448
        assert eng._unsloth_context_length(
            "http://x:8888/v1", "unsloth/Qwen3.8-27B-GGUF") == 8448

    def test_lmstudio_suggestion_names_slate(self):
        from jhora.ai.engine import _download_suggestion
        msg = _download_suggestion("lmstudio")
        assert "Ministral" in msg and "Qwen3.5 9B" in msg

    def test_supported_models_matchable(self):
        import jhora.ai.engine as eng
        items = [{"id": "mistralai/ministral-3-14b-reasoning",
                  "display": "Ministral"},
                 {"id": "qwen/qwen3.5-9b", "display": "Qwen"}]
        for preset in eng.SUPPORTED_MODELS:
            assert eng._match_preferred(items, preset["match"]), preset


class TestMessageRolesAlternate:
    """Strict chat templates (Ministral-3 500s) require user/assistant
    alternation after a single system message — no consecutive users."""

    @staticmethod
    def _assert_alternates(messages):
        roles = [m["role"] for m in messages]
        assert roles[0] == "system"
        assert roles.count("system") == 1
        for a, b in zip(roles[1:], roles[2:]):
            assert not (a == b == "user"), roles

    def test_first_turn(self):
        msgs = AiEngine._chat_messages("ANCHOR", "q?", [])
        self._assert_alternates(msgs)
        assert "ANCHOR" in msgs[0]["content"]
        assert msgs[-1] == {"role": "user", "content": "q?"}

    def test_history_and_lead_in(self):
        hist = [{"role": "user", "content": "q1"},
                {"role": "assistant", "content": "a1"}]
        msgs = AiEngine._chat_messages("ANCHOR", "q2?", hist,
                                       lead_in="SUMMARY")
        self._assert_alternates(msgs)
        assert "SUMMARY" in msgs[0]["content"]

    def test_teacher_compaction_single_user(self, monkeypatch):
        from jhora.ai.teacher import AiTeacher
        t = AiTeacher(provider="lmstudio", base_url="http://x:1234/v1",
                      model="m", max_context_tokens=50)
        hist = [{"role": "user", "content": "q1 " * 50},
                {"role": "assistant", "content": "a1 " * 50}]
        captured = {}

        def fake_stream(messages, on_token=None):
            captured["messages"] = messages
            return "done"
        monkeypatch.setattr(t, "_stream", fake_stream)
        ans, new_hist, reset = t.chat("Tell me about Saturn periods",
                                      chart=None, history=hist)
        assert reset is True
        assert ans == "done"
        self._assert_alternates(captured["messages"])


class TestThinkingCapGating:
    """Neither engine nor teacher may send max_thinking_tokens (proven live
    to end completions instead of answering); Ollama keeps reasoning_effort,
    which plain models ignore."""

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

    def test_lmstudio_omits_thinking_cap(self, monkeypatch):
        """Proven live: the cap ends the whole completion instead of
        transitioning to the answer (empty replies). Never send it."""
        captured = self._post(monkeypatch)
        engine = AiEngine(AiConfig(provider="lmstudio",
                                   base_url="http://x:1234/v1", model="m"))
        engine._call([{"role": "user", "content": "hi"}], stream=False)
        assert "max_thinking_tokens" not in captured["payload"]

    def test_ollama_omits_thinking_cap(self, monkeypatch):
        captured = self._post(monkeypatch)
        engine = AiEngine(AiConfig(provider="ollama",
                                   base_url="http://x:11434/v1", model="m"))
        engine._call([{"role": "user", "content": "hi"}], stream=False)
        assert "max_thinking_tokens" not in captured["payload"]

    def test_ollama_bounds_reasoning_effort_for_thinking_models(self, monkeypatch):
        captured = self._post(monkeypatch)
        engine = AiEngine(AiConfig(provider="ollama",
                                   base_url="http://x:11434/v1",
                                   model="qwen3:0.6b"))
        engine._call([{"role": "user", "content": "hi"}], stream=False)
        assert captured["payload"]["reasoning_effort"] == "low"

    def test_ollama_no_reasoning_effort_for_plain_models(self, monkeypatch):
        captured = self._post(monkeypatch)
        engine = AiEngine(AiConfig(provider="ollama",
                                   base_url="http://x:11434/v1", model="gemma3:1b"))
        engine._call([{"role": "user", "content": "hi"}], stream=False)
        assert "reasoning_effort" not in captured["payload"]

    def test_teacher_omits_thinking_cap(self, monkeypatch):
        from jhora.ai.teacher import AiTeacher
        captured = self._post(monkeypatch)
        t = AiTeacher(provider="lmstudio", base_url="http://x:1234/v1",
                      model="m")
        t._stream([{"role": "user", "content": "hi"}])
        assert "max_thinking_tokens" not in captured["payload"]


class TestNullModelCatalog:
    """Ollama returns `"data": null` on /v1/models when nothing is installed;
    the catalog and health check must degrade to empty, not crash."""

    def _null_resp(self, body):
        import types
        resp = types.SimpleNamespace()
        resp.status_code = 200
        resp.ok = True
        resp.json = lambda: body
        resp.raise_for_status = lambda: None
        return resp

    def test_generic_catalog_handles_null_data(self, monkeypatch):
        import requests as _requests
        monkeypatch.setattr(_requests, "get",
                            lambda *a, **k: self._null_resp(
                                {"object": "list", "data": None}))
        assert _generic_catalog("http://x:11434/v1") == []

    def test_health_check_handles_null_data(self, monkeypatch):
        import requests as _requests
        calls = {"n": [0]}

        def fake_get(url, timeout=None):
            calls["n"][0] += 1
            if url.endswith("/models"):
                return self._null_resp({"object": "list", "data": None})
            raise AssertionError(f"unexpected url {url}")

        monkeypatch.setattr(_requests, "get", fake_get)
        engine = AiEngine(AiConfig(provider="ollama",
                                   base_url="http://x:11434/v1",
                                   model="qwen3:0.6b"))
        monkeypatch.setattr(
            engine, "resolve_model",
            lambda timeout=6: {"status": "no_model", "model": "", "message": "m",
                               "available": [], "loaded": []})
        result = engine.health_check()
        assert result["ok"] is True
        assert result["models"] == []


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


# ---- Tasks 1.1–1.3: context detection ---------------------------------

class TestContextDetection:

    def test_lmstudio_ctx_from_catalog(self, monkeypatch):
        """_lmstudio_catalog exposes max_context_length as ctx."""
        from jhora.ai import engine as eng
        monkeypatch.setattr(eng, "_lmstudio_catalog", lambda base_url, timeout=5.0: [
            {"id": "m1", "loaded": True, "type": "chat",
             "arch": "qwen", "quant": "q4", "ctx": 16384},
        ])
        enginst = AiEngine(AiConfig(provider="lmstudio",
                                     base_url="http://x:1234/v1", model="m1"))
        ctx = enginst.detect_context_length()
        assert ctx == 16384

    def test_lmstudio_ctx_zero_when_absent(self, monkeypatch):
        from jhora.ai import engine as eng
        monkeypatch.setattr(eng, "_lmstudio_catalog", lambda base_url, timeout=5.0: [
            {"id": "m1", "loaded": True, "type": "chat", "ctx": 0},
        ])
        enginst = AiEngine(AiConfig(provider="lmstudio",
                                     base_url="http://x:1234/v1", model="m1"))
        assert enginst.detect_context_length() == 0

    def test_lmstudio_ctx_prefers_loaded_length(self, monkeypatch):
        """Loaded window wins over the theoretical maximum (1M vs 8K live)."""
        import requests as _requests
        import jhora.ai.engine as eng

        class _FakeResp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"data": [
                    {"id": "m1", "state": "loaded", "type": "llm",
                     "max_context_length": 1048576,
                     "loaded_context_length": 8192},
                    {"id": "m2", "state": "not-loaded", "type": "llm",
                     "max_context_length": 262144},
                ]}

        monkeypatch.setattr(_requests, "get", lambda *a, **k: _FakeResp())
        by_id = {m["id"]: m
                 for m in eng._lmstudio_catalog("http://x:1234/v1")}
        assert by_id["m1"]["ctx"] == 8192
        assert by_id["m2"]["ctx"] == 262144

    def test_ollama_ctx_from_model_info(self, monkeypatch):
        """Ollama /api/show model_info.gpt-oss.context_length is parsed."""
        import requests as _requests
        import types
        fake = types.SimpleNamespace()
        fake.raise_for_status = lambda: None
        fake.json = lambda: {"model_info": {"gpt-oss.context_length": 32768}}
        monkeypatch.setattr(_requests, "post", lambda url, json=None, timeout=None: fake)
        from jhora.ai.engine import _ollama_context_length
        assert _ollama_context_length("http://x:11434/v1", "gemma3:1b") == 32768

    def test_ollama_ctx_from_num_ctx_param(self, monkeypatch):
        import requests as _requests
        import types
        fake = types.SimpleNamespace()
        fake.raise_for_status = lambda: None
        fake.json = lambda: {"model_info": {},
                             "parameters": "temperature 0.7\nnum_ctx 8192"}
        monkeypatch.setattr(_requests, "post", lambda url, json=None, timeout=None: fake)
        from jhora.ai.engine import _ollama_context_length
        assert _ollama_context_length("http://x:11434/v1", "qwen3:0.6b") == 8192

    def test_ollama_ctx_zero_when_no_report(self, monkeypatch):
        import requests as _requests
        import types
        fake = types.SimpleNamespace()
        fake.raise_for_status = lambda: None
        fake.json = lambda: {"model_info": {}}
        monkeypatch.setattr(_requests, "post", lambda url, json=None, timeout=None: fake)
        from jhora.ai.engine import _ollama_context_length
        assert _ollama_context_length("http://x:11434/v1", "m") == 0

    def test_sync_context_length_uses_default_on_failure(self, monkeypatch):
        enginst = AiEngine(AiConfig(provider="custom",
                                     base_url="http://x:9999/v1", model="x"))
        enginst._sync_context_length()
        # custom provider — no detection; stays at default
        assert enginst.config.max_context_tokens == 4096

    def test_sync_context_length_overrides_default(self, monkeypatch):
        from jhora.ai import engine as eng
        monkeypatch.setattr(eng, "_lmstudio_catalog", lambda base_url, timeout=5.0: [
            {"id": "m1", "loaded": True, "type": "chat",
             "arch": "qwen", "quant": "q4", "ctx": 32768},
        ])
        enginst = AiEngine(AiConfig(provider="lmstudio",
                                     base_url="http://x:1234/v1", model="m1"))
        assert enginst.config.max_context_tokens == 4096  # default
        enginst._sync_context_length()
        assert enginst.config.max_context_tokens == 32768

    def test_sync_context_length_stays_when_user_set_explicit(self, monkeypatch):
        from jhora.ai import engine as eng
        monkeypatch.setattr(eng, "_lmstudio_catalog", lambda base_url, timeout=5.0: [
            {"id": "m1", "loaded": True, "type": "chat", "ctx": 65536},
        ])
        cfg = AiConfig(provider="lmstudio",
                       base_url="http://x:1234/v1", model="m1",
                       max_context_tokens=8192)  # user explicit
        enginst = AiEngine(cfg)
        enginst._sync_context_length()
        # explicit non-default is untouched (detect runs but keeps existing)
        assert enginst.config.max_context_tokens == 8192

    def test_sync_context_length_idempotent(self, monkeypatch):
        from jhora.ai import engine as eng
        calls = {"n": 0}
        def _cat(base_url, timeout=5.0):
            calls["n"] += 1
            return [{"id": "m1", "loaded": True, "type": "chat", "ctx": 16384}]
        monkeypatch.setattr(eng, "_lmstudio_catalog", _cat)
        enginst = AiEngine(AiConfig(provider="lmstudio",
                                     base_url="http://x:1234/v1", model="m1"))
        enginst._sync_context_length()
        assert calls["n"] == 1
        assert enginst.config.max_context_tokens == 16384
        enginst._sync_context_length()
        assert calls["n"] == 1  # second call skipped (model unchanged)


# ---- Tasks 2.1–2.3: threaded chat + budget monitor ---------------------

class TestConversationChat:

    def _engine(self):
        return AiEngine(AiConfig(provider="custom",
                                 base_url="http://localhost:1/v1", model="x",
                                 max_context_tokens=1_000_000))

    def test_chat_includes_prior_history_in_request(self, monkeypatch):
        """The engine re-sends the full thread (history + new question) to the model."""
        enginst = self._engine()
        captured = {}

        def fake_chat_completion(messages, on_token=None):
            captured["messages"] = messages
            return "Moon in Aries answer"

        monkeypatch.setattr(enginst, "_chat_completion", fake_chat_completion)
        cd = _sample_chart()
        hist = [{"role": "user", "content": "What about my career?"},
                {"role": "assistant", "content": "Mars in the 10th house."}]
        answer, new_hist, reset = enginst.chat(cd, "And marriage?",
                                               history=hist)
        msgs = captured["messages"]
        all_text = " ".join(m.get("content", "") for m in msgs)
        assert "What about my career?" in all_text
        assert "Mars in the 10th house." in all_text
        assert "And marriage?" in all_text
        assert answer == "Moon in Aries answer"
        assert reset is False
        assert new_hist[2]["content"] == "And marriage?"
        assert new_hist[3]["content"] == "Moon in Aries answer"

    def test_chat_does_not_rebuild_anchor_each_turn(self, monkeypatch):
        """Anchor is cached per chart; building it more than once per chart is a bug."""
        import jhora.ai.engine as eng_mod
        builds = {"n": 0}
        orig = eng_mod.conversation_anchor

        def counted(cd, max_context=4096):
            builds["n"] += 1
            return orig(cd, max_context)

        monkeypatch.setattr(eng_mod, "conversation_anchor", counted)
        enginst = self._engine()
        cd = _sample_chart()
        enginst.chat(cd, "Q1")
        enginst.chat(cd, "Q2")
        assert builds["n"] == 1  # cached second time

    def test_budget_threshold_trips_above_boundary(self):
        enginst = self._engine()
        enginst.config.max_context_tokens = 1000
        # 1000 * 0.70 = 700; reserved = 600; raw message tokens needed = 100
        # 100 tokens ≈ 400 chars at 4 chars/token
        msgs = [{"role": "user", "content": "A" * 400}]
        assert enginst._budget_exceeded(msgs) is True

    def test_budget_threshold_does_not_trip_below_boundary(self):
        enginst = self._engine()
        enginst.config.max_context_tokens = 1000000  # huge
        msgs = [{"role": "user", "content": "A" * 400}]
        assert enginst._budget_exceeded(msgs) is False

    def test_context_usage_below_threshold_empty_history(self):
        enginst = self._engine()  # max_context_tokens=1_000_000
        used, threshold = enginst.context_usage(_sample_chart(), history=[])
        assert threshold == int(1_000_000 * AiEngine._BUDGET_THRESHOLD)
        assert used < threshold

    def test_context_usage_near_threshold(self):
        enginst = self._engine()
        cd = _sample_chart()
        used_full, _ = enginst.context_usage(cd, history=[])
        # Size the window so the trip wire sits just above current usage.
        enginst.config.max_context_tokens = int((used_full + 50) / 0.70)
        used, threshold = enginst.context_usage(cd, history=[])
        assert used == used_full  # usage independent of window size
        assert used < threshold
        assert threshold - used < 200  # near, not far

    def test_context_usage_over_threshold(self):
        enginst = self._engine()
        enginst.config.max_context_tokens = 1000  # trip wire at 700
        fat = [{"role": "user", "content": "A" * 10000}]
        used, threshold = enginst.context_usage(_sample_chart(), history=fat)
        assert threshold == 700
        assert used >= threshold


# ---- fix-lm-context-truncation: honest stream endings --------------------

def _sse_chunk(content="", finish=None, reasoning=""):
    import json as _json
    delta = {}
    if content:
        delta["content"] = content
    if reasoning:
        delta["reasoning_content"] = reasoning
    return "data: " + _json.dumps(
        {"choices": [{"delta": delta, "finish_reason": finish}]})


class _FakeSSE:
    def __init__(self, lines):
        self._lines = lines

    def raise_for_status(self):
        pass

    def iter_lines(self, decode_unicode=False):
        for ln in self._lines:
            yield ln.encode("utf-8")


class TestStreamHonesty:

    def _engine(self):
        return AiEngine(AiConfig(provider="custom",
                                 base_url="http://localhost:1/v1", model="x",
                                 max_context_tokens=1_000_000))

    def test_length_finish_appends_truncation_notice(self):
        enginst = self._engine()
        seen = []
        text = enginst._stream_response(_FakeSSE([
            _sse_chunk("Part one. "),
            _sse_chunk("", finish="length"),
            "[DONE]",
        ]), on_token=seen.append)
        assert text.startswith("Part one.")
        assert "[truncated — output budget exhausted]" in text
        assert "[truncated — output budget exhausted]" in "".join(seen)

    def test_stop_finish_returns_clean_text(self):
        enginst = self._engine()
        text = enginst._stream_response(_FakeSSE([
            _sse_chunk("All good."),
            _sse_chunk("", finish="stop"),
            "[DONE]",
        ]))
        assert text == "All good."

    def test_vanishing_stream_appends_interruption_notice(self):
        enginst = self._engine()
        text = enginst._stream_response(_FakeSSE([
            _sse_chunk("Half an"),
        ]))
        assert text.startswith("Half an")
        assert "[interrupted — connection ended before completion]" in text

    def test_reasoning_only_length_keeps_both_notices(self):
        enginst = self._engine()
        text = enginst._stream_response(_FakeSSE([
            _sse_chunk(reasoning="thinking..."),
            _sse_chunk("", finish="length"),
            "[DONE]",
        ]))
        assert "no visible answer" in text
        assert "[truncated — output budget exhausted]" in text

    def test_compact_returns_fresh_history(self, monkeypatch):
        enginst = self._engine()
        captured = {}

        def fake_chat_completion(messages, on_token=None):
            captured["messages"] = messages
            return "after-reset answer"

        monkeypatch.setattr(enginst, "_chat_completion", fake_chat_completion)
        # Force threshold to trip immediately
        monkeypatch.setattr(enginst, "_budget_exceeded", lambda msgs: True)
        cd = _sample_chart()
        old_hist = [{"role": "user", "content": "old question"},
                    {"role": "assistant", "content": "old answer"}]
        answer, new_hist, reset = enginst.chat(cd, "new question",
                                               history=old_hist)
        assert reset is True
        # Fresh history: only the current Q/A, no trace of old thread
        assert len(new_hist) == 2
        assert new_hist[0] == {"role": "user", "content": "new question"}
        assert new_hist[1] == {"role": "assistant", "content": "after-reset answer"}
        assert "old question" not in str(new_hist)
        # The summary rides inside the system message (index 0, fused with
        # the anchor — strict templates forbid consecutive user messages)
        system_text = captured["messages"][0].get("content", "")
        assert "Earlier in this conversation" in system_text
        assert captured["messages"][-1] == {"role": "user",
                                            "content": "new question"}

    def test_compact_not_triggered_on_first_turn(self, monkeypatch):
        enginst = self._engine()
        called = {"flag": False}

        def tracking_budget(msgs):
            called["flag"] = True
            return False

        monkeypatch.setattr(enginst, "_budget_exceeded", tracking_budget)
        cd = _sample_chart()
        ans, hist, reset = enginst.chat(cd, "first question")
        assert called["flag"] is False  # skipped because history empty
        assert reset is False

    def test_continue_chat_aliases_chat(self, monkeypatch):
        enginst = self._engine()
        monkeypatch.setattr(enginst, "_chat_completion",
                            lambda msgs, on_token=None: "x")
        cd = _sample_chart()
        r1 = enginst.chat(cd, "Q")
        r2 = enginst.continue_chat(cd, "R", history=r1[1])
        assert r2[0] == "x"


# ---- Tasks 3.1–3.2: threaded teacher ------------------------------------

class TestTeacherChat:

    def _teacher(self):
        from jhora.ai.teacher import AiTeacher
        t = AiTeacher(provider="custom",
                      base_url="http://localhost:1/v1",
                      model="x",
                      max_context_tokens=1_000_000)
        # Stub the embedding store search so tests don't need a database
        t.store = type("Stub", (), {"search": lambda self, q, top_k=4: []})()
        return t

    def test_teacher_ask_one_shot_unchanged(self, monkeypatch):
        """ask() returns a plain string — no threading semantics."""
        t = self._teacher()
        monkeypatch.setattr(t, "_stream",
                            lambda messages, on_token=None: "one-shot answer")
        result = t.ask("What is Shadbala?")
        assert isinstance(result, str)
        assert result == "one-shot answer"

    def test_teacher_chat_returns_tuple_with_history(self, monkeypatch):
        t = self._teacher()
        monkeypatch.setattr(t, "_stream",
                            lambda messages, on_token=None: "chat answer")
        answer, hist, reset = t.chat("What is Shadbala?")
        assert answer == "chat answer"
        assert reset is False
        assert len(hist) == 2
        assert hist[0]["role"] == "user"
        assert hist[0]["content"] == "What is Shadbala?"
        assert hist[1]["content"] == "chat answer"

    def test_teacher_chat_sends_full_thread(self, monkeypatch):
        t = self._teacher()
        captured = {}
        monkeypatch.setattr(t, "_stream",
                            lambda messages, on_token=None: (
                                captured.__setitem__("msgs", messages),
                                "r")[1])
        hist = [{"role": "user", "content": "What is Rahu?"},
                {"role": "assistant", "content": "Rahu is the north node."}]
        answer, new_hist, reset = t.chat("And Ketu?", history=hist)
        msgs = captured["msgs"]
        all_text = " ".join(m.get("content", "") for m in msgs)
        assert "What is Rahu?" in all_text
        assert "And Ketu?" in all_text
        assert "Rahu is the north node" in all_text

    def test_teacher_chat_budget_compact(self, monkeypatch):
        """Budget exceeded → compact-and-restart with fresh history."""
        t = self._teacher()
        t.max_context_tokens = 1000  # tiny context
        monkeypatch.setattr(t, "_stream",
                            lambda messages, on_token=None: "after compact")
        monkeypatch.setattr(t, "_budget_exceeded", lambda msgs: True)
        old_hist = [{"role": "user", "content": "old Q"},
                    {"role": "assistant", "content": "old A"}]
        answer, new_hist, reset = t.chat("new Q", history=old_hist)
        assert reset is True
        assert len(new_hist) == 2  # only new Q/A
        assert new_hist[0]["content"] == "new Q"
        assert new_hist[1]["content"] == "after compact"
        assert "old Q" not in str(new_hist)

    def test_teacher_chat_no_compact_on_first_turn(self, monkeypatch):
        t = self._teacher()
        called = {"n": 0}
        def track(msgs):
            called["n"] += 1
            return False
        monkeypatch.setattr(t, "_budget_exceeded", track)
        monkeypatch.setattr(t, "_stream",
                            lambda messages, on_token=None: "first")
        answer, hist, reset = t.chat("first Q")
        assert called["n"] == 0
        assert reset is False

    def test_teacher_explain_feature_uses_ask(self, monkeypatch):
        t = self._teacher()
        monkeypatch.setattr(t, "_stream",
                            lambda messages, on_token=None: "feat")
        r = t.explain_feature("chart")
        assert r == "feat"

    def test_teacher_chat_with_chart(self, monkeypatch):
        t = self._teacher()
        captured = {}
        monkeypatch.setattr(t, "_stream",
                            lambda messages, on_token=None: (
                                captured.__setitem__("msgs", messages),
                                "chart taught")[1])
        cd = _sample_chart()
        answer, hist, reset = t.chat("What does my Moon mean?", chart=cd)
        msgs = captured["msgs"]
        all_text = " ".join(m.get("content", "") for m in msgs)
        assert "Moon" in all_text
        assert "CHART DATA" in all_text


    def test_teacher_stream_length_appends_truncation_notice(self, monkeypatch):
        import requests as _requests
        t = self._teacher()
        monkeypatch.setattr(
            _requests, "post",
            lambda *a, **k: _FakeSSE([
                _sse_chunk("Partial lesson. "),
                _sse_chunk("", finish="length"),
                "[DONE]",
            ]))
        seen = []
        text = t._stream([{"role": "user", "content": "Q"}],
                         on_token=seen.append)
        assert text.startswith("Partial lesson.")
        assert "[truncated — output budget exhausted]" in text
        assert "[truncated — output budget exhausted]" in "".join(seen)

    def test_teacher_stream_stop_returns_clean_text(self, monkeypatch):
        import requests as _requests
        t = self._teacher()
        monkeypatch.setattr(
            _requests, "post",
            lambda *a, **k: _FakeSSE([
                _sse_chunk("Complete lesson."),
                _sse_chunk("", finish="stop"),
                "[DONE]",
            ]))
        assert t._stream([{"role": "user", "content": "Q"}]) == \
            "Complete lesson."

    def test_teacher_stream_vanishing_appends_interruption(self, monkeypatch):
        import requests as _requests
        t = self._teacher()
        monkeypatch.setattr(
            _requests, "post",
            lambda *a, **k: _FakeSSE([_sse_chunk("Half a")]))
        text = t._stream([{"role": "user", "content": "Q"}])
        assert "[interrupted — connection ended before completion]" in text

    def test_teacher_static_block_cached_per_chart(self, monkeypatch):
        """Static chart/analysis block builds once; passages stay fresh."""
        import jhora.ai.teacher as teach_mod
        t = self._teacher()
        builds = {"detailed": 0, "analysis": 0}
        orig_cd, orig_an = (teach_mod._chart_detailed,
                            teach_mod.build_analysis_text)

        def counted_cd(chart):
            builds["detailed"] += 1
            return orig_cd(chart)

        def counted_an(chart):
            builds["analysis"] += 1
            return orig_an(chart)

        monkeypatch.setattr(teach_mod, "_chart_detailed", counted_cd)
        monkeypatch.setattr(teach_mod, "build_analysis_text", counted_an)
        cd = _sample_chart()
        m1 = t._build_user_message("Q1", chart=cd)
        m2 = t._build_user_message("Q2", chart=cd)
        assert builds == {"detailed": 1, "analysis": 1}
        assert "Q1" in m1 and "Q2" in m2  # questions still differ per turn

    def test_chat_records_last_sources(self, monkeypatch):
        t = self._teacher()
        t.store = type("Stub", (), {"search": lambda self, q, top_k=4: [
            {"source": "BPHS", "content": "x" * 500},
            {"source": "US", "content": "y"},
        ]})()
        monkeypatch.setattr(t, "_stream",
                            lambda messages, on_token=None: "taught")
        answer, hist, reset = t.chat("What is Shadbala?")
        assert answer == "taught"
        assert t.last_sources == [
            {"source": "BPHS", "excerpt": "x" * 400},
            {"source": "US", "excerpt": "y"},
        ]

    def test_budget_sums_contents_not_messages(self):
        t = self._teacher()
        t.max_context_tokens = 1000  # trip wire at 700
        fat = [{"role": "user", "content": "A" * 10000}]
        assert t._budget_exceeded(fat) is True
        assert t._budget_exceeded(
            [{"role": "user", "content": "hi"}]) is False

    def test_context_usage_below_and_over_threshold(self):
        t = self._teacher()  # max_context_tokens=1_000_000
        used, threshold = t.context_usage(chart=None, history=[])
        assert threshold == int(1_000_000 * 0.70)
        assert used < threshold
        t.max_context_tokens = 1000
        used, _ = t.context_usage(
            chart=None, history=[{"role": "user", "content": "A" * 10000}])
        assert used >= 700
