"""Tests for Argala — hand-built occupancies, houses from lagna."""

from jhora.calc.argala import argala_all, argala_for_house
from jhora.types.graha import Graha

Su, Mo, Ma, Me = Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY
Ju, Ve, Sa = Graha.JUPITER, Graha.VENUS, Graha.SATURN
Ra, Ke = Graha.RAHU, Graha.KETU


class TestPrimary:
    def test_second_house_argala(self):
        # Two planets in 2nd from lagna, empty 12th → effective, medium.
        occ = {2: [Ju, Ve]}
        out = argala_for_house(1, occ)
        assert len(out) == 1
        a = out[0]
        assert (a["argala_house"], a["virodha_house"]) == (2, 12)
        assert a["effective"] and a["grade"] == "medium"

    def test_blocked_tie(self):
        occ = {4: [Ma], 10: [Sa]}
        (a,) = argala_for_house(1, occ)
        assert not a["effective"] and a["grade"] == "blocked"

    def test_outnumbered_holds(self):
        occ = {11: [Me, Ve], 3: [Sa]}
        (a,) = argala_for_house(1, occ)
        assert a["effective"]

    def test_reference_relative(self):
        # 2nd from the 7th is the 8th from lagna.
        occ = {8: [Ju]}
        (a,) = argala_for_house(7, occ)
        assert (a["house"], a["argala_house"]) == (7, 8)


class TestVisesha:
    def test_three_malefics_unobstructed(self):
        occ = {3: [Su, Ma, Sa], 11: [Me, Ve, Ju]}
        out = argala_for_house(1, occ)
        vis = [a for a in out if a["virodha_house"] is None]
        assert len(vis) == 1 and vis[0]["effective"]

    def test_two_malefics_no_visesha(self):
        occ = {3: [Su, Ma]}
        assert argala_for_house(1, occ) == []


class TestKetu:
    def test_mirror(self):
        # Ketu in lagna: 10th-from-lagna house becomes argala (was 4th's blocker).
        occ = {1: [Ke], 10: [Ju]}
        (a,) = argala_for_house(1, occ, ketu_sign=1)
        assert (a["argala_house"], a["virodha_house"]) == (10, 4)
        assert a["effective"]


class TestAll:
    def test_twelve_refs(self):
        houses = {Su: 1, Mo: 2, Ma: 4, Me: 5, Ju: 7, Ve: 9,
                  Sa: 10, Ra: 11, Ke: 12}
        out = argala_all(houses)
        refs = {a["house"] for a in out}
        assert refs <= set(range(1, 13))
        assert all(a["planets"] for a in out)
