"""Tests for Avakahada — pada boundaries + gold syllables."""

from jhora.calc.avakahada import avakahada, nama_syllable
from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha


class TestSyllables:
    def test_pada_boundaries(self):
        assert nama_syllable(0, 1) == "Chu"   # Asvini 1
        assert nama_syllable(0, 4) == "La"    # Asvini 4
        assert nama_syllable(1, 1) == "Li"    # Bharani 1
        assert nama_syllable(26, 4) == "Chi"  # Revati 4
        assert nama_syllable(19, 3) == "Pha"  # Purva Ashadha 3
        assert nama_syllable(25, 4) == "Na"   # Uttara Bhadrapada 4

    def test_full_rows(self):
        from jhora.calc.avakahada import _SYLLABLES
        assert len(_SYLLABLES) == 27
        assert all(len(v) == 4 for v in _SYLLABLES.values())


class TestAvakahada:
    def test_jalkot_moon(self):
        # Moon Aquarius 19° = Shatabhisha pada 4 → Su.
        cd = ChartBuilder().build(2001, 2, 24, 6 + 11 / 60,
                                  lat=18 + 38 / 60, lon=77 + 12 / 60,
                                  tz="+0530", ayanamsa="lahiri")
        av = avakahada(cd.planet(Graha.MOON).longitude)
        assert av["nakshatra"] == "Shatabhisha"
        assert av["pada"] == "4"
        assert av["nama_syllable"] == "Su"
        assert av["gana"] == "Rakshasa"
        assert av["nadi"] == "Adya"

    def test_pada_start(self):
        av = avakahada(0.0)
        assert (av["nakshatra"], av["pada"],
                av["nama_syllable"]) == ("Asvini", "1", "Chu")
