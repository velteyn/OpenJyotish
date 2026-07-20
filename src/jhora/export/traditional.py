"""Traditional one-page report — AstroSage-style layout rendered to PNG/JPG.

Produces a single-page printable report containing:
  - Birth header (panchanga: tithi, yoga, karana, sunrise/sunset, dasa balance)
  - Lagna (D-1) and Navamsa (D-9) charts, North Indian diamond style
  - Vimshottari Dasha grid (9 mahadasas with antardasha end dates)
  - Planetary positions table (sign, longitude, nakshatra, pada)
  - Ashtakavarga table (7 BAVs + SAV total)
  - Chalit table (Sripati bhava begin / bhava madhya)

Rendering uses QPainter on a QImage (offscreen) — no browser needed.
"""

import math
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from jhora.charts.chart import ChartData, ChartBuilder
from jhora.dasas.vimsottari import VimsottariDasa
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra

# ── Name tables ───────────────────────────────────────────────────────────────

_LORD3 = {
    "Sun": "SUN", "Moon": "MON", "Mars": "MAR", "Mercury": "MER",
    "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
    "Rahu": "RAH", "Ketu": "KET",
}

_TITHI_NAMES = [
    "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Poornima/Amavasya",
]

_YOGA_NAMES = [
    "Vishkumbha", "Preeti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarman", "Dhrithi", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Varigha", "Paridha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]

_KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitula", "Garaja", "Vanija",
    "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna",
]

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday"]

_OUTER_ABBR = {"Uranus": "Ur", "Neptune": "Ne", "Pluto": "Pl"}

_YPD = 365.2425  # solar year in days (matches dasa engine default)


# ── Small formatting helpers ─────────────────────────────────────────────────

def _dms(longitude: float, sep: str = "-", pad_deg: int = 0) -> str:
    """Format longitude within its sign as D-MM-SS."""
    deg_in = longitude % 30.0
    d = int(deg_in)
    m_float = (deg_in - d) * 60
    m = int(m_float)
    s = int(round((m_float - m) * 60))
    if s >= 60:
        s -= 60
        m += 1
    if m >= 60:
        m -= 60
        d += 1
    return f"{d:0{pad_deg}d}{sep}{m:02d}{sep}{s:02d}"


def _deg_full(longitude: float, sep: str = "-") -> str:
    """Format absolute degrees as DDD-MM-SS."""
    v = longitude % 360.0
    d = int(v)
    m_float = (v - d) * 60
    m = int(m_float)
    s = int(round((m_float - m) * 60))
    if s >= 60:
        s -= 60
        m += 1
    if m >= 60:
        m -= 60
        d += 1
    return f"{d:03d}{sep}{m:02d}{sep}{s:02d}"


def _hms(hours: float) -> str:
    """Format decimal hours as H.MM.SS."""
    hours = hours % 24.0
    h = int(hours)
    m_float = (hours - h) * 60
    m = int(m_float)
    s = int(round((m_float - m) * 60))
    if s >= 60:
        s -= 60
        m += 1
    if m >= 60:
        m -= 60
        h = (h + 1) % 24
    return f"{h}.{m:02d}.{s:02d}"


def _jd_to_local_hours(jd_ut: float, tz_offset: float) -> float:
    """Convert a JD (UT) to local clock hours."""
    eng = SweEngine()
    _y, _m, _d, utc_hour = eng.revjul(jd_ut)
    return (utc_hour - tz_offset) % 24.0


def _fmt_jd_date(jd: float) -> str:
    """Format a JD as D/M/YY (UT date — good enough for dasa dates)."""
    eng = SweEngine()
    y, m, d, _h = eng.revjul(jd)
    return f"{d}/{m}/{y % 100:02d}"


def _latlon_str(value: float, pos: str, neg: str) -> str:
    hemi = pos if value >= 0 else neg
    v = abs(value)
    d = int(v)
    m = int(round((v - d) * 60))
    if m >= 60:
        m -= 60
        d += 1
    return f"{d}.{m:02d}.{hemi}"


