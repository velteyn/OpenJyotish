"""AI Chat Engine — connects to Ollama, LM Studio, Unsloth Studio for chart reading.

All three services expose an OpenAI-compatible /v1/chat/completions endpoint.
Only the base URL and default model differ between providers.

The engine is model-resilient: it works regardless of which model the server
has loaded. If the configured model is a placeholder or an embedding model, it
enumerates the server's catalogue, picks a usable chat model (preferring an
already-loaded one, else auto-loading the best small one), and falls back to a
download suggestion (models ≤9GB) when nothing usable exists.
"""

import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Generator, List, Optional, Tuple

import requests

from jhora.charts.chart import ChartData
from jhora.ai.prompts import (
    SYSTEM_PROMPT,
    CONVERSATION_SUMMARY_PROMPT,
    _estimate_tokens,
    conversation_anchor,
    interpret_prompt,
    question_prompt,
    remedy_prompt,
    thread_recap,
)

# Provider presets
PROVIDERS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3.2",
    },
    "lmstudio": {
        "base_url": "http://localhost:1234/v1",
        "default_model": "loaded",
    },
    "unsloth": {
        "base_url": "http://localhost:8000/v1",
        "default_model": "unsloth-model",
    },
    "custom": {
        "base_url": "http://localhost:8000/v1",
        "default_model": "model",
    },
}

# Model values that mean "whatever the server has" rather than a concrete
# choice the user made. These are resolved to a real chat model at request time.
PLACEHOLDER_MODELS = {"", "loaded", "model", "unsloth-model", "auto", "llama3.2", "llama3"}

# Substrings identifying embedding models (which expose no /chat/completions).
EMBED_HINTS = ("embed", "text-embedding", "nomic", "bge", "gte-", "e5-")

# Model types reported by LM Studio that cannot do chat completions.
NON_CHAT_TYPES = ("embeddings", "embedding", "embed", "reranker", "rerank",
                  "tts", "audio", "stt", "whisper", "image", "torch")

# Model types reported by LM Studio / Ollama that can chat.
CHAT_TYPES = ("chat", "llm", "reason", "reasoning", "vlm", "vl", "complete")

# Known chat families, ordered by preference for automatic selection.
CHAT_FAMILIES = ("qwen", "llama", "mistral", "ministral", "gemma", "phi",
                 "deepseek", "zaya")


def _root_url(base_url: str) -> str:
    """Strip the OpenAI-compatible /v1 prefix to reach provider-native APIs."""
    b = base_url.rstrip("/")
    return b[: -len("/v1")] if b.endswith("/v1") else b


def _bare_name(model_id: str) -> str:
    """Last path segment of a model id, lowercased (e.g. 'qwen3.5-9b')."""
    return model_id.split("/")[-1].split("\\")[-1].lower()


def _looks_embedding(model_id: str) -> bool:
    low = _bare_name(model_id)
    return any(h in low for h in EMBED_HINTS)


def _lmstudio_catalog(base_url: str, timeout: float = 5.0) -> List[dict]:
    """List available models from LM Studio, including load state and type."""
    root = _root_url(base_url)
    resp = requests.get(f"{root}/api/v0/models", timeout=timeout)
    resp.raise_for_status()
    out = []
    for m in resp.json().get("data", []):
        out.append({
            "id": m.get("id") or m.get("name") or m.get("path") or "",
            "loaded": str(m.get("state", "")).lower() == "loaded",
            "type": str(m.get("type", "")).lower(),
            "arch": str(m.get("arch", "")).lower(),
            "quant": str(m.get("quantization", "")).lower(),
            "ctx": m.get("max_context_length") or m.get("loaded_context_length") or 0,
        })
    return out


def _lmstudio_load(base_url: str, model_id: str, timeout: float = 15.0) -> bool:
    """Ask LM Studio to load a model into memory."""
    root = _root_url(base_url)
    resp = requests.post(f"{root}/api/v0/models/load",
                         json={"model": model_id}, timeout=timeout)
    return resp.status_code in (200, 201, 202)


