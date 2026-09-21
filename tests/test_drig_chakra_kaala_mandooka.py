"""Tests for Kaala / Chakra / Mandooka dasas (gated change).

Golden sources (see design.md for the full gate record):
- Mandooka KNR: the published "Mandooka dasa of K.N. Rao" table on the
  1990 fixture + the KNR school order tables for all lagna parities.
- Kaala/Chakra: the PVR paper tables (Rajiv Gandhi, Kennedy, Reagan).
  Caveat recorded in the tests: the paper's JFK/Reagan Kaala dates are
  structurally inconsistent with its own fraction rule (JFK needs
  F = 153 > 120), so those assert internal ratios only; Rajiv (whose
  residual is ~3 min of input-level slop) asserts absolute dates.
- Drig: deferred open (Aq-anchor anomaly) — its tests join this file
  once the Ta/Ar-lagna discriminator resolves it.
"""

from datetime import date

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaOptions
from jhora.dasas.chakra import ChakraDasa
from jhora.dasas.kaala import KaalaDasa, day_parts, kaala_fraction
from jhora.dasas.mandooka import (
    mandooka_order,
    mandooka_years,
    MandookaDasa,
    _count_years,
)
from jhora.types.dasa import PeriodLevel
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

_FIXTURE = dict(year=1990, month=1, day=15, hour=17.5,
                lat=12.9716, lon=77.5946, tz="+0530")


def _chart(**kw):
    args = dict(_FIXTURE)
    args.update(kw)
    cd = ChartBuilder().build(
        year=args["year"], month=args["month"], day=args["day"],
        hour=args["hour"], lat=args["lat"], lon=args["lon"], tz=args["tz"])
    return cd, {"planets": {g: {"longitude": p.longitude}
                            for g, p in cd.planets.items()},
                "lagna_lon": cd.ascendant,
                "lat": args["lat"], "lon": args["lon"], "tz": args["tz"]}


def _md_only():
    return DasaOptions(subdivision_level=PeriodLevel.MAHADASA,
                       include_subperiods=False)


def _lords(periods):
    return [Rasi(p.lord_index - 100).short_name for p in periods]


# ── Mandooka order (KNR school tables) ──────────────────────────────

def test_mandooka_order_aries():
    assert mandooka_order(0) == [0, 3, 6, 9, 1, 4, 7, 10, 2, 5, 8, 11]


def test_mandooka_order_taurus():
    assert mandooka_order(1) == [7, 4, 1, 10, 6, 3, 0, 9, 5, 2, 11, 8]


def test_mandooka_order_gemini():
    assert mandooka_order(2) == [2, 5, 8, 11, 3, 6, 9, 0, 4, 7, 10, 1]


def test_mandooka_order_covers_all_signs():
    for lagna in range(12):
        assert sorted(mandooka_order(lagna)) == list(range(12))


# ── Mandooka year counting ──────────────────────────────────────────

def test_mandooka_count_parity_is_sign_number_not_footedness():
    # Leo (even-footed but even index) counts FORWARD: the 1990 table
    # gives Le 6 (Le→Cp), which footedness would compute as 8.
    assert _count_years(4, 9, lagna=2) == 6
    # Aquarius (even-footed, even index) counts FORWARD: 11, not 3.
    assert _count_years(10, 8, lagna=2) == 11
    # Taurus (odd-footed, odd index) counts BACKWARD: 5, not 9.
    assert _count_years(1, 9, lagna=2) == 5


def test_mandooka_count_specials():
    assert _count_years(7, 7, lagna=2) == 12  # own sign
    assert _count_years(5, 8, lagna=2) == 10  # lord 7th from sign
    # 12th-from-lagna reading: Cp's lord in Sg is 12th from lagna Ge,
    # but plain backward count (2) stands — the naive "12th from the
    # dasa rasi" reading would wrongly give 12 (reference: Cp runs 2).
    assert _count_years(9, 8, lagna=2) == 2


