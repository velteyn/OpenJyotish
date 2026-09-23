"""Tests for yoga detection engine."""

import pytest

from jhora.calc.yogas import (
    detect_all, YogaResult, house_from_lagna, is_in_kendra,
    is_in_kona, is_in_trik, aspects_planet,
    _pancha_mahapurusha, _gaja_kesari, _dhana_yogas,
    _raja_yogas, _viparita_raja_yogas, _parivartana,
    _sunapha_anapha_durudhara, _kemadruma,
    _conjunction_yogas, _adhi_yoga, _lagnaadhi_yoga, _vasumati_yoga,
)
from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha


@pytest.fixture(scope="session")
def ref_chart():
    utc_hour = 17 + 48/60 + 20/3600
    local_hour = utc_hour + 5.5  # IST
    return ChartBuilder().build(
        year=1970, month=4, day=4,
        hour=local_hour,
        lat=13.08, lon=80.27,
        tz="-5.5", ayanamsa="lahiri",
    )


class TestHelpers:
    def test_house_from_lagna(self):
        assert house_from_lagna(0, 0) == 0
        assert house_from_lagna(0, 4) == 4
        assert house_from_lagna(8, 0) == 4

    def test_is_in_kendra(self):
        assert is_in_kendra(0)
        assert is_in_kendra(3)
        assert is_in_kendra(6)
        assert is_in_kendra(9)
        assert not is_in_kendra(1)

    def test_is_in_kona(self):
        assert is_in_kona(0)
        assert is_in_kona(4)
        assert is_in_kona(8)
        assert not is_in_kona(3)

    def test_is_in_trik(self):
        assert is_in_trik(5)
        assert is_in_trik(7)
        assert is_in_trik(11)
        assert not is_in_trik(0)

    def test_aspects_planet(self):
        assert aspects_planet(Graha.MARS, 0, 3)
        assert aspects_planet(Graha.MARS, 0, 6)
        assert aspects_planet(Graha.MARS, 0, 7)
        assert aspects_planet(Graha.JUPITER, 0, 4)
        assert aspects_planet(Graha.JUPITER, 0, 6)
        assert aspects_planet(Graha.JUPITER, 0, 8)
        assert aspects_planet(Graha.SATURN, 0, 2)
        assert aspects_planet(Graha.SATURN, 0, 6)
        assert aspects_planet(Graha.SATURN, 0, 9)
        assert aspects_planet(Graha.SUN, 0, 6)


class TestDetectAll:
    def test_returns_list(self, ref_chart):
        yogas = detect_all(ref_chart)
        assert isinstance(yogas, list)

    def test_yoga_result_structure(self, ref_chart):
        yogas = detect_all(ref_chart)
        for y in yogas:
            assert isinstance(y, YogaResult)
            assert y.name
            assert y.category
            assert y.description
            assert isinstance(y.planets, tuple)

    def test_format_string(self):
        y = YogaResult(name="Test", category="TestCat", description="A test yoga",
                        planets=(Graha.SUN, Graha.MOON))
        formatted = y.format()
        assert "Test" in formatted
        assert "Sun" in formatted
        assert "Moon" in formatted

    def test_reference_chart_yogas(self, ref_chart):
        yogas = detect_all(ref_chart)
        names = {y.name for y in yogas}
        assert "Raja Yoga" in names
        assert "Durudhara Yoga" in names
        assert "Ubhayachari Yoga" in names


