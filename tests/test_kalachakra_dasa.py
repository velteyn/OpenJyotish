"""Kalachakra dasa — Raghavaacharya method (nine mahadasas)."""

from jhora.dasas.base import DasaOptions
from jhora.dasas.kalachakra import KalachakraDasa, _GROUPS, _SEQUENCES
from jhora.types.graha import Graha


def _d(lon):
    return {"planets": {Graha.MOON: {"longitude": lon}}}


class TestKalachakraDasa:
    def test_ardra_third_pada_worked_example(self):
        # P.V.R. Rao's worked example: Ardra 3rd pada, 0.1 of the pada left.
        # Sequence Ge Le Cn Vi Li Sc Pi Aq Cp (paramayush 85); running sign
        # Pisces with 0.5 left, then Aq 4, Cp 4, Ge 9, ...
        lon = 66.6667 + 2 * 3.33333 + 0.9 * 3.33333
        periods = KalachakraDasa().compute(2440000.0, _d(lon), DasaOptions())
        lords = [p.lord_name for p in periods[:9]]
        assert lords == ["Pisces", "Aquarius", "Capricorn", "Gemini", "Leo",
                         "Cancer", "Virgo", "Libra", "Scorpio"]
        durs = [round(p.duration_years, 2) for p in periods[:6]]
        assert durs == [0.5, 4.0, 4.0, 9.0, 5.0, 21.0]

    def test_sequence_has_nine_signs_per_cycle(self):
        # Every group/pada sequence is nine signs summing to its paramayush.
        years = [7, 16, 9, 21, 5, 9, 16, 7, 10, 4, 4, 10]
        for group, table in _SEQUENCES.items():
            for seq, paramayush in table:
                assert len(seq) == 9
                assert sum(years[s] for s in seq) == paramayush

    def test_groups_cover_all_27_nakshatras(self):
        assert sorted(_GROUPS) == list(range(27))

    def test_antardasas_are_nine_signs(self):
        lon = 66.6667 + 2 * 3.33333 + 0.9 * 3.33333
        periods = KalachakraDasa().compute(2440000.0, _d(lon), DasaOptions())
        md = periods[0]
        assert len(md.sub_periods) == 9
        assert abs(sum(s.duration_years for s in md.sub_periods)
                   - md.duration_years) < 1e-9
