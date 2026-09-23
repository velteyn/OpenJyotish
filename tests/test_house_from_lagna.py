"""Whole-sign house counting must agree across the modules that need it.

Regression: `learning` and `comparison` used `int((lon - lagna) / 30)`, the
angular distance truncated toward zero, which reports house 1 for any planet
within 30° of the lagna even when it is in the next sign.
"""

from jhora.calc import comparison, learning


def _whole_sign(lon: float, lagna: float) -> int:
    return (int(lon // 30) - int(lagna // 30)) % 12 + 1


def test_learning_matches_whole_sign():
    for lagna in range(0, 360, 7):
        for lon in range(0, 360, 11):
            assert learning._house_from_lagna(lon, lagna) == _whole_sign(lon, lagna)


def test_comparison_matches_whole_sign():
    for lagna in range(0, 360, 7):
        for lon in range(0, 360, 11):
            assert comparison._house_from_lagna(lon, lagna) == _whole_sign(lon, lagna)


def test_regression_next_sign_is_not_house_one():
    # 80.75° (Gemini) from a 101.14° (Cancer) lagna is the 12th sign.
    assert learning._house_from_lagna(80.75, 101.14) == 12
    assert comparison._house_from_lagna(80.75, 101.14) == 12
    # Same sign stays house 1.
    assert learning._house_from_lagna(101.5, 101.14) == 1
