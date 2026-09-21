"""Tests for the conditional nakshatra dasa suite (BPHS gates).

Golden rules: PVR's unified conditional-dasas paper as the mainstream
statement, BPHS verses (Santhanam translation) cross-checked, and the
independent method tables as implementation reference.
"""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaOptions
from jhora.dasas.conditional import (
    ALL_CONDITIONAL,
    _ctx,
    dwadasamsa_sign,
    hora_lord,
    list_applicable,
    navamsa_sign,
    paksha,
)
from jhora.types.dasa import PeriodLevel
from jhora.types.graha import Graha


def _chart(year=1990, month=1, day=15, hour=17.5):
    return ChartBuilder().build(
        year=year, month=month, day=day, hour=hour,
        lat=12.9716, lon=77.5946, tz="+0530")


def test_totals_match_bphs():
    assert {k: v.total_years for k, v in ALL_CONDITIONAL.items()} == {
        "dwisaptati": 72, "shodasottari": 116, "dwadasottari": 112,
        "panchottari": 105, "shashtihayani": 60, "sataabdika": 100,
        "chaturaaseeti": 84, "shattrimsa": 36,
    }
    for dasa in ALL_CONDITIONAL.values():
        assert round(sum(dasa.durations.values()), 6) == dasa.total_years


def test_durations_match_bphs_tables():
    from jhora.dasas.conditional import (
        CHATURAASEETI, DWADASOTTARI, PANCHOTTARI, SATAABDIKA,
        SHASHTIHAYANI, SHATTRIMSA, SHODASOTTARI,
    )
    assert [SHODASOTTARI.durations[g] for g in SHODASOTTARI.order] == \
        [11, 12, 13, 14, 15, 16, 17, 18]
    assert [DWADASOTTARI.durations[g] for g in DWADASOTTARI.order] == \
        [7, 9, 11, 13, 15, 17, 19, 21]
    assert [PANCHOTTARI.durations[g] for g in PANCHOTTARI.order] == \
        [12, 13, 14, 15, 16, 17, 18]
    assert [SATAABDIKA.durations[g] for g in SATAABDIKA.order] == \
        [5, 5, 10, 10, 20, 20, 30]
    assert [SHATTRIMSA.durations[g] for g in SHATTRIMSA.order] == \
        [1, 2, 3, 4, 5, 6, 7, 8]
    assert [CHATURAASEETI.durations[g] for g in CHATURAASEETI.order] == \
        [12] * 7
    assert [SHASHTIHAYANI.durations[g] for g in SHASHTIHAYANI.order] == \
        [10, 10, 10, 6, 6, 6, 6, 6]


def test_seed_orders():
    from jhora.dasas.conditional import (
        DWISAPTATI, PANCHOTTARI, SATAABDIKA, SHODASOTTARI,
    )
    g = Graha
    assert DWISAPTATI.order[:2] == [g.SUN, g.MOON]
    assert SHODASOTTARI.order == [g.SUN, g.MARS, g.JUPITER, g.SATURN,
                                  g.KETU, g.MOON, g.MERCURY, g.VENUS]
    assert PANCHOTTARI.order == [g.SUN, g.MERCURY, g.SATURN, g.MARS,
                                 g.VENUS, g.MOON, g.JUPITER]
    assert SATAABDIKA.order == [g.SUN, g.MOON, g.VENUS, g.MERCURY,
                                g.JUPITER, g.MARS, g.SATURN]


def test_nak_lord_maps():
    d = ALL_CONDITIONAL
    # Pushya (7) starts Shodasottari with Sun; Revati (26) starts
    # Sataabdika with Sun; Sravana (21) starts Shattrimsa with Moon.
    assert d["shodasottari"].lord_for_nak(7) == Graha.SUN
    assert d["sataabdika"].lord_for_nak(26) == Graha.SUN
    assert d["shattrimsa"].lord_for_nak(21) == Graha.MOON
    # Dwadasottari counts anti-zodiacally from Revati: Revati→Sun,
    # U.Bhadra (25)→Jupiter, P.Bhadra (24)→Ketu.
    assert d["dwadasottari"].lord_for_nak(26) == Graha.SUN
    assert d["dwadasottari"].lord_for_nak(25) == Graha.JUPITER
    assert d["dwadasottari"].lord_for_nak(24) == Graha.KETU
    # Shashtihayani explicit BPHS map (incl. Chitra fallback).
    assert d["shashtihayani"].lord_for_nak(0) == Graha.JUPITER
    assert d["shashtihayani"].lord_for_nak(3) == Graha.SUN
    assert d["shashtihayani"].lord_for_nak(7) == Graha.MARS
    assert d["shashtihayani"].lord_for_nak(23) == Graha.RAHU


