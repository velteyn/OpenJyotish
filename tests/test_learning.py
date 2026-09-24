"""Tests for learning aids: Marana Karaka Sthana + Vaiseshikamsa ranks."""

from jhora.calc.learning import (_MARANA_KARAKA, marana_karaka_sthana,
                                 vaiseshikamsas)
from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha


def _chart(y, m, d, h, la, lo, tz):
    return ChartBuilder().build(y, m, d, h, lat=la, lon=lo, tz=tz,
                                ayanamsa="lahiri")


class TestMarana:
    def test_classical_eight_only(self):
        # Jataka Parijata 17.34-36 lists eight; Ketu has no assignment.
        assert Graha.KETU not in _MARANA_KARAKA
        assert _MARANA_KARAKA == {
            Graha.SUN: 12, Graha.MOON: 8, Graha.MARS: 7,
            Graha.MERCURY: 7, Graha.JUPITER: 3, Graha.VENUS: 6,
            Graha.SATURN: 1, Graha.RAHU: 9,
        }

    def test_sun_in_twelfth_reported(self):
        cd = _chart(1869, 10, 2, 7 + 12 / 60, 21.37, 69.49, "+0438")
        mk = marana_karaka_sthana(cd)
        suns = [m for m in mk if m["graha"] == "Sun"]
        assert len(suns) == 1 and suns[0]["house"] == 12

    def test_jalkot_clean(self):
        cd = _chart(2001, 2, 24, 6 + 11 / 60, 18 + 38 / 60,
                    77 + 12 / 60, "+0530")
        assert marana_karaka_sthana(cd) == []


class TestVaiseshikamsa:
    def test_seven_ranks_sorted(self):
        cd = _chart(2001, 2, 24, 6 + 11 / 60, 18 + 38 / 60,
                    77 + 12 / 60, "+0530")
        va = vaiseshikamsas(cd)
        assert len(va) == 7
        scores = [v["score"] for v in va]
        assert scores == sorted(scores, reverse=True)
        known = {"None", "Parijata", "Uttama", "Gopura", "Simhasana",
                 "Paravata", "Devaloka", "Brahmaloka"}
        assert all(v["rank"] in known for v in va)