def test_mandooka_scorpio_always_mars_reverse():
    assert mandooka_years(7, {Graha.MARS: 7, Graha.KETU: 1}, 2) == 12
    assert mandooka_years(7, {Graha.MARS: 5, Graha.KETU: 7}, 2) == 3


# ── Mandooka 1990 reference table ───────────────────────────────────

_REF_1990 = [
    ("Ge", 10, date(1990, 1, 15)), ("Vi", 10, date(2000, 1, 16)),
    ("Sg", 10, date(2010, 1, 16)), ("Pi", 10, date(2020, 1, 16)),
    ("Cn", 12, date(2030, 1, 16)), ("Li", 4, date(2042, 1, 16)),
    ("Cp", 2, date(2046, 1, 16)), ("Ar", 8, date(2048, 1, 16)),
    ("Le", 6, date(2056, 1, 16)), ("Sc", 12, date(2062, 1, 16)),
    ("Aq", 11, date(2074, 1, 16)), ("Ta", 5, date(2085, 1, 16)),
]


def test_mandooka_1990_reference_table():
    cd, chart = _chart()
    mds = MandookaDasa(_md_only()).compute(cd.julian_day, chart)
    assert _lords(mds) == [s for s, _, _ in _REF_1990]
    assert [round(m.duration_years) for m in mds] == [y for _, y, _ in _REF_1990]
    assert sum(m.duration_years for m in mds) == 100
    for m, (_, _, day) in zip(mds, _REF_1990):
        # Reference uses true sidereal years (365.25636d) and keeps
        # times-of-day; we use mean solar (365.2425d) truncated to dates,
        # so starts drift up to ~2d over a century. Lords, durations
        # and contiguity above are the exact assertions.
        assert abs((m.start_date.date() - day).days) <= 2
    assert all(abs(a.end_jd - b.start_jd) < 1e-9
               for a, b in zip(mds, mds[1:]))


def test_mandooka_ads_rotate_global_order_equal_shares():
    cd, chart = _chart()
    mds = MandookaDasa().compute(cd.julian_day, chart)
    order = mandooka_order(2)
    first = mds[0]
    assert [Rasi(a.lord_index - 100).short_name
            for a in first.sub_periods] == [
                Rasi(s).short_name for s in order]
    assert first.sub_periods[0].duration_years == pytest.approx(
        first.duration_years / 12.0)
    fifth = mds[4]  # Cn MD: rotated to start at Cn
    assert Rasi(fifth.sub_periods[0].lord_index - 100).short_name == "Cn"


# ── Kaala ───────────────────────────────────────────────────────────

def test_kaala_needs_geo():
    cd, chart = _chart()
    del chart["lat"]
    with pytest.raises(ValueError):
        KaalaDasa(_md_only()).compute(cd.julian_day, chart)


def test_kaala_day_parts_rajiv_dawn():
    from datetime import datetime
    parts = day_parts(datetime(1944, 8, 20), 18.9667, 72.8167, 5.5)
    name, frac = kaala_fraction(7 + 12 / 60.0, parts)
    assert name == "dawn"
    assert 0.66 < frac < 0.70


