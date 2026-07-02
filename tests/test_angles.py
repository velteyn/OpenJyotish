"""Tests for longitudinal arithmetic in calc/angles.py."""

from jhora.calc.angles import (
    normalize, diff, signed_diff, add, midpoint, aspect_angle,
)


class TestNormalize:
    def test_zero(self):
        assert normalize(0) == 0.0

    def test_within_range(self):
        assert normalize(45) == 45.0

    def test_wrap_around(self):
        assert normalize(360) == 0.0
        assert normalize(370) == 10.0
        assert normalize(720) == 0.0

    def test_negative(self):
        assert normalize(-10) == 350.0
        assert normalize(-360) == 0.0
        assert normalize(-370) == 350.0


class TestDiff:
    def test_same(self):
        assert diff(0, 0) == 0.0

    def test_forward(self):
        assert diff(10, 30) == 20.0

    def test_shorter_arc(self):
        assert diff(350, 10) == 20.0  # 20° not 340°
        assert diff(10, 350) == 20.0

    def test_exact_opposite(self):
        assert diff(0, 180) == 180.0

    def test_no_diff(self):
        assert diff(45, 45) == 0.0


class TestSignedDiff:
    def test_positive(self):
        d = signed_diff(30, 10)
        assert abs(d - 20.0) < 0.001

    def test_negative(self):
        d = signed_diff(10, 30)
        assert abs(d - (-20.0)) < 0.001

    def test_wrap_positive(self):
        d = signed_diff(10, 350)
        assert abs(d - 20.0) < 0.001

    def test_wrap_negative(self):
        d = signed_diff(350, 10)
        assert abs(d - (-20.0)) < 0.001


class TestAdd:
    def test_no_wrap(self):
        assert add(10, 20) == 30.0

    def test_wrap(self):
        assert add(350, 20) == 10.0

    def test_negative_delta(self):
        assert add(10, -20) == 350.0


class TestMidpoint:
    def test_simple(self):
        assert midpoint(0, 60) == 30.0

    def test_wrap(self):
        assert midpoint(350, 10) == 0.0

    def test_opposite(self):
        m = midpoint(0, 180)
        assert m == 90.0 or m == 270.0  # 90 is correct midpoint


class TestAspectAngle:
    def test_conjunction(self):
        assert aspect_angle(10, 12) == 0

    def test_no_aspect(self):
        assert aspect_angle(10, 40) == 0

    def test_sextile(self):
        assert aspect_angle(10, 72) == 60

    def test_square(self):
        assert aspect_angle(10, 100) == 90

    def test_trine(self):
        assert aspect_angle(10, 130) == 120

    def test_opposition(self):
        assert aspect_angle(10, 192) == 180

    def test_wrap_sextile(self):
        assert aspect_angle(350, 52) == 60

    def test_wrap_square(self):
        assert aspect_angle(350, 82) == 90