def _ollama_catalog(base_url: str, timeout: float = 5.0) -> List[dict]:
    """List installed models from Ollama, flagging currently loaded ones."""
    root = _root_url(base_url)
    resp = requests.get(f"{root}/api/tags", timeout=timeout)
    resp.raise_for_status()
    loaded = set()
    try:
        ps = requests.get(f"{root}/api/ps", timeout=2)
        if ps.ok:
            loaded = {str(m.get("name", "")) for m in ps.json().get("models", [])}
    except requests.exceptions.RequestException:
        pass
    out = []
    for m in resp.json().get("models", []):
        name = str(m.get("name", ""))
        details = m.get("details") or {}
        out.append({
            "id": name,
            "loaded": name in loaded,
            "type": "chat",
            "arch": str(details.get("family", "")).lower(),
            "quant": str(details.get("quantization_level", "")).lower(),
            "ctx": 0,
        })
    return out


_DEFAULT_CONTEXT_TOKENS = 4096  # conservative fallback when the server says nothing


def _ollama_context_length(base_url: str, model_id: str,
                           timeout: float = 5.0) -> int:
    """Best-effort context window for an Ollama model via ``/api/show``.

    Ollama exposes the model's GGUF metadata under ``model_info`` with a
    ``context_length`` key for the architecture (e.g. ``gpt-oss.context_length``
    or ``llama.context_length``). Some servers/setups report a ``num_ctx``
    parameter instead. Returns ``0`` when nothing usable is reported.
    """
    root = _root_url(base_url)
    try:
        resp = requests.post(f"{root}/api/show",
                             json={"model": model_id}, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        mi = data.get("model_info") or {}
        for key, value in mi.items():
            if "context_length" in key:
                try:
                    ctx = int(value)
                except (TypeError, ValueError):
                    continue
                if ctx > 0:
                    return ctx
        params = str(data.get("parameters") or "")
        m = re.search(r"num_ctx\s+(\d+)", params)
        if m:
            return int(m.group(1))
    except requests.exceptions.RequestException:
        pass
    return 0


def _generic_catalog(base_url: str, timeout: float = 5.0) -> List[dict]:
    """List models from any OpenAI-compatible /models endpoint."""
    resp = requests.get(f"{base_url.rstrip('/')}/models", timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    models = data if isinstance(data, list) else (data.get("data") or [])
    out = []
    for m in models:
        if isinstance(m, str):
            out.append({"id": m, "type": "chat"})
        else:
            out.append({"id": m.get("id") or m.get("name") or "", "type": "chat"})
    return out


def _is_chat_model(info: dict) -> bool:
    """True if the catalogue entry can answer chat requests."""
    itype = str(info.get("type") or "").lower()
    if itype:
        if itype in NON_CHAT_TYPES:
            return False
        if itype in CHAT_TYPES:
            return True
    return not _looks_embedding(info.get("id") or "")


_THINKING_FAMILIES = ("qwen3", "deepseek-r1", "deepseek-v3", "gpt-oss",
                      "kimi", "glm-4", "glm-5", "r1")


def _is_thinking_model(model_id: str) -> bool:
    """True for reasoning-capable chat models (they stream reasoning_content)."""
    name = _bare_name(model_id)
    for fam in _THINKING_FAMILIES:
        if fam in name:
            return True
    return False


def _chat_score(info: dict) -> float:
    """Lower = better for automatic chat-model selection (small ≤9GB first)."""
    item = _bare_name(info.get("id") or "")
    score = 100.0
    if info.get("loaded"):
        score -= 60.0
    m = re.search(r"(\d+(?:\.\d+)?)b\b", item)
    params = float(m.group(1)) if m else 0.0
    if 0 < params <= 9:
        score -= 20.0
    elif params > 9:
        score += 40.0
    for i, fam in enumerate(CHAT_FAMILIES):
        if fam in item:
            score += i
            break
    if _looks_embedding(item):
        score += 200.0
    return score


def _download_suggestion(provider: str) -> str:
    """Human-readable "what to download" guide, always models ≤9GB."""
    if provider == "ollama":
        return (
            "No usable chat model found. Install a small one (≤9GB):\n"
            "  ollama pull qwen3:8b      (recommended, ~4.9GB)\n"
            "  ollama pull llama3.2:3b   (~2GB)\n"
            "Then try again."
        )
    if provider == "lmstudio":
        return (
            "No usable chat model loaded. In LM Studio use a model ≤9GB:\n"
            "  Download 'Qwen 3 8B' (Q4_K_M, ~4.9GB)\n"
            "  or 'Llama 3.2 3B' (~2GB)\n"
            "Open the model's chat page so it loads, then retry."
        )
    if provider == "unsloth":
        return (
            "No usable chat model available from Unsloth Studio. Start it with "
            "a model loaded (e.g. Qwen 3 8B, ≤9GB) and retry."
        )
    return (
        "No usable chat model available. Load a chat LLM (≤9GB) on your server "
        "and retry."
    )


@dataclass
class AiConfig:
    provider: str = "ollama"
    base_url: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 16384  # total budget; must exceed reasoning + answer length
    max_thinking_tokens: int = 1024  # cap Qwen3-class reasoning so the answer fits
    max_context_tokens: int = 4096  # total prompt budget (truncates if exceeded)
    timeout: int = 120
    short_context: bool = False  # if True, use compact mode (<2K tokens)
    llm_compact_summary: bool = False  # if True, summarize threads with the LLM
    # rather than a rule-based recap on budget compaction


class AiEngine:
    def __init__(self, config: Optional[AiConfig] = None):
        self.config = config or AiConfig()
        if not self.config.base_url and self.config.provider in PROVIDERS:
            preset = PROVIDERS[self.config.provider]
            self.config.base_url = preset["base_url"]
            if not self.config.model:
                self.config.model = preset["default_model"]
        self._resolved = False
        self._retried_model = False
        self._ctx_detected_for: Optional[str] = None  # model context was detected for
        self._anchor_cache: dict = {}  # id(cd) -> conversation_anchor text

    def _call(self, messages: List[dict], stream: bool = False) -> dict:
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": stream,
        }
        # LM Studio exposes a thinking-token cap for Qwen3-class reasoning models
        # (via max_thinking_tokens). Without a cap these models burn the entire
        # output budget on reasoning and never produce a visible answer. Ollama's
        # OpenAI-compatible endpoint rejects unknown keys, so gate it to LM Studio.
        if self.config.provider == "lmstudio" and self.config.max_thinking_tokens:
            payload["max_thinking_tokens"] = self.config.max_thinking_tokens
        # Ollama controls reasoning via reasoning_effort instead. Bound thinking
        # on reasoning models so the answer always has output budget left;
        # non-thinking models (e.g. gemma3) ignore the field.
        if self.config.provider == "ollama" and _is_thinking_model(
                self.config.model):
            payload["reasoning_effort"] = "low"
        resp = requests.post(
            url,
            json=payload,
            timeout=self.config.timeout,
            stream=stream,
        )
        resp.raise_for_status()
        if stream:
            return resp  # return raw response for streaming
        return resp.json()

    def _stream_response(self, response: requests.Response,
                         on_token: Optional[Callable[[str], None]] = None,
                         ) -> str:
        """Iterate SSE stream, calling on_token for the visible answer.

        Reasoning models (e.g. Qwen3, DeepSeek) stream their "thinking" into
        ``delta.reasoning_content`` and only emit the answer in ``delta.content``
        after the reasoning phase ends. The thinking is accumulated internally so
        the ``on_token`` callback (and therefore the user-facing output window)
        only ever shows the final answer — never raw chain-of-thought. If the
        token budget is exhausted mid-reasoning, a short notice is emitted
        instead of an empty reply.
        """
        full = []
        reasoning = []
        for line in response.iter_lines(decode_unicode=False):
            if not line:
                continue
            line = line.decode("utf-8")
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
            except (json.JSONDecodeError, KeyError):
                continue
            content = delta.get("content", "")
            think = delta.get("reasoning_content", "")
            if think:
                reasoning.append(think)
            if content:
                full.append(content)
                if on_token:
                    on_token(content)
        text = "".join(full).strip()
        if not text:
            if reasoning:
                msg = reasoning_only_message()
                if on_token:
                    on_token(msg)
                return msg
            return text
        return text

    def interpret(self, cd: ChartData, style: str = "detailed",
                  topic: str = "general",
                  on_token: Optional[Callable[[str], None]] = None) -> str:
        """Generate a full chart interpretation."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": interpret_prompt(
                cd, style, topic, max_context=self.config.max_context_tokens,
            )},
        ]
        return self._chat_completion(messages, on_token)

    def ask(self, cd: ChartData, question: str,
            on_token: Optional[Callable[[str], None]] = None) -> str:
        """Answer a specific question about the chart."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question_prompt(
                cd, question, max_context=self.config.max_context_tokens,
            )},
        ]
        return self._chat_completion(messages, on_token)

    def remedies(self, cd: ChartData,
                 on_token: Optional[Callable[[str], None]] = None) -> str:
        """Suggest Vedic remedies based on chart weaknesses."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": remedy_prompt(
                cd, max_context=self.config.max_context_tokens,
            )},
        ]
        return self._chat_completion(messages, on_token)

    # --- Threaded conversation chat ----------------------------------------

    _BUDGET_THRESHOLD = 0.70  # compact-and-restart trips near 70% of context
    _RESERVED_RESPONSE_TOKENS = 600

    def chat(self, cd: ChartData, question: str,
             history: Optional[List[dict]] = None,
             on_token: Optional[Callable[[str], None]] = None):
        """Threaded multi-turn conversation.

        Builds the fixed conversation anchor once (cached per engine), appends
        ``{user: question}`` and the prior ``history``, monitors the running
        token budget, and compacts-and-restarts when the thread nears ~70% of
        the detected context window.

        Returns ``(answer, new_history, reset_flag)`` where ``new_history`` is
        the caller's next ``history`` argument and ``reset_flag`` is True when
        the thread was compacted into a fresh session seeded from a summary.
        """
        history = list(history or [])
        anchor = self._conversation_anchor(cd)
        messages = self._chat_messages(anchor, question, history)
        reset = False
        if history and self._budget_exceeded(messages):
            summary = self._compact_history(history)
            reset = True
            history = []
            messages = self._chat_messages(
                anchor, question, history,
                lead_in=f"{summary}\n\nContinuing a follow-up conversation.",
            )
        answer = self._chat_completion(messages, on_token)
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
        return answer, history, reset

    def continue_chat(self, cd: ChartData, question: str,
                      history: Optional[List[dict]] = None,
                      on_token: Optional[Callable[[str], None]] = None):
        """Alias for ``chat`` — the caller keeps a growing history list."""
        return self.chat(cd, question, history=history, on_token=on_token)

    def _conversation_anchor(self, cd: ChartData) -> str:
        key = id(cd)
        if self._anchor_cache.get(key) is None:
            self._anchor_cache[key] = conversation_anchor(
                cd, max_context=self.config.max_context_tokens)
        return self._anchor_cache[key]

    @staticmethod
    def _chat_messages(anchor: str, question: str,
                       history: List[dict],
                       lead_in: Optional[str] = None) -> List[dict]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": anchor},
        ]
        if lead_in:
            messages.append({"role": "user", "content": lead_in})
        messages.extend(history)
        messages.append({"role": "user", "content": question})
        return messages

    def _budget_exceeded(self, messages: List[dict]) -> bool:
        used = sum(_estimate_tokens(m.get("content") or "")
                   for m in messages)
        used += self._RESERVED_RESPONSE_TOKENS
        threshold = int(self.config.max_context_tokens * self._BUDGET_THRESHOLD)
        return used >= threshold

    def context_usage(self, cd: ChartData,
                      history: Optional[List[dict]] = None) -> Tuple[int, int]:
        """Estimated prompt tokens in use vs the ~70% compaction trip wire.

        Additive readout for the GUI context meter. Uses the same accounting
        as `_budget_exceeded` (system prompt + cached anchor + history +
        reserved response) without changing any budget logic.
        Returns (used_estimate, threshold).
        """
        history = list(history or [])
        anchor = self._conversation_anchor(cd)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": anchor},
        ]
        messages.extend(history)
        used = sum(_estimate_tokens(m.get("content") or "")
                   for m in messages)
        used += self._RESERVED_RESPONSE_TOKENS
        threshold = int(self.config.max_context_tokens * self._BUDGET_THRESHOLD)
        return used, threshold

    def _compact_history(self, history: List[dict]) -> str:
        """Render a short summary of the thread and return it as the seed text.

        Defaults to a cheap rule-based recap (``thread_recap``). When configured
        with ``llm_compact_summary=True`` a small LLM summarization request is
        attempted first, falling back to the recap on any error.
        """
        if not self.config.llm_compact_summary:
            return thread_recap(history)
        try:
            recap = thread_recap(history)
            resp = self._chat_completion(
                [{"role": "system", "content": CONVERSATION_SUMMARY_PROMPT},
                 {"role": "user", "content": recap}])
            if resp and "no visible answer" not in resp:
                return resp
        except Exception:
            pass
        return thread_recap(history)

    def resolve_model(self, timeout: float = 8.0) -> dict:
        """Pick a usable chat model for the configured provider.

        Returns ``{"status", "model", "message", "available", "loaded"}`` where
        ``status`` is ``"ok"`` (``self.config.model`` now names a chat model),
        ``"no_model"`` (``message`` holds a ≤9GB download suggestion) or
        ``"offline"`` (server unreachable). ``available``/``loaded`` list the
        chat-capable model ids found on the server.
        """
        prov = self.config.provider
        base = (self.config.base_url
                or PROVIDERS.get(prov, {}).get("base_url", "")).rstrip("/")
        try:
            if prov == "lmstudio":
                catalog = _lmstudio_catalog(base, timeout=timeout)
            elif prov == "ollama":
                catalog = _ollama_catalog(base, timeout=timeout)
            else:
                catalog = _generic_catalog(base, timeout=timeout)
        except requests.exceptions.ConnectionError:
            return {"status": "offline", "model": "",
                    "message": "Could not reach the AI server for model lookup. "
                               "Is it running?",
                    "available": [], "loaded": []}
        except requests.exceptions.RequestException:
            return {"status": "no_model", "model": "",
                    "message": _download_suggestion(prov),
                    "available": [], "loaded": []}

        chat = [m for m in catalog if _is_chat_model(m)]
        chat_ids = [m["id"] for m in chat]
        loaded_ids = [m["id"] for m in chat if m.get("loaded")]
        if not chat:
            return {"status": "no_model", "model": "",
                    "message": _download_suggestion(prov),
                    "available": [], "loaded": []}

        current = (self.config.model or "").strip()
        # A concrete, chat-capable model the user chose is kept as-is.
        if current and current not in PLACEHOLDER_MODELS and not _looks_embedding(current):
            if current in chat_ids:
                return {"status": "ok", "model": current,
                        "message": f"Using {current}",
                        "available": chat_ids, "loaded": loaded_ids}

        # Prefer whatever chat model is already loaded.
        if loaded_ids:
            best = min(chat, key=_chat_score)
            self.config.model = best["id"]
            return {"status": "ok", "model": best["id"],
                    "message": f"Using loaded model {best['id']}",
                    "available": chat_ids, "loaded": loaded_ids}

        # Nothing loaded: try to load the best small chat model.
        best = min(chat, key=_chat_score)
        if prov == "lmstudio":
            try:
                if _lmstudio_load(base, best["id"], timeout=10):
                    self.config.model = best["id"]
                    return {"status": "ok", "model": best["id"],
                            "message": f"Loaded {best['id']} automatically",
                            "available": chat_ids, "loaded": loaded_ids}
            except requests.exceptions.RequestException:
                pass
            return {"status": "no_model", "model": "",
                    "message": "No chat model is loaded. " + _download_suggestion(prov),
                    "available": chat_ids, "loaded": loaded_ids}

        # Ollama loads a model on first inference, so naming it is enough.
        self.config.model = best["id"]
        return {"status": "ok", "model": best["id"],
                "message": f"Will auto-load {best['id']} on first request",
                "available": chat_ids, "loaded": loaded_ids}

    def _ensure_chat_model(self,
                           on_token: Optional[Callable[[str], None]] = None
                           ) -> Optional[str]:
        """Return a blocking message if no usable chat model is available.

        If ``config.model`` is a placeholder (e.g. ``loaded``) or an embedding
        model, resolve a real chat model, auto-loading it when possible.
        Returns None once a usable model is configured.
        """
        current = (self.config.model or "").strip()
        if current not in PLACEHOLDER_MODELS and not _looks_embedding(current):
            return None
        result = self.resolve_model()
        if result["status"] != "ok":
            if on_token:
                on_token(result["message"])
            return result["message"]
        return None

    def detect_context_length(self, model_id: Optional[str] = None) -> int:
        """Detect the local server's actual context window for a model.

        Works per provider: LM Studio reads ``max_context_length`` /
        ``loaded_context_length`` from its model catalog (already surfaced as
        ``ctx`` by ``_lmstudio_catalog``); Ollama queries ``/api/show``. Returns
        ``0`` if the server does not report a usable value so the caller can
        fall back to ``_DEFAULT_CONTEXT_TOKENS``.
        """
        prov = self.config.provider
        model_id = (model_id or self.config.model) or ""
        base = (self.config.base_url
                or PROVIDERS.get(prov, {}).get("base_url", "")).rstrip("/")
        try:
            if prov == "lmstudio":
                for m in _lmstudio_catalog(base):
                    if m["id"] == model_id or model_id in ("", "loaded"):
                        ctx = m.get("ctx") or 0
                        return int(ctx) if ctx else 0
                return 0
            if prov == "ollama" and model_id:
                return _ollama_context_length(base, model_id)
        except requests.exceptions.RequestException:
            pass
        return 0

    def _sync_context_length(self):
        """Update ``config.max_context_tokens`` from the server's reported value.

        Runs once per resolved model (guarded by ``_ctx_detected_for``). Mirrors
        the runtime window so the budget monitor behaves correctly on a 4K
        laptop model or a 128K GPU box. When the server does not report a value,
        keeps the conservative default. An explicit user-specified value (anything
        other than the default 4096) is never overridden so that the user's
        intentional choice always wins.
        """
        prov = self.config.provider
        model = (self.config.model or "").strip()
        if not model or self._ctx_detected_for == model:
            return
        if self.config.max_context_tokens != _DEFAULT_CONTEXT_TOKENS:
            self._ctx_detected_for = model
            return
        ctx = self.detect_context_length(model)
        if ctx > 0:
            self.config.max_context_tokens = ctx
        self._ctx_detected_for = model

    def _chat_completion(self, messages: List[dict],
                         on_token: Optional[Callable[[str], None]] = None) -> str:
        """Stream a chat completion resolving the model and retrying once.

        The prompt-building callers agree on this single path so that model
        resolution, reasoning-model streaming and graceful failure messages are
        identical for interpretation, Q&A and remedies.
        """
        self._resolved = False
        self._retried_model = False
        block = self._ensure_chat_model(on_token)
        if block is not None:
            return block
        try:
            self._sync_context_length()
            resp = self._call(messages, stream=True)
            return self._stream_response(resp, on_token)
        except requests.exceptions.ConnectionError:
            return _offline_message("your chart reading", on_token)
        except requests.exceptions.Timeout:
            return _timeout_message(on_token)
        except requests.exceptions.HTTPError as e:
            if self._retried_model:
                return self._model_error(e, on_token)
            self._retried_model = True
            retry = self.resolve_model()
            if retry["status"] != "ok":
                if on_token:
                    on_token(retry["message"])
                return retry["message"]
            try:
                self._sync_context_length()
                resp = self._call(messages, stream=True)
                return self._stream_response(resp, on_token)
            except requests.exceptions.ConnectionError:
                return _offline_message("your chart reading", on_token)
            except requests.exceptions.Timeout:
                return _timeout_message(on_token)
            except requests.exceptions.HTTPError as e2:
                return self._model_error(e2, on_token)

    def _model_error(self, error: Exception,
                     on_token: Optional[Callable[[str], None]] = None) -> str:
        text = getattr(getattr(error, "response", None), "text", "") or str(error)
        msg = (
            f"\n\n---\nThe model could not generate a reply ({error}).\n"
            f"{text[:200]}\n\n{_download_suggestion(self.config.provider)}"
        )
        if on_token:
            on_token(msg)
        return msg

    def health_check(self) -> dict:
        """Check if the configured provider is reachable (and resolve a model)."""
        try:
            url = f"{self.config.base_url.rstrip('/')}/models"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = data if isinstance(data, list) else (data.get("data") or [])
                model_names = [m.get("id", m.get("name", str(m))) for m in models]
                info = {"ok": True, "models": model_names[:20]}
                try:
                    res = self.resolve_model(timeout=6)
                    info["status"] = res["status"]
                    info["message"] = res["message"]
                    info["model"] = res["model"] if res["status"] == "ok" else ""
                    info["available"] = res["available"][:20]
                    if res["status"] == "ok":
                        self._sync_context_length()
                        info["context_tokens"] = self.config.max_context_tokens
                except Exception:
                    pass
                return info
            return {"ok": False, "error": f"HTTP {resp.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"ok": False, "error": "Connection refused — is the server running?"}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def reasoning_only_message() -> str:
    """Notice shown when a model spent its budget thinking but gave no answer."""
    return (
        "\n\nThe model produced no visible answer — it only returned internal "
        "reasoning. Try a shorter question, or generate again."
    )


def _offline_message(kind: str, on_token: Optional[Callable] = None) -> str:
    msg = (
        f"\n\n---\nCould not reach the AI server. Please ensure your local LLM "
        f"is running.\n\nStart one of:\n"
        f"  ollama serve      (Ollama)\n"
        f"  lm-studio         (LM Studio)\n"
        f"  unsloth serve     (Unsloth Studio)\n\n"
        f"Then generate the {kind} again."
    )
    if on_token:
        on_token(msg)
    return msg


def _timeout_message(on_token: Optional[Callable] = None) -> str:
    msg = "\n\n---\nRequest timed out. Try again with a simpler question or a faster model."
    if on_token:
        on_token(msg)
    return msg
