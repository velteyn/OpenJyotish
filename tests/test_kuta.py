"""Tests for Kuta Porutham (marriage matchmaking)."""

import unittest
from jhora.calc.kuta import (
    compute_kuta, KutaResult, Porutham,
    _check_dina, _check_gana, _check_yoni, _check_rasi,
    _check_rasyadhipati, _check_nadi, _check_rajju,
    _check_vedha, _check_vashya, _check_mahendra,
)
from jhora.types.nakshatra import Nakshatra
from jhora.types.rasi import Rasi


class TestDinaPorutham(unittest.TestCase):
    """Dina: count girl→boy nakshatra, mod 9 ∈ {2,4,6,8,0}."""

    def test_count_1_not_good(self):
        """Same nakshatra → count=1 → not good."""
        r = _check_dina(Nakshatra.ASVINI, Nakshatra.ASVINI)
        self.assertEqual(r.score, 0.0)

    def test_count_2_good(self):
        """Count=2 → remainder 2 → good."""
        r = _check_dina(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(r.score, 1.0)

    def test_count_9_good(self):
        """Count=9 → remainder 0 → good."""
        r = _check_dina(Nakshatra.ASVINI, Nakshatra.ASHLESHA)
        self.assertEqual(r.score, 1.0)

    def test_count_5_not_good(self):
        """Count=5 → remainder 5 → not good."""
        r = _check_dina(Nakshatra.ASVINI, Nakshatra.MRIGASHIRA)
        self.assertEqual(r.score, 0.0)

    def test_wraparound(self):
        """Girl Ashlesha (8), Boy Ashwini (0): count = (0-8)%27+1 = 20, 20%9=2 → good."""
        r = _check_dina(Nakshatra.ASHLESHA, Nakshatra.ASVINI)
        self.assertEqual(r.score, 1.0)


class TestGanaPorutham(unittest.TestCase):
    """Gana: same gana → good."""

    def test_same_gana(self):
        """Sun, Mars, Jupiter — all 'Deva'."""
        r = _check_gana(Nakshatra.ASVINI, Nakshatra.PUNARVASU)
        self.assertEqual(r.score, 1.0)

    def test_diff_gana(self):
        """Ashwini (Deva) vs Bharani (Manushya)."""
        r = _check_gana(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(r.score, 0.0)

    def test_manushya_both(self):
        """Bharani + Rohini both Manushya."""
        r = _check_gana(Nakshatra.BHARANI, Nakshatra.ROHINI)
        self.assertEqual(r.score, 1.0)

    def test_rakshasa_both(self):
        """Krittika + Magha both Rakshasa."""
        r = _check_gana(Nakshatra.KRITTIKA, Nakshatra.MAGHA)
        self.assertEqual(r.score, 1.0)


class TestYoniPorutham(unittest.TestCase):
    """Yoni: animal + sex compatibility."""

    def test_same_animal_opposite_sex(self):
        """Ashwini (Horse M) + Shatabhisha (Horse F) → best."""
        r = _check_yoni(Nakshatra.ASVINI, Nakshatra.SHATABHISHA)
        self.assertEqual(r.score, 1.0)

    def test_same_animal_same_sex(self):
        """Ashwini (Horse M) + ... only one male Horse, so skip.
        Use Dog: Ardra (M) + Mula (F) → opposite sex → best.
        """
        r = _check_yoni(Nakshatra.ARDRA, Nakshatra.MULA)
        self.assertEqual(r.score, 1.0)  # Dog M + Dog F = opposite sex

    def test_friend_animals(self):
        """Horse ↔ Elephant are friends."""
        r = _check_yoni(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(r.score, 0.75)

    def test_enemy_animals(self):
        """Serpent ↔ Cat are friends, not enemies.
        Use Dog ↔ Cat (not listed as friends).
        """
        r = _check_yoni(Nakshatra.ARDRA, Nakshatra.PUNARVASU)
        self.assertEqual(r.score, 0.0)  # Dog ↔ Cat = enemy


class TestRasiPorutham(unittest.TestCase):
    """Rasi: count girl→boy signs, even is good."""

    def test_even_count(self):
        """Aries(0) → Gemini(2): count=3 → odd → not good.
        Aries(0) → Cancer(3): count=4 → even → good.
        """
        r = _check_rasi(Rasi.ARIES, Rasi.CANCER)
        self.assertEqual(r.score, 2.0)

    def test_odd_count(self):
        r = _check_rasi(Rasi.ARIES, Rasi.GEMINI)
        self.assertEqual(r.score, 0.0)

    def test_same_sign(self):
        """Same sign → count=1 → not good (odd)."""
        r = _check_rasi(Rasi.ARIES, Rasi.ARIES)
        self.assertEqual(r.score, 0.0)

    def test_twelfth(self):
        """Aries(0) → Pisces(11): count=12 → good."""
        r = _check_rasi(Rasi.ARIES, Rasi.PISCES)
        self.assertEqual(r.score, 2.0)


class TestRasyadhipatiPorutham(unittest.TestCase):
    """Rasyadhipati: sign lord friendship."""

    def test_same_lord(self):
        """Aries(Mars) & Scorpio(Mars) → same lord."""
        r = _check_rasyadhipati(Rasi.ARIES, Rasi.SCORPIO)
        self.assertEqual(r.score, 1.0)

    def test_friend_lords(self):
        """Leo(Sun) & Sagittarius(Jupiter) → Sun-Jupiter friends."""
        r = _check_rasyadhipati(Rasi.LEO, Rasi.SAGITTARIUS)
        self.assertEqual(r.score, 1.0)

    def test_enemy_lords(self):
        """Libra(Venus) & Leo(Sun) → Venus-Sun enemies."""
        r = _check_rasyadhipati(Rasi.LIBRA, Rasi.LEO)
        self.assertEqual(r.score, 0.0)


class TestNadiPorutham(unittest.TestCase):
    """Nadi: same nadi = bad."""

    def test_diff_nadi(self):
        """Ashwini (Adya) + Bharani (Madhya)."""
        r = _check_nadi(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(r.score, 8.0)

    def test_same_nadi(self):
        """Ashwini (Adya) + Ardra (Adya)."""
        r = _check_nadi(Nakshatra.ASVINI, Nakshatra.ARDRA)
        self.assertEqual(r.score, 0.0)

    def test_antya_both(self):
        r = _check_nadi(Nakshatra.KRITTIKA, Nakshatra.ROHINI)
        self.assertEqual(r.score, 0.0)


class TestRajjuPorutham(unittest.TestCase):
    """Rajju: same group = longevity issue."""

    def test_same_rajju(self):
        """Ashwini(0) + Magha(9) → both Moola Rajju (group 1)."""
        r = _check_rajju(Nakshatra.ASVINI, Nakshatra.MAGHA)
        self.assertEqual(r.score, 0.0)

    def test_diff_rajju(self):
        """Ashwini(Moola=1) + Bharani(Agni=2)."""
        r = _check_rajju(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(r.score, 1.0)

    def test_rajju_hina(self):
        """Ardra(0) + Punarvasu(0) → both rajju-hina."""
        r = _check_rajju(Nakshatra.ARDRA, Nakshatra.PUNARVASU)
        self.assertEqual(r.score, 1.0)


class TestVedhaPorutham(unittest.TestCase):
    """Vedha: opposite nakshatras cause obstruction."""

    def test_vedha_pair(self):
        """Ashwini ↔ Jyeshtha."""
        r = _check_vedha(Nakshatra.ASVINI, Nakshatra.JYESHTHA)
        self.assertEqual(r.score, 0.0)

    def test_no_vedha(self):
        r = _check_vedha(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(r.score, 1.0)

    def test_reverse_vedha(self):
        r = _check_vedha(Nakshatra.JYESHTHA, Nakshatra.ASVINI)
        self.assertEqual(r.score, 0.0)


class TestVashyaPorutham(unittest.TestCase):
    """Vashya: same nature group or avoid 6/8."""

    def test_same_group(self):
        """Aries + Cancer both chara."""
        r = _check_vashya(Rasi.ARIES, Rasi.CANCER)
        self.assertEqual(r.score, 2.0)

    def test_six_eight_opposition(self):
        """Aries(0) ↔ Virgo(5): diff=5 (6th)."""
        r = _check_vashya(Rasi.ARIES, Rasi.VIRGO)
        self.assertEqual(r.score, 0.0)

    def test_partial_mixed(self):
        """Aries(chara) + Taurus(sthira) → different group, no 6/8."""
        r = _check_vashya(Rasi.ARIES, Rasi.TAURUS)
        self.assertEqual(r.score, 0.5)


class TestMahendraPorutham(unittest.TestCase):
    """Mahendra: prosperity via nak count ∈ {4,7,9,13,22,26}."""

    def test_good_4(self):
        """Ashwini(0) → Kruttika(2): count=3, not good.
        Ashwini(0) → Mrigashira(4): count=5, not good.
        Ashwini(0) → Rohini(3): count=4 → good.
        """
        r = _check_mahendra(Nakshatra.ASVINI, Nakshatra.ROHINI)
        self.assertEqual(r.score, 1.0)

    def test_not_good(self):
        r = _check_mahendra(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(r.score, 0.0)

    def test_good_22(self):
        """Ashwini(0) → Shravana(21): count=22 → good."""
        r = _check_mahendra(Nakshatra.ASVINI, Nakshatra.SHRAVANA)
        self.assertEqual(r.score, 1.0)

    def test_good_27_full_cycle(self):
        """Full cycle: Ashwini(0) → Revati(26): count=27 → good."""
        r = _check_mahendra(Nakshatra.ASVINI, Nakshatra.REVATI)
        self.assertEqual(r.score, 1.0)

    def test_good_27_wraparound(self):
        """Bharani(1) → Ashwini(0): count=(0-1)%27+1 = 27 → good."""
        r = _check_mahendra(Nakshatra.BHARANI, Nakshatra.ASVINI)
        self.assertEqual(r.score, 1.0)


class TestComputeKuta(unittest.TestCase):
    """Integration test for full compute_kuta."""

    def test_returns_all_poruthams(self):
        """Verify 10 poruthams are always returned."""
        r = compute_kuta(10.0, 100.0)
        self.assertIsInstance(r, KutaResult)
        self.assertEqual(len(r.poruthams), 10)
        self.assertGreater(r.max_score, 0)

    def test_score_bounds(self):
        """Total score should be within bounds."""
        r = compute_kuta(10.0, 100.0)
        self.assertGreaterEqual(r.total_score, 0)
        self.assertLessEqual(r.total_score, r.max_score)

    def test_nakshatra_detection(self):
        """Verify nakshatra detection from longitude."""
        # 10° = Ashwini (0), 100° = 100/13.33 ≈ 7.5 → Pushya(7)
        r = compute_kuta(10.0, 100.0)
        self.assertEqual(r.girl_nakshatra, Nakshatra.ASVINI)
        self.assertEqual(r.boy_nakshatra, Nakshatra.PUSHYA)

    def test_rasi_detection(self):
        """10° → Aries(0), 100° → Cancer(3)."""
        r = compute_kuta(10.0, 100.0)
        self.assertEqual(r.girl_rasi, Rasi.ARIES)
        self.assertEqual(r.boy_rasi, Rasi.CANCER)

    def test_all_porutham_names(self):
        r = compute_kuta(10.0, 100.0)
        expected = ["Dina", "Gana", "Yoni", "Rasi", "Rasyadhipati",
                     "Nadi", "Rajju", "Vedha", "Vashya", "Mahendra"]
        names = [p.name for p in r.poruthams]
        self.assertEqual(names, expected)

    def test_percentage(self):
        r = compute_kuta(10.0, 100.0)
        self.assertAlmostEqual(r.percentage, r.total_score / r.max_score * 100)

    def test_fraction_on_porutham(self):
        p = _check_dina(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(p.fraction, "1/1")


if __name__ == "__main__":
    unittest.main()
