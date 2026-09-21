"""Tests for KP (Krishnamurti Paddhati) — cusps, lord chains, Ruling Planets.

Tradition: Krishnamurti's KP uses Placidus cusps and the Vimsottari
fourfold chain; the first sub of a nakshatra is its own lord.
"""

from jhora.calc.kp import (
    SIGN_LORDS,
    cusp_longitudes,
    day_lord,
    house_of,
    kp_chart,
    lord_chain,
    ruling_planets,
)
from jhora.calc.special_lagnas import kp_sublord
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


class TestSubLordRotation:
    """The Vimsottari subdivision must start at the nakshatra's own lord."""

    def test_ashwini_starts_at_ketu(self):
        assert kp_sublord(0.5, 1)[0]["graha"] == Graha.KETU

    def test_bharani_starts_at_venus(self):
        # 13°20'–15°33'20" of Aries is Bharani's Venus sub.
        assert kp_sublord(13.4, 1)[0]["graha"] == Graha.VENUS

    def test_bharani_second_sub_is_sun(self):
        # After Venus (2°13'20") the Sun runs to 16°13'20".
        assert kp_sublord(16.0, 1)[0]["graha"] == Graha.SUN

    def test_krittika_starts_at_sun(self):
        # Krittika begins at 26°40'; its lord is the Sun.
        assert kp_sublord(27.0, 1)[0]["graha"] == Graha.SUN

    def test_deeper_level_starts_at_parent_sub(self):
        subs = kp_sublord(13.4, 2)
        assert subs[0]["graha"] == Graha.VENUS
        assert subs[1]["graha"] == Graha.VENUS

    def test_levels_nest(self):
        for lon in (0.0, 13.4, 27.1, 100.0, 250.0, 359.9):
            sub = kp_sublord(lon, 1)[0]
            sub_sub = kp_sublord(lon, 2)[1]
            assert sub["start"] <= lon < sub["end"]
            assert sub["start"] <= sub_sub["start"]
            assert sub_sub["end"] <= sub["end"] + 1e-9

    def test_span_widths_follow_vimsottari_years(self):
        # Venus sub of Bharani = 20/120 of 13°20'.
        sub = kp_sublord(13.4, 1)[0]
        assert abs((sub["end"] - sub["start"]) - (20 / 120) * (360 / 27)) < 1e-6


class TestLordChain:
    def test_chain_has_four_lords(self, ref_chart):
        chain = lord_chain(ref_chart.ascendant)
        assert all(isinstance(x, Graha) for x in (
            chain.sign_lord, chain.star_lord, chain.sub_lord, chain.sub_sub_lord))

    def test_bharani_chain(self):
        chain = lord_chain(14.0)
        assert chain.sign_lord == Graha.MARS      # Aries
        assert chain.star_lord == Graha.VENUS     # Bharani
        assert chain.sub_lord == Graha.VENUS

    def test_sign_lord_is_never_a_node(self):
        assert all(not g.is_node for g in SIGN_LORDS.values())

    def test_chain_string(self):
        assert lord_chain(0.0).string == "Mars-Ketu-Ketu-Ketu"


class TestHouseOf:
    def test_interval_lookup(self):
        cusps = [350.0, 20.0, 50.0, 80.0, 110.0, 140.0,
                 170.0, 200.0, 230.0, 260.0, 290.0, 320.0]
        assert house_of(355.0, cusps) == 1
        assert house_of(10.0, cusps) == 1
        assert house_of(0.0, cusps) == 1
        assert house_of(25.0, cusps) == 2
        assert house_of(325.0, cusps) == 12


class TestKPChart:
    def test_twelve_cusps(self, ref_chart):
        kpc = kp_chart(ref_chart)
        assert [c.house for c in kpc.cusps] == list(range(1, 13))

    def test_first_cusp_is_the_ascendant(self, ref_chart):
        cusps = cusp_longitudes(ref_chart)
        sep = (cusps[0] - ref_chart.ascendant + 180) % 360 - 180
        assert abs(sep) < 0.1

    def test_cusps_are_placidus_not_whole_sign(self, ref_chart):
        cusps = cusp_longitudes(ref_chart)
        gaps = [(cusps[(i + 1) % 12] - cusps[i]) % 360 for i in range(12)]
        assert any(abs(g - 30.0) > 0.5 for g in gaps)

    def test_all_planets_placed_in_a_bhava(self, ref_chart):
        kpc = kp_chart(ref_chart)
        assert {p.graha for p in kpc.planets} == set(ref_chart.planets)
        assert all(1 <= p.house <= 12 for p in kpc.planets)

    def test_planet_sign_matches_longitude(self, ref_chart):
        for p in kp_chart(ref_chart).planets:
            assert p.sign == Rasi.from_longitude(p.longitude)

    def test_ayanamsa_is_reported(self, ref_chart):
        kpc = kp_chart(ref_chart)
        assert kpc.ayanamsa == ref_chart.ayanamsa_name
        assert kpc.cusp_system == "Placidus"

    def test_deterministic(self, ref_chart):
        a = kp_chart(ref_chart)
        b = kp_chart(ref_chart)
        assert [c.chain for c in a.cusps] == [c.chain for c in b.cusps]


class TestRulingPlanets:
    def test_day_lord_is_saturday(self, ref_chart):
        # 1970-04-04 was a Saturday; 23:18 local is after sunrise.
        assert day_lord(ref_chart) == Graha.SATURN

    def test_day_lord_before_sunrise_uses_previous_day(self):
        # 01:00 local on a Saturday is before sunrise, so the Hindu weekday
        # is still Friday and the day lord is Venus.
        from jhora.charts.chart import ChartBuilder

        cd = ChartBuilder().build(
            year=1970, month=4, day=4, hour=1.0,
            lat=13.08, lon=80.27, tz="-5.5", ayanamsa="lahiri",
        )
        assert day_lord(cd) == Graha.VENUS

    def test_roles_are_deduplicated(self, ref_chart):
        rps = ruling_planets(ref_chart)
        assert len({r.graha for r in rps}) == len(rps)
        assert rps[0].graha == Graha.SATURN
        assert "day lord" in rps[0].roles

    def test_expected_roles_present(self, ref_chart):
        roles = {role for r in ruling_planets(ref_chart) for role in r.roles}
        assert roles == {
            "day lord", "Moon's star lord", "Moon's sign lord",
            "lagna's star lord", "lagna's sign lord",
        }

    def test_repr_includes_roles(self, ref_chart):
        rp = ruling_planets(ref_chart)[0]
        assert "day lord" in rp.role_string
