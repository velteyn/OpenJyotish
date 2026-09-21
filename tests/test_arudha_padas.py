"""Tests for arudha padas: classical names, first-class Upapada/Darapada
and per-varga computation (classical table in "Vedic Astrology: An
Integrated Approach", ch. 9)."""

from jhora.calc.arudha import (
    BHAVA_PADA_ALIASES,
    BHAVA_PADA_NAMES,
    all_bhava_arudhas,
    all_graha_arudhas,
    bhava_arudha,
    bhava_pada_name,
    darapada,
    graha_arudha,
    graha_pada_name,
    upapada,
    varga_arudhas,
)
from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha
from jhora.types.varga import VargaLevel


def _chart():
    cd = ChartBuilder().build(
        year=1990, month=1, day=15, hour=17.5,
        lat=12.9716, lon=77.5946, tz="+0530")
    planets = {g: {"longitude": p.longitude} for g, p in cd.planets.items()}
    return cd, planets


def test_all_twelve_padas_named():
    assert set(BHAVA_PADA_NAMES) == set(range(1, 13))
    names = list(BHAVA_PADA_NAMES.values())
    assert len(names) == len(set(names))
    assert BHAVA_PADA_NAMES[1] == "Arudha Lagna"
    assert BHAVA_PADA_NAMES[7] == "Dara pada"
    assert BHAVA_PADA_NAMES[12] == "Upapada"


def test_alias_table_matches_classical_list():
    assert set(BHAVA_PADA_ALIASES) == set(range(1, 13))
    for n, primary in BHAVA_PADA_NAMES.items():
        aliases = [a.lower() for a in BHAVA_PADA_ALIASES[n]]
        assert aliases, n
        # A12 carries the Upapada/Gaunapada/Moksha synonyms.
        if n == 12:
            assert "upapada" in aliases and "moksha pada" in aliases
        if n == 7:
            assert "dararudha" in aliases
    assert bhava_pada_name(2) == "Dhana pada"


def test_upapada_and_darapada_are_a12_a7():
    cd, planets = _chart()
    assert upapada(cd.ascendant, planets) == bhava_arudha(12, cd.ascendant,
                                                          planets)
    assert darapada(cd.ascendant, planets) == bhava_arudha(7, cd.ascendant,
                                                           planets)


def test_graha_pada_names():
    expected = {
        Graha.SUN: "Surya pada", Graha.MOON: "Chandra pada",
        Graha.MARS: "Mangala pada", Graha.MERCURY: "Budha pada",
        Graha.JUPITER: "Guru pada", Graha.VENUS: "Shukra pada",
        Graha.SATURN: "Shani pada", Graha.RAHU: "Rahu pada",
        Graha.KETU: "Ketu pada",
    }
    for g, name in expected.items():
        assert graha_pada_name(g) == name


def test_varga_arudhas_d1_matches_rasi():
    cd, planets = _chart()
    bhava, graha_arus = varga_arudhas(cd, VargaLevel.D_1)
    ref = all_bhava_arudhas(cd.ascendant, planets)
    assert {n: bhava[n] for n in range(1, 13)} == ref
    assert graha_arus == all_graha_arudhas(planets)


def test_varga_arudhas_navamsa_differs_and_is_complete():
    cd, _ = _chart()
    bhava_d1, _ = varga_arudhas(cd, VargaLevel.D_1)
    bhava_d9, graha_d9 = varga_arudhas(cd, VargaLevel.D_9)
    assert len(bhava_d9) == 12 and len(graha_d9) == 9
    # A different chart must move at least one pada.
    assert any(bhava_d9[n] != bhava_d1[n] for n in range(1, 13))


def test_graha_arudha_rule_is_stable_across_calls():
    _, planets = _chart()
    assert graha_arudha(Graha.SUN, planets) == graha_arudha(Graha.SUN, planets)


def test_json_export_arudha_names():
    from jhora.ai.json_export import full_analysis
    r = full_analysis("1990-01-15 17:30:00 +0530 12.9716 77.5946")
    a = r["arudhas"]
    assert a["upapada"] and a["darapada"]
    row7 = [x for x in a["bhava"] if x["house"] == 7][0]
    assert row7["name"] == "Dara pada"
    assert row7["pada"] == "A7 (Dara pada)"
    assert all("pada" in g for g in a["graha"])


def test_cli_arudhas_runs():
    from typer.testing import CliRunner
    from jhora.cli.main import app
    bd = "1990-01-15 17:30:00 +0530 12.9716 77.5946"
    out = CliRunner().invoke(app, ["arudhas", bd])
    assert out.exit_code == 0, out.output
    assert "Dara pada" in out.stdout and "Upapada" in out.stdout
    out9 = CliRunner().invoke(app, ["arudhas", bd, "--varga", "D-9"])
    assert out9.exit_code == 0
    assert "Navamsa" in out9.stdout
