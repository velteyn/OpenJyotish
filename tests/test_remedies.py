"""Rule-based remedy engine."""

from datetime import datetime
from types import SimpleNamespace

from jhora.charts.chart import ChartBuilder
from jhora.calc.remedies import compute_remedies
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


def _chart():
    return ChartBuilder().build(1990, 1, 15, 17.5, 12.9716, 77.5946,
                                tz="+0530")


def _fake(lagna_sign, mars_sign, extra=None):
    """Minimal ChartData stand-in for the dosha helpers."""
    planets = {g: SimpleNamespace(longitude=(3 + i) * 30 + 5,
                                  rasi=Rasi(3 + i))
               for i, g in enumerate(Graha)}
    planets[Graha.MARS] = SimpleNamespace(longitude=mars_sign * 30 + 5,
                                          rasi=Rasi(mars_sign))
    for g, sign in (extra or {}).items():
        planets[g] = SimpleNamespace(longitude=sign * 30 + 5, rasi=Rasi(sign))
    return SimpleNamespace(ascendant=lagna_sign * 30 + 5, planets=planets)


class TestRemedies:
    def test_ishta_devata_from_karakamsa(self):
        rep = compute_remedies(_chart())
        assert rep.ishta_devata.category == "deity"
        assert rep.ishta_devata.title
        assert "Karakamsa" in rep.ishta_devata.detail
        assert rep.palana_devata.title

    def test_every_item_is_sourced(self):
        rep = compute_remedies(_chart(), when=datetime(2026, 9, 22))
        assert rep.ishta_devata.source and rep.palana_devata.source
        assert rep.items
        assert all(it.source for it in rep.items)

    def test_gemstone_is_a_functional_benefic(self):
        # Gemini lagna: lagna lord Mercury is a functional benefic -> emerald.
        rep = compute_remedies(_chart())
        gems = [it for it in rep.items if it.category == "gemstone"]
        assert gems and "Emerald" in gems[0].title
        assert gems[0].planet == Graha.MERCURY

    def test_avoid_list_excludes_functional_benefics(self):
        rep = compute_remedies(_chart())
        avoid = next(it for it in rep.items if it.category == "avoid")
        # Gemini benefics (Venus, Mercury, Saturn) must not appear in avoid.
        assert "Emerald" not in avoid.detail
        assert "Blue Sapphire" not in avoid.detail
        assert "Diamond" not in avoid.detail

    def test_mantra_targets_lowest_shadbala(self):
        from jhora.calc.shadbala import ShadbalaComputer
        cd = _chart()
        bal = {g: r.total_rupa for g, r in ShadbalaComputer(cd).compute().items()}
        rep = compute_remedies(cd)
        mantra = next(it for it in rep.items if it.category == "mantra")
        assert mantra.planet in bal
        assert bal[mantra.planet] <= min(bal.values()) * 1.10

    def test_charity_for_target(self):
        rep = compute_remedies(_chart())
        charity = next(it for it in rep.items if it.category == "charity")
        assert "fast" in charity.detail.lower()


class TestDoshas:
    def test_kuja_dosha_detected(self):
        from jhora.calc.remedies import _kuja
        # Mars in the 1st from lagna (Aries lagna, Mars in Aries).
        assert _kuja(_fake(0, 0)) is not None
        # Mars in the 3rd (Aries lagna, Mars in Gemini) -> no Kuja.
        assert _kuja(_fake(0, 2)) is None

    def test_kaala_sarpa_detected(self):
        from jhora.calc.remedies import _kaala_sarpa
        # Rahu Aries, Ketu Libra, all seven between them.
        planets = {g: SimpleNamespace(longitude=(3 + i) * 30 + 5,
                                      rasi=Rasi(3 + i))
                   for i, g in enumerate(Graha)}
        planets[Graha.RAHU] = SimpleNamespace(longitude=3 * 30 + 5, rasi=Rasi(3))
        planets[Graha.KETU] = SimpleNamespace(longitude=9 * 30 + 5, rasi=Rasi(9))
        cd = SimpleNamespace(ascendant=5.0, planets=planets)
        assert _kaala_sarpa(cd) is not None

    def test_grahana_dosha(self):
        from jhora.calc.remedies import _grahana
        cd = _fake(0, 2, {Graha.SUN: 5, Graha.RAHU: 5})
        assert _grahana(cd) is not None

    def test_guru_chandala(self):
        from jhora.calc.remedies import _guru_chandala
        assert _guru_chandala(_fake(0, 2, {Graha.JUPITER: 6,
                                           Graha.RAHU: 6})) is not None
        assert _guru_chandala(_fake(0, 2, {Graha.JUPITER: 6,
                                           Graha.RAHU: 7})) is None

    def test_shrapit(self):
        from jhora.calc.remedies import _shrapit
        assert _shrapit(_fake(0, 2, {Graha.SATURN: 6,
                                     Graha.RAHU: 6})) is not None

    def test_kemadruma(self):
        from jhora.calc.remedies import _kemadruma
        planets = {g: SimpleNamespace(longitude=6 * 30 + 5, rasi=Rasi(6))
                   for g in Graha}
        planets[Graha.MOON] = SimpleNamespace(longitude=5, rasi=Rasi(0))
        cd = SimpleNamespace(ascendant=5.0, planets=planets)
        assert _kemadruma(cd) is not None

    def test_daridra(self):
        from jhora.calc.remedies import _daridra
        # Aries lagna: 11th (Aquarius) lord Saturn in the 6th (Virgo).
        assert _daridra(_fake(0, 2, {Graha.SATURN: 5})) is not None


class TestExtensions:
    def test_yantra_and_timing_present(self):
        rep = compute_remedies(_chart())
        cats = {it.category for it in rep.items}
        assert "yantra" in cats and "timing" in cats

    def test_dasha_lord_remedy_when_dated(self):
        rep = compute_remedies(_chart(), when=datetime(2026, 9, 22))
        dasha = [it for it in rep.items if it.category == "dasha"]
        assert dasha and "mahadasa lord" in dasha[0].title

    def test_no_dasha_remedy_without_date(self):
        rep = compute_remedies(_chart())
        assert not any(it.category == "dasha" for it in rep.items)
