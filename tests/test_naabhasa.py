"""Tests for Naabhasa yogas (PVR ch. 11.5 worked examples as gold)."""

from jhora.calc.naabhasa import (akriti_yogas, asraya_yogas, dala_yogas,
                                 naabhasa_yogas, sankhya_yoga)
from jhora.types.graha import Graha


class TestAsraya:
    def test_rajju(self):
        assert asraya_yogas({0, 3, 6}) == ["Rajju Yoga"]

    def test_musala(self):
        assert asraya_yogas({1, 4, 7}) == ["Musala Yoga"]

    def test_nala(self):
        assert asraya_yogas({2, 5, 11}) == ["Nala Yoga"]

    def test_mixed_none(self):
        assert asraya_yogas({0, 1, 2}) == []
        assert asraya_yogas(set()) == []


class TestDala:
    def test_maalaa_example(self):
        # Lagna Ar; Ju Cn(4th), Ve Cp(10th), Me Li(7th).
        occ = {4: {Graha.JUPITER}, 10: {Graha.VENUS}, 7: {Graha.MERCURY}}
        assert dala_yogas(occ) == ["Maalaa Yoga"]

    def test_sarpa_example(self):
        # Lagna Sc; Ma Ta(7th), Ra Le(10th), Ke Aq(4th).
        occ = {7: {Graha.MARS}, 10: {Graha.RAHU}, 4: {Graha.KETU}}
        assert dala_yogas(occ) == ["Sarpa Yoga"]

    def test_fewer_than_three(self):
        assert dala_yogas({4: {Graha.JUPITER}}) == []


class TestAkriti:
    def test_gadaa(self):
        assert "Gadaa Yoga" in akriti_yogas({4, 7}, {})

    def test_sakata(self):
        assert "Sakata Yoga" in akriti_yogas({1, 7}, {})

    def test_sringaataka(self):
        assert "Sringaataka Yoga" in akriti_yogas({1, 5, 9}, {})

    def test_hala(self):
        assert "Hala Yoga" in akriti_yogas({2, 6, 10}, {})

    def test_kamala(self):
        assert "Kamala Yoga" in akriti_yogas({1, 4, 7, 10}, {})

    def test_chakra_samudra(self):
        assert "Chakra Yoga" in akriti_yogas({1, 3, 5}, {})
        assert "Samudra Yoga" in akriti_yogas({2, 4, 6}, {})

    def test_yoopa_sara(self):
        assert "Yoopa Yoga" in akriti_yogas({1, 2, 3}, {})
        assert "Sara Yoga" in akriti_yogas({5, 6}, {})

    def test_naukaa_span(self):
        assert "Naukaa Yoga" in akriti_yogas({1, 2, 3, 4, 5, 6, 7}, {})
        assert "Naukaa Yoga" not in akriti_yogas({1, 2, 8}, {})

    def test_vajra_yava(self):
        kinds = {"benefic": {1, 7}, "malefic": {4, 10}}
        assert "Vajra Yoga" in akriti_yogas({1, 4, 7, 10}, kinds)
        assert "Vajra Yoga" not in akriti_yogas({1, 4, 7, 10}, {})


class TestSankhya:
    def test_mapping(self):
        assert sankhya_yoga(7) == "Veenaa Yoga"
        assert sankhya_yoga(6) == "Daama Yoga"
        assert sankhya_yoga(1) == "Gola Yoga"
        assert sankhya_yoga(0) is None
        assert sankhya_yoga(8) is None

    def test_suppressed_when_others_apply(self):
        from jhora.charts.chart import ChartBuilder
        charts = [
            ChartBuilder().build(2001, 2, 24, 6 + 11 / 60, lat=18.63,
                                 lon=77.2, tz="+0530", ayanamsa="lahiri"),
            ChartBuilder().build(1970, 4, 4, 23.3, lat=13.08, lon=80.27,
                                 tz="-5.5", ayanamsa="lahiri"),
            ChartBuilder().build(1869, 10, 2, 7 + 12 / 60, lat=21.37,
                                 lon=69.49, tz="+0438", ayanamsa="lahiri"),
        ]
        for cd in charts:
            names = [r.name for r in naabhasa_yogas(cd)]
            sankhya = {"Veenaa Yoga", "Daama Yoga", "Paasa Yoga",
                       "Kedaara Yoga", "Soola Yoga", "Yuga Yoga",
                       "Gola Yoga"}
            if set(names) - sankhya:
                assert not (set(names) & sankhya), names
