"""Drafter: turn engine facts into training pairs.

Two pair families (spec tasks 1.3):
- fact-recall: deterministic Q&A generated from facts WITHOUT any LLM.
  Checkable claims verify clean by construction (same engine, same chart).
- readings / primer-qa: drafted by an LLM through an injected ``call_fn``
  (provider-agnostic: LM Studio, Unsloth Studio, frontier API). Mock-tested
  here; live drafting runs when an endpoint is reachable.

Provenance of every pair: primer / pd-classic / engine-generated.
"""

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


def lmstudio_call(base_url: str, model: str, temperature: float = 0.3,
                  timeout: int = 600) -> CallFn:
    """Provider-agnostic OpenAI-compatible caller (LM Studio, Unsloth
    Studio, or any chat-completions endpoint).

    NOTE: LM Studio answers 200 with an error body on unknown endpoints,
    so the base URL MUST include /v1 (added automatically when missing)
    and responses are validated for a real choice payload.
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
