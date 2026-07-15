"""Prompt templates for LLM-powered chart interpretation."""

from jhora.charts.chart import ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra


def _format_planet(g: Graha, cd: ChartData) -> str:
    p = cd.planet(g)
    r = Rasi.from_longitude(p.longitude)
    n, pada = Nakshatra.from_longitude(p.longitude)
    return (
        f"{g.full_name}: {p.longitude:.2f}° in {r.full_name} "
        f"(lord {r.lord}), {n.name.replace('_',' ').title()} pada {pada}"
        f"{', Retrograde' if p.is_retrograde else ''}"
    )


def chart_to_text(cd: ChartData) -> str:
    """Convert ChartData to a compact astrological text summary."""
    lagna_rasi = Rasi.from_longitude(cd.ascendant)
    lines = [
        f"Birth: {cd.birth_date.strftime('%Y-%m-%d %H:%M')}",
        f"Location: {cd.latitude:.2f}°{'N' if cd.latitude >= 0 else 'S'}, "
        f"{cd.longitude:.2f}°{'E' if cd.longitude >= 0 else 'W'}",
        f"Timezone: {cd.timezone}",
        f"Ayanamsa: {cd.ayanamsa_name} ({cd.ayanamsa_value:.4f}°)",
        f"Lagna (Ascendant): {cd.ascendant:.2f}° in {lagna_rasi.full_name}",
        "",
        "Planetary Positions:",
    ]
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
        lines.append("  " + _format_planet(g, cd))

    # House cusps
    lines.append("")
    lines.append("House Cusps:")
    for h in range(12):
        cusp = cd.house_cusps[h]
        r = Rasi.from_longitude(cusp)
        lines.append(f"  House {h+1}: {cusp:.2f}° in {r.full_name} (lord {r.lord})")

    return "\n".join(lines)


SYSTEM_PROMPT = """You are a professional Vedic astrologer trained in Parasara, Jaimini, and 
Tajaka systems. You interpret birth charts using classical principles from Brihat Parasara Hora 
Sastra. You are precise, educational, and avoid vague generalities. 

When given chart data, you analyze:
1. Lagna (ascendant) — the native's nature, body, and life path
2. Planetary placements — each planet's sign, house, dignity, nakshatra
3. House lords — which houses planets rule and where they sit
4. Aspects (drishti) — mutual planetary relationships
5. Yogas — special planetary combinations and their effects
6. Strengths — which planets and houses are strongest/weakest

Respond in clear paragraphs. Use Sanskrit astrological terms with brief English explanations.
Focus on what makes this chart unique, not generic descriptions."""


def interpret_prompt(cd: ChartData, style: str = "detailed") -> str:
    """Build the prompt for a full chart interpretation."""
    chart_text = chart_to_text(cd)
    depth = {
        "concise": "Give a short overview of the most important 3-5 features.",
        "detailed": "Give a thorough analysis covering lagna, all planets, key yogas, and overall life themes.",
        "professional": "Full professional reading: analyze every planet in detail, all major yogas, dasha implications, and remedial measures.",
    }.get(style, "detailed")

    return f"""{chart_text}

Please interpret this Vedic astrology birth chart. {depth}

Include in your analysis:
- The native's personality and life direction from the lagna
- Each planet's strength, dignity, and what it indicates in its house/sign
- Any notable yogas or planetary combinations
- Overall chart strengths and challenges

Use classical Vedic terminology with brief explanations."""


def question_prompt(cd: ChartData, question: str) -> str:
    """Build the prompt for a specific chart-related question."""
    chart_text = chart_to_text(cd)
    return f"""{chart_text}

Question about this chart: {question}

Answer specifically and directly. Reference the relevant planetary positions, 
house lords, and yogas from the chart above to support your answer."""


def remedy_prompt(cd: ChartData) -> str:
    """Build the prompt for remedial measures."""
    chart_text = chart_to_text(cd)
    return f"""{chart_text}

Based on this birth chart, suggest appropriate Vedic remedial measures (upayas).
Focus on the weakest planets and most afflicted houses.

For each issue identified, suggest:
1. The planetary affliction and its likely effects
2. Gemstone recommendation (if applicable, with wearing instructions)
3. Mantra for recitation (with count and timing)
4. Ritual or charitable act (daan) that can help

Keep suggestions practical and grounded in classical Parasara principles.
Warn that gemstones should only be worn after proper consultation."""


def streaming_delta(content: str) -> dict:
    """Format a token as an OpenAI-compatible streaming chunk."""
    import json
    chunk = {
        "choices": [{
            "delta": {"content": content},
            "index": 0,
            "finish_reason": None,
        }],
    }
    return chunk
