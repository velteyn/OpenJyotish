"""Jaimini rasi strength (the sign-strength ladder).

Golden vectors are validated against an independent oracle.
`signs[p]`: 0 = lagna, 1 = Sun … 9 = Ketu.
"""

from jhora.calc.jaimini_strength import rasi_drishti, stronger_rasi

GOLDEN = [
    ([1, 5, 8, 8, 10, 1, 3, 9, 9, 8],
     {1: 163, 2: 265, 3: 258, 4: 317, 5: 56, 6: 113, 7: 294, 8: 294, 9: 255},
     (6, 1, 8, 9, 10, 5)),
    ([9, 7, 3, 0, 9, 1, 1, 4, 1, 7],
     {1: 210, 2: 116, 3: 28, 4: 291, 5: 45, 6: 51, 7: 130, 8: 36, 9: 222},
     (0, 1, 2, 9, 4, 5)),
    ([4, 5, 5, 6, 11, 8, 10, 1, 11, 5],
     {1: 152, 2: 167, 3: 197, 4: 339, 5: 249, 6: 314, 7: 34, 8: 358, 9: 170},
     (6, 1, 8, 9, 10, 5)),
    ([11, 11, 9, 4, 0, 11, 5, 5, 7, 6],
     {1: 332, 2: 282, 3: 148, 4: 18, 5: 347, 6: 165, 7: 177, 8: 213, 9: 193},
     (0, 7, 8, 9, 4, 11)),
    ([8, 9, 7, 6, 8, 4, 6, 9, 7, 8],
     {1: 286, 2: 235, 3: 180, 4: 258, 5: 127, 6: 204, 7: 274, 8: 236, 9: 241},
     (6, 7, 8, 9, 4, 5)),
    ([11, 8, 10, 1, 11, 9, 6, 7, 2, 7],
     {1: 268, 2: 307, 3: 57, 4: 358, 5: 273, 6: 200, 7: 232, 8: 74, 9: 231},
     (6, 7, 2, 9, 10, 11)),
    ([7, 11, 8, 4, 8, 6, 10, 4, 8, 10],
     {1: 346, 2: 262, 3: 135, 4: 265, 5: 208, 6: 312, 7: 133, 8: 246, 9: 309},
     (6, 1, 8, 9, 4, 11)),
    ([4, 0, 0, 2, 10, 9, 7, 8, 7, 5],
     {1: 29, 2: 6, 3: 68, 4: 322, 5: 285, 6: 224, 7: 256, 8: 234, 9: 176},
     (0, 7, 8, 9, 10, 5)),
    ([7, 6, 8, 10, 0, 4, 5, 7, 1, 7],
     {1: 202, 2: 262, 3: 325, 4: 16, 5: 128, 6: 164, 7: 239, 8: 35, 9: 223},
     (0, 7, 8, 9, 4, 5)),
    ([11, 7, 1, 10, 4, 7, 5, 1, 3, 11],
     {1: 237, 2: 43, 3: 304, 4: 134, 5: 239, 6: 150, 7: 32, 8: 90, 9: 344},
     (0, 7, 8, 3, 4, 11)),
]


class TestStrongerRasi:
    def test_golden_vectors(self):
        for signs, lons, expected in GOLDEN:
            for a in range(6):
                got = stronger_rasi(a, a + 6, signs, lons)
                assert got == expected[a], (signs, a, got, expected[a])

    def test_returns_one_of_the_pair(self):
        for signs, lons, _ in GOLDEN:
            for a in range(6):
                assert stronger_rasi(a, a + 6, signs, lons) in (a, a + 6)

    def test_more_occupied_sign_wins(self):
        # Sun+Moon+Mars in Aries (0), one planet in Libra (6)
        signs = [0, 0, 0, 0, 5, 11, 11, 11, 11, 11]
        lons = {p: signs[p] * 30.0 for p in range(1, 10)}
        assert stronger_rasi(0, 6, signs, lons) == 0
        assert stronger_rasi(6, 0, signs, lons) == 0


class TestRasiDrishti:
    def test_movable_aspects_fixed(self):
        assert rasi_drishti(0, 4)      # Aries (movable) aspects Leo (fixed)

    def test_dual_aspects_dual(self):
        assert rasi_drishti(2, 5)      # Gemini aspects Virgo (both dual)

    def test_no_self_adjacent_movable_fixed(self):
        assert not rasi_drishti(1, 0)  # Taurus (fixed) does not aspect Aries
