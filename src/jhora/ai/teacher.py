"""AI Teacher — interactive Vedic astrology instructor powered by textbook corpus.

Uses embedding-based semantic search over 16 textbooks combined with
a teaching-focused system prompt to explain concepts, interpret charts,
and guide users through the software's features.
"""

from typing import Callable, List, Optional

import requests

from jhora.charts.chart import ChartData
from jhora.ai.embeddings import EmbeddingStore
from jhora.ai.prompts import _chart_compact, _chart_detailed
from jhora.ai.analysis import build_analysis_text

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
                 model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.store = EmbeddingStore(base_url=base_url.replace("/v1", ""))
        self.provider = provider

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
            "max_tokens": 2048,
            "stream": True,
        }
        try:
            resp = requests.post(url, json=payload, timeout=120, stream=True)
            resp.raise_for_status()
            full = []
            for line in resp.iter_lines(decode_unicode=False):
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
                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if content:
                        full.append(content)
                        if on_token:
                            on_token(content)
                except (json.JSONDecodeError, KeyError):
                    continue
            return "".join(full)
        except requests.exceptions.ConnectionError:
            msg = "AI server not running. Start Ollama: ollama serve"
            if on_token:
                on_token(msg)
            return msg
        except Exception as e:
            if on_token:
                on_token(str(e))
            return str(e)
