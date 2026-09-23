"""Tests for the traditional one-page report (layout + data parity)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from jhora.charts.chart import ChartBuilder


def _chart():
    b = ChartBuilder()
    return b.build(1995, 10, 31, 12 + 25 / 60 + 30 / 3600,
                   19.18, 72.50, tz="+0530")


def test_planet_rows_cover_lagna_nine_grahas():
    from jhora.export.traditional import _planet_rows
    rows = _planet_rows(_chart())
    labels = [r[0].replace(" [R]", "") for r in rows]
    assert labels[0] == "ASC"
    for want in ("Sun", "Moon", "Mars", "Merc", "Jupt", "Venu", "Satn",
                 "Rahu", "Ketu"):
        assert want in labels, labels


def test_sav_totals_match_reference_grid():
    """SAV row must reproduce the classical totals exactly."""
    from jhora.export.traditional import _classical_bav
    _bavs, sav = _classical_bav(_chart())
    assert sav == [28, 26, 34, 28, 30, 33, 26, 34, 22, 24, 26, 26]
    assert sum(sav) == 337


def test_chalit_twelve_signed_rows():
    from jhora.export.traditional import _chalit_rows
    rows = _chalit_rows(_chart())
    assert len(rows) == 12
    assert rows[0][1] == "Sagittarius"  # bhava-1 begin sign
    assert rows[0][3] == "Capricorn"    # bhava-1 madhya sign


def test_vimshottari_nine_boxes_start_at_birth():
    from jhora.export.traditional import _vimshottari_boxes
    boxes = _vimshottari_boxes(_chart())
    assert len(boxes) == 9
    assert boxes[0]["start"] == "31/10/95"
    assert boxes[0]["antars"][0][1] == "00/00/00"  # pre-birth AD blanked
    assert boxes[-1]["end"] == "28/3/09"


def test_render_smoke(tmp_path):
    from jhora.export.traditional import render_traditional_report
    img = render_traditional_report(_chart(), "Native", "F", "Mumbai")
    assert img.width() == 1488
    assert img.height() > 2000
    out = str(tmp_path / "trad.png")
    assert img.save(out) and os.path.getsize(out) > 100_000


def _jalkot_lahiri():
    b = ChartBuilder()
    return b.build(2001, 2, 24, 6 + 11 / 60,
                   lat=18 + 38 / 60, lon=77 + 12 / 60,
                   tz="+0530", ayanamsa="lahiri")


_YOGA_ALIASES = {
    ("Vishkambha", "Vishkumbha"), ("Priti", "Preeti"),
    ("Sukarma", "Sukarman"), ("Dhriti", "Dhrithi"),
    ("Shula", "Shoola"), ("Variyana", "Varigha"),
    ("Parigha", "Paridha"),
}
_KARANA_ALIASES = {("Taitila", "Taitula"), ("Gara", "Garaja")}


def _same_or_alias(a, b, aliases):
    return a == b or (a, b) in aliases or (b, a) in aliases


class TestOnePagerEngineParity:
    """Every value on the one-pager must equal the engine's value.

    The page shows limbs at the birth moment (Janma tithi etc.); the
    daily calendar shows sunrise limbs — different moments by design,
    so these tests compare against the low-level limb functions at
    birth longitudes, not against the calendar day.
    """

    def test_tithi_names_aligned(self):
        # muhurta keeps its 15-name list local to _tithi; pin the shared
        # convention explicitly (Poornima/Amavasya shared at index 14).
        from jhora.export.traditional import _TITHI_NAMES as PAGE_TITHI
        assert list(PAGE_TITHI) == [
            "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
            "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
            "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
            "Poornima/Amavasya",
        ]

    def test_yoga_lists_same_order_modulo_aliases(self):
        from jhora.calc.muhurta import _YOGA_NAMES as ENG
        from jhora.export.traditional import _YOGA_NAMES as PAGE
        assert len(ENG) == len(PAGE) == 27
        for e, p in zip(ENG, PAGE):
            assert _same_or_alias(e, p, _YOGA_ALIASES), (e, p)

    def test_karana_lists_same_order_modulo_aliases(self):
        from jhora.calc.muhurta import _KARANA_NAMES as ENG
        from jhora.export.traditional import _KARANA_NAMES as PAGE
        assert len(ENG) == len(PAGE) == 11
        for e, p in zip(ENG, PAGE):
            assert _same_or_alias(e, p, _KARANA_ALIASES), (e, p)

    def test_header_limbs_match_engine(self):
        from jhora.calc.muhurta import _karana, _tithi, _yoga
        from jhora.export.traditional import (
            _YOGA_NAMES as PAGE_YOGA, _panchanga_fields)
        from jhora.types.graha import Graha
        for cd in (_chart(), _jalkot_lahiri()):
            sun = cd.planet(Graha.SUN).longitude
            moon = cd.planet(Graha.MOON).longitude
            page = _panchanga_fields(cd)
            tithi = _tithi(sun, moon)
            assert page["tithi"] == tithi.name
            assert PAGE_YOGA.index(page["yoga"]) == _yoga(sun, moon)
            _, karana_name = _karana(sun, moon)
            assert _same_or_alias(page["karana"], karana_name,
                                  _KARANA_ALIASES)

    def test_bav_sav_match_engine(self):
        from jhora.calc.ashtakavarga import (
            all_bhinna_ashtakavarga, sarva_ashtakavarga)
        from jhora.export.traditional import _classical_bav
        for cd in (_chart(), _jalkot_lahiri()):
            bavs, sav = _classical_bav(cd)
            eng_bavs = all_bhinna_ashtakavarga(cd)
            assert sav == sarva_ashtakavarga(cd)
            for g in bavs:
                assert bavs[g] == eng_bavs[g]

    def test_dasa_balance_matches_engine(self):
        from jhora.dasas.vimsottari import VimsottariDasa
        from jhora.export.traditional import _dasa_balance
        for cd in (_chart(), _jalkot_lahiri()):
            lord, balance = _dasa_balance(cd)
            eng = VimsottariDasa()
            chart = {"planets": {g.value: {"longitude": p.longitude}
                                 for g, p in cd.planets.items()},
                     "lagna_lon": cd.ascendant}
            first = eng.compute(cd.julian_day, chart)[0]
            assert lord.full_name == first.lord_name
            assert balance == pytest.approx(first.duration_years, rel=1e-3)
