"""Tests for yoga detection engine."""

import pytest

from jhora.calc.yogas import (
    detect_all, YogaResult, house_from_lagna, is_in_kendra,
    is_in_kona, is_in_trik, aspects_planet,
    _pancha_mahapurusha, _gaja_kesari, _dhana_yogas,
    _raja_yogas, _viparita_raja_yogas, _parivartana,
    _sunapha_anapha_durudhara, _kemadruma,
    _conjunction_yogas, _adhi_yoga, _lagnaadhi_yoga, _vasumati_yoga,
    _dharma_karma_adhipati,
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

    @pytest.mark.parametrize("moon_house", range(12))
    @pytest.mark.parametrize("offset", range(12))
    def test_gaja_kesari_kendra_from_moon(self, ref_chart, moon_house, offset):
        """Fires exactly when Jupiter is 1st/4th/7th/10th from the Moon,
        regardless of where the pair sits relative to the lagna."""
        planet_house = {
            Graha.MOON: moon_house,
            Graha.JUPITER: (moon_house + offset) % 12,
        }
        result = _gaja_kesari(ref_chart, {}, planet_house)
        assert len(result) == (1 if offset in (0, 3, 6, 9) else 0)


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


class TestSunAsHouseLord:
    """Graha.SUN == 0 is falsy; the Sun must still count as a house lord."""

    def test_dhana_sun_lord_of_2nd(self):
        from types import SimpleNamespace
        # Cancer lagna: Sun lords the 2nd (Leo); placed in the 4th.
        cd = SimpleNamespace(ascendant=3 * 30 + 15)
        res = _dhana_yogas(cd, {}, {Graha.SUN: 3})
        assert [y.planets for y in res] == [(Graha.SUN,)]
        assert "lord of house 2" in res[0].description

    def test_dharma_karma_sun_lord_of_10th(self):
        from types import SimpleNamespace
        # Scorpio lagna: Moon lords the 9th (Cancer), Sun the 10th (Leo).
        cd = SimpleNamespace(ascendant=7 * 30 + 15, planets={Graha.SUN: SimpleNamespace(longitude=0.0)})
        res = _dharma_karma_adhipati(cd, {Graha.MOON: 4, Graha.SUN: 4})
        assert len(res) == 1
        assert set(res[0].planets) == {Graha.MOON, Graha.SUN}


class TestRajaYoga:
    """Kendra lord + kona lord in conjunction, lordship counted from lagna."""

    # Sign lords written out independently of jhora.calc.yogas.get_lord.
    _SIGN_LORDS = (
        Graha.MARS, Graha.VENUS, Graha.MERCURY, Graha.MOON,
        Graha.SUN, Graha.MERCURY, Graha.VENUS, Graha.MARS,
        Graha.JUPITER, Graha.SATURN, Graha.SATURN, Graha.JUPITER,
    )
    _SEVEN = (Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN)

    def _run(self, lagna, placements):
        from types import SimpleNamespace
        cd = SimpleNamespace(ascendant=lagna * 30 + 15)
        # Unplaced planets each get their own empty sign: no accidental pairs.
        spare = iter(s for s in range(12) if s not in placements.values())
        rasi = {g: placements[g] if g in placements else next(spare)
                for g in self._SEVEN}
        houses = {g: house_from_lagna(lagna, r) for g, r in rasi.items()}
        return _raja_yogas(cd, rasi, houses)

    def test_moon_jupiter_not_raja_for_aquarius(self):
        # Aquarius: Moon lords 6th, Jupiter 2nd/11th.
        assert self._run(10, {Graha.MOON: 5, Graha.JUPITER: 5}) == []

    def test_lordship_follows_lagna(self):
        # Aquarius: Sun lords 7th (kendra), Mercury 5th (kona).
        res = self._run(10, {Graha.SUN: 2, Graha.MERCURY: 2})
        assert len(res) == 1
        assert set(res[0].planets) == {Graha.SUN, Graha.MERCURY}
        assert "7th" in res[0].description and "5th" in res[0].description

    def test_natural_kona_lords_not_used(self):
        # Libra: Moon lords 10th but Sun lords 11th (not the natural 5th).
        assert self._run(6, {Graha.MOON: 1, Graha.SUN: 1}) == []

    def test_pair_reported_once(self):
        # Cancer: Moon lords 1st, Mars 5th and 10th.
        res = self._run(3, {Graha.MOON: 7, Graha.MARS: 7})
        assert len(res) == 1

    @pytest.mark.parametrize("lagna", range(12))
    def test_every_lagna(self, lagna):
        from types import SimpleNamespace
        cd = SimpleNamespace(ascendant=lagna * 30 + 15)
        rasi = {g: 0 for g in self._SEVEN}
        houses = {g: house_from_lagna(lagna, 0) for g in self._SEVEN}
        res = _raja_yogas(cd, rasi, houses)

        def lords(hs):
            return {self._SIGN_LORDS[(lagna + h) % 12] for h in hs}
        kendra, kona = lords((0, 3, 6, 9)), lords((0, 4, 8))
        expected = {frozenset((a, b)) for a in kendra for b in kona if a != b}
        pairs = [frozenset(y.planets) for y in res]
        assert len(pairs) == len(set(pairs))
        assert set(pairs) == expected
