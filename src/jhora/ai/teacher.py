"""AI Teacher — interactive Vedic astrology instructor powered by textbook corpus.

Uses embedding-based semantic search over 16 textbooks combined with
a teaching-focused system prompt to explain concepts, interpret charts,
and guide users through the software's features.
"""

from typing import Callable, List, Optional, Tuple

import json
import requests

from jhora.charts.chart import ChartData
from jhora.ai.embeddings import EmbeddingStore
from jhora.ai.prompts import (
    _chart_compact, _chart_detailed, _estimate_tokens, thread_recap,
)
from jhora.ai.analysis import build_analysis_text

# Default context budget — mirrors AiEngine until Ollama/LM Studio detection is
# wired into the teacher.  Overridable via ``max_context_tokens`` on init.
_DEFAULT_CONTEXT_TOKENS = 4096
_BUDGET_RATIO = 0.70   # trip compaction at 70% of context
_RESERVED_TOKENS = 600  # headroom for the model's reply

TEACHER_SYSTEM_PROMPT = """You are Guru, a patient Vedic astrology teacher trained on the complete 
corpus of Parasara, Jaimini, and modern Vedic astrology texts. Your role is to TEACH, not just interpret.

You have access to:
- The user's birth chart (if provided) with full planetary positions
- Computed analysis (strengths, yogas, dasa periods, transits)
- Passages from Vedic astrology textbooks relevant to the question
- Knowledge of all 24 CLI commands and 18 GUI tabs of the Jhora software

Your teaching approach:
1. Explain concepts using simple language with Sanskrit terms explained
2. Reference specific textbook passages when available
3. Show the user which Jhora commands/tabs to use for further exploration
4. Break complex topics into digestible steps
5. Encourage hands-on practice — tell the user to try specific commands

When a chart is provided, teach the user how to read it themselves rather than 
just giving the answer. Point out what THEY should look for and why.

Jhora commands the user can try:
- jhora chart "birthdata" --chalit
- jhora shadbala "birthdata" --bhava --vimsopaka
- jhora yogas "birthdata"
- jhora dasa-timeline "birthdata"
- jhora compare "birthdata" transit
- jhora progression "birthdata"
- jhora tithi-pravesha "birthdata"
- jhora transit "birthdata"
- jhora knowledge "query"
- jhora mundane 2026
- jhora export "birthdata" -o report.html
- jhora tui "birthdata"
- jhora ai --topic relationship "birthdata"
- jhora gui (for full desktop app with 18 tabs)

GUI tabs: Planets, Houses, Dasa, Varga, Yogas, Shadbala (with Bhava+Vimsopaka),
Arudha & Karaka, Ashtakavarga, Transit, Tajaka (+Tithi Pravesha + Progressions),
Matchmaking, Prasna, Muhurta, Knowledge, Reading, AI Chat, Mundane, Ephemeris."""


