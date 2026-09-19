"""Drafter: turn engine facts into training pairs.

Pair families (spec tasks 1.3):
- fact-recall: deterministic Q&A generated from facts WITHOUT any LLM.
  Checkable claims verify clean by construction (same engine, same chart).
- primer-qa: deterministic Q&A extracted verbatim from the bundled Primer
  chapters (``primer_sections`` / ``primer_qa_pairs``). Every answer is a
  substring of a cited library source, so it cannot hallucinate; the filter
  only has to check citations + grounding (see ``tools/train/filter.py``).
- readings: drafted by an LLM through an injected ``call_fn``
  (provider-agnostic: LM Studio, Unsloth Studio, frontier API). Mock-tested
  here; live drafting runs when an endpoint is reachable. Per the live
  economics in docs/AI_LESSONS.md §12 this is a low-yield bonus source.

Provenance of every pair: primer / pd-classic / engine-generated.
"""

import re
from pathlib import Path
from typing import Callable, Dict, List, Optional

CallFn = Callable[[List[Dict]], str]

READING_SYSTEM = (
    "You are a Vedic astrology teacher. Answer using ONLY the facts below. "
    "State placements, lords, houses and dasa periods exactly as given. "
    "Cite textbooks only as [Source] names from the provided passages. "
    "Never invent signs, dates, yogas or citations.")

READING_INSTRUCTION = (
    "Write a short chart reading by RESTATING the facts above in clear "
    "prose. Copy every planet, sign, house number, lord, date and strength "
    "figure EXACTLY as written — do not compute, infer, adjust or add "
    "anything. Never mention a house, sign, date, yoga or citation that "
    "does not appear above.")


def fact_text(facts: Dict) -> str:
    """Render the fixed fact schema as drafter context."""
    lines = [
        f"Birth: {facts['birth']['date']} {facts['birth']['time']}.",
        f"Lagna: {facts['lagna']['sign']} ({facts['lagna']['lon']} deg).",
    ]
    for p in facts["placements"]:
        retro = " retrograde" if p["retrograde"] else ""
        lines.append(
            f"{p['planet']} in {p['sign']} {p['deg_in_sign']:.2f} deg, "
            f"{p['nakshatra']} pada {p['pada']}, house {p['house']}{retro}.")
    lords = ", ".join(f"H{h} {facts['house_lords'][h]}"
                      for h in range(1, 13))
    lines.append(f"House lords: {lords}.")
    for g, v in facts["shadbala"].items():
        lines.append(f"{g} Shadbala {v:.0f} virupas.")
    for md in facts["vimsottari"]:
        ads = ", ".join(
            f"{a['lord']} {a['start']} to {a['end']}"
            for a in md["antardashas"])
        lines.append(
            f"{md['lord']} Mahadasha {md['start']} to {md['end']}: {ads}.")
    if facts["yogas"]:
        lines.append("Yogas: " + "; ".join(
            f"{y['name']} ({', '.join(y['planets'])})"
            for y in facts["yogas"]) + ".")
    return "\n".join(lines)


