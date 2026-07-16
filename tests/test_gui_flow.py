"""Integration test — mimics full GUI Calculate button flow.

Exercises every populate function that runs when a user
clicks Calculate in the GUI. One test catches all attribute
errors, unpacking errors, and crashes at once.
"""

import pytest
from datetime import datetime

from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra


@pytest.fixture(scope="module")
def chart():
    b = ChartBuilder()
    return b.build(1973, 3, 13, 13.0 + 55 / 60.0, 45.41, 11.88, tz="+0100")


def test_planets(chart):
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
        p = chart.planet(g)
        Rasi.from_longitude(p.longitude)
        Nakshatra.from_longitude(p.longitude)


def test_houses(chart):
    for h in range(12):
        Rasi.from_longitude(chart.house_cusps[h])


def test_dasa(chart):
    from jhora.dasas.vimsottari import VimsottariDasa
    dasa = VimsottariDasa()
    cd = {"planets": {g.value: {"longitude": p.longitude}
                      for g, p in chart.planets.items()},
          "lagna_lon": chart.ascendant}
    periods = dasa.compute(chart.julian_day, cd)
    assert len(periods) == 9


def test_yogas(chart):
    from jhora.calc.yogas import detect_all
    yogas = detect_all(chart)
    assert len(yogas) > 0


def test_shadbala(chart):
    from jhora.calc.shadbala import ShadbalaComputer
    sb = ShadbalaComputer(chart)
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
        r = sb.compute_one(g)
        assert 0 < r.total_virupa < 1000


def test_bhava_bala(chart):
    from jhora.calc.bhava_bala import BhavaBalaComputer
    bb = BhavaBalaComputer(chart)
    report = bb.compute_all()
    assert len(report.results) == 12


def test_vimsopaka(chart):
    from jhora.calc.vimsopaka import VimsopakaComputer, VimsopakaScheme
    vc = VimsopakaComputer(chart)
    results = vc.compute_all(VimsopakaScheme.SHADVARGA)
    assert len(results) == 7
    for r in results:
        assert 0 <= r.total <= 20


def test_arudha_karaka_sahama(chart):
    from jhora.calc.arudha import all_bhava_arudhas
    from jhora.calc.karaka import compute_chara_karakas
    from jhora.calc.sahama import compute_sahamas
    planets = {g: {"longitude": p.longitude, "speed": p.speed}
               for g, p in chart.planets.items()}
    bhava = all_bhava_arudhas(chart.ascendant, planets)
    assert len(bhava) == 12
    cks = compute_chara_karakas(planets)
    assert len(cks) == 8
    for k in cks:
        assert k.short_name  # attribute exists
        assert k.full_name   # attribute exists
    is_day = chart.birth_date.hour >= 6 and chart.birth_date.hour < 18
    sahamas = compute_sahamas(chart.ascendant, planets, day=is_day)
    assert len(sahamas) == 36


def test_ashtakavarga(chart):
    from jhora.calc.ashtakavarga import sarva_ashtakavarga, all_bhinna_ashtakavarga
    sav = sarva_ashtakavarga(chart)
    assert sum(sav) > 0
    bavs = all_bhinna_ashtakavarga(chart)
    assert len(bavs) >= 7


def test_transit(chart):
    from jhora.calc.gochara import compute_transits
    from jhora.ephemeris.swe import SweEngine
    eng = SweEngine()
    now = datetime.now()
    jd = eng.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)
    tr = compute_transits(chart, jd)
    assert len(tr.entries) == 7


def test_tajaka(chart):
    from jhora.calc.tajaka import build_tajaka_chart
    from jhora.ephemeris.swe import SweEngine
    eng = SweEngine()
    cbb = ChartBuilder()
    tr = build_tajaka_chart(eng, cbb, chart, chart.birth_date.year + 1, tropical=False)
    assert tr.year_index == 2


def test_tithi_pravesha(chart):
    from jhora.calc.tithi_pravesha import TithiPraveshaCalculator
    tp = TithiPraveshaCalculator(chart)
    entry = tp.compute(chart.birth_date.year + 1)
    assert entry.chart is not None


def test_progression(chart):
    from jhora.calc.progressions import ProgressionCalculator
    pc = ProgressionCalculator(chart)
    age = (datetime.now() - chart.birth_date).total_seconds() / (365.25 * 86400)
    sec = pc.secondary(target_age=age)
    assert sec.chart is not None


def test_upagrahas(chart):
    from jhora.calc.upagraha import compute_solar_upagrahas
    from jhora.calc.special_lagnas import compute_special_lagnas
    upas = compute_solar_upagrahas(chart.planet(Graha.SUN).longitude)
    assert len(upas) == 5
    sl = compute_special_lagnas(chart)
    assert len(sl) == 5


def test_chalit(chart):
    from jhora.calc.chalit import ChalitComputer
    cc = ChalitComputer(chart)
    cr = cc.compute()
    assert len(cr.entries) == 9


def test_json_export(chart):
    from jhora.ai.json_export import chart_to_json
    data = chart_to_json(chart)
    assert len(data) == 16
    assert "planets" in data
    assert "dasa" in data
    assert "transits" in data
    # Check karaka names use correct attribute
    for k in data["karakas"]:
        assert k["karaka"]  # should be short_name like "AK", "AmK"


def test_muhurta(chart):
    from jhora.calc.muhurta import MuhurtaTask, evaluate_time
    now = datetime.now()
    r = evaluate_time(now, chart.latitude, chart.longitude, 5.5, MuhurtaTask.GENERAL)
    assert 0 <= r.score <= 1


def test_prasna():
    from jhora.calc.prasna import PrasnaMode, compute_prasna
    for pm in PrasnaMode:
        r = compute_prasna(108, pm)
        assert r.rasi is not None


def test_matchmaking(chart):
    b = ChartBuilder()
    c2 = b.build(1980, 6, 15, 8.0, 45.41, 11.88, tz="+0100")
    from jhora.calc.kuta import compute_kuta, ScoringSystem
    from jhora.types.graha import Graha
    girl_moon = chart.planet(Graha.MOON).longitude
    boy_moon = c2.planet(Graha.MOON).longitude
    result = compute_kuta(girl_moon, boy_moon)
    assert 0 <= result.total_score <= 36


def test_learning(chart):
    from jhora.calc.learning import marana_karaka_sthana, vaiseshikamsas, ishta_kashta_phala
    mk = marana_karaka_sthana(chart)
    va = vaiseshikamsas(chart)
    ik = ishta_kashta_phala(chart)
    assert isinstance(mk, list)
    assert isinstance(va, list)
    assert isinstance(ik, list)
