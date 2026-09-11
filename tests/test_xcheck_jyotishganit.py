"""Cross-check vs jyotishganit reference fixtures (offline replay).

Fixtures live in tools/xcheck/fixtures/<lib-version>/ (generated with the
isolated venv library). No network, no extra dependency at test time.
Layers: L0 ayanamsa-normalized longitudes, L1 panchanga indices.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.calc.muhurta import compute_panchanga
from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra

FIXTURES = Path(__file__).resolve().parent.parent / "tools" / "xcheck" \
    / "fixtures" / "0.1.0"

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
GRAHA_BY_BODY = {"Sun": Graha.SUN, "Moon": Graha.MOON, "Mars": Graha.MARS,
                 "Mercury": Graha.MERCURY, "Jupiter": Graha.JUPITER,
                 "Venus": Graha.VENUS, "Saturn": Graha.SATURN,
                 "Rahu": Graha.RAHU, "Ketu": Graha.KETU}
TITHI_NAMES = ["Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
               "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
               "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
               "Purnima"]
YOGA_NAMES = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
              "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi",
              "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi",
              "Vyatipata", "Variyana", "Parigha", "Shiva", "Siddha",
              "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"]
KARANA_ALIASES = {"taitula": "taitila", "garaja": "gara",
                  "naaga": "naga", "visti": "vishti"}


def _norm(name):
    return name.strip().lower().replace("poornima", "purnima")


def _norm_nakshatra(name):
    key = _norm(name).upper().replace(" ", "").replace("-", "").replace("_", "")
    key = key.replace("ASHADHA", "SHADHA")  # our enum spelling
    for member in Nakshatra:
        if member.name.replace("_", "") == key:
            return member
    raise KeyError(key)


def _adjacent(a, b, mod):
    return (a - b) % mod in (1, mod - 1)


def _load(cid):
    return json.loads((FIXTURES / f"{cid}.json").read_text())


def _chart_ids():
    return sorted(p.stem for p in FIXTURES.glob("*.json")
                  if p.stem != "index")


def _ours(fix):
    b = fix["birth"]
    y, mo, d = (int(x) for x in b["date"].split("-"))
    builder = ChartBuilder()
    cd = builder.build(y, mo, d, b["hour"], lat=b["lat"], lon=b["lon"],
                       tz=b["tz_str"])
    total_min = int(round(b["hour"] * 60.0))
    dt = datetime(y, mo, d, total_min // 60, total_min % 60)
    pc = compute_panchanga(dt, b["lat"], b["lon"], b["tz"])
    return cd, pc


def _their_tithi_index(tithi):
    paksha, _, name = tithi.partition(" ")
    names = [_norm(t) for t in TITHI_NAMES]
    idx = names.index(_norm(name))
    if "krishna" in paksha.lower():
        idx += 15
    return idx


@pytest.mark.parametrize("cid", _chart_ids())
def test_l0_longitudes_systematic_offset(cid):
    """The 7 planets share one near-constant offset (ayanamsa delta).

    Spread < 0.015° incl. lunar arcminute noise; center within 0.05°.
    Nodes are classified separately (different theory — see below).
    """
    fix = _load(cid)
    cd, _pc = _ours(fix)
    deltas = []
    for p in fix["data"]["planets"]:
        if p["body"] not in GRAHA_BY_BODY or p["body"] in ("Rahu", "Ketu"):
            continue
        if p["abs_lon"] is None:
            continue
        ours = cd.planet(GRAHA_BY_BODY[p["body"]]).longitude
        delta = (ours - p["abs_lon"] + 180.0) % 360.0 - 180.0
        deltas.append(delta)
    assert deltas, "no comparable planets"
    spread = max(deltas) - min(deltas)
    assert spread < 0.015, f"non-systematic longitudes: {spread:.4f}"
    assert abs(sum(deltas) / len(deltas)) < 0.05, "offset beyond ayanamsa"


def test_l0_nodes_use_different_theory():
    """Rahu gaps vary chart to chart (up to ~0.4°), unlike the planetary
    systematic — a different node theory (TRIAGE-1, open).

    Locks the finding: if either side's node theory changes, the range
    collapses and this fails loud for re-triage.
    """
    deltas = []
    for cid in _chart_ids():
        fix = _load(cid)
        cd, _pc = _ours(fix)
        p = next(x for x in fix["data"]["planets"] if x["body"] == "Rahu")
        ours = cd.planet(GRAHA_BY_BODY["Rahu"]).longitude
        deltas.append((ours - p["abs_lon"] + 180.0) % 360.0 - 180.0)
    assert max(deltas) - min(deltas) > 0.1, \
        f"node gaps converged unexpectedly: {deltas}"


@pytest.mark.parametrize("cid", _chart_ids())
def test_l1_panchanga_indices(cid):
    """Tithi/nakshatra/yoga/vara agree exactly — except the *-cusp charts,
    which sit on ayanamsa boundaries by design: there an off-by-one bin on
    either side is the expected systematic flip, not a mismatch."""
    fix = _load(cid)
    cd, pc = _ours(fix)
    pan = fix["data"]["panchanga"]
    cusp = cid.endswith("-cusp")
    want_tithi = _their_tithi_index(pan["tithi"])
    assert pc.tithi.index == want_tithi or (
        cusp and _adjacent(pc.tithi.index, want_tithi, 30)), pan["tithi"]
    want_nak = _norm_nakshatra(pan["nakshatra"])
    assert pc.nakshatra == want_nak or (
        cusp and _adjacent(pc.nakshatra.value, want_nak.value, 27)), \
        pan["nakshatra"]
    assert pc.weekday_name == pan["vaara"], pan["vaara"]
    assert pc.yoga_index == [_norm(y) for y in YOGA_NAMES].index(
        _norm(pan["yoga"])), pan["yoga"]


@pytest.mark.parametrize("cid", _chart_ids())
def test_l1_karana_index(cid):
    """Karana names agree via the canonical half-tithi rule.

    On *-cusp charts a neighboring half is accepted (arcminute ayanamsa
    differences flip 6° halves, same systematic class as the tithi flips).
    """
    from jhora.calc.muhurta import _KARANA_NAMES
    from jhora.types.graha import Graha
    fix = _load(cid)
    cd, pc = _ours(fix)
    pan = fix["data"]["panchanga"]
    karana = KARANA_ALIASES.get(_norm(pan["karana"].split()[0]),
                                _norm(pan["karana"].split()[0]))
    want = [_norm(k) for k in _KARANA_NAMES].index(karana)
    if cid.endswith("-cusp"):
        sun = cd.planet(Graha.SUN).longitude
        moon = cd.planet(Graha.MOON).longitude
        k = int(((moon - sun) % 360.0) // 6.0) % 60

        def _idx(kk):
            return 10 if kk == 0 else kk - 50 if kk >= 57 else (kk - 1) % 7

        allowed = {_idx((k - 1) % 60), _idx(k), _idx((k + 1) % 60)}
        assert pc.karana_index in allowed, pan["karana"]
    else:
        assert pc.karana_index == want, pan["karana"]
        assert pc.karana_name == _KARANA_NAMES[want]


@pytest.mark.parametrize("cid", _chart_ids())
def test_l2_dasa_mahadasa_boundaries(cid):
    """Mahadasa ends agree within days (catches year conventions); the birth
    MD balance fraction agrees to 0.3% (convention-free Moon agreement).

    Antardashas are NOT compared here: their ADs rotate from the MD lord
    while ours always start at Ketu (TRIAGE-3, open) — asserting equality
    would enshrine either behavior.
    """
    from datetime import date
    from jhora.dasas.vimsottari import VimsottariDasa
    fix = _load(cid)
    cd, _pc = _ours(fix)
    chart = {"planets": {g.value: {"longitude": p.longitude}
                         for g, p in cd.planets.items()},
             "lagna_lon": cd.ascendant}
    engine = VimsottariDasa()
    our_periods = engine.compute(cd.julian_day, chart)
    ours = {md.lord_name: md for md in our_periods}
    full_years = {lord.name.title(): yrs for lord, yrs in
                  zip(engine.CYCLE_LORDS, engine.CYCLE_YEARS)}
    b = fix["birth"]
    y, mo, d = (int(x) for x in b["date"].split("-"))
    birth = date(y, mo, d)
    # Our first MD starts at the birth moment (start_date is UTC-day
    # precision, so compare JDs, not calendar dates).
    assert abs(our_periods[0].start_jd - cd.julian_day) < 0.001
    for lord, span in fix["data"]["dashas"].items():
        assert lord in ours, f"MD lord {lord} missing on our side"
        md = ours[lord]
        their_end = datetime.fromisoformat(span["end"]).date()
        assert abs((md.end_date.date() - their_end).days) <= 10, lord
    # Birth MD only: balance fraction agreed (full MDs are 1.0 both sides).
    first = our_periods[0]
    t = fix["data"]["dashas"][first.lord_name]
    their_start = datetime.fromisoformat(t["start"]).date()
    their_end = datetime.fromisoformat(t["end"]).date()
    frac_ours = first.duration_years / full_years[first.lord_name]
    frac_theirs = ((their_end - birth).days
                   / (their_end - their_start).days)
    assert abs(frac_ours - frac_theirs) < 0.003, first.lord_name
    # Antardasas of full MDs (birth MD excluded: balance-shifted by design).
    # Order must match exactly; boundaries within 10 d (micro-differences
    # in Moon position accumulate down long MDs; convention errors would
    # show in months).
    for md in our_periods[1:]:
        t = fix["data"]["dashas"][md.lord_name]
        assert [ad.lord_name for ad in (md.sub_periods or [])] == \
            list(t["antardashas"].keys()), md.lord_name
        for ad in (md.sub_periods or []):
            ta = t["antardashas"][ad.lord_name]
            assert abs((ad.start_date.date()
                        - datetime.fromisoformat(
                            ta["start"]).date()).days) <= 10, \
                f"{md.lord_name}/{ad.lord_name}"


@pytest.mark.parametrize("cid", _chart_ids())
def test_l3_positional_strengths_agree(cid):
    """Uchcha/Dig/Kendra/Naisargika agree (positions, dignity, houses, and
    constants validated); Saptavargaja/Ojha/Drek/Paksha/Tribhaga/VMDH/Ayana/
    Cheshta/Drik follow different authority variants (TRIAGE-4, open) and
    are NOT asserted here."""
    from jhora.calc.shadbala import ShadbalaComputer
    fix = _load(cid)
    cd, _pc = _ours(fix)
    comp = ShadbalaComputer(cd)
    for g in (Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN):
        r = comp.compute_one(g)
        t = fix["data"]["shadbala"][g.name.title()]
        assert abs(r.sthana["uchcha"].virupa
                   - t["Sthanabala"]["Uchhabala"]) < 0.1, g.name
        assert r.sthana["kendra"].virupa == t["Sthanabala"]["Kendradhibala"], \
            g.name
        assert abs(r.dig["dig"].virupa - t["Digbala"]) < 6.0, g.name
        assert abs(r.naisargika.virupa - t["Naisargikabala"]) < 1e-9, g.name