def draft_reading(facts: Dict, call_fn: CallFn,
                  passages: Optional[List[str]] = None) -> Dict:
    """Draft one chart-reading pair via LLM. Provenance: engine-generated."""
    user = fact_text(facts)
    if passages:
        user += ("\nTextbook passages:\n" + "\n".join(
            f"[{i}] {p[:400]}" for i, p in enumerate(passages)))
    user += "\n" + READING_INSTRUCTION
    answer = call_fn([
        {"role": "system", "content": READING_SYSTEM},
        {"role": "user", "content": user},
    ])
    return {
        "messages": [
            {"role": "system", "content": READING_SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": answer},
        ],
        "provenance": "engine-generated",
        "kind": "reading",
    }


def draft_qa(question: str, passage: str, source: str,
             call_fn: CallFn) -> Dict:
    """Draft one Primer Q&A pair via LLM, grounded in a single passage."""
    answer = call_fn([
        {"role": "system", "content": READING_SYSTEM},
        {"role": "user", "content": (
            f"Passage [{source}]:\n{passage}\n\n"
            f"Question: {question}\nAnswer using ONLY the passage. "
            f"Cite it as [{source}].")},
    ])
    return {
        "messages": [
            {"role": "system", "content": READING_SYSTEM},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
        "provenance": "primer" if "primer" in source.lower() else "pd-classic",
        "kind": "qa",
        "source": source,
    }


def fact_recall_pairs(facts: Dict) -> List[Dict]:
    """Deterministic Q&A from facts — no LLM, clean by construction."""
    pairs = []

    def _add(q: str, a: str):
        pairs.append({
            "messages": [
                {"role": "system", "content": READING_SYSTEM},
                {"role": "user", "content": q},
                {"role": "assistant", "content": a},
            ],
            "provenance": "engine-generated",
            "kind": "fact-recall",
        })

    lagna = facts["lagna"]["sign"]
    _add("What is the lagna?", f"The lagna is {lagna}.")
    for p in facts["placements"]:
        g, s = p["planet"], p["sign"]
        _add(f"In which sign is {g}?", f"{g} is in {s}.")
        _add(f"Which house is {g} in?",
             f"{g} is in H{p['house']} (whole-sign from lagna).")
        _add(f"Which nakshatra is {g} in?",
             f"{g} is in {p['nakshatra']} pada {p['pada']}.")
    for h in range(1, 13):
        _add(f"Which planet rules house {h}?",
             f"The lord of H{h} is {facts['house_lords'][h]}.")
    for md in facts["vimsottari"]:
        _add(f"When does {md['lord']} Mahadasha start and end?",
             f"{md['lord']} Mahadasha runs {md['start']} to {md['end']}.")
    return pairs


PRIMER_DIR = (Path(__file__).resolve().parents[2]
              / "src" / "jhora" / "data" / "books")

_HEADING = re.compile(r"^(\d+)\.\s+(.+?)\s*$")
_RULE = re.compile(r"^-{3,}\s*$")

_QA_TEMPLATES = (
    "What does the OpenJyotish Primer teach about {topic}?",
    "Explain {topic} as taught in the OpenJyotish Primer.",
    "Summarize {topic} from the OpenJyotish Primer.",
    "What is {topic}, according to the OpenJyotish Primer?",
)


def _source_name(stem: str) -> str:
    """Library source name for a book file stem (matches KnowledgeBase)."""
    return stem.replace("_", " ").replace("-", " ").replace(".pdf", "").title()


def _topic(title: str) -> str:
    """Title-case a section heading, preserving known acronyms."""
    out = title.title()
    for acr in ("Sav", "Bav", "D24"):
        out = out.replace(acr, acr.upper())
    return out


def primer_sections(books_dir: Optional[Path] = None) -> List[Dict]:
    """Parse bundled Primer chapters into ``{source,title,body}`` sections.

    A section starts at a numbered heading (``N. TITLE``) underlined with a
    run of dashes; the body is every line up to the next heading. Bodies are
    verbatim source text, which is what makes the Q&A pairs unspoofable.
    """
    books_dir = Path(books_dir) if books_dir else PRIMER_DIR
    out: List[Dict] = []
    for path in sorted(books_dir.glob("primer-*.txt")):
        source = _source_name(path.stem)
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        starts = [i for i in range(len(lines) - 1)
                  if _HEADING.match(lines[i]) and _RULE.match(lines[i + 1])]
        for n, i in enumerate(starts):
            title = _HEADING.match(lines[i]).group(2).strip()
            end = starts[n + 1] if n + 1 < len(starts) else len(lines)
            body = "\n".join(lines[i + 2:end]).strip()
            if body:
                out.append({"source": source, "title": title, "body": body})
    return out


def primer_qa_pairs(books_dir: Optional[Path] = None) -> List[Dict]:
    """Deterministic Primer Q&A pairs — verbatim, cited, no LLM.

    Each answer ends with a ``[Source]`` citation naming the bundled library
    book; the answer body is copied from that book, so the pair is grounded
    by construction. Provenance: ``primer``.
    """
    pairs = []
    for n, sec in enumerate(primer_sections(books_dir)):
        topic = _topic(sec["title"])
        question = _QA_TEMPLATES[n % len(_QA_TEMPLATES)].format(topic=topic)
        answer = f"{sec['body']}\n\n[{sec['source']}]"
        pairs.append({
            "messages": [
                {"role": "system", "content": READING_SYSTEM},
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ],
            "provenance": "primer",
            "kind": "qa",
            "source": sec["source"],
            "passage": sec["body"],
        })
    return pairs


def lmstudio_call(base_url: str, model: str, temperature: float = 0.3,
                  timeout: int = 600) -> CallFn:
    """Thin OpenAI-compatible caller (LM Studio, Unsloth Studio, or any
    chat-completions endpoint).

    NOTE: LM Studio answers 200 with an error body on unknown endpoints,
    so the base URL MUST include /v1 (added automatically when missing)
    and responses are validated for a real choice payload. For bulk
    drafting prefer engine_call() below (thinking caps, model resolution).
    """
    import requests
    root = base_url.rstrip("/")
    if "/v1" not in root and "/api/" not in root:
        root += "/v1"

    def _call(messages: List[Dict]) -> str:
        r = requests.post(
            root + "/chat/completions",
            json={"model": model, "messages": messages,
                  "temperature": temperature, "stream": False},
            timeout=timeout)
        r.raise_for_status()
        data = r.json()
        try:
            content = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise ValueError(f"no choice payload (server said: "
                             f"{str(data)[:160]})")
        if not content.strip():
            raise ValueError("empty completion content")
        return content
    return _call


def engine_call(base_url: str, model: str, provider: str = "lmstudio",
                temperature: float = 0.2, timeout: int = 300) -> CallFn:
    """Drafter calls through the app's AiEngine path (model resolution,
    reasoning-model thinking caps, truncation notices). Never evicts the
    user's loaded model (auto_ensure=False). Prefer this for bulk runs."""
    from jhora.ai.engine import AiEngine, AiConfig
    eng = AiEngine(AiConfig(
        provider=provider, base_url=base_url, model=model,
        temperature=temperature, timeout=timeout, auto_ensure=False))

    def _call(messages: List[Dict]) -> str:
        text = eng._chat_completion(messages) or ""
        if not text.strip():
            raise ValueError("empty completion content")
        return text
    return _call
