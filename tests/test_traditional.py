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
