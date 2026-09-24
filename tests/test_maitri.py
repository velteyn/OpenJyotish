"""Tests for Graha Maitri (BPHS natural/temporal/compound)."""

from typer.testing import CliRunner

from jhora.calc.maitri import naisargika, panchadha, tatkalika
from jhora.cli.main import app
from jhora.types.graha import Graha

runner = CliRunner()
JALKOT = "2001-02-24 06:11:00 +0530 18.6333 77.2"


class TestNaisargika:
    def test_symmetric_friends(self):
        assert naisargika(Graha.SUN, Graha.JUPITER) == "friend"
        assert naisargika(Graha.VENUS, Graha.SATURN) == "friend"

    def test_asymmetric_mars_moon(self):
        # Mars befriends the Moon; the Moon stays neutral to Mars.
        assert naisargika(Graha.MARS, Graha.MOON) == "friend"
        assert naisargika(Graha.MOON, Graha.MARS) == "neutral"

    def test_moon_has_no_enemies(self):
        for g in (Graha.SUN, Graha.MARS, Graha.MERCURY, Graha.JUPITER,
                  Graha.VENUS, Graha.SATURN):
            assert naisargika(Graha.MOON, g) != "enemy"

    def test_known_enemies(self):
        assert naisargika(Graha.SUN, Graha.SATURN) == "enemy"
        assert naisargika(Graha.MERCURY, Graha.MOON) == "enemy"
        assert naisargika(Graha.SATURN, Graha.MARS) == "enemy"


class TestTatkalika:
    def test_friend_houses(self):
        for offset in (1, 2, 3, 9, 10, 11):
            assert tatkalika(0, offset) == "friend"

    def test_enemy_houses(self):
        for offset in (0, 4, 5, 6, 7, 8):
            assert tatkalika(0, offset) == "enemy"

    def test_mutual(self):
        assert tatkalika(2, 5) == tatkalika(5, 2)


class TestPanchadha:
    def test_all_six_combos(self):
        # F+F=Adhimitra, N+F=Mitra, F+E=E+F=Sama, N+E=Shatru, E+E=Adhishatru.
        cases = [
            # (g1, g2, rasi1, rasi2, name, score)
            (Graha.SUN, Graha.MARS, 0, 1, "Adhimitra", 4),
            (Graha.MOON, Graha.MARS, 0, 1, "Mitra", 3),
            (Graha.MERCURY, Graha.MOON, 0, 1, "Sama", 2),
            (Graha.MERCURY, Graha.SUN, 0, 5, "Sama", 2),
            (Graha.MOON, Graha.MARS, 0, 5, "Shatru", 1),
            (Graha.SUN, Graha.SATURN, 0, 5, "Adhishatru", 0),
        ]
        for g1, g2, r1, r2, name, score in cases:
            assert panchadha(g1, g2, r1, r2) == (name, score)


class TestMaitriCli:
    def test_command(self):
        result = runner.invoke(app, ["maitri", JALKOT])
        assert result.exit_code == 0, result.output
        assert "Panchadha Maitri" in result.output
        # Rich may truncate to "Adhimit…" at narrow widths.
        assert "Adhimit" in result.output