# ── Data assembly ─────────────────────────────────────────────────────────────

def _panchanga_fields(cd: ChartData) -> Dict[str, str]:
    """Tithi, yoga, karana names from Sun/Moon longitudes."""
    sun = cd.planet(Graha.SUN).longitude
    moon = cd.planet(Graha.MOON).longitude

    tithi_angle = (moon - sun) % 360.0
    tithi_idx = int(tithi_angle // 12)
    tithi_name = _TITHI_NAMES[tithi_idx % 15]

    yoga_idx = int(((sun + moon) % 360.0) // (360.0 / 27))
    yoga_name = _YOGA_NAMES[yoga_idx % 27]

    # Karana: 60 half-tithis. n=0 → Kimstughna; n=1..56 → 7 movable karanas
    # cycling (Bava..Vishti); n=57/58/59 → Shakuni, Chatushpada, Naga.
    half = 0 if (tithi_angle % 12) < 6.0 else 1
    n = tithi_idx * 2 + half
    if n == 0:
        karana_name = "Kimstughna"
    elif n >= 57:
        karana_name = ["Shakuni", "Chatushpada", "Naga"][n - 57]
    else:
        karana_name = _KARANA_NAMES[(n - 1) % 7]

    return {"tithi": tithi_name, "yoga": yoga_name, "karana": karana_name}


def _sunrise_sunset(cd: ChartData) -> Tuple[str, str]:
    from jhora.calc.muhurta import _sunrise_sunset as _ss
    tz_offset = ChartBuilder._parse_tz(cd.timezone)
    sr_jd, ss_jd = _ss(cd.birth_date, cd.latitude, cd.longitude, tz_offset)
    sunrise = _hms(_jd_to_local_hours(sr_jd, tz_offset))
    sunset = _hms(_jd_to_local_hours(ss_jd, tz_offset))
    return sunrise, sunset


def _sidereal_time(cd: ChartData) -> str:
    """Local apparent sidereal time at birth, H.MM.SS."""
    import swisseph as swe_lib
    gmst = swe_lib.sidtime(cd.julian_day)
    last = (gmst + cd.longitude / 15.0) % 24.0
    return _hms(last)


def _dasa_balance(cd: ChartData) -> Tuple[Graha, float]:
    """Return (first dasa lord, balance in years remaining at birth)."""
    moon = cd.planet(Graha.MOON).longitude
    nak, _pada = Nakshatra.from_longitude(moon)
    span = 360.0 / 27.0
    progressed = (moon - nak.value * span) % span
    remaining = (span - progressed) / span
    eng = VimsottariDasa()
    first_lord = eng._nakshatra_to_graha(nak)
    years = eng._cycle_years[first_lord]
    return first_lord, remaining * years


def _header_columns(cd: ChartData, name: str, sex: str, place: str
                    ) -> List[List[Tuple[str, str]]]:
    panch = _panchanga_fields(cd)
    sunrise, sunset = _sunrise_sunset(cd)
    first_lord, balance = _dasa_balance(cd)

    total_days = balance * _YPD
    by = int(total_days // _YPD)
    rem = total_days % _YPD
    bm = int(rem // 30.4369)
    bd = int(rem % 30.4369)
    bal_str = f"{first_lord.full_name} {by} Y {bm} M {bd} D"

    moon_p = cd.planet(Graha.MOON)
    lagna_rasi = Rasi.from_longitude(cd.ascendant)

    col1 = [
        ("Name", name),
        ("Sex", sex),
        ("Date", f"{cd.birth_date.day}.{cd.birth_date.month}.{cd.birth_date.year}"),
        ("Day", _WEEKDAYS[cd.birth_date.weekday()]),
        ("Time of Birth", _hms(cd.time_of_day_hours)),
        ("SID", _sidereal_time(cd)),
    ]
    col2 = [
        ("Julian Day", f"{math.ceil(cd.julian_day)}"),
        ("Ayan Type", cd.ayanamsa_name.title()),
        ("Ayan", _deg_full(cd.ayanamsa_value)),
        ("Place", place),
        ("Longitude", _latlon_str(cd.longitude, "E", "W")),
        ("Latitude", _latlon_str(cd.latitude, "N", "S")),
    ]
    col3 = [
        ("Asc Lord", _LORD3[lagna_rasi.lord]),
        ("Asc", lagna_rasi.full_name),
        ("Yoga", panch["yoga"]),
        ("Tithi", panch["tithi"]),
        ("Sunset", sunset),
        ("Sunrise", sunrise),
    ]
    col4 = [
        ("Bal. Dasa", bal_str),
        ("Karan", panch["karana"]),
        ("Star Lord", _LORD3[moon_p.nakshatra.lord]),
        ("Star - Pada", f"{moon_p.nakshatra_name.replace(' ', '')}-{moon_p.nakshatra_pada}"),
        ("Rasi Lord", _LORD3[moon_p.rasi.lord]),
        ("Rasi", moon_p.rasi.full_name),
    ]
    return [col1, col2, col3, col4]


def _planet_rows(cd: ChartData) -> List[List[str]]:
    """Planetary positions table rows."""
    rows = []

    def _row(label: str, longitude: float, retro: bool):
        r = Rasi.from_longitude(longitude)
        n, pada = Nakshatra.from_longitude(longitude)
        rows.append([
            label + (" [R]" if retro else ""),
            r.full_name,
            _dms(longitude),
            n.name.replace("_", " ").title(),
            str(pada),
        ])

    _row("ASC", cd.ascendant, False)
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
        p = cd.planet(g)
        _row(g.full_name, p.longitude, p.is_retrograde)
    for oname in ("Uranus", "Neptune", "Pluto"):
        od = cd.outer_planets.get(oname)
        if od:
            _row(oname, od["longitude"], od.get("is_retrograde", False))
    return rows


# ── Classical Ashtakavarga benefic-place tables (BPHS) ───────────────────────
# _AV_TABLES[subject][reference] = 1-based houses from the reference's sign
# that receive a bindu for the subject's Bhinna Ashtakavarga.
# Validated: reproduces AstroSage's BAV rows exactly (totals 48/49/39/54/56/52/39,
# SAV total 337) for a known reference chart.

_AV_TABLES: Dict[str, Dict[str, List[int]]] = {
    "Sun": {"Sun": [1, 2, 4, 7, 8, 9, 10, 11], "Moon": [3, 6, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11], "Mercury": [3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [5, 6, 9, 11], "Venus": [6, 7, 12],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Ascendant": [3, 4, 6, 10, 11, 12]},
    "Moon": {"Sun": [3, 6, 7, 8, 10, 11], "Moon": [1, 3, 6, 7, 10, 11],
             "Mars": [2, 3, 5, 6, 9, 10, 11], "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
             "Jupiter": [1, 4, 7, 8, 10, 11, 12], "Venus": [3, 4, 5, 7, 9, 10, 11],
             "Saturn": [3, 5, 6, 11], "Ascendant": [3, 6, 10, 11]},
    "Mars": {"Sun": [3, 5, 6, 10, 11], "Moon": [3, 6, 11],
             "Mars": [1, 2, 4, 7, 8, 10, 11], "Mercury": [3, 5, 6, 11],
             "Jupiter": [6, 10, 11, 12], "Venus": [6, 8, 11, 12],
             "Saturn": [1, 4, 7, 8, 9, 10, 11], "Ascendant": [1, 3, 6, 10, 11]},
    "Mercury": {"Sun": [5, 6, 9, 11, 12], "Moon": [2, 4, 6, 8, 10, 11],
                "Mars": [1, 2, 4, 7, 8, 9, 10, 11], "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
                "Jupiter": [6, 8, 11, 12], "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
                "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Ascendant": [1, 2, 4, 6, 8, 10, 11]},
    "Jupiter": {"Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11], "Moon": [2, 5, 7, 9, 11],
                "Mars": [1, 2, 4, 7, 8, 10, 11], "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
                "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11], "Venus": [2, 5, 6, 9, 10, 11],
                "Saturn": [3, 5, 6, 12], "Ascendant": [1, 2, 4, 5, 6, 7, 9, 10, 11]},
    "Venus": {"Sun": [8, 11, 12], "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
              "Mars": [3, 5, 6, 9, 11, 12], "Mercury": [3, 5, 6, 9, 11],
              "Jupiter": [5, 8, 9, 10, 11], "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
              "Saturn": [3, 4, 5, 8, 9, 10, 11], "Ascendant": [1, 2, 3, 4, 5, 8, 9, 11]},
    "Saturn": {"Sun": [1, 2, 4, 7, 8, 10, 11], "Moon": [3, 6, 11],
               "Mars": [3, 5, 6, 10, 11, 12], "Mercury": [6, 8, 9, 10, 11, 12],
               "Jupiter": [5, 6, 11, 12], "Venus": [6, 11, 12],
               "Saturn": [3, 5, 6, 11], "Ascendant": [1, 3, 4, 6, 10, 11]},
}

_AV_SUBJECTS = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                Graha.JUPITER, Graha.VENUS, Graha.SATURN]


def _classical_bav(cd: ChartData) -> Tuple[Dict[Graha, List[int]], List[int]]:
    """BAV per subject + SAV using the classical BPHS benefic-place tables."""
    positions: Dict[str, int] = {
        g.full_name: cd.planet(g).rasi.value for g in _AV_SUBJECTS
    }
    positions["Ascendant"] = Rasi.from_longitude(cd.ascendant).value

    bavs: Dict[Graha, List[int]] = {g: [0] * 12 for g in _AV_SUBJECTS}
    sav = [0] * 12
    for g in _AV_SUBJECTS:
        for ref_name, houses in _AV_TABLES[g.full_name].items():
            ref_sign = positions[ref_name]
            for h in houses:
                target = (ref_sign + h - 1) % 12
                bavs[g][target] += 1
                sav[target] += 1
    return bavs, sav


def _ashtakavarga_rows(cd: ChartData) -> Tuple[List[str], List[List[str]]]:
    """Header + rows for the Ashtakavarga (BAV/SAV) table."""
    bavs, sav = _classical_bav(cd)
    header = ["Sign No"] + [str(i) for i in range(1, 13)]
    rows = []
    for g in _AV_SUBJECTS:
        rows.append([g.full_name] + [str(v) for v in bavs[g]])
    rows.append(["Total"] + [str(v) for v in sav])
    return header, rows


def _sripati_bhavas(cd: ChartData) -> List[Tuple[float, float]]:
    """Return [(bhava_begin, bhava_madhya)] for houses 1..12 (Sripati)."""
    asc = cd.ascendant % 360.0
    mc = cd.mc % 360.0
    mid = [0.0] * 13  # 1-indexed
    mid[1] = asc
    mid[10] = mc
    mid[7] = (asc + 180.0) % 360.0
    mid[4] = (mc + 180.0) % 360.0

    def _fill(anchor_from: int, anchor_to: int, targets: Tuple[int, int]):
        arc = (mid[anchor_to] - mid[anchor_from]) % 360.0
        mid[targets[0]] = (mid[anchor_from] + arc / 3.0) % 360.0
        mid[targets[1]] = (mid[anchor_from] + 2.0 * arc / 3.0) % 360.0

    _fill(10, 1, (11, 12))
    _fill(1, 4, (2, 3))
    _fill(4, 7, (5, 6))
    _fill(7, 10, (8, 9))

    result = []
    for h in range(1, 13):
        prev_mid = mid[12] if h == 1 else mid[h - 1]
        arc = (mid[h] - prev_mid) % 360.0
        begin = (prev_mid + arc / 2.0) % 360.0
        result.append((begin, mid[h]))
    return result


def _chalit_rows(cd: ChartData) -> List[List[str]]:
    rows = []
    for h, (begin, mid) in enumerate(_sripati_bhavas(cd), start=1):
        rows.append([
            str(h),
            Rasi.from_longitude(begin).full_name,
            _dms(begin, sep="."),
            Rasi.from_longitude(mid).full_name,
            _dms(mid, sep="."),
        ])
    return rows


def _vimshottari_boxes(cd: ChartData) -> List[dict]:
    """9 mahadasa boxes with traditional antardasha rotation (from MD lord).

    Antardashas of the first (balance) mahadasa that ended before birth
    display '00/00/00', matching the classic report style.
    """
    first_lord, balance = _dasa_balance(cd)
    eng = VimsottariDasa()
    lords = eng.CYCLE_LORDS
    years = eng.CYCLE_YEARS
    first_idx = lords.index(first_lord)

    boxes = []
    birth_jd = cd.julian_day
    # First MD starts on the local birth date (as entered), not the UT date.
    birth_local = f"{cd.birth_date.day}/{cd.birth_date.month}/{cd.birth_date.year % 100:02d}"
    cur_start = birth_jd
    for i in range(9):
        li = (first_idx + i) % 9
        lord = lords[li]
        full = years[li]
        if i == 0:
            conceptual_start = birth_jd - (full - balance) * _YPD
        else:
            conceptual_start = cur_start
        end = conceptual_start + full * _YPD

        antars = []
        cum = 0.0
        for j in range(9):
            sj = (li + j) % 9
            cum += full * years[sj] / 120.0
            sub_end = conceptual_start + cum * _YPD
            label = "00/00/00" if sub_end <= birth_jd else _fmt_jd_date(sub_end)
            antars.append((lords[sj], label))

        boxes.append({
            "lord": lord,
            "full_years": full,
            "start": birth_local if i == 0 else _fmt_jd_date(cur_start),
            "end": _fmt_jd_date(end),
            "antars": antars,
        })
        cur_start = end
    return boxes


def _chart_occupants(cd: ChartData) -> Dict[int, List[str]]:
    """D-1: {house_number (from lagna): [planet abbreviations]}."""
    asc_rasi = Rasi.from_longitude(cd.ascendant)
    houses: Dict[int, List[str]] = {}
    for g, p in cd.planets.items():
        house = (p.rasi.value - asc_rasi.value) % 12 + 1
        houses.setdefault(house, []).append(g.short_name)
    for oname, abbr in _OUTER_ABBR.items():
        od = cd.outer_planets.get(oname)
        if od:
            r = Rasi.from_longitude(od["longitude"])
            house = (r.value - asc_rasi.value) % 12 + 1
            houses.setdefault(house, []).append(abbr)
    return houses


def _navamsa_sign(longitude: float) -> Rasi:
    """Standard D-9 sign for any longitude (used for outer planets)."""
    sign = int(longitude // 30) % 12
    deg = longitude % 30.0
    pada = int(deg // (30.0 / 9.0))
    r = Rasi(sign)
    if r.is_movable:
        start = sign
    elif r.is_fixed:
        start = (sign + 8) % 12
    else:
        start = (sign + 4) % 12
    return Rasi((start + pada) % 12)


def _navamsa_occupants(cd: ChartData) -> Tuple[Rasi, Dict[int, List[str]]]:
    """D-9 lagna rasi + {house_number: [abbreviations]}.

    Uses the standard Parashara navamsa (movable→same sign, fixed→9th,
    dual→5th) — the convention used by JHora/AstroSage traditional reports.
    """
    lagna_rasi = _navamsa_sign(cd.ascendant)
    houses: Dict[int, List[str]] = {}
    for g, p in cd.planets.items():
        r = _navamsa_sign(p.longitude)
        house = (r.value - lagna_rasi.value) % 12 + 1
        houses.setdefault(house, []).append(g.short_name)
    for oname, abbr in _OUTER_ABBR.items():
        od = cd.outer_planets.get(oname)
        if od:
            r = _navamsa_sign(od["longitude"])
            house = (r.value - lagna_rasi.value) % 12 + 1
            houses.setdefault(house, []).append(abbr)
    return lagna_rasi, houses


# ── Rendering (QPainter → QImage) ─────────────────────────────────────────────

_QAPP = None


def _ensure_qapp():
    """Return a QApplication, creating one if needed.

    Keeps a module-level reference — if the wrapper is garbage-collected,
    the underlying QApplication is destroyed and later painting crashes.

    Note: does NOT force the offscreen platform — offscreen Qt cannot load
    fonts and renders all text as boxes. Respects QT_QPA_PLATFORM if the
    environment already set it (e.g. CI), otherwise uses the native desktop
    platform (no window is ever shown).
    """
    global _QAPP
    from PyQt6.QtWidgets import QApplication
    _QAPP = QApplication.instance() or QApplication([])
    return _QAPP


# North Indian house-region centroids (fractions of chart size).
_NI_CENTROIDS = {
    1: (0.50, 0.24), 2: (0.25, 0.09), 3: (0.09, 0.25), 4: (0.24, 0.50),
    5: (0.09, 0.75), 6: (0.25, 0.91), 7: (0.50, 0.76), 8: (0.75, 0.91),
    9: (0.91, 0.75), 10: (0.76, 0.50), 11: (0.91, 0.25), 12: (0.75, 0.09),
}


def _draw_north_indian(painter, x: float, y: float, size: float,
                       lagna_rasi: Rasi, houses: Dict[int, List[str]],
                       ink, dim):
    """Classic North Indian diamond chart (black on white)."""
    from PyQt6.QtCore import QPointF, Qt
    from PyQt6.QtGui import QPen, QFont

    s = size
    painter.setPen(QPen(ink, 2))
    painter.drawRect(int(x), int(y), int(s), int(s))

    # Diamond through side midpoints
    mid_top = QPointF(x + s / 2, y)
    mid_right = QPointF(x + s, y + s / 2)
    mid_bottom = QPointF(x + s / 2, y + s)
    mid_left = QPointF(x, y + s / 2)
    painter.setPen(QPen(ink, 1.4))
    for a, b in ((mid_top, mid_right), (mid_right, mid_bottom),
                 (mid_bottom, mid_left), (mid_left, mid_top)):
        painter.drawLine(a, b)

    # Corner diagonals
    painter.drawLine(QPointF(x, y), QPointF(x + s, y + s))
    painter.drawLine(QPointF(x, y + s), QPointF(x + s, y))

    sign_font = QFont("Arial", 11)
    planet_font = QFont("Arial", 13, QFont.Weight.Bold)

    for house in range(1, 13):
        sign_num = (lagna_rasi.value + house - 1) % 12 + 1  # Aries = 1
        fx, fy = _NI_CENTROIDS[house]
        cx = x + fx * s
        cy = y + fy * s

        painter.setFont(sign_font)
        painter.setPen(dim)
        painter.drawText(int(cx - 14), int(cy - 13), str(sign_num))

        planets = houses.get(house, [])
        if planets:
            painter.setFont(planet_font)
            painter.setPen(ink)
            line_h = 17
            total_h = len(planets) * line_h
            ty = cy + 16 - max(0, (total_h - line_h) // 2)
            for abbr in planets:
                w = painter.fontMetrics().horizontalAdvance(abbr)
                painter.drawText(int(cx - w / 2), int(ty + 10), abbr)
                ty += line_h


def _draw_table(painter, x: float, y: float, title: str,
                headers: List[str], rows: List[List[str]],
                col_widths: List[float], row_h: float = 24,
                ink=None, shade=None) -> float:
    """Draw a titled grid table; return total height consumed."""
    from PyQt6.QtCore import QRectF, Qt
    from PyQt6.QtGui import QPen, QFont, QBrush

    title_font = QFont("Arial", 15, QFont.Weight.Bold)
    head_font = QFont("Arial", 12, QFont.Weight.Bold)
    cell_font = QFont("Arial", 12)

    painter.setFont(title_font)
    painter.setPen(ink)
    painter.drawText(int(x), int(y + 20), title)
    ty = y + 28

    total_w = sum(col_widths)

    # Header row
    painter.fillRect(QRectF(x, ty, total_w, row_h), QBrush(shade))
    painter.setFont(head_font)
    cx = x
    for htext, cw in zip(headers, col_widths):
        painter.setPen(ink)
        painter.drawRect(QRectF(cx, ty, cw, row_h).toRect())
        painter.drawText(QRectF(cx + 4, ty, cw - 8, row_h),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         htext)
        cx += cw
    ty += row_h

    painter.setFont(cell_font)
    for row in rows:
        cx = x
        for value, cw in zip(row, col_widths):
            painter.setPen(ink)
            painter.drawRect(QRectF(cx, ty, cw, row_h).toRect())
            painter.drawText(QRectF(cx + 4, ty, cw - 8, row_h),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             str(value))
            cx += cw
        ty += row_h
    return (ty - y)


def render_traditional_report(cd: ChartData, name: str = "", sex: str = "",
                              place: str = ""):
    """Render the full report to a QImage."""
    _ensure_qapp()
    from PyQt6.QtCore import QRectF, Qt
    from PyQt6.QtGui import QImage, QPainter, QColor, QPen, QFont

    ink = QColor("#000000")
    dim = QColor("#444444")
    shade = QColor("#d9d9d9")

    # ── Layout constants ──
    W = 1660
    M = 36                      # page margin
    CW = W - 2 * M              # content width = 1588
    GAP = 16

    title_h = 64
    header_h = 176
    chart_label_h = 30
    chart_size = 640
    dasha_title_h = 34
    box_h = 50 + 9 * 22         # dasa box: header + 9 antardasha rows
    dasha_grid_h = 3 * box_h + 2 * 12
    planets_h = 28 + 26 + 13 * 24
    chalit_h = 28 + 26 + 12 * 24
    bottom_h = planets_h + GAP + chalit_h
    footer_h = 44

    H = (M + title_h + header_h + GAP + chart_label_h + chart_size + GAP
         + dasha_title_h + dasha_grid_h + GAP + bottom_h + footer_h + M)

    image = QImage(W, H, QImage.Format.Format_RGB32)
    image.fill(QColor("#ffffff"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    y = M

    # ── Title ──
    painter.setFont(QFont("Arial", 26, QFont.Weight.Bold))
    painter.setPen(ink)
    painter.drawText(QRectF(0, y, W, 40), Qt.AlignmentFlag.AlignCenter,
                     "Traditional")
    line_y = y + 30
    painter.setPen(QPen(ink, 1.6))
    painter.drawLine(M, line_y, W // 2 - 190, line_y)
    painter.drawLine(W // 2 + 190, line_y, W - M, line_y)
    y += title_h

    # ── Header box ──
    painter.setPen(QPen(ink, 1.8))
    painter.drawRoundedRect(QRectF(M, y, CW, header_h), 10, 10)
    cols = _header_columns(cd, name, sex, place)
    col_x = [M + 16, M + 420, M + 800, M + 1180]
    label_font = QFont("Arial", 13, QFont.Weight.Bold)
    value_font = QFont("Arial", 13)
    row_h = (header_h - 20) / 6.0
    for ci, col in enumerate(cols):
        ry = y + 12
        for label, value in col:
            painter.setFont(label_font)
            painter.setPen(ink)
            painter.drawText(int(col_x[ci]), int(ry + 14), label)
            lw = painter.fontMetrics().horizontalAdvance(label)
            painter.setFont(value_font)
            painter.drawText(int(col_x[ci] + lw + 50), int(ry + 14), value)
            ry += row_h
    y += header_h + GAP

    # ── Charts (Lagna + Navamsa) ──
    chart_col_w = (CW - GAP) / 2.0
    lx = M + (chart_col_w - chart_size) / 2.0
    rx = M + chart_col_w + GAP + (chart_col_w - chart_size) / 2.0

    painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
    painter.setPen(ink)
    painter.drawText(QRectF(M, y, chart_col_w, 24),
                     Qt.AlignmentFlag.AlignCenter, "Lagna Chart")
    painter.drawText(QRectF(M + chart_col_w + GAP, y, chart_col_w, 24),
                     Qt.AlignmentFlag.AlignCenter, "Navamasa Chart")
    y += chart_label_h

    lagna_rasi = Rasi.from_longitude(cd.ascendant)
    _draw_north_indian(painter, lx, y, chart_size, lagna_rasi,
                       _chart_occupants(cd), ink, dim)
    nav_lagna, nav_houses = _navamsa_occupants(cd)
    _draw_north_indian(painter, rx, y, chart_size, nav_lagna,
                       nav_houses, ink, dim)
    y += chart_size + GAP

    # ── Vimshottari Dasha ──
    painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
    painter.setPen(ink)
    painter.drawText(QRectF(M, y, CW, 26), Qt.AlignmentFlag.AlignCenter,
                     "Vimshottari Dasha")
    y += dasha_title_h

    boxes = _vimshottari_boxes(cd)
    box_gap = 12
    box_w = (CW - 2 * box_gap) / 3.0
    head_font = QFont("Arial", 13, QFont.Weight.Bold)
    cell_font = QFont("Arial", 12)
    for bi, box in enumerate(boxes):
        brow, bcol = divmod(bi, 3)
        bx = M + bcol * (box_w + box_gap)
        by = y + brow * (box_h + box_gap)
        painter.setPen(QPen(ink, 1.4))
        painter.drawRect(QRectF(bx, by, box_w, box_h).toRect())

        painter.setFont(head_font)
        lord3 = _LORD3[box["lord"].full_name]
        painter.drawText(QRectF(bx, by + 4, box_w, 20),
                         Qt.AlignmentFlag.AlignCenter,
                         f"{lord3} - {box['full_years']} Years")
        painter.drawText(QRectF(bx, by + 24, box_w, 20),
                         Qt.AlignmentFlag.AlignCenter,
                         f"{box['start']} - {box['end']}")
        painter.setPen(QPen(ink, 1.0))
        painter.drawLine(int(bx), int(by + 48), int(bx + box_w), int(by + 48))

        painter.setFont(cell_font)
        ay = by + 52
        for sub_lord, end_label in box["antars"]:
            painter.setPen(ink)
            painter.drawText(int(bx + 14), int(ay + 15),
                             _LORD3[sub_lord.full_name])
            painter.drawText(int(bx + box_w - 100), int(ay + 15), end_label)
            ay += 22
    y += dasha_grid_h + GAP

    # ── Bottom tables ──
    left_w = 560
    right_x = M + left_w + GAP
    right_w = CW - left_w - GAP

    planet_rows = _planet_rows(cd)
    _draw_table(painter, M, y, "Planetary Positions",
                ["Planets", "Sign", "Longitude", "Nakshatra", "Pada"],
                planet_rows, [120, 110, 110, 160, 60], row_h=24,
                ink=ink, shade=shade)

    av_header, av_rows = _ashtakavarga_rows(cd)
    label_w = 110
    num_w = (right_w - label_w) / 12.0
    _draw_table(painter, right_x, y, "Ashtakvarga Table",
                av_header, av_rows, [label_w] + [num_w] * 12, row_h=24,
                ink=ink, shade=shade)

    chalit_rows = _chalit_rows(cd)
    _draw_table(painter, M, y + planets_h + GAP, "Chalit Table",
                ["Bhav", "Sign", "Bhav Begin", "Sign", "Mid Bhav"],
                chalit_rows, [60, 140, 110, 140, 110], row_h=24,
                ink=ink, shade=shade)

    # ── Footer ──
    painter.setFont(QFont("Arial", 10))
    painter.setPen(dim)
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    painter.drawText(QRectF(0, H - footer_h, W, 20),
                     Qt.AlignmentFlag.AlignCenter,
                     f"Generated by OpenJyotish (Jhora) — {now}")

    painter.end()
    return image


def generate_traditional_report(cd: ChartData, output_path: str,
                                name: str = "", sex: str = "",
                                place: str = "") -> str:
    """Render the traditional report and save as PNG or JPG (by extension)."""
    image = render_traditional_report(cd, name, sex, place)
    if not image.save(output_path):
        raise RuntimeError(f"Failed to save image: {output_path}")
    return output_path
