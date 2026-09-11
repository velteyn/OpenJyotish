"""Tests for LM Studio setup management (v1 API + preferred model).

Policy under test: per-machine preferred key, VRAM-safe load with context
halving, unload only instances the app itself loaded — never user models.
"""

import pytest

import jhora.ai.engine as eng
from jhora.ai.engine import AiConfig, AiEngine


def _v1_payload():
    return {"models": [
        {"type": "llm", "publisher": "x", "key": "mythos-9b",
         "display_name": "Mythos 9B Tale", "architecture": "qwen35",
         "quantization": {"name": "Q4_K"}, "params_string": "9B",
         "max_context_length": 1048576,
         "loaded_instances": [
             {"id": "inst-mythos", "config": {"context_length": 8192},
              "remaining_ttl_seconds": 3000}]},
        {"type": "llm", "publisher": "x", "key": "qwen/qwen3.5-9b",
         "display_name": "Qwen3.5 9B", "architecture": "qwen35",
         "quantization": {"name": "Q4_K_XL"}, "params_string": "9B",
         "max_context_length": 262144, "loaded_instances": []},
        {"type": "llm", "publisher": "x", "key": "ministral-14b",
         "display_name": "Ministral 3 14B Reasoning", "architecture": "mistral",
         "quantization": {"name": "Q4_K_M"}, "params_string": "14B",
         "max_context_length": 262144, "loaded_instances": []},
        {"type": "embeddings", "publisher": "x", "key": "emb",
         "display_name": "nomic-embed", "architecture": "bert",
         "quantization": {"name": "Q4_0"}, "params_string": "",
         "max_context_length": 2048, "loaded_instances": []},
    ]}


class _Resp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")


class TestV1Catalog:
    def test_parses_instances_params_ctx(self, monkeypatch):
        monkeypatch.setattr("requests.get",
                            lambda url, timeout=5.0: _Resp(_v1_payload()))
        items = eng._lmstudio_catalog("http://x:1234/v1")
        by_id = {m["id"]: m for m in items}
        mythos = by_id["mythos-9b"]
        assert mythos["loaded"] is True
        assert mythos["instance_id"] == "inst-mythos"
        assert mythos["ctx"] == 8192
        assert mythos["params"] == 9.0
        assert mythos["ttl"] == 3000
        qwen = by_id["qwen/qwen3.5-9b"]
        assert qwen["loaded"] is False
        assert qwen["ctx"] == 0
        assert qwen["max_ctx"] == 262144

    def test_falls_back_to_v0(self, monkeypatch):
        import requests

        def fake_get(url, timeout=5.0):
            if "/api/v1/models" in url:
                raise requests.exceptions.HTTPError("HTTP 404")
            return _Resp({"data": [{"id": "old-qwen", "state": "loaded",
                                    "type": "llm",
                                    "loaded_context_length": 4096}]})
        monkeypatch.setattr("requests.get", fake_get)
        items = eng._lmstudio_catalog("http://x:1234/v1")
        assert items[0]["id"] == "old-qwen"
        assert items[0]["loaded"] is True
        assert items[0]["ctx"] == 4096


class TestHelpers:
    def test_params_size(self):
        assert eng._params_size("9B") == 9.0
        assert eng._params_size("Qwen 7.5B tale") == 7.5
        assert eng._params_size("???") == 0.0

    def test_match_preferred_exact_first(self):
        items = [{"id": "a/qwen-9b", "display": "Qwen"},
                 {"id": "qwen-9b", "display": "Qwen exact"}]
        assert eng._match_preferred(items, "qwen-9b")[0]["id"] == "qwen-9b"
        assert eng._match_preferred(items, "QWEN")[0]["id"] == "a/qwen-9b"
        assert eng._match_preferred(items, "nope") == []


class TestLoadFallback:
    def test_halves_context_on_refusal(self, monkeypatch):
        calls = []

        def fake_load(base, key, ctx, timeout=120.0):
            calls.append(ctx)
            return "inst-x" if ctx <= 4096 else ""
        monkeypatch.setattr(eng, "_lmstudio_load_v1", fake_load)
        inst = eng._load_with_fallback("http://x", "k", 8192, 4096)
        assert inst == "inst-x"
        assert calls == [8192, 4096]

    def test_gives_up_below_floor(self, monkeypatch):
        monkeypatch.setattr(eng, "_lmstudio_load_v1",
                            lambda b, k, c, timeout=120.0: "")
        assert eng._load_with_fallback("http://x", "k", 2048, 1024) == ""