def test_kaala_rajiv_vectors():
    from jhora.charts.chart import ChartBuilder as CB
    cd = CB().build(year=1944, month=8, day=20, hour=7 + 12 / 60.0,
                    lat=18.9667, lon=72.8167, tz="+0530")
    chart = {"planets": {g: {"longitude": p.longitude}
                         for g, p in cd.planets.items()},
             "lagna_lon": cd.ascendant,
             "lat": 18.9667, "lon": 72.8167, "tz": "+0530"}
    mds = KaalaDasa(_md_only()).compute(cd.julian_day, chart)
    assert len(mds) == 18  # two Sun..Ketu cycles
    assert round(sum(m.duration_years for m in mds), 6) == 120.0
    assert mds[0].lord_name == "Sun"
    # Paper: Sun ends 1946-06-05. Residual (~12d solar) is ~3 min of
    # input-level slop (birth time/sunrise); the paper's own JFK/Reagan
    # tables are structurally inconsistent (JFK needs F = 153 > 120),
    # so absolute dates pin only Rajiv, and loosely.
    assert abs((mds[0].end_date.date() - date(1946, 6, 5)).days) <= 15
    # Internal 1:2:...:9 ratios hold on all three paper charts.
    for args in [(1944, 8, 20, 7 + 12 / 60.0, 18.9667, 72.8167, "+0530"),
                 (1917, 5, 29, 16.0, 42.33, -71.12, "-0400"),
                 (1911, 2, 6, 2 + 3 / 60.0 + 15 / 3600.0,
                  41.63, -89.78, "-0600")]:
        cd2 = CB().build(year=args[0], month=args[1], day=args[2],
                         hour=args[3], lat=args[4], lon=args[5], tz=args[6])
        ch2 = {"planets": {g: {"longitude": p.longitude}
                           for g, p in cd2.planets.items()},
               "lagna_lon": cd2.ascendant,
               "lat": args[4], "lon": args[5], "tz": args[6]}
        first = KaalaDasa(_md_only()).compute(cd2.julian_day, ch2)[:9]
        unit = first[0].duration_years
        assert [round(m.duration_years / unit) for m in first] == list(
            range(1, 10))


def test_kaala_two_phase_ads():
    cd, chart = _chart()
    mds = KaalaDasa().compute(cd.julian_day, chart)
    sun_ads = mds[0].sub_periods
    assert len(sun_ads) == 18  # 9 + 9 across the two phases
    assert [a.lord_name for a in sun_ads[:9]] == [
        a.lord_name for a in sun_ads[9:]]
    assert sun_ads[0].lord_name == "Sun"
    assert sum(a.duration_years for a in sun_ads) == pytest.approx(
        mds[0].duration_years)


# ── Chakra ──────────────────────────────────────────────────────────

def test_chakra_needs_geo():
    cd, chart = _chart()
    del chart["tz"]
    with pytest.raises(ValueError):
        ChakraDasa(_md_only()).compute(cd.julian_day, chart)


def test_chakra_starts():
    from jhora.charts.chart import ChartBuilder as CB
    cases = [
        # (birthdata, expected start): Rajiv dawn→lagna+1, JFK day→lord,
        # Reagan night→lagna.
        ((1944, 8, 20, 7.2, 18.9667, 72.8167, "+0530"), "Vi"),
        ((1917, 5, 29, 16.0, 42.33, -71.12, "-0400"), "Ar"),
        ((1911, 2, 6, 2.054, 41.63, -89.78, "-0600"), "Sc"),
    ]
    for (y, m, d, h, lat, lon, tz), exp in cases:
        cd = CB().build(year=y, month=m, day=d, hour=h,
                        lat=lat, lon=lon, tz=tz)
        chart = {"planets": {g: {"longitude": p.longitude}
                             for g, p in cd.planets.items()},
                 "lagna_lon": cd.ascendant,
                 "lat": lat, "lon": lon, "tz": tz}
        mds = ChakraDasa(_md_only()).compute(cd.julian_day, chart)
        assert Rasi(mds[0].lord_index - 100).short_name == exp
        assert [round(m.duration_years) for m in mds] == [10] * 12
        assert round(sum(m.duration_years for m in mds)) == 120
        assert all(abs(a.end_jd - b.start_jd) < 1e-6
                   for a, b in zip(mds, mds[1:]))


def test_chakra_ads_start_at_parent_equal_split():
    cd, chart = _chart()
    mds = ChakraDasa().compute(cd.julian_day, chart)
    first = mds[0]
    assert Rasi(first.sub_periods[0].lord_index - 100).short_name == \
        Rasi(first.lord_index - 100).short_name
    assert len(first.sub_periods) == 12
    assert first.sub_periods[0].duration_years == pytest.approx(
        first.duration_years / 12.0)
