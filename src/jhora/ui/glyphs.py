"""Glyph provider for the circular wheel — bundled fonts only.

Primary: Zodiac Free (OFL, Private Use Area codepoints recorded from the
foundry's glyphs.json). Backstop: Noto Sans Symbols 2 (OFL, standard
Unicode astro codepoints). Last resort: the ASCII abbreviations the
diamond charts already use. System fonts are never consulted; every
lookup is verified with ``QFontMetrics.inFont``.
"""

import os
from typing import Dict, Optional, Tuple

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

_FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "assets", "fonts")

ZODIAC_FAMILY = "Zodiac Font FREE"
NOTO_FAMILY = "Noto Sans Symbols 2"

#: Zodiac Free PUA codepoints (foundry glyphs.json).
_ZODIAC_SIGNS = {
    Rasi.ARIES: 0xE000, Rasi.TAURUS: 0xE005, Rasi.GEMINI: 0xE009,
    Rasi.CANCER: 0xE001, Rasi.LEO: 0xE006, Rasi.VIRGO: 0xE00A,
    Rasi.LIBRA: 0xE002, Rasi.SCORPIO: 0xE007, Rasi.SAGITTARIUS: 0xE00B,
    Rasi.CAPRICORN: 0xE004, Rasi.AQUARIUS: 0xE008, Rasi.PISCES: 0xE00C,
}
_ZODIAC_GRAHAS = {
    Graha.SUN: 0xE101, Graha.MOON: 0xE102, Graha.MERCURY: 0xE103,
    Graha.VENUS: 0xE104, Graha.MARS: 0xE105, Graha.JUPITER: 0xE106,
    Graha.SATURN: 0xE107, Graha.RAHU: 0xE300, Graha.KETU: 0xE301,
}

#: Noto Sans Symbols 2 standard Unicode astro codepoints.
_NOTO_SIGNS = {r: 0x2648 + i for i, r in enumerate(Rasi)}
_NOTO_GRAHAS = {
    Graha.SUN: 0x2609, Graha.MOON: 0x263D, Graha.MERCURY: 0x263F,
    Graha.VENUS: 0x2640, Graha.MARS: 0x2642, Graha.JUPITER: 0x2643,
    Graha.SATURN: 0x2644, Graha.RAHU: 0x260A, Graha.KETU: 0x260B,
}

_loaded: Optional[Dict[str, str]] = None
_loaded_app = None


def ensure_fonts() -> Dict[str, str]:
    """Load bundled fonts for the current QApplication; return {key: family}.

    Idempotent per application instance. The cache is keyed on
    ``QApplication.instance()`` because application fonts die with
    their application (notably across test modules that each build
    their own offscreen QApplication).
    """
    global _loaded, _loaded_app
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if _loaded is not None and _loaded_app is app:
        return _loaded
    from PyQt6.QtGui import QFontDatabase
    out = {}
    for key, path in (("zodiac", os.path.join(_FONTS_DIR,
                                              "ZodiacFontFREE.woff2")),
                      ("noto", os.path.join(_FONTS_DIR,
                                            "NotoSansSymbols2-Regular.ttf"))):
        fid = QFontDatabase.addApplicationFont(path)
        fams = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
        out[key] = fams[0] if fams else ""
    _loaded, _loaded_app = out, app
    return out


def _in_font(char: str, family: str) -> bool:
    from PyQt6.QtGui import QFont, QFontMetrics
    return QFontMetrics(QFont(family)).inFont(char)


def glyph_for_graha(g: Graha) -> Tuple[str, str, bool]:
    """(text, font family, is_glyph) for a planet."""
    fams = ensure_fonts()
    zc = chr(_ZODIAC_GRAHAS[g])
    if fams["zodiac"] and _in_font(zc, fams["zodiac"]):
        return zc, fams["zodiac"], True
    nc = chr(_NOTO_GRAHAS[g])
    if fams["noto"] and _in_font(nc, fams["noto"]):
        return nc, fams["noto"], True
    return g.short_name, "", False


def glyph_for_rasi(r: Rasi) -> Tuple[str, str, bool]:
    """(text, font family, is_glyph) for a sign."""
    fams = ensure_fonts()
    zc = chr(_ZODIAC_SIGNS[r])
    if fams["zodiac"] and _in_font(zc, fams["zodiac"]):
        return zc, fams["zodiac"], True
    nc = chr(_NOTO_SIGNS[r])
    if fams["noto"] and _in_font(nc, fams["noto"]):
        return nc, fams["noto"], True
    return r.short_name, "", False