class AiTeacher:
    def __init__(self, provider: str = "ollama",
                 base_url: str = "http://localhost:11434/v1",
                 model: str = "llama3.2",
                 max_context_tokens: int = _DEFAULT_CONTEXT_TOKENS):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.store = EmbeddingStore(base_url=base_url.replace("/v1", ""))
        self.provider = provider
        self.max_context_tokens = max_context_tokens
        self._static_cache: dict = {}  # id(chart) -> (detailed, analysis)
        self._last_passages: list = []
        self.last_sources: list = []

    def ask(self, question: str, chart: Optional[ChartData] = None,
            on_token: Optional[Callable[[str], None]] = None) -> str:
        """Answer a teaching question with textbook references."""

        # Search textbook corpus for relevant passages
        passages = self.store.search(question, top_k=4)
        context = ""
        if passages:
            context = "Relevant textbook passages:\n\n"
            for i, p in enumerate(passages):
                context += f"[{p['source']}]: {p['content'][:400]}\n\n"

        # Build the prompt
        if chart:
            chart_data = _chart_detailed(chart)
            analysis = build_analysis_text(chart)
            prompt = (
                f"CHART DATA:\n{chart_data}\n\n"
                f"COMPUTED ANALYSIS:\n{analysis}\n\n"
                f"{context}"
                f"QUESTION: {question}\n\n"
                f"Teach me step by step. Reference the data and textbooks. "
                f"Tell me which Jhora commands to use for deeper analysis."
            )
        else:
            prompt = (
                f"{context}"
                f"QUESTION: {question}\n\n"
                f"Teach me comprehensively. Reference the textbooks. "
                f"Explain the relevant Vedic astrology concepts clearly."
            )

        return self._stream(messages=[
            {"role": "system", "content": TEACHER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], on_token=on_token)

    def explain_feature(self, feature: str,
                        on_token: Optional[Callable[[str], None]] = None) -> str:
        """Explain how to use a specific Jhora feature."""
        return self.ask(
            f"How do I use the {feature} feature? What does it calculate "
            f"and how do I interpret the results for chart reading and prediction?",
            on_token=on_token,
        )

    def explain_placement(self, chart: ChartData, planet: str,
                          on_token: Optional[Callable[[str], None]] = None) -> str:
        """Teach about a specific planetary placement in the user's chart."""
        return self.ask(
            f"What does {planet} in my chart indicate? Teach me how to "
            f"interpret its sign, house, nakshatra, dignity, and aspects. "
            f"What should I look for in the dasa periods related to this planet?",
            chart=chart,
            on_token=on_token,
        )

    def _stream(self, messages: List[dict],
                on_token: Optional[Callable[[str], None]] = None) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 16384,
            "stream": True,
        }
        # Cap Qwen3-class reasoning on LM Studio via its thinking-token limit so
        # the answer has output budget left. Ollama instead uses reasoning_effort
        # (bound thinking on thinking models, ignored by plain chat models).
        from jhora.ai.engine import _is_thinking_model
        if self.provider == "lmstudio":
            payload["max_thinking_tokens"] = 1024
        elif self.provider == "ollama" and _is_thinking_model(self.model):
            payload["reasoning_effort"] = "low"
        try:
            resp = requests.post(url, json=payload, timeout=180, stream=True)
            resp.raise_for_status()
            full = []
            reasoning = []
            finish = None
            saw_done = False
            for line in resp.iter_lines(decode_unicode=False):
                if not line:
                    continue
                line = line.decode("utf-8").strip()
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    saw_done = True
                    break
                try:
                    chunk = json.loads(data)
                    choice = chunk.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                fr = choice.get("finish_reason")
                if fr:
                    finish = fr
                content = delta.get("content", "")
                think = delta.get("reasoning_content", "")
                if think:
                    reasoning.append(think)
                if content:
                    full.append(content)
                    if on_token:
                        on_token(content)
            suffix = ""
            if finish == "length":
                suffix = "\n\n[truncated — output budget exhausted]"
            elif finish is not None and finish != "stop":
                suffix = f"\n\n[stopped early — reason: {finish}]"
            elif not saw_done and finish is None and (full or reasoning):
                suffix = "\n\n[interrupted — connection ended before completion]"
            text = "".join(full).strip()
            if not text and reasoning:
                from jhora.ai.engine import reasoning_only_message
                base = reasoning_only_message()
                if on_token:
                    on_token(base)
            else:
                base = text
            if suffix:
                if on_token:
                    on_token(suffix)
                return (base + suffix) if base else suffix
            return base
        except requests.exceptions.ConnectionError:
            msg = "AI server not running. Start Ollama: ollama serve"
            if on_token:
                on_token(msg)
            return msg
        except Exception as e:
            if on_token:
                on_token(str(e))
            return str(e)

    # -- conversation threading (per-turn RAG) ------------------------------

    _RESERVED_RESPONSE_TOKENS = 600

    def _budget_exceeded(self, messages: List[dict]) -> bool:
        threshold = int(self.max_context_tokens * _BUDGET_RATIO)
        used = sum(_estimate_tokens(m.get("content") or "")
                   for m in messages)
        used += self._RESERVED_RESPONSE_TOKENS
        return used >= threshold

    def _compact_history(self, history: List[dict]) -> str:
        return thread_recap(history)

    def _static_block(self, chart):
        """Cached (chart_detailed, analysis) pair — static per chart.

        Only the textbook passages stay freshly retrieved per question;
        mirrors the chat anchor cache.
        """
        key = id(chart)
        if self._static_cache.get(key) is None:
            self._static_cache[key] = (_chart_detailed(chart),
                                       build_analysis_text(chart))
        return self._static_cache[key]

    def _build_user_message(self, question: str,
                            chart: Optional[ChartData] = None) -> str:
        """Build the user message for a single teaching turn with fresh RAG."""
        passages = self.store.search(question, top_k=4)
        self._last_passages = [
            {"source": p.get("source", "textbook"),
             "excerpt": str(p.get("content", ""))[:400]}
            for p in (passages or [])
        ]
        context = ""
        if passages:
            context = "Relevant textbook passages:\n\n"
            for p in passages:
                context += f"[{p['source']}]: {p['content'][:400]}\n\n"

        if chart:
            chart_data, analysis = self._static_block(chart)
            return (
                f"CHART DATA:\n{chart_data}\n\n"
                f"COMPUTED ANALYSIS:\n{analysis}\n\n"
                f"{context}"
                f"QUESTION: {question}\n\n"
                f"Teach me step by step. Reference the data and textbooks. "
                f"Tell me which Jhora commands to use for deeper analysis."
            )
        return (
            f"{context}"
            f"QUESTION: {question}\n\n"
            f"Teach me comprehensively. Reference the textbooks. "
            f"Explain the relevant Vedic astrology concepts clearly."
        )

    def chat(self, question: str,
             chart: Optional[ChartData] = None,
             history: Optional[List[dict]] = None,
             on_token: Optional[Callable[[str], None]] = None
             ) -> Tuple[str, List[dict], bool]:
        """Threaded teaching conversation with per-turn RAG.

        Returns ``(answer, updated_history, reset_flag)`` where *reset_flag*
        is True when a compact-and-restart just occurred.
        """
        history = list(history or [])
        reset = False
        user_msg = self._build_user_message(question, chart=chart)
        self.last_sources = list(self._last_passages)

        messages = [{"role": "system", "content": TEACHER_SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_msg})

        if history and self._budget_exceeded(messages):
            summary = self._compact_history(history)
            reset = True
            history = []
            messages = [
                {"role": "system", "content": TEACHER_SYSTEM_PROMPT},
                {"role": "user", "content":
                 f"Earlier in this conversation:\n{summary}\n\n"
                 f"Continuing a follow-up conversation."},
                {"role": "user", "content": user_msg},
            ]

        answer = self._stream(messages, on_token=on_token)
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
        return answer, history, reset

    def context_usage(self, chart: Optional[ChartData] = None,
                      history: Optional[List[dict]] = None) -> Tuple[int, int]:
        """Estimated prompt tokens in use vs the ~70% compaction trip wire.

        Additive readout for the GUI context meter; mirrors the engine
        accounting (system + static block + history + reserved response)
        without changing any budget logic.
        Returns (used_estimate, threshold).
        """
        history = list(history or [])
        used = _estimate_tokens(TEACHER_SYSTEM_PROMPT)
        if chart is not None:
            chart_data, analysis = self._static_block(chart)
            used += _estimate_tokens(chart_data)
            used += _estimate_tokens(analysis)
        used += sum(_estimate_tokens(m.get("content") or "")
                    for m in history)
        used += self._RESERVED_RESPONSE_TOKENS
        threshold = int(self.max_context_tokens * _BUDGET_RATIO)
        return used, threshold
