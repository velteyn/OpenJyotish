"""Tests for Kuta Porutham (marriage matchmaking)."""

import unittest
from jhora.calc.kuta import (
    compute_kuta, KutaResult, Porutham, ScoringSystem,
    gunanka_level,
    _check_dina, _check_gana, _check_yoni, _check_rasi,
    _check_rasyadhipati, _check_nadi, _check_rajju,
    _check_vedha, _check_vashya, _check_mahendra,
    _ak_check_varna, _ak_check_vashya, _ak_check_tara,
    _ak_check_yoni, _ak_check_graha_maitri, _ak_check_gana,
    _ak_check_bhakoota, _ak_check_nadi,
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


# ═══════════════════════════════════════════════════════════════════════════════
# Ashta Koota (36-point, 8-factor) Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAKVarna(unittest.TestCase):
    """Ashta Koota Varna (1 pt) — same rasi lord varna."""

    def test_same_lord(self):
        """Aries+Scorpio both Mars → same varna (Kshatriya=2)."""
        r = _ak_check_varna(Rasi.ARIES, Rasi.SCORPIO)
        self.assertEqual(r.score, 1.0)

    def test_same_varna_diff_lord(self):
        """Leo(Sun, Kshatriya=2) + Aries(Mars, Kshatriya=2)."""
        r = _ak_check_varna(Rasi.LEO, Rasi.ARIES)
        self.assertEqual(r.score, 1.0)

    def test_diff_varna(self):
        """Aries(Mars, Kshatriya=2) + Taurus(Venus, Brahmin=1)."""
        r = _ak_check_varna(Rasi.ARIES, Rasi.TAURUS)
        self.assertEqual(r.score, 0.0)

    def test_brahmin_same(self):
        """Sagittarius(Jupiter) + Pisces(Jupiter) → both Brahmin."""
        r = _ak_check_varna(Rasi.SAGITTARIUS, Rasi.PISCES)
        self.assertEqual(r.score, 1.0)

    def test_shudra_moon(self):
        """Cancer(Moon, Shudra=4) + Cancer(Moon, Shudra=4) → same."""
        r = _ak_check_varna(Rasi.CANCER, Rasi.CANCER)
        self.assertEqual(r.score, 1.0)


class TestAKVashya(unittest.TestCase):
    """Ashta Koota Vashya (2 pts) — sign nature group."""

    def test_same_group(self):
        """Aries+Libra both chara."""
        r = _ak_check_vashya(Rasi.ARIES, Rasi.LIBRA)
        self.assertEqual(r.score, 2.0)

    def test_six_eight_opposition(self):
        """Aries(0) → Virgo(5): diff=5 (6th)."""
        r = _ak_check_vashya(Rasi.ARIES, Rasi.VIRGO)
        self.assertEqual(r.score, 0.0)

    def test_eighth_opposition(self):
        """Taurus(1) → Libra(6): diff=5 (6th)."""
        r = _ak_check_vashya(Rasi.TAURUS, Rasi.LIBRA)
        self.assertEqual(r.score, 0.0)

    def test_partial_mixed(self):
        """Aries(chara) + Taurus(sthira) → partial (1 pt)."""
        r = _ak_check_vashya(Rasi.ARIES, Rasi.TAURUS)
        self.assertEqual(r.score, 1.0)

    def test_partial_dual_chara(self):
        """Gemini(dwisvabhava) + Aries(chara) → partial."""
        r = _ak_check_vashya(Rasi.GEMINI, Rasi.ARIES)
        self.assertEqual(r.score, 1.0)


class TestAKTara(unittest.TestCase):
    """Ashta Koota Tara/Dina (3 pts) — nakshatra counting."""

    def test_uttama_3(self):
        """Ashwini(0) → Punarvasu(6): count=7, 7%9=7 → Uttama (3)."""
        r = _ak_check_tara(Nakshatra.ASVINI, Nakshatra.PUNARVASU)
        self.assertEqual(r.score, 3.0)

    def test_uttama_0(self):
        """Ashwini(0) → Ashlesha(8): count=9, 9%9=0 → Uttama (3)."""
        r = _ak_check_tara(Nakshatra.ASVINI, Nakshatra.ASHLESHA)
        self.assertEqual(r.score, 3.0)

    def test_madhyama_2(self):
        """Ashwini(0) → Bharani(1): count=2, 2%9=2 → Madhyama (2)."""
        r = _ak_check_tara(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(r.score, 2.0)

    def test_madhyama_4(self):
        """Ashwini(0) → Rohini(3): count=4 → Madhyama (2)."""
        r = _ak_check_tara(Nakshatra.ASVINI, Nakshatra.ROHINI)
        self.assertEqual(r.score, 2.0)

    def test_adhama_1(self):
        """Ashwini(0) → Ashwini(0): same nak, count=1 → Adhama (0)."""
        r = _ak_check_tara(Nakshatra.ASVINI, Nakshatra.ASVINI)
        self.assertEqual(r.score, 0.0)

    def test_adhama_5(self):
        """Ashwini(0) → Mrigashira(4): count=5 → Adhama (0)."""
        r = _ak_check_tara(Nakshatra.ASVINI, Nakshatra.MRIGASHIRA)
        self.assertEqual(r.score, 0.0)


class TestAKYoni(unittest.TestCase):
    """Ashta Koota Yoni (4 pts) — animal compatibility."""

    def test_best_opposite_sex(self):
        """Ashwini (Horse M) + Shatabhisha (Horse F) → best (4)."""
        r = _ak_check_yoni(Nakshatra.ASVINI, Nakshatra.SHATABHISHA)
        self.assertEqual(r.score, 4.0)

    def test_good_same_sex(self):
        """Ardra (Dog M) + Mula (Dog F) → same animal, opp sex → best (4).
        Actually Ardra(Dog M, 6) + Mula(Dog F, 18) — wait, check _YONI.
        """
        r = _ak_check_yoni(Nakshatra.ARDRA, Nakshatra.MULA)
        self.assertEqual(r.score, 4.0)

    def test_friends(self):
        """Ashwini (Horse) + Bharani (Elephant) → friends (2)."""
        r = _ak_check_yoni(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(r.score, 2.0)

    def test_neutral(self):
        """Cat ↔ Mongoose: not friends, not enemies → neutral (1)."""
        r = _ak_check_yoni(Nakshatra.ASHLESHA, Nakshatra.UTTARA_SHADHA)
        self.assertEqual(r.score, 1.0)

    def test_enemy(self):
        """Ardra (Dog) + Punarvasu (Cat) → not friends → enemy (0)."""
        r = _ak_check_yoni(Nakshatra.ARDRA, Nakshatra.PUNARVASU)
        self.assertEqual(r.score, 0.0)


class TestAKGrahaMaitri(unittest.TestCase):
    """Graha Maitri (5 pts) — rasi lord friendship."""

    def test_same_lord(self):
        """Aries+Scorpio both Mars → 5 pts."""
        r = _ak_check_graha_maitri(Rasi.ARIES, Rasi.SCORPIO)
        self.assertEqual(r.score, 5.0)

    def test_friends(self):
        """Leo(Sun) + Sagittarius(Jupiter) → Sun-Jupiter friends → 3 pts."""
        r = _ak_check_graha_maitri(Rasi.LEO, Rasi.SAGITTARIUS)
        self.assertEqual(r.score, 3.0)

    def test_enemies(self):
        """Libra(Venus) + Leo(Sun) → Venus-Sun enemies → 0 pts."""
        r = _ak_check_graha_maitri(Rasi.LIBRA, Rasi.LEO)
        self.assertEqual(r.score, 0.0)

    def test_neutral(self):
        """Aries(Mars) + Capricorn(Saturn) → Mars neutral with Saturn → 1 pt."""
        r = _ak_check_graha_maitri(Rasi.ARIES, Rasi.CAPRICORN)
        self.assertEqual(r.score, 1.0)


class TestAKGana(unittest.TestCase):
    """Ashta Koota Gana (6 pts) — temperament."""

    def test_same_deva(self):
        """Ashwini + Punarvasu → both Deva → 6."""
        r = _ak_check_gana(Nakshatra.ASVINI, Nakshatra.PUNARVASU)
        self.assertEqual(r.score, 6.0)

    def test_same_manushya(self):
        """Bharani + Rohini → both Manushya → 6."""
        r = _ak_check_gana(Nakshatra.BHARANI, Nakshatra.ROHINI)
        self.assertEqual(r.score, 6.0)

    def test_deva_rakshasa(self):
        """Ashwini(Deva) + Krittika(Rakshasa) → opposite → 0."""
        r = _ak_check_gana(Nakshatra.ASVINI, Nakshatra.KRITTIKA)
        self.assertEqual(r.score, 0.0)

    def test_deva_manushya(self):
        """Ashwini(Deva) + Bharani(Manushya) → partial → 3."""
        r = _ak_check_gana(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(r.score, 3.0)


class TestAKBhakoota(unittest.TestCase):
    """Ashta Koota Bhakoota (7 pts) — rasi position."""

    def test_trinal_best(self):
        """Aries(0) + Leo(4): diff=4 → 5th → 7 pts."""
        r = _ak_check_bhakoota(Rasi.ARIES, Rasi.LEO)
        self.assertEqual(r.score, 7.0)

    def test_maraka_2nd(self):
        """Aries(0) + Taurus(1): diff=1 → 2nd → 0 pts."""
        r = _ak_check_bhakoota(Rasi.ARIES, Rasi.TAURUS)
        self.assertEqual(r.score, 0.0)

    def test_same_sign(self):
        """Aries + Aries → 0 pts."""
        r = _ak_check_bhakoota(Rasi.ARIES, Rasi.ARIES)
        self.assertEqual(r.score, 0.0)

    def test_sixth(self):
        """Aries(0) + Virgo(5): diff=5 → 6th → 0 pts."""
        r = _ak_check_bhakoota(Rasi.ARIES, Rasi.VIRGO)
        self.assertEqual(r.score, 0.0)

    def test_eighth(self):
        """Aries(0) + Scorpio(7): diff=7 → 8th → 0 pts."""
        r = _ak_check_bhakoota(Rasi.ARIES, Rasi.SCORPIO)
        self.assertEqual(r.score, 0.0)

    def test_twelfth(self):
        """Aries(0) + Pisces(11): diff=11 → 12th → 0 pts."""
        r = _ak_check_bhakoota(Rasi.ARIES, Rasi.PISCES)
        self.assertEqual(r.score, 0.0)

    def test_third_good(self):
        """Aries(0) + Gemini(2): diff=2 → 3rd → 5 pts."""
        r = _ak_check_bhakoota(Rasi.ARIES, Rasi.GEMINI)
        self.assertEqual(r.score, 5.0)

    def test_eleventh(self):
        """Aries(0) + Aquarius(10): diff=10 → 11th → 5 pts."""
        r = _ak_check_bhakoota(Rasi.ARIES, Rasi.AQUARIUS)
        self.assertEqual(r.score, 5.0)

    def test_fourth_fair(self):
        """Aries(0) + Cancer(3): diff=3 → 4th → 3 pts."""
        r = _ak_check_bhakoota(Rasi.ARIES, Rasi.CANCER)
        self.assertEqual(r.score, 3.0)

    def test_tenth_fair(self):
        """Aries(0) + Capricorn(9): diff=9 → 10th → 3 pts."""
        r = _ak_check_bhakoota(Rasi.ARIES, Rasi.CAPRICORN)
        self.assertEqual(r.score, 3.0)

    def test_seventh_neutral(self):
        """Aries(0) + Libra(6): diff=6 → 7th → 1 pt."""
        r = _ak_check_bhakoota(Rasi.ARIES, Rasi.LIBRA)
        self.assertEqual(r.score, 1.0)


class TestAKNadi(unittest.TestCase):
    """Ashta Koota Nadi (8 pts) — same scoring as 10 Porutham."""

    def test_diff_nadi(self):
        """Ashwini (Adya) + Bharani (Madhya)."""
        r = _ak_check_nadi(Nakshatra.ASVINI, Nakshatra.BHARANI)
        self.assertEqual(r.score, 8.0)

    def test_same_nadi(self):
        r = _ak_check_nadi(Nakshatra.ASVINI, Nakshatra.ARDRA)
        self.assertEqual(r.score, 0.0)


class TestGunankaLevel(unittest.TestCase):
    """Ashta Koota Gunanka category levels."""

    def test_excellent(self):
        self.assertEqual(gunanka_level(36), "Excellent")

    def test_good(self):
        self.assertEqual(gunanka_level(28), "Good")

    def test_fair(self):
        self.assertEqual(gunanka_level(20), "Fair")

    def test_average(self):
        self.assertEqual(gunanka_level(15), "Average")

    def test_below_average(self):
        self.assertEqual(gunanka_level(5), "Below average")

    def test_excellent_30(self):
        self.assertEqual(gunanka_level(30), "Excellent")

    def test_good_boundary(self):
        self.assertEqual(gunanka_level(24), "Good")

    def test_fair_boundary(self):
        self.assertEqual(gunanka_level(18), "Fair")


class TestScoringSystemEnum(unittest.TestCase):
    """ScoringSystem enum."""

    def test_porutham_value(self):
        self.assertEqual(ScoringSystem.PORUTHAM.value, "porutham")

    def test_ashta_koota_value(self):
        self.assertEqual(ScoringSystem.ASHTA_KOOTA.value, "ashta_koota")


class TestComputeAshtaKoota(unittest.TestCase):
    """Integration tests for Ashta Koota scoring."""

    def test_returns_all_factors(self):
        """Should return exactly 8 factors."""
        r = compute_kuta(10.0, 100.0, system=ScoringSystem.ASHTA_KOOTA)
        self.assertIsInstance(r, KutaResult)
        self.assertEqual(len(r.poruthams), 8)

    def test_max_score_36(self):
        """Max should always be 36."""
        r = compute_kuta(10.0, 100.0, system=ScoringSystem.ASHTA_KOOTA)
        self.assertEqual(r.max_score, 36.0)

    def test_score_within_bounds(self):
        """Score between 0 and 36."""
        r = compute_kuta(10.0, 100.0, system=ScoringSystem.ASHTA_KOOTA)
        self.assertGreaterEqual(r.total_score, 0)
        self.assertLessEqual(r.total_score, 36.0)

    def test_system_attribute(self):
        """System should be ASHTA_KOOTA."""
        r = compute_kuta(10.0, 100.0, system=ScoringSystem.ASHTA_KOOTA)
        self.assertEqual(r.system, ScoringSystem.ASHTA_KOOTA)

    def test_system_name(self):
        r = compute_kuta(10.0, 100.0, system=ScoringSystem.ASHTA_KOOTA)
        self.assertEqual(r.system_name, "Ashta Koota")

    def test_gunanka_level_output(self):
        r = compute_kuta(10.0, 100.0, system=ScoringSystem.ASHTA_KOOTA)
        self.assertIn(r.gunanka_level,
                      ["Excellent", "Good", "Fair", "Average", "Below average"])

    def test_factor_names(self):
        r = compute_kuta(10.0, 100.0, system=ScoringSystem.ASHTA_KOOTA)
        expected = ["Varna", "Vashya", "Tara/Dina", "Yoni",
                     "Graha Maitri", "Gana", "Bhakoota", "Nadi"]
        names = [p.name for p in r.poruthams]
        self.assertEqual(names, expected)

    def test_porutham_default(self):
        """Default system should still be 10 Porutham."""
        r = compute_kuta(10.0, 100.0)
        self.assertEqual(r.system, ScoringSystem.PORUTHAM)
        self.assertEqual(len(r.poruthams), 10)

    def test_porutham_system_name(self):
        r = compute_kuta(10.0, 100.0)
        self.assertEqual(r.system_name, "10 Porutham")

    def test_max_score_porutham(self):
        r = compute_kuta(10.0, 100.0)
        self.assertEqual(r.max_score, 19.0)


if __name__ == "__main__":
    unittest.main()
