"""Mechanical answer verification — check model claims against engine truth.

Parses a generated answer for checkable claims (planet-in-sign, houses,
lagna, dasa/birth dates, strength numbers, karaka roles, quoted passages)
and verifies each against computed chart data. Returns flags; never
rewrites prose. A clean report ("all N checkable claims verified") is a
reputation asset; flags catch invented signs, dates and quotations before
an astrologer does.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from jhora.charts.chart import ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

_PLANETS = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
            Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU,
            Graha.KETU]
_PLANET_NAMES = {g: g.name.capitalize() for g in _PLANETS}
_PLANET_BY_NAME = {v.lower(): g for g, v in _PLANET_NAMES.items()}
_SIGN_BY_NAME = {}
for _r in Rasi:
    _SIGN_BY_NAME[_r.full_name.lower()] = _r
    _SIGN_BY_NAME[_r.short_name.lower()] = _r

_MONTHS = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
           "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
           "november": 11, "december": 12}
_MONTH_ABBR = {m[:3]: n for m, n in _MONTHS.items()}

_KARAKA_ROLES = ["atma", "amatya", "bhratru", "bhrathru", "matru", "matri",
                 "pitru", "pitri", "putra", "gnati", "gnathi", "dara"]


@dataclass
class Flag:
    """One failed check: what was claimed vs computed truth."""
    kind: str
    claim: str
    expected: str


@dataclass
class Verification:
    checked: int = 0
    flags: List[Flag] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return self.checked - len(self.flags)


def _rasi_index(lon: float) -> int:
    return int(lon // 30) % 12


def _sentences(answer: str) -> List[str]:
    return re.split(r"(?<=[.!?\n])\s+", answer)


def _planet_positions(cd: ChartData) -> Dict[Graha, float]:
    return {g: cd.planet(g).longitude for g in _PLANETS}


def _whole_house(cd: ChartData, lon: float) -> int:
    return (_rasi_index(lon) - _rasi_index(cd.ascendant)) % 12 + 1


def _known_dates(cd: ChartData) -> Dict[Tuple[int, int, int], str]:
    """Map (y, m, d) -> event label for birth + all dasa boundaries."""
    from jhora.dasas.vimsottari import VimsottariDasa
    known = {}
    b = cd.birth_date
    known[(b.year, b.month, b.day)] = "birth date"
    chart_dict = {"planets": {g: {"longitude": p.longitude}
                              for g, p in cd.planets.items()},
                  "lagna_lon": cd.ascendant}
    try:
        periods = VimsottariDasa().compute(cd.julian_day, chart_dict)
    except Exception:
        return known
    for md in periods:
        for p in (md, *(md.sub_periods or [])):
            for attr, label in (("start_date", "begins"), ("end_date", "ends")):
                d = getattr(p, attr, None)
                if isinstance(d, datetime):
                    known.setdefault((d.year, d.month, d.day),
                                     f"{p.lord_name} {label}")
    return known


def _parse_date(text: str) -> Optional[Tuple[int, int, int]]:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    m = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", text)
    if m and m.group(1).lower()[:3] in _MONTH_ABBR:
        return (int(m.group(3)), _MONTH_ABBR[m.group(1).lower()[:3]],
                int(m.group(2)))
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
    if m and m.group(2).lower()[:3] in _MONTH_ABBR:
        return (int(m.group(3)), _MONTH_ABBR[m.group(2).lower()[:3]],
                int(m.group(1)))
    return None


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def verify_answer(answer: str, cd: ChartData,
                  passages: Optional[List[str]] = None) -> Verification:
    """Check every extractable claim. Pure function, no network."""
    v = Verification()
    positions = _planet_positions(cd)
    known_dates = _known_dates(cd)

    planet_pat = ("Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu")
    sign_pat = ("Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|"
                "Sagittarius|Capricorn|Aquarius|Pisces")

    try:
        from jhora.calc.karaka import compute_chara_karakas, karaka_dict
        kplanets = {g: {"longitude": positions[g]} for g in _PLANETS
                    if g in (Graha.SUN, Graha.MOON, Graha.MARS,
                             Graha.MERCURY, Graha.JUPITER, Graha.VENUS,
                             Graha.SATURN, Graha.RAHU)}
        karakas = karaka_dict(compute_chara_karakas(kplanets))
    except Exception:
        karakas = {}
    try:
        from jhora.calc.shadbala import ShadbalaComputer
        shadbala = {g: ShadbalaComputer(cd).compute_one(g).total_virupa
                    for g in _PLANETS[:7]}
    except Exception:
        shadbala = {}
    try:
        from jhora.calc.ashtakavarga import sarva_ashtakavarga
        sav = sarva_ashtakavarga(cd)
    except Exception:
        sav = []

    for sent in _sentences(answer):
        s = sent.strip()
        if len(s) < 8:
            continue
        # Transit sentences describe the moving sky, not the natal chart —
        # sign/house checks below only apply to natal claims.
        natal_claim = not re.search(
            r"transit|gochar|passes? through|passage of", s, re.IGNORECASE)
        # Examples and hypotheticals illustrate; they assert nothing.
        example = bool(re.search(
            r"\be\.g\.|for example|such as|for instance|imagine\b|"
            r"\bsuppose\b|\bif\b.*\bwere\b", s, re.IGNORECASE))

        # planet-in-sign: "Mars in Sagittarius", "Venus placed in Aquarius"
        if natal_claim and not example:
            for m in re.finditer(
                    rf"\b({planet_pat})\b[^.!?\n]{{0,90}}?\b(?:in|placed in|sits? "
                    rf"in|positioned in|occupies|occupying)\s+({sign_pat})\b", s):
                g = _PLANET_BY_NAME[m.group(1).lower()]
                claimed = _SIGN_BY_NAME[m.group(2).lower()]
                actual = Rasi.from_longitude(positions[g])
                v.checked += 1
                if actual != claimed:
                    v.flags.append(Flag(
                        "sign", f"{m.group(1)} in {m.group(2)}",
                        f"{m.group(1)} is in {actual.full_name}"))

        # lagna: "Cancer lagna", "Gemini Ascendant", "Cancer Rising"
        # (lagna is natal by definition — no transit guard needed)
        for m in re.finditer(
                rf"\b({sign_pat})\b\s+(?:lagna|ascendant|rising)\b"
                rf"|\b(?:lagna|ascendant)\s+(?:is\s+)?({sign_pat})\b", s,
                re.IGNORECASE):
            name = m.group(1) or m.group(2)
            claimed = _SIGN_BY_NAME[name.lower()]
            actual = Rasi.from_longitude(cd.ascendant)
            v.checked += 1
            if actual != claimed:
                v.flags.append(Flag(
                    "lagna", f"lagna {name}",
                    f"lagna is {actual.full_name}"))

        # whole-sign house near a planet: "Sun ... (H8)", "Mars in H7"
        if natal_claim and not example:
            for m in re.finditer(
                rf"\b({planet_pat})\b[^.!?\n]{{0,80}}?\bH\s?(\d{{1,2}})\b"
                rf"|\bH\s?(\d{{1,2}})\b[^.!?\n]{{0,20}}?\b({planet_pat})\b",
                s):
                gname = m.group(1) or m.group(4)
                house = int(m.group(2) or m.group(3))
                g = _PLANET_BY_NAME[gname.lower()]
                actual = _whole_house(cd, positions[g])
                if 1 <= house <= 12:
                    v.checked += 1
                    if actual != house:
                        v.flags.append(Flag(
                            "house", f"{gname} in H{house}",
                            f"{gname} is in H{actual} (whole-sign from lagna)"))

        # karaka roles: "DK is Jupiter", "Dara Karaka: Moon",
        # "(Dara Karaka): Jupiter"
        for m in re.finditer(
                rf"\b({'|'.join(_KARAKA_ROLES)})\s+karaka\b\s*\)?\s*:?\s*"
                rf"(?:is\s+)?({planet_pat})\b"
                rf"|\bDK\b\s*:?\s*({planet_pat})\b", s, re.IGNORECASE):
            if m.group(1):
                role, gname = m.group(1).lower(), m.group(2)
                key = {"atma": "AK", "amatya": "AmK", "bhratru": "BK",
                       "bhrathru": "BK", "matru": "MK", "matri": "MK",
                       "pitru": "PiK", "pitri": "PiK", "putra": "PutK",
                       "gnati": "GnK", "gnathi": "GnK",
                       "dara": "DK"}.get(role)
            else:
                key, gname = "DK", m.group(3)
            if key and key in karakas:
                actual = karakas[key].graha.name.capitalize()
                v.checked += 1
                if actual.lower() != gname.lower():
                    v.flags.append(Flag(
                        "karaka", f"{m.group(1)} Karaka {gname}",
                        f"{m.group(1)} Karaka is {actual}"))

        # strength numbers with context: "558 virupas", "40 bindus"
        for m in re.finditer(r"(\d{2,4})\s*(virupas|bindus)\b", s,
                             re.IGNORECASE):
            val, unit = int(m.group(1)), m.group(2).lower()
            window = s[max(0, m.start() - 120):m.end()]
            if unit.startswith("virupa"):
                gm = re.search(rf"\b({planet_pat})\b", window)
                if gm and gm.group(1).lower() in _PLANET_BY_NAME:
                    g = _PLANET_BY_NAME[gm.group(1).lower()]
                    if g in shadbala:
                        v.checked += 1
                        if abs(shadbala[g] - val) > 2:
                            v.flags.append(Flag(
                                "strength",
                                f"{gm.group(1)} {val} virupas",
                                f"{gm.group(1)} Shadbala is "
                                f"{shadbala[g]:.0f} virupas"))
            else:
                sm = re.search(rf"\b({sign_pat})\b", window)
                if sm and sav:
                    actual = sav[_SIGN_BY_NAME[sm.group(1).lower()].value]
                    v.checked += 1
                    if abs(actual - val) > 2:
                        v.flags.append(Flag(
                            "strength", f"{sm.group(1)} {val} bindus",
                            f"SAV {sm.group(1)} is {actual}"))

        # dates: each must match a computed event (dasa boundary or birth).
        # Full dates match exactly; month precision matches (year, month).
        for dm in re.finditer(
                r"\d{4}-\d{2}-\d{2}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+"
                r"[A-Za-z]+\s+\d{4}", s):
            parsed = _parse_date(dm.group(0))
            if not parsed:
                continue
            v.checked += 1
            if parsed not in known_dates:
                v.flags.append(Flag(
                    "date", dm.group(0),
                    "no computed dasa boundary or birth date matches"))
        for dm in re.finditer(
                r"\b([A-Za-z]+)\s+(\d{4})\b", s):
            mon = dm.group(1).lower()[:3]
            if mon not in _MONTH_ABBR or _parse_date(dm.group(0)):
                continue
            y, m = int(dm.group(2)), _MONTH_ABBR[mon]
            v.checked += 1
            if not any(k[0] == y and k[1] == m for k in known_dates):
                v.flags.append(Flag(
                    "date", dm.group(0),
                    "no computed dasa boundary falls in this month"))

    # quoted passages must exist in the provided texts. Skipped: questions,
    # code spans and mantras (quoted for use, not as classical authority).
    text = re.sub(r"```.*?```", " ", answer, flags=re.DOTALL)
    for m in re.finditer(r"['\"]([^'\"\n]{25,400})['\"]", text):
        raw = m.group(1).strip()
        if re.match(r"How |What |When |Why |Which |Who ", raw):
            continue
        if "--" in raw or raw.startswith("Om ") or " Namaha" in raw \
                or " Svaha" in raw:
            continue
        quote = _norm(raw)
        if not passages:
            continue
        v.checked += 1
        if not any(quote in _norm(p) for p in passages):
            v.flags.append(Flag(
                "quote", m.group(1)[:90] + "…",
                "not found in the provided textbook passages"))
    return v


def format_report(v: Verification) -> str:
    """Render verification notes for display under an answer."""
    if not v.checked:
        return ""
    if not v.flags:
        return (f"\n\n✓ Verified: all {v.checked} checkable claims match "
                f"the computed chart.")
    lines = [f"\n\n⚠ Verification: {len(v.flags)} of {v.checked} checkable "
             f"claims differ from the computed chart:"]
    for f in v.flags[:12]:
        lines.append(f"  • {f.claim} → engine says: {f.expected}")
    if len(v.flags) > 12:
        lines.append(f"  …and {len(v.flags) - 12} more.")
    return "\n".join(lines)