def test_helpers():
    # Hora: odd signs (1st, 3rd, …) run Sun then Moon; even signs
    # run Moon then Sun.
    assert hora_lord(65.0) == "Sun"    # 5° Gemini (3rd sign), 1st half
    assert hora_lord(80.0) == "Moon"   # 20° Gemini, 2nd half
    assert hora_lord(10.0) == "Sun"    # early Aries (odd) → Sun hora
    assert hora_lord(20.0) == "Moon"   # late Aries → Moon hora
    assert paksha(280.0, 10.0) == "Shukla"   # waxing
    assert paksha(10.0, 200.0) == "Krishna"  # waning
    assert navamsa_sign(0.0) == 0
    assert navamsa_sign(3.34) == 1  # 3.34° → 2nd navamsa Taurus
    assert dwadasamsa_sign(0.0) == 0
    assert dwadasamsa_sign(2.6) == 1  # 2.6° → 2nd dwadasamsa Taurus


def test_1990_gates():
    cd = _chart()
    names = [d["name"] for d in list_applicable(cd)]
    # Lagna lord Mercury in 7th (Sg) → Dwisaptati; Moon hora +
    # Krishna paksha → Shodasottari. Nothing else fires here.
    assert names == ["dwisaptati", "shodasottari"]


def test_gate_logic_units():
    from jhora.dasas.conditional import _GatedDasa
    base = dict(moon_nak=10, lagna=2,
                signs={Graha.MERCURY: 8, Graha.SUN: 9},
                nav_lagna=0, d12_lagna=9, paksha="Krishna",
                hora="Moon", day=True)
    by_gate = {d.gate: d for d in ALL_CONDITIONAL.values()}
    assert by_gate["dwisaptati"].is_applicable(base)
    assert by_gate["shodasottari"].is_applicable(base)
    assert not by_gate["dwadasottari"].is_applicable(base)
    assert not by_gate["panchottari"].is_applicable(base)
    assert not by_gate["shashtihayani"].is_applicable(base)
    assert not by_gate["sataabdika"].is_applicable(base)
    assert not by_gate["chaturaaseeti"].is_applicable(base)
    assert not by_gate["shattrimsa"].is_applicable(base)
    # Flip one condition at a time.
    assert by_gate["dwadasottari"].is_applicable(
        {**base, "nav_lagna": 1})
    assert by_gate["panchottari"].is_applicable(
        {**base, "lagna": 3, "d12_lagna": 3})
    assert by_gate["shashtihayani"].is_applicable(
        {**base, "signs": {Graha.SUN: 2}})
    assert by_gate["sataabdika"].is_applicable(
        {**base, "nav_lagna": 2})
    assert by_gate["chaturaaseeti"].is_applicable(
        {**base, "lagna": 9, "signs": {Graha.VENUS: 6}})
    assert not by_gate["shattrimsa"].is_applicable(base)
    # Moon hora + day is correctly out; Moon hora + night is in.
    assert by_gate["shattrimsa"].is_applicable({**base, "day": False})


def test_compute_structure_and_balance():
    cd = _chart()
    chart = {"planets": {g: {"longitude": p.longitude}
                         for g, p in cd.planets.items()}}
    for key, dasa in ALL_CONDITIONAL.items():
        mds = dasa.compute(cd.julian_day, chart, DasaOptions(
            subdivision_level=PeriodLevel.MAHADASA,
            include_subperiods=False))
        assert len(mds) == len(dasa.order), key
        assert round(sum(m.duration_years for m in mds), 6) == \
            dasa.total_years, key
        assert all(abs(a.end_jd - b.start_jd) < 1e-6
                   for a, b in zip(mds, mds[1:])), key
        assert mds[0].start_jd <= cd.julian_day <= mds[-1].end_jd, key


def test_compute_respects_year_definition():
    cd = _chart()
    chart = {"planets": {g: {"longitude": p.longitude}
                         for g, p in cd.planets.items()}}
    dasa = ALL_CONDITIONAL["sataabdika"]
    solar = dasa.compute(cd.julian_day, chart, DasaOptions(
        year_definition="solar", subdivision_level=PeriodLevel.MAHADASA,
        include_subperiods=False))
    savana = dasa.compute(cd.julian_day, chart, DasaOptions(
        year_definition="savana", subdivision_level=PeriodLevel.MAHADASA,
        include_subperiods=False))
    assert solar[1].duration_years == pytest.approx(
        savana[1].duration_years)
    assert solar[1].end_jd - solar[1].start_jd != pytest.approx(
        savana[1].end_jd - savana[1].start_jd)


def test_cli_lists_with_gates():
    from typer.testing import CliRunner
    from jhora.cli.main import app
    out = CliRunner().invoke(app, ["conditional-dasas"])
    assert out.exit_code == 0
    for key in ALL_CONDITIONAL:
        assert key in out.stdout
    out2 = CliRunner().invoke(
        app, ["conditional-dasas",
              "1990-01-15 17:30:00 +0530 12.9716 77.5946"])
    assert out2.exit_code == 0
    assert "dwisaptati" in out2.stdout