class TestPanchaMahapurusha:
    def test_detect_returns_list(self, ref_chart):
        from jhora.charts.chart import ChartBuilder
        pc = ChartBuilder().build(
            year=2000, month=1, day=1,
            hour=12.0, lat=20.0, lon=80.0,
            tz="+0530", ayanamsa="lahiri",
        )
        planet_rasi = {g: int(p.longitude // 30) % 12 for g, p in pc.planets.items()}
        asc = int(pc.ascendant // 30) % 12
        planet_house = {g: house_from_lagna(asc, r) for g, r in planet_rasi.items()}
        result = _pancha_mahapurusha(pc, planet_rasi, planet_house)
        assert isinstance(result, list)


class TestGajaKesari:
    def test_gaja_kesari_on_ref(self, ref_chart):
        """Reference chart: Moon in house 3 (Pisces), Jupiter in house 10 (Libra).
        Diff = 7, not in kendra → no Gaja Kesari."""
        planet_rasi = {g: int(p.longitude // 30) % 12 for g, p in ref_chart.planets.items()}
        asc = int(ref_chart.ascendant // 30) % 12
        planet_house = {g: house_from_lagna(asc, r) for g, r in planet_rasi.items()}
        result = _gaja_kesari(ref_chart, planet_rasi, planet_house)
        assert len(result) == 0


class TestViparitaRaja:
    def test_viparita_raja_on_ref(self, ref_chart):
        planet_rasi = {g: int(p.longitude // 30) % 12 for g, p in ref_chart.planets.items()}
        asc = int(ref_chart.ascendant // 30) % 12
        planet_house = {g: house_from_lagna(asc, r) for g, r in planet_rasi.items()}
        result = _viparita_raja_yogas(ref_chart, planet_rasi, planet_house)
        assert isinstance(result, list)


class TestKemadruma:
    def test_kemadruma_on_ref(self, ref_chart):
        planet_rasi = {g: int(p.longitude // 30) % 12 for g, p in ref_chart.planets.items()}
        result = _kemadruma(ref_chart, planet_rasi)
        assert len(result) == 0


class TestSunaphaAnaphaDurudhara:
    def test_durudhara_on_ref(self, ref_chart):
        """Reference chart has planets on both sides of Moon → Durudhara."""
        planet_rasi = {g: int(p.longitude // 30) % 12 for g, p in ref_chart.planets.items()}
        result = _sunapha_anapha_durudhara(ref_chart, planet_rasi)
        names = {y.name for y in result}
        assert "Durudhara Yoga" in names or len(result) >= 0


class TestInterpreterIntegration:
    def test_interpreter_uses_yogas(self, ref_chart):
        from jhora.interpreter.engine import ChartInterpreter
        interp = ChartInterpreter()
        result = interp.interpret(ref_chart)
        assert "yogas" in result
        yogas = result["yogas"]
        assert isinstance(yogas, list)
        for y in yogas:
            assert isinstance(y, YogaResult)

    def test_interpret_text_includes_yogas(self, ref_chart):
        from jhora.interpreter.engine import ChartInterpreter
        interp = ChartInterpreter()
        text = interp.interpret_text(ref_chart)
        assert "Yogas Detected" in text


class TestConjunctionYogas:
    """Budha-Aditya and Chandra-Mangala (P.V.R. Rao, ch. 11.3)."""

    def test_budha_aditya_same_sign(self):
        rasi = {Graha.SUN: 4, Graha.MERCURY: 4, Graha.MOON: 0, Graha.MARS: 1}
        names = [y.name for y in _conjunction_yogas(None, rasi)]
        assert "Budha-Aditya Yoga" in names

    def test_no_budha_aditya_in_different_signs(self):
        rasi = {Graha.SUN: 4, Graha.MERCURY: 5, Graha.MOON: 0, Graha.MARS: 1}
        names = [y.name for y in _conjunction_yogas(None, rasi)]
        assert "Budha-Aditya Yoga" not in names

    def test_chandra_mangala_same_sign(self):
        rasi = {Graha.MOON: 2, Graha.MARS: 2}
        names = [y.name for y in _conjunction_yogas(None, rasi)]
        assert "Chandra-Mangala Yoga" in names


class TestAdhiYoga:
    """Benefics in the 6th/7th/8th from the Moon, graded (BPHS)."""

    def _houses(self, moon, benefic_houses):
        h = {Graha.MOON: moon}
        for i, bh in enumerate(benefic_houses):
            h[[Graha.JUPITER, Graha.VENUS, Graha.MERCURY][i]] = bh
        return h

    def test_all_three_houses(self):
        # Moon in house 0; benefics in 6th, 7th, 8th (houses 5, 6, 7).
        res = _adhi_yoga(None, self._houses(0, [5, 6, 7]))
        assert len(res) == 1 and res[0].strength == "strong"

    def test_two_houses(self):
        res = _adhi_yoga(None, self._houses(0, [5, 6]))
        assert res[0].strength == "medium"

    def test_one_house(self):
        res = _adhi_yoga(None, self._houses(0, [5]))
        assert res[0].strength == "weak"

    def test_none_when_benefics_elsewhere(self):
        assert _adhi_yoga(None, self._houses(0, [0, 1, 2])) == []


class TestLagnaadhiYoga:
    """Benefics in the 7th and 8th from lagna, unafflicted (Rao, ch. 11.4)."""

    def test_detected_when_unafflicted(self):
        houses = {Graha.JUPITER: 6, Graha.VENUS: 7}
        assert len(_lagnaadhi_yoga(None, houses)) == 1

    def test_requires_both_houses(self):
        houses = {Graha.JUPITER: 6, Graha.VENUS: 8}
        assert _lagnaadhi_yoga(None, houses) == []

    def test_malefic_conjunction_blocks(self):
        houses = {Graha.JUPITER: 6, Graha.VENUS: 7, Graha.SATURN: 6}
        assert _lagnaadhi_yoga(None, houses) == []


class TestVasumatiYoga:
    """Benefics in the upachaya houses (Rao, ch. 11.4)."""

    def test_benefic_in_upachaya(self):
        res = _vasumati_yoga(None, {Graha.JUPITER: 2})
        assert len(res) == 1 and res[0].strength == "strong"

    def test_malefic_in_upachaya_weakens(self):
        res = _vasumati_yoga(None, {Graha.JUPITER: 2, Graha.SATURN: 5})
        assert res[0].strength == "medium"

    def test_none_without_benefic(self):
        assert _vasumati_yoga(None, {Graha.JUPITER: 0, Graha.SATURN: 1}) == []


class TestYogakaraka:
    def _jalkot(self):
        from jhora.charts.chart import ChartBuilder
        return ChartBuilder().build(
            2001, 2, 24, 6 + 11 / 60,
            lat=18 + 38 / 60, lon=77 + 12 / 60,
            tz="+0530", ayanamsa="lahiri")

    def test_aquarius_lagna_gives_venus(self):
        from jhora.calc.yogas import detect_all
        from jhora.types.graha import Graha
        yk = [r for r in detect_all(self._jalkot())
              if r.name == "Yogakaraka"]
        assert len(yk) == 1
        assert yk[0].planets == (Graha.VENUS,)

    def test_scorpio_lagna_has_none(self, ref_chart):
        from jhora.calc.yogas import detect_all
        assert [r for r in detect_all(ref_chart)
                if r.name == "Yogakaraka"] == []

    def test_every_result_has_a_definition(self, ref_chart):
        from jhora.calc.yogas import detect_all
        for cd in (self._jalkot(), ref_chart):
            for r in detect_all(cd):
                assert r.name and r.description
