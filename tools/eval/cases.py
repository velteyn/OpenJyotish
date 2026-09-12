"""Eval probe definitions: question builders + deterministic assertions.

Assertions are substring checks (case-insensitive) against engine ground
truth for the local chart (Cancer lagna, Ketu MD 2024-04-12..2031-04-13,
Moon AD 2026-03-16..2026-10-15, DK Jupiter, AmK Sun, Moon Gemini
Punarvasu). must_not holds confabulations seen in the wild.
"""

SPOUSE_Q = ("im married with a Virgo born in 26-08-1982 and married in "
            "20-12-2008. ")


def _spouse(chart_cfg):
    return chart_cfg.get("spouse", "Virgo born in 26-08-1982")


CASES = [
    {
        "id": "dasa-now",
        "max_tokens": 4096,
        "question": lambda c: (
            "What mahadasha and antardasha am I in right now, and on what "
            "exact date does the current antardasha end? "
            "Answer in two sentences with exact dates."),
        "must_contain": ["Ketu", "Moon", "2026"],
        "must_not_contain": ["Gemini Ascendant", "Moon in Aquarius",
                             "Mars Antardasha ends", "2027"],
    },
    {
        "id": "dasa-followup",
        "follows": "dasa-now",
        "max_tokens": 4096,
        "question": lambda c: (
            "And when does the antardasha after that one begin and end? "
            "Just give the planet and the two dates."),
        "must_contain": ["Mars", "2027"],
        "must_not_contain": ["Gemini Ascendant", "Moon in Aquarius",
                             "Venus Antardasha"],
    },
    {
        "id": "dasa-followup-seeded",
        "max_tokens": 4096,
        "seed": {
            "q": "What mahadasha and antardasha am I in right now?",
            "a": "You are in Ketu Mahadasha with Moon Antardasha, "
                 "which ends on 2026-10-15.",
        },
        "question": lambda c: (
            "And when does the antardasha after that one begin and end? "
            "Just give the planet and the two dates."),
        "must_contain": ["Mars", "2027"],
        "must_not_contain": ["Gemini Ascendant", "Moon in Aquarius",
                             "Venus Antardasha"],
    },
    {
        "id": "karaka-identity",
        "max_tokens": 4096,
        "question": lambda c: (
            "Who is my Dara Karaka and who is my Amatya Karaka? "
            "Name each planet and the sign it occupies. "
            "Answer in two sentences."),
        "must_contain": ["Jupiter", "Sun"],
        "must_not_contain": ["Dara Karaka is Moon", "Dara Karaka is Mars",
                             "Amatya Karaka is Mars", "Aquarius at 329"],
    },
    {
        "id": "lagna-moon",
        "max_tokens": 4096,
        "question": lambda c: (
            "What is my lagna (ascendant sign) and in which sign and "
            "nakshatra is my natal Moon? Answer in one sentence."),
        "must_contain": ["Cancer", "Gemini", "Punarvasu"],
        "must_not_contain": ["Gemini Ascendant", "Moon in Aquarius",
                             "Virgo Ascendant"],
    },
    {
        "id": "marriage-full",
        "long": True,
        "max_tokens": 8192,
        "question": lambda c: (
            SPOUSE_Q + "How is this relationship going in the future, "
            "if you see difficulties please give also suggestion based "
            "on the stars"),
        "must_contain": ["Ketu", "2031", "Moon", "2026", "Mars", "Rahu",
                         "Jupiter", "Saturn"],
        "must_not_contain": ["Gemini Ascendant", "Moon in Aquarius",
                             "born 26-08-1982 and I am",
                             "Emerald is the gemstone of Venus",
                             "ruby is the gemstone of Mars"],
    },
    {
        "id": "guru-dara",
        "guru": True,
        "max_tokens": 8192,
        "question": lambda c: (
            "Teach me about Dara Karaka: how is it determined, what is "
            "mine in this chart, and what does it indicate for marriage?"),
        "must_contain": ["spouse", "Jupiter"],
        "must_not_contain": ["Dara = Enemy", "Dara Karaka) (enemy",
                             "enemy significator", "Moon in Aquarius"],
    },
]
