"""AI Chat Engine — connects to Ollama, LM Studio, Unsloth Studio for chart reading.

All three services expose an OpenAI-compatible /v1/chat/completions endpoint.
Only the base URL and default model differ between providers.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Callable, Generator, List, Optional

import requests

from jhora.charts.chart import ChartData
from jhora.ai.prompts import (
    SYSTEM_PROMPT,
    interpret_prompt,
    question_prompt,
    remedy_prompt,
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


@dataclass
class AiConfig:
    provider: str = "ollama"
    base_url: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    max_context_tokens: int = 4096  # total prompt budget (truncates if exceeded)
    timeout: int = 120
    short_context: bool = False  # if True, use compact mode (<2K tokens)


class AiEngine:
    def __init__(self, config: Optional[AiConfig] = None):
        self.config = config or AiConfig()
        if not self.config.base_url and self.config.provider in PROVIDERS:
            preset = PROVIDERS[self.config.provider]
            self.config.base_url = preset["base_url"]
            if not self.config.model:
                self.config.model = preset["default_model"]

    def _call(self, messages: List[dict], stream: bool = False) -> dict:
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": stream,
        }
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
        """Iterate SSE stream, calling on_token for each chunk. Returns full text."""
        full = []
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    full.append(content)
                    if on_token:
                        on_token(content)
            except (json.JSONDecodeError, KeyError):
                continue
        return "".join(full)

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
        try:
            resp = self._call(messages, stream=True)
            return self._stream_response(resp, on_token)
        except requests.exceptions.ConnectionError:
            return _offline_message("interpretation", on_token)
        except requests.exceptions.Timeout:
            return _timeout_message(on_token)

    def ask(self, cd: ChartData, question: str,
            on_token: Optional[Callable[[str], None]] = None) -> str:
        """Answer a specific question about the chart."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question_prompt(
                cd, question, max_context=self.config.max_context_tokens,
            )},
        ]
        try:
            resp = self._call(messages, stream=True)
            return self._stream_response(resp, on_token)
        except requests.exceptions.ConnectionError:
            return _offline_message("an answer", on_token)
        except requests.exceptions.Timeout:
            return _timeout_message(on_token)

    def remedies(self, cd: ChartData,
                 on_token: Optional[Callable[[str], None]] = None) -> str:
        """Suggest Vedic remedies based on chart weaknesses."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": remedy_prompt(
                cd, max_context=self.config.max_context_tokens,
            )},
        ]
        try:
            resp = self._call(messages, stream=True)
            return self._stream_response(resp, on_token)
        except requests.exceptions.ConnectionError:
            return _offline_message("remedy suggestions", on_token)
        except requests.exceptions.Timeout:
            return _timeout_message(on_token)

    def health_check(self) -> dict:
        """Check if the configured provider is reachable."""
        try:
            url = f"{self.config.base_url.rstrip('/')}/models"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = data if isinstance(data, list) else data.get("data", [])
                model_names = [m.get("id", m.get("name", str(m))) for m in models]
                return {"ok": True, "models": model_names[:20]}
            return {"ok": False, "error": f"HTTP {resp.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"ok": False, "error": "Connection refused — is the server running?"}
        except Exception as e:
            return {"ok": False, "error": str(e)}


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
