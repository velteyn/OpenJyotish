"""Tests for Buddhi Gati Dasa (Agni Purana tradition, most-used form)."""

from jhora.dasas.base import DasaOptions, PeriodLevel
from jhora.dasas.buddhi_gati import (BuddhiGatiDasa, LIFESPAN_YEARS,
                                     buddhi_gati_progression)
from jhora.types.graha import Graha

JALKOT_LONS = {
    Graha.SUN: 310.72, Graha.MOON: 318.21, Graha.MARS: 219.98,
    Graha.MERCURY: 290.81, Graha.JUPITER: 37.89, Graha.VENUS: 349.83,
    Graha.SATURN: 30.14, Graha.RAHU: 79.60, Graha.KETU: 259.60,
}
JALKOT_LAGNA = 299.78
JALKOT_SEQ = [(4, 8), (6, 9), (7, 10), (2, 5), (8, 6), (3, 5),
              (1, 5), (0, 6), (5, 7)]


def _md_opts(**kw):
    kw.setdefault("subdivision_level", PeriodLevel.MAHADASA)
    kw.setdefault("include_subperiods", False)
    return DasaOptions(**kw)


class TestProgression:
    def test_hand_worked(self):
        lons = {Graha.SUN: 120.0, Graha.MOON: 100.0, Graha.MARS: 10.0}
        prog = buddhi_gati_progression(lons, 0)
        assert [(g, y) for g, y in prog] == [
            (Graha.MOON, 9), (Graha.SUN, 9), (Graha.MARS, 2)]

    def test_sweep_starts_at_fourth(self):
        # Lagna Aq(10): sweep opens at Ta(1); Ju there leads the order.
        lons = {Graha.JUPITER: 37.89, Graha.SATURN: 200.0}
        prog = buddhi_gati_progression(lons, 10)
        assert prog[0][0] == Graha.JUPITER

    def test_descending_longitude_within_house(self):
        lons = {Graha.SUN: 311.0, Graha.MOON: 319.0}
        prog = buddhi_gati_progression(lons, 10)
        # Moon first (0 span: kept for rotation, opens no MD), then Sun.
        assert [g for g, _ in prog] == [Graha.MOON, Graha.SUN]
        assert [y for _, y in prog] == [0, 1]

    def test_exalted_plus_one(self):
        # Sun in Aries, lagna Taurus: (1 + 0 - 0) % 12 = 1, +1 = 2.
        prog = buddhi_gati_progression({Graha.SUN: 10.0}, 1)
        assert prog == [(Graha.SUN, 2)]

    def test_debilitated_minus_one(self):
        # Mars in Cancer, lagna Aries: (0 + 0 - 3) % 12 = 9, -1 = 8.
        prog = buddhi_gati_progression({Graha.MARS: 100.0}, 0)
        assert prog == [(Graha.MARS, 8)]

    def test_node_dignity(self):
        # Rahu in Taurus, lagna Aries: (0 + 0 - 1) % 12 = 11, +1 = 12.
        prog = buddhi_gati_progression({Graha.RAHU: 40.0}, 0)
        assert prog == [(Graha.RAHU, 12)]

    def test_zero_span_kept_for_rotation(self):
        # Mercury debilitated in Pisces, lagna Aries: 1 - 1 = 0.
        # Kept in the order (rotation seat) but opens no mahadasa.
        assert buddhi_gati_progression({Graha.MERCURY: 350.0}, 0) == [
            (Graha.MERCURY, 0)]


class TestEngine:
    def _chart(self):
        return {"planets": {g: {"longitude": v}
                            for g, v in JALKOT_LONS.items()},
                "lagna_lon": JALKOT_LAGNA}

    def test_jalkot_gold_sequence(self):
        ps = BuddhiGatiDasa(_md_opts()).compute(0.0, self._chart(),
                                                _md_opts())
        assert len(ps) == 18  # two full cycles of nine
        assert [(p.lord_index, round(p.duration_years))
                for p in ps[:9]] == JALKOT_SEQ
        assert sum(p.duration_years for p in ps) == 122.0

    def test_contiguous_from_birth(self):
        jd = 2451964.5
        ps = BuddhiGatiDasa(_md_opts()).compute(jd, self._chart(),
                                                _md_opts())
        assert ps[0].start_jd == jd
        for a, b in zip(ps, ps[1:]):
            assert a.end_jd == b.start_jd

    def test_empty_progression(self):
        d = {"planets": {Graha.MERCURY: {"longitude": 350.0}},
             "lagna_lon": 10.0}
        assert BuddhiGatiDasa(_md_opts()).compute(0.0, d, _md_opts()) == []

    def test_sub_levels_rotate_from_parent(self):
        opts = DasaOptions(subdivision_level=PeriodLevel.ANTARDASA)
        ps = BuddhiGatiDasa(opts).compute(0.0, self._chart(), opts)
        first = ps[0]
        assert first.sub_periods
        assert first.sub_periods[0].lord_index == first.lord_index
        assert len(first.sub_periods) == 9
        total = sum(s.duration_years for s in first.sub_periods)
        assert abs(total - first.duration_years) < 1e-6

    def test_varga_override(self):
        d = self._chart()
        d["buddhi_gati_varga"] = {
            "planets": {g: {"longitude": 150.0 + int(g)}
                        for g in JALKOT_LONS},
            "lagna_lon": 10.0,
        }
        ps = BuddhiGatiDasa(_md_opts()).compute(0.0, d, _md_opts())
        base = BuddhiGatiDasa(_md_opts()).compute(0.0, self._chart(),
                                                  _md_opts())
        assert ([p.lord_index for p in ps[:9]]
                != [p.lord_index for p in base[:9]])