class TestEnsureSetup:
    def _eng(self, monkeypatch, items, load_map=None, **cfg_kw):
        import jhora.ai.engine as e
        monkeypatch.setattr(e, "_lmstudio_catalog",
                            lambda base_url, timeout=8.0: items)
        calls = {"load": [], "unload": []}

        def fake_load(base, key, ctx, timeout=120.0):
            calls["load"].append((key, ctx))
            if load_map is None:
                return "inst-new"
            return load_map.get((key, ctx), "")

        def fake_unload(base, inst, timeout=15.0):
            calls["unload"].append(inst)
            return True

        monkeypatch.setattr(e, "_lmstudio_load_v1", fake_load)
        monkeypatch.setattr(e, "_lmstudio_unload", fake_unload)
        cfg = AiConfig(provider="lmstudio", **cfg_kw)
        engine = AiEngine(cfg)
        return engine, calls

    def _items(self):
        return [
            {"id": "qwen/qwen3.5-9b", "display": "Qwen3.5 9B",
             "loaded": True, "instance_id": "inst-qwen", "type": "llm",
             "ctx": 8192, "max_ctx": 262144, "params": 9.0},
            {"id": "mythos-9b", "display": "Mythos", "loaded": False,
             "instance_id": "", "type": "llm", "ctx": 0,
             "max_ctx": 1048576, "params": 9.0},
        ]

    def test_uses_loaded_preferred_without_action(self, monkeypatch):
        engine, calls = self._eng(monkeypatch, self._items(),
                                  preferred_model="qwen/qwen3.5-9b")
        r = engine.ensure_setup()
        assert r["status"] == "ok" and r["action"] == "using"
        assert r["model"] == "inst-qwen"
        assert engine.config.model == "inst-qwen"
        assert calls["load"] == [] and calls["unload"] == []

    def test_loads_missing_preferred_and_tracks(self, monkeypatch):
        items = [dict(m, loaded=False, instance_id="", ctx=0)
                 for m in self._items()]
        engine, calls = self._eng(monkeypatch, items,
                                  preferred_model="qwen/qwen3.5-9b",
                                  ensure_context=8192)
        r = engine.ensure_setup()
        assert r["status"] == "ok" and r["action"] == "loaded"
        assert calls["load"] == [("qwen/qwen3.5-9b", 8192)]
        assert "inst-new" in engine._managed_instances
        assert engine.config.model == "inst-new"

    def test_under_ctx_foreign_instance_is_kept_with_warning(self, monkeypatch):
        items = [dict(self._items()[0], ctx=2048)]
        engine, calls = self._eng(monkeypatch, items,
                                  preferred_model="qwen/qwen3.5-9b",
                                  min_context=4096)
        r = engine.ensure_setup()
        assert r["status"] == "ok" and r["action"] == "using"
        assert calls["unload"] == [] and calls["load"] == []
        assert "truncate" in r["message"]

    def test_under_ctx_managed_instance_is_reloaded(self, monkeypatch):
        items = [dict(self._items()[0], ctx=2048)]
        engine, calls = self._eng(monkeypatch, items,
                                  preferred_model="qwen/qwen3.5-9b",
                                  min_context=4096, ensure_context=8192)
        engine._managed_instances.add("inst-qwen")
        r = engine.ensure_setup()
        assert r["status"] == "ok" and r["action"] == "loaded"
        assert calls["load"] == [("qwen/qwen3.5-9b", 8192)]
        assert "inst-qwen" not in engine._managed_instances

    def test_replacement_unloads_old_managed(self, monkeypatch):
        items = [dict(m, loaded=False, instance_id="", ctx=0)
                 for m in self._items()]
        engine, calls = self._eng(monkeypatch, items,
                                  preferred_model="qwen/qwen3.5-9b")
        engine._managed_instances.add("inst-old")
        engine.ensure_setup()
        assert calls["unload"] == ["inst-old"]
        assert "inst-old" not in engine._managed_instances

    def test_unknown_preferred_falls_back(self, monkeypatch):
        engine, calls = self._eng(monkeypatch, self._items(),
                                  preferred_model="does-not-exist")
        r = engine.ensure_setup()
        assert r["status"] == "ok" and r["action"] == "fallback"
        assert "not found" in r["message"]
        assert calls["load"] == []  # something usable is already loaded

    def test_ensure_runs_once_per_key(self, monkeypatch):
        engine, calls = self._eng(monkeypatch, self._items(),
                                  preferred_model="qwen/qwen3.5-9b")
        assert engine._ensure_chat_model() is None
        assert engine._ensure_chat_model() is None  # second call is free
