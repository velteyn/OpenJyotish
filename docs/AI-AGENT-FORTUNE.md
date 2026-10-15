# Read your future with any AI coding agent

OpenJyotish computes. Any AI agent reads. The engine owns every fact;
the agent owns only wording.

## 1. Export your chart once

```bash
openjyotish analyze "1990-01-15 17:30 +0530 12.9716 77.5946" > chart.json
```

That file holds 32 sections: planets, lagna, nakshatras, Vimshottari,
transits, Sade-Sati, yogas, strengths, transits search windows.
Use your own birth data in the same format
(`"YYYY-MM-DD HH:MM TZ LAT LON"`).

## 2. Ask any agent

opencode:
```bash
opencode "Read chart.json. Using only its dates and positions, tell me
about career in the next 6 months: current Mahadasha/Antardasha lords,
their house lordships from lagna, Jupiter/Saturn transits, and one
concrete caution. Quote engine dates verbatim, invent nothing."
```

Claude Code:
```bash
claude "Read chart.json and give a short career reading for the next
6 months from Vimshottari + gochara only. End with what would prove
this reading wrong."
```

Any LLM chat: attach `chart.json` and paste the same prompt.

## 3. Rules for a credible reading

- Dates and positions come from `chart.json` only, never from memory.
- Wording is assistance; facts are engine output (`openjyotish dasa`,
  `transit-search`, `yogas` re-check anything quoted).
- Tradition: Parasara mainstream (SJC/Rath, K.N. Rao, Raman, PVR).
  Name the rule behind each claim (e.g. Yogakaraka, Sade-Sati phase).

Built-in alternative (needs Ollama/LM Studio): `openjyotish ai "birthdata"`.
Full guide: https://github.com/velteyn/OpenJyotish/wiki/AI-Complete-Guide
