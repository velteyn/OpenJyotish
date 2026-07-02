"""Tests for type enums: Graha, Rasi, Nakshatra, Varga, Bhava."""

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra
from jhora.types.bhava import Bhava
from jhora.types.varga import VargaLevel, VargaVariant
from jhora.types.dasa import DasaSystem, PeriodLevel, DasaPeriod


class TestGraha:
    def test_count(self):
        assert len(Graha) == 9

    def test_names(self):
        assert Graha.SUN.full_name == "Sun"
        assert Graha.MOON.full_name == "Moon"
        assert Graha.RAHU.full_name == "Rahu"

    def test_short_names(self):
        assert Graha.SUN.short_name == "Su"
        assert Graha.MOON.short_name == "Mo"
        assert Graha.SATURN.short_name == "Sa"

    def test_benefic_malefic(self):
        assert all(g.is_benefic for g in [Graha.JUPITER, Graha.VENUS, Graha.MERCURY])
        assert all(g.is_malefic for g in [Graha.SUN, Graha.MARS, Graha.SATURN, Graha.RAHU, Graha.KETU])
        assert not Graha.MOON.is_benefic and not Graha.MOON.is_malefic

    def test_planet_node(self):
        assert all(g.is_planet for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                                          Graha.JUPITER, Graha.VENUS, Graha.SATURN])
        assert all(g.is_node for g in [Graha.RAHU, Graha.KETU])

    def test_vimsottari_years(self):
        assert Graha.SUN.vimsottari_years == 6
        assert Graha.MOON.vimsottari_years == 10
        assert Graha.KETU.vimsottari_years == 7
        assert Graha.VENUS.vimsottari_years == 20
        assert sum(g.vimsottari_years for g in Graha) == 120

    def test_lordship(self):
        assert Graha.MARS.lordship_signs == [1, 8]
        assert Graha.VENUS.lordship_signs == [2, 7]
        assert Graha.MERCURY.lordship_signs == [3, 6]
        assert Graha.JUPITER.lordship_signs == [9, 12]
        assert Graha.SATURN.lordship_signs == [10, 11]


class TestRasi:
    def test_count(self):
        assert len(Rasi) == 12

    def test_from_longitude(self):
        assert Rasi.from_longitude(0) == Rasi.ARIES
        assert Rasi.from_longitude(29) == Rasi.ARIES
        assert Rasi.from_longitude(30) == Rasi.TAURUS
        assert Rasi.from_longitude(350) == Rasi.PISCES
        assert Rasi.from_longitude(360) == Rasi.ARIES

    def test_movable_fixed_dual(self):
        assert all(r.is_movable for r in [Rasi.ARIES, Rasi.CANCER, Rasi.LIBRA, Rasi.CAPRICORN])
        assert all(r.is_fixed for r in [Rasi.TAURUS, Rasi.LEO, Rasi.SCORPIO, Rasi.AQUARIUS])
        assert all(r.is_dual for r in [Rasi.GEMINI, Rasi.VIRGO, Rasi.SAGITTARIUS, Rasi.PISCES])

    def test_even_odd(self):
        assert Rasi.ARIES.is_odd
        assert Rasi.TAURUS.is_even

    def test_lords(self):
        assert Rasi.ARIES.lord == "Mars"
        assert Rasi.TAURUS.lord == "Venus"
        assert Rasi.CANCER.lord == "Moon"
        assert Rasi.LEO.lord == "Sun"
        assert Rasi.SAGITTARIUS.lord == "Jupiter"
        assert Rasi.AQUARIUS.lord == "Saturn"

    def test_elements(self):
        assert Rasi.ARIES.element == "fire"
        assert Rasi.TAURUS.element == "earth"
        assert Rasi.GEMINI.element == "air"
        assert Rasi.CANCER.element == "water"

    def test_short_names(self):
        assert Rasi.ARIES.short_name == "Ar"
        assert Rasi.PISCES.short_name == "Pi"

    def test_to_angle(self):
        assert Rasi.ARIES.to_angle() == 0.0
        assert Rasi.TAURUS.to_angle() == 30.0
        assert Rasi.PISCES.to_angle() == 330.0


