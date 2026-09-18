"""Mechanical answer verification — check model claims against engine truth.

Parses a generated answer for checkable claims (planet-in-sign, houses,
lagna, house lords, dasa levels and periods, [Source] citations, transit
positions, birth dates, strength numbers, karaka roles, quoted passages)
and verifies each against computed chart data. Returns flags; never
rewrites prose. A clean report ("all N checkable claims verified") is a
reputation asset; flags catch invented signs, lords, periods and quotations
before an astrologer does.
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

_DASA_MD_WORDS = r"Maha\s?dasha|Mahadasa|Maha\s+Dasha|MD\b"
_DASA_AD_WORDS = r"Antar\s?dasha|Antardasha|Antar\s+Dasha|\bAD\b"
_ENGINE_SUFFIXES = ("truncat", "interrupt", "stopped", "done",
                    "thinking", "budget exhausted")

_library_sources_cache: Optional[List[str]] = None


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
    # Split after end punctuation/whitespace AND after a colon-newline
    # (section header followed by its body) so headers stand alone.
    return re.split(r"(?<=[.!?\n])\s+|(?<=:)\n", answer)


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


def _today():
    return datetime.now().date()


def _dasa_periods(cd: ChartData) -> List[dict]:
    """Structured Vimsottari MD/AD periods: lord, level, start, end."""
    from jhora.dasas.vimsottari import VimsottariDasa
    out = []
    chart_dict = {"planets": {g: {"longitude": p.longitude}
                              for g, p in cd.planets.items()},
                  "lagna_lon": cd.ascendant}
    try:
        mds = VimsottariDasa().compute(cd.julian_day, chart_dict)
    except Exception:
        return out
    for md in mds:
        mlord = getattr(md, "lord_name", "")
        out.append({"lord": mlord, "level": "MD",
                    "start": getattr(md, "start_date", None),
                    "end": getattr(md, "end_date", None)})
        for sp in (getattr(md, "sub_periods", None) or []):
            out.append({"lord": getattr(sp, "lord_name", ""),
                        "parent": mlord, "level": "AD",
                        "start": getattr(sp, "start_date", None),
                        "end": getattr(sp, "end_date", None)})
    return out


def _periods_covering(periods: List[dict], level: str,
                      y: int, m: int, d: int) -> List[dict]:
    hits = []
    for p in periods:
        if p["level"] != level or not isinstance(p["start"], datetime):
            continue
        s, e = p["start"].date(), p["end"].date()
        if s <= datetime(y, m, d).date() <= e:
            hits.append(p)
    return hits


def _house_lord_name(cd: ChartData, house: int) -> str:
    """Whole-sign lord of house N from lagna (classical lordship)."""
    idx = (_rasi_index(cd.ascendant) + house - 1) % 12
    lord = Rasi(idx).lord
    return lord.name.capitalize() if hasattr(lord, "name") else str(lord).capitalize()


def _library_sources() -> List[str]:
    """Normalized names of books in the local library (cached)."""
    global _library_sources_cache
    if _library_sources_cache is None:
        try:
            from jhora.interpreter.knowledge_base import KnowledgeBase
            _library_sources_cache = [
                _norm(s) for s in KnowledgeBase().list_sources()]
        except Exception:
            _library_sources_cache = []
    return _library_sources_cache


def _transit_truth(cd: ChartData) -> Dict[str, dict]:
    """Today's transit sign/house/SAV per planet (empty when unavailable)."""
    try:
        from jhora.calc.gochara import compute_transits
        res = compute_transits(cd)
    except Exception:
        return {}
    out = {}
    for e in (getattr(res, "entries", None) or []):
        try:
            out[e.graha.name.capitalize()] = {
                "sign": str(e.transit_rasi_name),
                "house": int(e.house_from_lagna),
                "sav": int(e.sav_score),
            }
        except Exception:
            continue
    return out


