"""RAG prompt builder — injects computed analysis + textbook citations into LLM prompts.

The pipeline:
1. Chart data → compact astrological text
2. Computed analysis → dasa, transits, strengths, yogas (priority-ordered)
3. Knowledge base → FTS5 search for relevant passages
4. Topic-specific instructions → relationship, career, health, etc.
5. Context budget management → truncates to fit local model limits

Token estimation: ~4 chars per token for English text. Prompt is prioritized:
  computed analysis > chart data > chart details > textbook refs
"""

from typing import List

from jhora.charts.chart import ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra
from jhora.ai.analysis import (
    build_analysis_text,
    strengths_snapshot,
    yogas_snapshot,
    dasa_snapshot,
    transit_snapshot,
)
from jhora.interpreter.knowledge_base import KnowledgeBase


SYSTEM_PROMPT = """You are a Vedic astrologer (Parasara school). Be precise, cite data provided, avoid generalities. Use Sanskrit terms with brief English.

FORMAT: Plain text only. No HTML tags, no LaTeX, no $ signs, no Markdown.
Write planet and sign names as normal words: Sun, Moon, Libra, Aquarius.
Separate sections with blank lines. Keep it clean and readable."""


def _fmt_planet(g: Graha, cd: ChartData) -> str:
    p = cd.planet(g)
    r = Rasi.from_longitude(p.longitude)
    n, pada = Nakshatra.from_longitude(p.longitude)
    return (
        f"{g.short_name} {r.short_name} {p.longitude:.1f}° {n.name.title()}-{pada}"
        f"{' R' if p.is_retrograde else ''}"
    )


def _chart_compact(cd: ChartData) -> str:
    """Minimal chart: one line per planet, one line for houses."""
    l = Rasi.from_longitude(cd.ascendant)
    parts = [f"Asc {l.short_name} {cd.ascendant:.1f}°"]
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
        parts.append(_fmt_planet(g, cd))
    # Houses
    houses = [f"H{h+1}:{Rasi.from_longitude(cd.house_cusps[h]).short_name}"
              for h in range(12)]
    return " | ".join(parts) + "\nHouses: " + " ".join(houses)


def _chart_detailed(cd: ChartData) -> str:
    """Full chart with sign names, lords, nakshatras."""
    lagna_rasi = Rasi.from_longitude(cd.ascendant)
    lines = [
        f"Birth: {cd.birth_date.strftime('%Y-%m-%d %H:%M')} "
        f"at {cd.latitude:.1f}°{'N' if cd.latitude>=0 else 'S'} "
        f"{abs(cd.longitude):.1f}°{'E' if cd.longitude>=0 else 'W'}",
        f"Lagna: {cd.ascendant:.1f}° {lagna_rasi.full_name}",
        "",
        "Planets:",
    ]
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
        lines.append("  " + _fmt_planet(g, cd))

    lines.append("")
    lines.append("Houses:")
    for h in range(12):
        r = Rasi.from_longitude(cd.house_cusps[h])
        lines.append(f"  H{h+1}: {cd.house_cusps[h]:.1f}° {r.short_name} lord {r.lord}")

    return "\n".join(lines)


def _search_knowledge(cd: ChartData, topic: str, n: int = 3) -> str:
    try:
        kb = KnowledgeBase()
        lagna_name = Rasi.from_longitude(cd.ascendant).full_name
        queries = [f"{lagna_name}", topic]
        # Strongest planet
        from jhora.calc.shadbala import ShadbalaComputer
        sb = ShadbalaComputer(cd)
        strongest = max(
            [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
             Graha.JUPITER, Graha.VENUS, Graha.SATURN],
            key=lambda g: sb.compute_one(g).total_virupa,
        )
        queries.append(f"{strongest.full_name}")
        all_r = []
        for q in queries:
            all_r.extend(kb.search(q, max_results=2))
        seen = set()
        uniq = []
        for r in all_r:
            if r["source"] not in seen:
                seen.add(r["source"])
                uniq.append(r)
            if len(uniq) >= n:
                break
        if not uniq:
            return ""
        return "\n".join(
            f"[{r['source']}]: {r['excerpt'][:200]}"
            for r in uniq
        )
    except Exception:
        return ""