class TestNakshatra:
    def test_count(self):
        assert len(Nakshatra) == 27

    def test_from_longitude_aries(self):
        """Sun at 14.54° Aries → Bharani, Pada 1."""
        n, pada = Nakshatra.from_longitude(14.54)
        assert n == Nakshatra.BHARANI
        assert pada == 1

    def test_from_longitude_pisces(self):
        """Moon at 355.34° Pisces → Revati, Pada 3."""
        n, pada = Nakshatra.from_longitude(355.34)
        assert n == Nakshatra.REVATI
        assert pada == 3

    def test_from_longitude_scorpio(self):
        """Venus at 213.18° Scorpio → Vishakha, Pada 4."""
        n, pada = Nakshatra.from_longitude(213.18)
        assert n == Nakshatra.VISHAKHA
        assert pada == 4

    def test_from_longitude_sagittarius(self):
        """Lagna at 264.70° Sagittarius → Purva Shadha, Pada 4."""
        n, pada = Nakshatra.from_longitude(264.70)
        assert n == Nakshatra.PURVA_SHADHA
        assert pada == 4

    def test_lords(self):
        assert Nakshatra.ASVINI.lord == "Ketu"
        assert Nakshatra.BHARANI.lord == "Venus"
        assert Nakshatra.REVATI.lord == "Mercury"

    def test_span(self):
        assert abs(Nakshatra.ASVINI.span - 13.33333) < 0.001

    def test_vimsottari_sequence(self):
        assert Nakshatra.ASVINI.vimsottari_sequence == 0
        assert Nakshatra.MAGHA.vimsottari_sequence == 0  # same lord sequence as Ashwini
        assert Nakshatra.MULA.vimsottari_sequence == 0
        assert Nakshatra.BHARANI.vimsottari_sequence == 1
        assert Nakshatra.KRITTIKA.vimsottari_sequence == 2

    def test_start_longitude(self):
        assert Nakshatra.ASVINI.start_longitude == 0.0
        assert Nakshatra.BHARANI.start_longitude > 13.0


class TestBhava:
    def test_count(self):
        assert len(Bhava) == 12

    def test_kendra(self):
        assert all(b.is_kendra for b in [Bhava.BHAVA_1, Bhava.BHAVA_4, Bhava.BHAVA_7, Bhava.BHAVA_10])
        assert not Bhava.BHAVA_2.is_kendra

    def test_trikona(self):
        assert all(b.is_trikona for b in [Bhava.BHAVA_1, Bhava.BHAVA_5, Bhava.BHAVA_9])

    def test_duhsthana(self):
        assert all(b.is_duhsthana for b in [Bhava.BHAVA_6, Bhava.BHAVA_8, Bhava.BHAVA_12])

    def test_maraka(self):
        assert all(b.is_maraka for b in [Bhava.BHAVA_2, Bhava.BHAVA_7])

    def test_meaning(self):
        assert "wealth" in Bhava.BHAVA_2.meaning.lower()
        assert "spouse" in Bhava.BHAVA_7.meaning.lower()


class TestVargaLevel:
    def test_count(self):
        assert len(VargaLevel) == 24

    def test_divisions(self):
        assert VargaLevel.D_1.divisions == 1
        assert VargaLevel.D_9.divisions == 9
        assert VargaLevel.D_60.divisions == 60

    def test_short_name(self):
        assert VargaLevel.D_9.short_name == "D-9"
        assert VargaLevel.D_60.short_name == "D-60"

    def test_full_name(self):
        assert VargaLevel.D_9.full_name == "Navamsa"
        assert VargaLevel.D_60.full_name == "Shashtiamsa"

    def test_bhava_supported(self):
        assert VargaLevel.D_1.bhava_supported
        assert VargaLevel.D_9.bhava_supported
        assert not VargaLevel.D_150.bhava_supported


class TestVargaVariant:
    def test_members(self):
        assert VargaVariant.DEFAULT == 0
        assert VargaVariant.TRD > 0
        assert VargaVariant.K_N_RAO > 0

    def test_known_variants(self):
        assert VargaVariant.DEFAULT is not None
        assert VargaVariant.K is not None
        assert VargaVariant.KM is not None
        assert VargaVariant.UKM is not None


class TestDasaPeriod:
    def test_create(self):
        p = DasaPeriod(
            lord_index=0, lord_name="Sun",
            start_jd=2440000.0, end_jd=2442191.5,
            duration_years=6.0,
        )
        assert p.lord_index == 0
        assert p.lord_name == "Sun"
        assert p.duration_years == 6.0
        assert p.level.name == "MAHADASA"

    def test_sub_periods(self):
        p = DasaPeriod(
            lord_index=0, lord_name="Sun",
            start_jd=2440000.0, end_jd=2442191.5,
            duration_years=6.0,
            sub_periods=[
                DasaPeriod(0, "Ketu", 2440000.0, 2440420.0, 1.15),
            ],
        )
        assert len(p.sub_periods) == 1
        assert p.sub_periods[0].lord_name == "Ketu"
