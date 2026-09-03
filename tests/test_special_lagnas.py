"""Tests for the special lagnas (Bhava, Hora, Ghati, Sree, Upapada)."""

import pytest

from jhora.calc import special_lagnas as sl
from jhora.calc.arudha import bhava_arudha
from jhora.charts.chart import ChartBuilder
from jhora.dasas.sudasa import Sudasa
from jhora.types.graha import Graha


def _chart():
    b = ChartBuilder()
    return b.build(year=1973, month=3, day=13, hour=13 + 55 / 60.0,
                   lat=28.6, lon=77.2, tz="-5.5")


def test_chart_fields_populated():
    cd = _chart()
    assert cd.bhava_lagna is not None
    assert cd.hora_lagna is not None
    assert cd.ghati_lagna is not None
    assert cd.sree_lagna is not None
    for lon in (cd.bhava_lagna.longitude, cd.hora_lagna.longitude,
                cd.ghati_lagna.longitude, cd.sree_lagna.longitude):
        assert 0 <= lon < 360


def test_time_lagnas_share_sunrise_base():
    """BL/HL/GL all advance from the same sun-at-sunrise base at their rates."""
    cd = _chart()
    base = sl._sun_at_sunrise(cd)
    minutes = sl._minutes_since_sunrise(cd)
    assert base is not None and minutes is not None
    assert sl.bhava_lagna(cd) == pytest.approx(
        (base + minutes * sl._DEG_PER_MIN["bhava"]) % 360.0)
    assert sl.hora_lagna(cd) == pytest.approx(
        (base + minutes * sl._DEG_PER_MIN["hora"]) % 360.0)
    assert sl.ghati_lagna(cd) == pytest.approx(
        (base + minutes * sl._DEG_PER_MIN["ghati"]) % 360.0)


def test_sree_lagna_matches_independent_formula():
    """Engine Sree matches the sudasa module's own nakshatra-fraction method."""
    cd = _chart()
    moon_lon = cd.planets[Graha.MOON].longitude
    assert sl.sree_lagna(cd) == pytest.approx(
        Sudasa._compute_sree_lagna(cd.ascendant, moon_lon))


def test_sree_lagna_nakshatra_fraction():
    """Sree = lagna + (Moon's nakshatra fraction) * 360°."""
    import dataclasses
    from jhora.charts.chart import ChartData
    b = ChartBuilder()
    cd = b.build(year=1973, month=3, day=13, hour=13 + 55 / 60.0,
                 lat=28.6, lon=77.2, tz="-5.5")
    # Moon exactly at its nakshatra start -> fraction 0 -> Sree = lagna
    from jhora.types.nakshatra import Nakshatra
    nak, _pada = Nakshatra.from_longitude(cd.planets[Graha.MOON].longitude)
    moon_at_start = nak.start_longitude
    cd2 = dataclasses.replace(cd, planets={
        **cd.planets,
        Graha.MOON: dataclasses.replace(cd.planets[Graha.MOON],
                                        longitude=moon_at_start),
    })
    assert sl.sree_lagna(cd2) == pytest.approx(cd.ascendant % 360.0)


def test_upapada_equals_arudha_of_12th():
    cd = _chart()
    planets = {g: {"longitude": cd.planet(g).longitude} for g in cd.planets}
    expected = int(bhava_arudha(12, cd.ascendant, planets))
    assert sl.upapada_lagna(cd) == expected


def test_compute_special_lagnas_includes_new():
    names = {s.name for s in sl.compute_special_lagnas(_chart())}
    for expected in ("Bhava Lagna", "Hora Lagna", "Ghati Lagna",
                     "Sree Lagna", "Upapada Lagna"):
        assert expected in names
