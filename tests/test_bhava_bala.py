"""Tests for Bhava Bala (house strength) computation."""

from jhora.charts.chart import ChartBuilder
from jhora.calc.bhava_bala import BhavaBalaComputer, BhavaBalaReport


def _sample_chart():
    builder = ChartBuilder()
    return builder.build(
        year=2026, month=7, day=7, hour=10.5,
        lat=13.08, lon=80.27, tz="+0530",
    )


class TestBhavaBala:
    def test_compute_all_returns_12_houses(self):
        cd = _sample_chart()
        comp = BhavaBalaComputer(cd)
        report = comp.compute_all()
        assert len(report.results) == 12
        for h in range(1, 13):
            assert h in report.results

    def test_house_ranges(self):
        cd = _sample_chart()
        comp = BhavaBalaComputer(cd)
        report = comp.compute_all()
        for _h, r in report.results.items():
            assert 0 <= r.sthana <= 60, f"House {_h} sthana out of range: {r.sthana}"
            assert 0 <= r.drishti <= 60, f"House {_h} drishti out of range: {r.drishti}"
            assert 0 <= r.dig <= 60, f"House {_h} dig out of range: {r.dig}"
            assert 0 <= r.adhipati <= 60, f"House {_h} adhipati out of range: {r.adhipati}"
            assert -30 <= r.drig <= 30, f"House {_h} drig out of range: {r.drig}"

    def test_kendra_has_max_sthana(self):
        cd = _sample_chart()
        comp = BhavaBalaComputer(cd)
        report = comp.compute_all()
        for h in [1, 4, 7, 10]:
            assert report.results[h].sthana == 60, f"House {h} kendra should have 60 sthana"
        for h in [2, 5, 8, 11]:
            assert report.results[h].sthana == 30, f"House {h} panapara should have 30 sthana"
        for h in [3, 6, 9, 12]:
            assert report.results[h].sthana == 15, f"House {h} apoklima should have 15 sthana"

    def test_dig_bala_peaks_at_kendras(self):
        cd = _sample_chart()
        comp = BhavaBalaComputer(cd)
        report = comp.compute_all()
        for h in [1, 4, 7, 10]:
            assert report.results[h].dig == 60, f"House {h} dig bala should be 60"

    def test_total_is_sum_of_components(self):
        cd = _sample_chart()
        comp = BhavaBalaComputer(cd)
        report = comp.compute_all()
        for _h, r in report.results.items():
            expected = r.sthana + r.drishti + r.dig + r.adhipati + r.drig
            assert abs(r.total - expected) < 0.1, (
                f"House {_h}: {r.total} != {expected}"
            )

    def test_strongest_and_weakest(self):
        cd = _sample_chart()
        comp = BhavaBalaComputer(cd)
        report = comp.compute_all()
        strongest = report.strongest()
        weakest = report.weakest()
        assert strongest.total >= weakest.total
        assert strongest.house != weakest.house

    def test_different_chart(self):
        builder = ChartBuilder()
        cd = builder.build(
            year=1990, month=1, day=15, hour=5.5,
            lat=28.6, lon=77.2, tz="+0530",
        )
        comp = BhavaBalaComputer(cd)
        report = comp.compute_all()
        assert len(report.results) == 12
        for h in range(1, 13):
            r = report.results[h]
            assert r.total > 0, f"House {h} should have positive total"
