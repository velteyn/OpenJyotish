# Jagannatha Hora — Project Vision

## The North Star

To become the **world's first point of reference** for Vedic astrology — the tool that students learn on, professionals rely on, lecturers teach from, and the curious public discovers the subject through. Free, open, beautiful, and intelligent.

---

## Why This Matters

Vedic astrology (Jyotisha) is one of the world's oldest and most sophisticated predictive sciences, yet its software ecosystem is stuck in the 1990s:

- The best tools are **Windows-only, expensive ($250–$450), and closed-source**
- Modern developers don't touch astrology because the domain knowledge is locked in proprietary binaries and rare textbooks
- Students and lecturers have no free, cross-platform tool to study and teach with
- There is **no single authoritative open-source reference** that implements all 25+ dasa systems, 23+ varga charts, and the full array of classical techniques

This project breaks all of that open.

---

## The Three Audiences

### 1. Lecturers & Educators
- A **teaching platform** they can put in front of students — works on any OS, no license fees
- Every calculation is **transparent and verifiable** (open source, documented algorithms, cross-checked against the original JHora)
- A **Python API** that students can script against for research: batch charts, statistical studies, algorithm experimentation
- The knowledge base + AI chat means students can ask "why" and get answers drawn from classical texts

### 2. Professionals
- **All the numbers they need**: shadbala virupas, varga positions, ashtakavarga bindus, dasa periods, transit analysis — matching or exceeding $300 tools
- A **stylish, fast, dark-themed GUI** that doesn't look like it was built in 1998
- **Export and reporting** for client deliverables
- A **local AI assistant** (Ollama/LM Studio) that never sends client data to the cloud — privacy-first
- _No annual subscription, no license key, no DRM_

### 3. Casual Users
- Enter a birth date → get a **beautiful, readable chart reading** in two clicks
- Ask "what does my 7th house lord mean?" and get a **plain-English answer** from the AI
- A **warm, organic, inviting** interface — not a cold spreadsheet of numbers
- Zero cost, zero registration, zero data collection

---

## The GUI Philosophy

The interface must be the **most inviting** of any astrology tool ever made. It should feel like a well-crafted instrument, not a database frontend.

### Principles

| Principle | Why |
|-----------|-----|
| **Warm & organic** | Soft colors, rounded corners, thoughtful spacing, natural gradients — not harsh lines and gray rectangles. The UI should feel like a dim-lit study, not a hospital lobby. |
| **Effortless entry** | The default path is: open app → enter birth data → get a reading. No config required. No manual reading. |
| **Progressive disclosure** | Casual users see one beautiful chart and a reading. Professionals can drill into virupas, bindus, vargas, dasas — the complexity is there but hidden until needed. |
| **Consistent & harmonic** | Dark theme across the board (no white flashes), tight 10px grid, proportional spacing. Every element has its place. |
| **Cross-platform native feel** | PyQt6 Fusion style as base, but tuned to feel at home on Linux, macOS, and Windows alike. |

---

## AI as the Fortune Teller

Local AI (Ollama / LM Studio) transforms the tool from a **calculator** into a **reader**:

### The Flow
```
Birth data → ChartData (pure calculations, 0% AI)
    → Rule-based interpreter (dignities, house lords, yogas)
    → AI interpreter (natural language reading)
    → Interactive chat ("what does this mean for my career?")
```

### Why Local AI Matters
- **Privacy**: Client birth charts never leave the user's machine
- **Offline**: Works without internet — usable anywhere
- **Free**: No API fees, no per-call costs
- **Customizable**: Swap models, tune temperature, write custom system prompts
- **Pedagogical**: Students can ask "why did you say that?" and get an explanation

### The Experience
- "Tell my fortune" — generates a full chart reading in natural language
- "What will happen in my Jupiter dasa?" — the AI reads the chart + dasa period + transits
- "Should I start business next month?" — electional + transit analysis, explained in plain terms
- All backed by the **knowledge base** — the AI's answers are grounded in the actual textbook, not generalities

---

## What "First Point of Reference" Looks Like

1. A **student** in Mumbai downloads it to study — it's free, it works on their laptop, every calculation is documented
2. A **professional** in California uses it alongside their paid tools — when numbers match, they trust it; when they differ, the open source lets them verify
3. A **university** in Europe teaches Vedic astrology using it — cross-platform, scriptable, no licensing headaches
4. A **curious person** types their birth time into the app, gets a reading, and wants to learn more — the AI explains the terms, the knowledge base gives them depth
5. A **researcher** runs 10,000 charts through the Python API to study planetary strength patterns
6. A **Sanskrit scholar** contributes a new dasa algorithm from a newly-translated text — the plugin system makes it possible

---

## The Ultimate Test

> A person who has never heard of Vedic astrology should be able to open this app, enter their birth details, and within 30 seconds feel like they've learned something meaningful about themselves — without being overwhelmed.

And:

> A professional who has used $300 software for 20 years should be able to switch to this tool and not miss a single feature they rely on.