def verify_answer(answer: str, cd: ChartData,
                  passages: Optional[List[str]] = None) -> Verification:
    """Check every extractable claim. Pure function, no network."""
    # Drop any previous verification report appended to the answer so its
    # quoted claims are not re-checked as new assertions.
    answer = re.split(r"\n\s*[✓⚠]\s*(?:Verification|Verified)\s*:",
                      answer, maxsplit=1)[0]
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
    dasa_periods = _dasa_periods(cd)
    transits = _transit_truth(cd)
    library = _library_sources()
    today = _today()

    sents = [s.strip() for s in _sentences(answer)]
    # Transit context: the sentence itself names the moving sky, or the
    # nearest section header does. A new header resets the context so natal
    # sections after a transit block are not misread as transits.
    header_si, header_transit = -1, False
    in_transit_list = []
    for si, sent in enumerate(sents):
        if re.match(r"^\s*(#{1,6}\s+|\d+\.\s+)?\*{0,2}[^*:\n]{1,60}"
                    r"\*{0,2}\s*:?\s*$", sent):
            header_si = si
            header_transit = bool(re.search(
                r"transit|gochar", sent, re.IGNORECASE))
        self_match = bool(re.search(
            r"transit|gochar", sent, re.IGNORECASE))
        in_transit_list.append(
            self_match or (header_transit and 0 < si - header_si <= 8))
    for si, sent in enumerate(sents):
        s = sent.strip()
        if len(s) < 8:
            continue
        in_transit = in_transit_list[si]
        # Transit sentences describe the moving sky, not the natal chart —
        # sign/house checks below only apply to natal claims.
        natal_claim = not re.search(
            r"transit|gochar|passes? through|passage of", s, re.IGNORECASE)
        # Examples and hypotheticals illustrate; they assert nothing.
        example = bool(re.search(
            r"\be\.g\.|for example|such as|for instance|imagine\b|"
            r"\bsuppose\b|\bif\b.*\bwere\b", s, re.IGNORECASE))

        # planet-in-sign: "Mars in Sagittarius", "Venus placed in Aquarius".
        # Transit-section claims check against today's sky, not the natal chart.
        if (natal_claim or (in_transit and transits)) and not example:
            for m in re.finditer(
                    rf"\b({planet_pat})\b[^.!?\n]{{0,90}}?\b(?:in|placed in|sits? "
                    rf"in|positioned in|occupies|occupying)\s+({sign_pat})\b", s):
                gname, sname = m.group(1), m.group(2)
                g = _PLANET_BY_NAME[gname.lower()]
                claimed = _SIGN_BY_NAME[sname.lower()]
                if in_transit and gname in transits:
                    actual_name = transits[gname]["sign"]
                    ok = _norm(actual_name) in (
                        _norm(claimed.full_name), _norm(claimed.short_name))
                    kind = "transit-sign"
                    exp = f"today {gname} transits {actual_name}"
                else:
                    actual = Rasi.from_longitude(positions[g])
                    ok = actual == claimed
                    kind = "sign"
                    exp = f"{gname} is in {actual.full_name}"
                v.checked += 1
                if not ok:
                    v.flags.append(Flag(kind, f"{gname} in {sname}", exp))

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

        # houses: "Sun ... (H8)", "Mars in H7", "Venus in the 7th house",
        # "H7 (Cancer)", "Mars in House 3". Transit-section claims check
        # against today's houses from lagna.
        if (natal_claim or (in_transit and transits)) and not example:
            house_hits = []
            for m in re.finditer(
                    rf"\b({planet_pat})\b[^.!?\n]{{0,80}}?\bH\s?(\d{{1,2}})\b"
                    rf"|\bH\s?(\d{{1,2}})\b[^.!?\n]{{0,20}}?\b({planet_pat})\b",
                    s):
                if m.group(1):
                    house_hits.append((m.group(1), int(m.group(2)),
                                       m.start(), m.end(), True))
                else:
                    house_hits.append((m.group(4), int(m.group(3)),
                                       m.start(), m.end(), False))
            for m in re.finditer(
                    rf"\b({planet_pat})\b[^.!?\n]{{0,60}}?"
                    rf"(?:in\s+)?(?:the\s+)?(\d{{1,2}})(?:st|nd|rd|th)"
                    rf"\s+house\b"
                    rf"|\bHouse\s+(\d{{1,2}})\b[^.!?\n]{{0,20}}?"
                    rf"\b({planet_pat})\b", s, re.IGNORECASE):
                if m.group(1):
                    house_hits.append((m.group(1), int(m.group(2)),
                                       m.start(), m.end(), True))
                else:
                    house_hits.append((m.group(4), int(m.group(3)),
                                       m.start(), m.end(), False))
            for gname, house, ms, me, planet_first in house_hits:
                if gname.lower() not in _PLANET_BY_NAME:
                    continue
                if not 1 <= house <= 12:
                    continue
                # Lordship language ("H7 ruled by Saturn", "lord of H7
                # is Saturn") asserts rulership, not placement — the lord
                # check below owns those.
                lord_zone = s[ms:me] if planet_first else s[max(0, ms - 25):me]
                if re.search(r"lord|ruler|ruled|lorded", lord_zone,
                             re.IGNORECASE):
                    continue
                g = _PLANET_BY_NAME[gname.lower()]
                if in_transit and gname in transits:
                    actual = transits[gname]["house"]
                    kind = "transit-house"
                    exp = (f"today {gname} transits H{actual} "
                           f"from lagna")
                else:
                    actual = _whole_house(cd, positions[g])
                    kind = "house"
                    exp = (f"{gname} is in H{actual} "
                           f"(whole-sign from lagna)")
                v.checked += 1
                if actual != house:
                    v.flags.append(Flag(kind, f"{gname} in H{house}", exp))
            # house-sign consistency: "H7 (Cancer)" asserts H7 IS Cancer.
            for m in re.finditer(
                    rf"\bH\s?(\d{{1,2}})\b\s*\(\s*({sign_pat})\s*\)", s):
                house = int(m.group(1))
                if not 1 <= house <= 12:
                    continue
                claimed = _SIGN_BY_NAME[m.group(2).lower()]
                idx = (_rasi_index(cd.ascendant) + house - 1) % 12
                actual = Rasi(idx)
                v.checked += 1
                if actual != claimed:
                    v.flags.append(Flag(
                        "house-sign", f"H{house} ({m.group(2)})",
                        f"H{house} from lagna is {actual.full_name}"))
            # Nth-from: "Saturn in 12th from Moon".
            for m in re.finditer(
                    rf"\b({planet_pat})\b[^.!?\n]{{0,60}}?"
                    rf"\b(\d{{1,2}})(?:st|nd|rd|th)\s+from\s+"
                    rf"(Moon|Lagna)\b", s, re.IGNORECASE):
                gname, n, ref = m.group(1), int(m.group(2)), m.group(3)
                if gname.lower() not in _PLANET_BY_NAME or n > 12:
                    continue
                g = _PLANET_BY_NAME[gname.lower()]
                base = (positions[Graha.MOON] if ref.lower() == "moon"
                        else cd.ascendant)
                actual = Rasi((_rasi_index(base) + n - 1) % 12)
                v.checked += 1
                if Rasi.from_longitude(positions[g]) != actual:
                    v.flags.append(Flag(
                        "relative-house", f"{gname} {n}th from {ref}",
                        f"{gname} is in "
                        f"{Rasi.from_longitude(positions[g]).full_name}"))

        # house lords: "Lord of 7th: Jupiter", "H7 lorded by the Moon",
        # "Jupiter is the lord of H9". Classical whole-sign lordship.
        if natal_claim and not example:
            lord_hits = []
            for m in re.finditer(
                    rf"\b(?:lord|ruler)(?:s|ship)? of (?:the )?H?\s?"
                    rf"(\d{{1,2}})(?:st|nd|rd|th)?\s*(?:house|bhava)?\b"
                    rf"[^.!?\n]{{0,50}}?\b({planet_pat})\b", s,
                    re.IGNORECASE):
                lord_hits.append((int(m.group(1)), m.group(2)))
            for m in re.finditer(
                    rf"\bH\s?(\d{{1,2}})\b[^.!?\n]{{0,50}}?"
                    rf"\b(?:lorded by|ruled by|lord|ruler)\b[^.!?\n]{{0,30}}?"
                    rf"\b({planet_pat})\b", s, re.IGNORECASE):
                lord_hits.append((int(m.group(1)), m.group(2)))
            for m in re.finditer(
                    rf"\b({planet_pat})\b[^.!?\n]{{0,60}}?"
                    rf"\b(?:is\s+)?(?:the\s+)?(?:lord|ruler)(?:s|ship)? of\b"
                    rf"[^.!?\n]{{0,20}}?\bH?\s?(\d{{1,2}})"
                    rf"(?:st|nd|rd|th)?\s*(?:house|bhava)?\b", s,
                    re.IGNORECASE):
                lord_hits.append((int(m.group(2)), m.group(1)))
            for m in re.finditer(
                    rf"\b({planet_pat})\b[^.!?\n]{{0,40}}?"
                    rf"\b(?:lord|ruler)(?:s|ship)? of (?:the )?"
                    rf"(?:house|bhava)\s*(\d{{1,2}})\b", s,
                    re.IGNORECASE):
                lord_hits.append((int(m.group(2)), m.group(1)))
            for m in re.finditer(
                    rf"\b({planet_pat})\b[^.!?\n]{{0,40}}?"
                    rf"\bas\s+(?:its|the)\s+lord\b[^.!?\n]{{0,30}}?"
                    rf"(?:in\s+)?(?:H\s?(\d{{1,2}})|(?:house|bhava)\s*"
                    rf"(\d{{1,2}}))", s, re.IGNORECASE):
                house = m.group(2) or m.group(3)
                if house:
                    lord_hits.append((int(house), m.group(1)))
            for house, gname in lord_hits:
                if not 1 <= house <= 12:
                    continue
                if gname.lower() not in _PLANET_BY_NAME:
                    continue
                actual = _house_lord_name(cd, house)
                v.checked += 1
                if actual.lower() != gname.lower():
                    v.flags.append(Flag(
                        "lord", f"lord of H{house}: {gname}",
                        f"lord of H{house} from lagna is {actual}"))

        # dasa levels: "Jupiter Mahadasha (2028-2029)" must be a real MD;
        # "Mars Antardasha (Oct 2026–Mar 2027)" a real AD. Catches the
        # classic Mahadasha/Antardasha level confusion.
        if dasa_periods and not example:
            for m in re.finditer(
                    rf"\b({planet_pat})\s+({_DASA_MD_WORDS}|{_DASA_AD_WORDS})",
                    s):
                gname, word = m.group(1), m.group(2).strip()
                level = ("MD" if word.lower().startswith(("maha", "md"))
                         else "AD")
                dates = re.findall(r"(\d{4})-(\d{2})-(\d{2})", s)
                years = [int(y) for y in
                         re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", s)]
                if dates:
                    y, mo, d = (int(dates[0][0]), int(dates[0][1]),
                                int(dates[0][2]))
                    hits = [p for p in _periods_covering(
                        dasa_periods, level, y, mo, d)
                        if p["lord"].lower() == gname.lower()]
                    v.checked += 1
                    if not hits:
                        v.flags.append(Flag(
                            "dasa-level", f"{gname} {level} at "
                            f"{y}-{mo:02d}-{d:02d}",
                            f"no {gname} {level} covers that date"))
                elif years:
                    y1, y2 = min(years), max(years)
                    ok = any(
                        p["level"] == level
                        and p["lord"].lower() == gname.lower()
                        and isinstance(p["start"], datetime)
                        and p["start"].year <= y1
                        and p["end"].year >= y2
                        for p in dasa_periods)
                    v.checked += 1
                    if not ok:
                        v.flags.append(Flag(
                            "dasa-level", f"{gname} {level} {y1}-{y2}",
                            f"no {gname} {level} spans those years"))
                elif re.search(r"\bcurrent(?:ly)?\b|\bpresent(?:ly)?\b|"
                               r"\bnow\b|\bongoing\b", s, re.IGNORECASE):
                    cur = _periods_covering(
                        dasa_periods, level, today.year, today.month,
                        today.day)
                    v.checked += 1
                    if not any(p["lord"].lower() == gname.lower()
                               for p in cur):
                        have = ", ".join(sorted(
                            {p["lord"] for p in cur})) or "none"
                        v.flags.append(Flag(
                            "dasa-level", f"current {gname} {level}",
                            f"current {level} is {have}"))

        # [Source] citations must name books actually in the local library.
        if library:
            for m in re.finditer(r"\[([A-Za-z][A-Za-z .'\-&]{2,60})\]", s):
                raw = m.group(1).strip()
                low = raw.lower()
                if any(k in low for k in _ENGINE_SUFFIXES):
                    continue
                v.checked += 1
                if _norm(raw) not in library:
                    v.flags.append(Flag(
                        "citation", f"[{raw}]",
                        "not in the local library — cite bundled or "
                        "imported books"))
        # karaka roles: "DK is Jupiter", "Dara Karaka: Moon",
        # "Matru Karaka (Venus)", "(Dara Karaka): Jupiter"
        for m in re.finditer(
                rf"\b({'|'.join(_KARAKA_ROLES)})\s+karaka\b\s*\)?\s*:?\s*"
                rf"(?:is\s+)?\(?({planet_pat})\)?"
                rf"|\bDK\b\s*:?\s*\(?({planet_pat})\)?", s, re.IGNORECASE):
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

        # birth time: a stated clock time next to birth/born words, or an
        # ISO datetime on the birth date, must match the computed chart.
        # (Catches "00:00" midnight-defaulting on a 13:55 chart.)
        # Other people's times AND dates are unknowable — only yours verify;
        # strengths, signs and quotes below still check regardless.
        bt = cd.birth_date
        other_person = bool(re.search(
            r"spouse|partner|\bwife\b|\bhusband\b|marriage|married",
            s, re.IGNORECASE))
        if not other_person:
            for m in re.finditer(
                    r"\b(?:birth|born)\b[^.!?\n]{0,80}?(\d{1,2}):(\d{2})\b"
                    r"|(\d{4})-(\d{2})-(\d{2})[ T](\d{1,2}):(\d{2})", s,
                    re.IGNORECASE):
                if m.group(1) is not None:
                    hh, mm = int(m.group(1)), int(m.group(2))
                else:
                    y, mo, d = (int(m.group(3)), int(m.group(4)),
                                int(m.group(5)))
                    if (y, mo, d) != (bt.year, bt.month, bt.day):
                        continue
                    hh, mm = int(m.group(6)), int(m.group(7))
                if 0 <= hh <= 23 and 0 <= mm <= 59:
                    v.checked += 1
                    if (hh, mm) != (bt.hour, bt.minute):
                        v.flags.append(Flag(
                            "birth-time", f"birth time {hh:02d}:{mm:02d}",
                            f"chart birth time is "
                            f"{bt.hour:02d}:{bt.minute:02d}"))
            for dm in re.finditer(
                    r"\d{4}-\d{2}-\d{2}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+"
                    r"[A-Za-z]+\s+\d{4}", s):
                parsed = _parse_date(dm.group(0))
                if not parsed:
                    continue
                if parsed == (today.year, today.month, today.day):
                    continue  # today's date (e.g. transit headers) is not a claim
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
                if (y, m) == (today.year, today.month):
                    continue  # current month is context, not a claim
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
