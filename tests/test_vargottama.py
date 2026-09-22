"""Tests for the vargottama calculation and the CLI view."""

from jhora.charts.chart import ChartBuilder
from jhora.charts.varga import VargaChartComputer
from jhora.calc.vargottama import compute_vargottama
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.varga import VargaLevel, VargaVariant


def _chart():
    cd = ChartBuilder().build(year=1970, month=4, day=4, hour=23.3,
                              lat=13.08, lon=80.27, tz="-5.5",
                              ayanamsa="lahiri")
    return cd


class TestVargottama:
    def test_matches_manual_d1_versus_d9(self):
        cd = _chart()
        res = compute_vargottama(cd)
        d9 = VargaChartComputer().compute(cd, VargaLevel.D_9,
                                          VargaVariant.DEFAULT)
        for g, p in cd.planets.items():
            d1_sign = Rasi.from_longitude(p.longitude)
            expected = d9.positions[g].rasi == d1_sign
            assert res.is_vargottama(g, VargaLevel.D_9) == expected

    def test_lagna_vargottama_in_d9_for_the_1970_chart(self):
        cd = _chart()
        res = compute_vargottama(cd)
        assert VargaLevel.D_9 in res.lagna

    def test_d1_never_counts(self):
        cd = _chart()
        res = compute_vargottama(cd)
        for g in cd.planets:
            assert VargaLevel.D_1 not in res.planets[g]
        assert VargaLevel.D_1 not in res.lagna

    def test_every_varga_is_self_consistent(self):
        # A body is vargottama in D-1 by construction, so D-1 is excluded; in
        # every reported varga the sign must equal the D-1 sign.
        cd = _chart()
        res = compute_vargottama(cd)
        comp = VargaChartComputer()
        for g, p in cd.planets.items():
            d1 = Rasi.from_longitude(p.longitude)
            for level in res.planets[g]:
                chart = comp.compute(cd, level, VargaVariant.DEFAULT)
                assert chart.positions[g].rasi == d1
