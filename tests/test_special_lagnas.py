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


# ── User's Special Lagna ─────────────────────────────────────────────────────

def test_usl_jupiter_factor_1():
    """USL with Jupiter, factor=1 should be a valid longitude."""
    cd = _chart()
    lon = sl.user_special_lagna(cd, Graha.JUPITER, 1.0)
    assert lon is not None
    assert 0 <= lon < 360


def test_usl_returns_none_for_body_without_rise():
    """Graceful handling when rise_trans can't determine a rise time."""
    import dataclasses
    # Artificial: midnight birth near Arctic circle may have no moonrise
    cd = _chart()
    # Just verify the function doesn't crash for every planet
    for p in Graha:
        result = sl.user_special_lagna(cd, p, 1.0)
        # Either a valid longitude or None — both are acceptable
        assert result is None or 0 <= result < 360


def test_usl_reverse_opposes_forward():
    """With reverse=True the rate is negated — result differs from forward."""
    cd = _chart()
    fwd = sl.user_special_lagna(cd, Graha.JUPITER, 5.0, reverse=False)
    rev = sl.user_special_lagna(cd, Graha.JUPITER, 5.0, reverse=True)
    assert fwd is not None and rev is not None
    # At a non-trivial time after rise, forward ≠ reverse (unless minutes_since_rise == 0)
    rise_jd = sl._planet_rise(cd, Graha.JUPITER)[1]
    minutes_since = (cd.julian_day - rise_jd) * 1440.0
    if minutes_since != 0:
        assert fwd != pytest.approx(rev)


def test_usl_ketu_base_is_rahu_plus_180():
    """Ketu base = Rahu's longitude at Rahu's rise + 180°."""
    cd = _chart()
    rahu_lon, rahu_rise_jd = sl._planet_rise(cd, Graha.RAHU)
    ketu_lon, ketu_rise_jd = sl._planet_rise(cd, Graha.KETU)
    assert rahu_lon is not None and ketu_lon is not None
    assert ketu_lon == pytest.approx((rahu_lon + 180.0) % 360.0, abs=0.01)
    # Both use Rahu's rise as the time reference
    assert ketu_rise_jd == pytest.approx(rahu_rise_jd)


def test_usl_speed_factor_rate():
    """USL advances at speed_factor × 15°/hr from the rise base."""
    cd = _chart()
    factor = 3.0
    lon = sl.user_special_lagna(cd, Graha.MOON, factor)
    assert lon is not None
    base, rise_jd = sl._planet_rise(cd, Graha.MOON)
    minutes_since = (cd.julian_day - rise_jd) * 1440.0
    expected = (base + minutes_since * factor * 15.0 / 60.0) % 360.0
    assert lon == pytest.approx(expected)


def test_usl_name_integer_factor():
    cfg = sl.UserSpecialLagnaConfig(Graha.JUPITER, 9.0)
    assert sl.user_special_lagna_name(cfg) == "Ju9"


def test_usl_name_fractional_factor():
    cfg = sl.UserSpecialLagnaConfig(Graha.RAHU, 3.5, reverse=True)
    assert sl.user_special_lagna_name(cfg) == "Ra3.5R"


def test_usl_name_no_reverse():
    cfg = sl.UserSpecialLagnaConfig(Graha.SATURN, 2.0, reverse=False)
    assert sl.user_special_lagna_name(cfg) == "Sa2"
