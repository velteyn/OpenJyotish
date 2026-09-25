"""Tests for birth omens — Ganda Moola set + Vishti karana."""

from jhora.calc.omens import birth_omens, ganda_moola, karana_at
from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha


class TestGandaMoola:
    def test_six(self):
        assert ganda_moola(0) == "Asvini"
        assert ganda_moola(8) == "Ashlesha"
        assert ganda_moola(9) == "Magha"
        assert ganda_moola(17) == "Jyeshtha"
        assert ganda_moola(18) == "Mula"
        assert ganda_moola(26) == "Revati"

    def test_others_clean(self):
        assert ganda_moola(3) is None
        assert ganda_moola(13) is None

    def test_gandhi_moon(self):
        # Moon Cancer ~27° = Ashlesha → ganda-moola birth.
        cd = ChartBuilder().build(1869, 10, 2, 7 + 12 / 60,
                                  lat=21.37, lon=69.49, tz="+0438",
                                  ayanamsa="lahiri")
        om = birth_omens(cd.planet(Graha.MOON).longitude,
                         cd.ascendant,
                         cd.planet(Graha.SUN).longitude)
        assert om["moon_ganda_moola"] == "Ashlesha"


class TestVishti:
    def test_vishti_band(self):
        # Elongation 42-48° → k=7 → Vishti.
        assert karana_at(0.0, 45.0) == "Vishti"

    def test_not_vishti(self):
        assert karana_at(0.0, 100.0) != "Vishti"
