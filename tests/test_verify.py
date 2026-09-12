"""Tests for mechanical answer verification (no server needed)."""

from jhora.ai.verify import verify_answer, format_report
from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


def _chart():
    b = ChartBuilder()
    return b.build(1990, 1, 15, 17.5, 12.9716, 77.5946, tz="-5.5")


def _sign(cd, g):
    return Rasi.from_longitude(cd.planet(g).longitude).full_name


def _house(cd, lon):
    asc = int(cd.ascendant // 30) % 12
    return (int(lon // 30) % 12 - asc) % 12 + 1


def test_clean_answer_has_no_flags():
    cd = _chart()
    sun, moon = _sign(cd, Graha.SUN), _sign(cd, Graha.MOON)
    lagna = Rasi.from_longitude(cd.ascendant).full_name
    h = _house(cd, cd.planet(Graha.MARS).longitude)
    from jhora.dasas.vimsottari import VimsottariDasa
    chart_dict = {"planets": {g: {"longitude": p.longitude}
                              for g, p in cd.planets.items()},
                  "lagna_lon": cd.ascendant}
    md = VimsottariDasa().compute(cd.julian_day, chart_dict)[0]
    s, e = md.start_date.strftime("%Y-%m-%d"), md.end_date.strftime("%Y-%m-%d")
    ans = (f"Lagna is {lagna}. Sun in {sun}. Moon in {moon}. "
           f"Mars in H{h}. {md.lord_name} Mahadasha runs {s} to {e}. "
           f"Born 1990-01-15.")
    v = verify_answer(ans, cd)
    assert v.checked >= 5, v.checked
    assert v.flags == []
    assert "all" in format_report(v)


def test_wrong_sign_flagged():
    cd = _chart()
    right = _sign(cd, Graha.MARS)
    wrong = "Pisces" if right != "Pisces" else "Aries"
    v = verify_answer(f"Mars in {wrong}.", cd)
    assert len(v.flags) == 1
    assert v.flags[0].kind == "sign"
    assert right in v.flags[0].expected


def test_wrong_house_and_lagna_flagged():
    cd = _chart()
    lagna = Rasi.from_longitude(cd.ascendant).full_name
    other = "Gemini" if lagna != "Gemini" else "Leo"
    h = _house(cd, cd.planet(Graha.SUN).longitude)
    bad_h = h % 12 + 1
    v = verify_answer(f"{other} lagna shapes this whole chart. "
                      f"Sun sits prominently in H{bad_h} today.", cd)
    kinds = sorted(f.kind for f in v.flags)
    assert kinds == ["house", "lagna"], kinds


def test_unknown_date_flagged():
    cd = _chart()
    v = verify_answer("Mars Antardasha begins 1999-12-31.", cd)
    assert any(f.kind == "date" for f in v.flags)


def test_wrong_strength_flagged():
    cd = _chart()
    from jhora.calc.shadbala import ShadbalaComputer
    real = ShadbalaComputer(cd).compute_one(Graha.SUN).total_virupa
    v = verify_answer(f"Sun Shadbala is {real + 200:.0f} virupas.", cd)
    assert any(f.kind == "strength" for f in v.flags)
    v2 = verify_answer(f"Sun Shadbala is {real:.0f} virupas.", cd)
    assert v2.flags == []


def test_wrong_sav_flagged():
    cd = _chart()
    from jhora.calc.ashtakavarga import sarva_ashtakavarga
    sav = sarva_ashtakavarga(cd)
    assert sum(sav) == 337
    v = verify_answer(f"Sagittarius carries {sav[8] + 10} bindus.", cd)
    assert any(f.kind == "strength" for f in v.flags)


def test_wrong_karaka_flagged():
    cd = _chart()
    from jhora.calc.karaka import compute_chara_karakas, karaka_dict
    planets = {g: {"longitude": cd.planet(g).longitude}
               for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                         Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU]}
    dk = karaka_dict(compute_chara_karakas(planets))["DK"].graha.name.capitalize()
    impostor = "Saturn" if dk != "Saturn" else "Mars"
    v = verify_answer(f"Dara Karaka is {impostor}.", cd)
    assert any(f.kind == "karaka" and dk in f.expected for f in v.flags)


def test_fabricated_quote_flagged():
    cd = _chart()
    passages = ["Jupiter represents wisdom and expansion in the texts."]
    v = verify_answer('As noted in texts, "the Moon is made of cheese".',
                      cd, passages)
    assert any(f.kind == "quote" for f in v.flags)
    v2 = verify_answer(
        'As written, "Jupiter represents wisdom and expansion".', cd,
        passages)
    assert v2.flags == []


def test_quotes_skipped_without_passages():
    cd = _chart()
    v = verify_answer('He said "something unverifiable here at all".', cd)
    assert v.flags == []


def test_birth_datetime_carries_time():
    """Regression: ChartData.birth_date dropped the clock time (midnight),
    so every Birth line read 00:00."""
    from jhora.charts.chart import ChartBuilder
    cd = ChartBuilder().build(1973, 3, 13, 13 + 55 / 60,
                              lat=45.41, lon=11.88, tz="+0100")
    assert (cd.birth_date.hour, cd.birth_date.minute) == (13, 55)


def test_birth_time_flagged():
    cd = _chart()
    v = verify_answer("Birth line: 1990-01-15 00:00 here.", cd)
    assert any(f.kind == "birth-time" for f in v.flags)


def test_spouse_dates_not_flagged():
    cd = _chart()
    v = verify_answer("Spouse born 1982-08-26 06:00.", cd)
    assert v.flags == []
