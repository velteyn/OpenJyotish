"""Tests for the wheel glyph provider — bundled fonts only."""

import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PyQt6.QtWidgets import QApplication

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.ui import glyphs


@pytest.fixture(scope="module")
def _qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(scope="module")
def _fonts(_qapp):
    return glyphs.ensure_fonts()


class TestProvider:
    def test_fonts_load(self, _fonts):
        assert _fonts["zodiac"]
        assert _fonts["noto"]

    def test_all_grahas_glyph(self, _fonts):
        for g in Graha:
            text, family, is_glyph = glyphs.glyph_for_graha(g)
            assert is_glyph, g
            assert family == _fonts["zodiac"]
            assert len(text) == 1

    def test_all_rasis_glyph(self, _fonts):
        for r in Rasi:
            text, family, is_glyph = glyphs.glyph_for_rasi(r)
            assert is_glyph, r
            assert family == _fonts["zodiac"]

    def test_distinct_codepoints(self):
        graha_chars = {glyphs._ZODIAC_GRAHAS[g] for g in Graha}
        assert len(graha_chars) == 9
        assert len(set(glyphs._ZODIAC_SIGNS.values())) == 12

    def test_noto_backstop_unicode(self):
        assert glyphs._NOTO_GRAHAS[Graha.SUN] == 0x2609
        assert glyphs._NOTO_SIGNS[Rasi.ARIES] == 0x2648
        assert glyphs._NOTO_SIGNS[Rasi.PISCES] == 0x2653

    def test_reloads_for_new_application(self, _qapp, _fonts):
        # Application fonts die with their QApplication: a stale cache
        # must reload instead of serving dead family names.
        glyphs._loaded_app = object()
        try:
            fresh = glyphs.ensure_fonts()
            assert fresh["zodiac"]
            text, family, is_glyph = glyphs.glyph_for_graha(Graha.MARS)
            assert is_glyph and family == fresh["zodiac"]
        finally:
            glyphs._loaded_app = _qapp