TOPIC_GUIDANCE = {
    "general": "Full life reading: personality, career, relationships, health, spirituality. Use dasa periods for timing.",
    "relationship": "Relationships/marriage: 7H, Venus, 7H lord. Afflictions, compatibility, timing via dasa.",
    "career": "Career/wealth: 10H, 2H, 11H. Sun/Saturn/Mercury. Rajayogas. Best fields. Dasa timing.",
    "health": "Health: Lagna, 6H, 8H. Afflicted planets. Dasa periods needing caution.",
    "spirituality": "Spiritual path: 5H, 9H, 12H. Jupiter/Ketu/Saturn. Moksha indicators.",
    "children": "Children: 5H, Jupiter. Afflictions. Timing/number indicated.",
    "finance": "Wealth: 2H, 11H, 5H, 9H. Jupiter/Venus. Dhana yogas. Financial timing.",
    "mundane": """Analyze this chart for WORLD/NATIONAL events (mundane astrology).
Use mundane house meanings:
  H1=People/masses, H2=Economy/treasury, H3=Media/neighbors,
  H4=Land/agriculture, H5=Education/speculation, H6=Military/conflict,
  H7=Foreign relations/war, H8=Disasters/debt, H9=Religion/law,
  H10=Government/leader, H11=Parliament/allies, H12=Hidden enemies.

Focus on:
- Conflict indicators: Mars/Saturn afflictions, Rahu in kendras
- Economic indicators: Jupiter/Venus/Mercury in 2H/11H
- Leadership: Sun in 10H, 10H lord strength
- Major planetary conjunctions indicating world shifts
- Eclipses and their mundane effects
- The country whose capital was used to cast this chart""",
}


def _estimate_tokens(text: str) -> int:
    """Conservative token estimate: ~3.5 chars per token for mixed Sanskrit/English."""
    return max(1, len(text) // 3)


def _truncate_sections(sections: dict, budget: int) -> str:
    """Merge sections in priority order until budget exhausted."""
    priority = ["analysis", "chart_detail", "chart_compact", "knowledge", "instruction"]
    parts = []
    used = _estimate_tokens("")  # baseline
    for key in priority:
        if key not in sections:
            continue
        text = sections[key]
        tok = _estimate_tokens(text)
        if used + tok > budget:
            # Truncate this section proportionally
            remaining = budget - used
            if remaining < 100:
                break
            chars = remaining * 3
            text = text[:chars] + "\n...(truncated)"
        parts.append(text)
        used += _estimate_tokens(text)
        if used >= budget:
            break
    return "\n\n".join(parts)


def interpret_prompt(cd: ChartData, style: str = "detailed",
                     topic: str = "general",
                     max_context: int = 4096) -> str:
    """Build RAG prompt with context budget management."""
    guidance = TOPIC_GUIDANCE.get(topic, TOPIC_GUIDANCE["general"])
    depth = {"concise": "Brief: 3-5 key points.", "detailed": "Thorough analysis.",
             "professional": "Full professional reading with timing."}.get(
                 style, "Thorough analysis.")

    # Prepare sections (lazy — only compute what we use)
    sections = {}
    budget = max_context - 600  # reserve for system prompt + response

    # Priority 1: computed analysis (compact — numbers, not prose)
    analysis = build_analysis_text(cd)
    if analysis:
        sections["analysis"] = f"--- COMPUTED ANALYSIS ---\n{analysis}"

    # Priority 2: detailed chart (if budget allows)
    if budget > 2000:
        sections["chart_detail"] = f"--- CHART ---\n{_chart_detailed(cd)}"
    else:
        sections["chart_detail"] = f"--- CHART ---\n{_chart_compact(cd)}"

    # Priority 3: compact chart as fallback
    sections["chart_compact"] = f"--- CHART (compact) ---\n{_chart_compact(cd)}"

    # Priority 4: knowledge base
    kb = _search_knowledge(cd, topic, n=2)
    if kb:
        sections["knowledge"] = f"--- TEXTBOOK ---\n{kb}"

    # Priority 5: instruction
    sections["instruction"] = (
        f"--- TASK ---\n{depth}\n{guidance}\n\n"
        f"Reference the data above. Cite textbook passages when quoting. "
        f"Use Sanskrit terms with English explanations."
    )

    return _truncate_sections(sections, budget)


def question_prompt(cd: ChartData, question: str,
                    max_context: int = 4096) -> str:
    base = interpret_prompt(cd, style="detailed", topic="general",
                            max_context=max_context - 200)
    q_block = f"\n\n--- QUESTION ---\n{question}\n\nAnswer specifically. Reference the data above."
    return base + q_block


def remedy_prompt(cd: ChartData, max_context: int = 4096) -> str:
    analysis = build_analysis_text(cd)
    chart = _chart_compact(cd)
    prompt = (
        f"--- CHART ---\n{chart}\n\n"
        f"--- ANALYSIS ---\n{analysis}\n\n"
        f"--- REMEDIES ---\n"
        f"Suggest Vedic remedies for the weakest areas above. For each:\n"
        f"1. Affliction + effects\n"
        f"2. Gemstone (stone, metal, weight, finger, day)\n"
        f"3. Mantra (text, count, timing)\n"
        f"4. Daan/ritual\n\n"
        f"Practical, Parasara-based. Warn: consult before wearing gems."
    )
    budget = max_context - 600
    tok = _estimate_tokens(prompt)
    if tok > budget:
        # Drop to compact mode with truncated analysis
        prompt = (
            f"--- CHART ---\n{chart}\n\n"
            f"Remedies for weak planets/houses in this chart. "
            f"Suggest gem, mantra, ritual for each. Practical only."
        )
    return prompt
