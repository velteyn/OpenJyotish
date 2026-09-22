"""Daily panchanga calendar + canonical trikalam (Rahu/Gulika/Yama) tables."""

from datetime import datetime, timedelta

from jhora.calc.monthly_panchanga import monthly_panchanga
from jhora.calc.muhurta import (
    _inauspicious_periods, sunrise_sunset_hours, _YOGA_NAMES, _KARANA_NAMES,
)

LAT, LON, TZ = 12.97, 77.59, 5.5

# Canonical drik-panchanga trikalam: 0-based eighth of the day from sunrise,
# indexed Sun..Sat.
RAHU = [7, 1, 6, 4, 5, 3, 2]
GULIKA = [6, 5, 4, 3, 2, 1, 0]
YAMA = [4, 3, 2, 1, 0, 6, 5]


def _local_hours(jd: float) -> float:
    return ((jd + 0.5) % 1.0) * 24.0 + TZ


def test_trikalam_eighths_match_canonical_tables():
    # 2026-09-20 is a Sunday; walk a full week.
    for i in range(7):
        dt = datetime(2026, 9, 20) + timedelta(days=i)
        sr, ss = sunrise_sunset_hours(dt, LAT, LON, TZ)
        seg = (ss - sr) / 8.0
        periods = {p.kind.split()[0]: p for p in
                   _inauspicious_periods(dt, LAT, LON, TZ)}
        for kind, table in (("Rahu", RAHU), ("Gulika", GULIKA),
                            ("Yama", YAMA)):
            idx = round((_local_hours(periods[kind].start) - sr) / seg)
            assert idx == table[i], (dt.strftime("%a"), kind, idx)


def test_weekday_is_correct():
    days = {d.date: d for d in monthly_panchanga(2026, 9, LAT, LON, TZ)}
    for date in ("2026-09-01", "2026-09-22"):
        d = datetime.strptime(date, "%Y-%m-%d")
        assert days[date].weekday == d.strftime("%a")


def test_limbs_are_names_not_indices():
    days = {d.date: d for d in monthly_panchanga(2026, 9, LAT, LON, TZ)}
    d = days["2026-09-22"]
    assert d.paksha in ("Shukla", "Krishna")
    assert d.yoga in _YOGA_NAMES
    assert d.karana in _KARANA_NAMES
    assert d.tithi == "Ekadashi"
    assert d.nakshatra == "Uttara Shadha"


def test_sunrise_matches_verified_source():
    sr, _ = sunrise_sunset_hours(datetime(2026, 9, 22), LAT, LON, TZ)
    d = next(x for x in monthly_panchanga(2026, 9, LAT, LON, TZ)
             if x.date == "2026-09-22")
    assert d.sunrise == f"{int(sr):02d}:{int((sr % 1) * 60):02d}"


def test_adjunct_windows_match_muhurta():
    from jhora.calc.muhurta import compute_adjuncts, _datetime_to_jd

    day = datetime(2026, 9, 22)
    d = next(x for x in monthly_panchanga(2026, 9, LAT, LON, TZ,
                                          with_adjuncts=True)
             if x.date == "2026-09-22")
    assert d.durmuhurta1 != "—" and d.varjya1 != "—"

    base = _datetime_to_jd(day, TZ)
    adj = compute_adjuncts(day, LAT, LON, TZ, None)

    def _start(jd):
        h = (jd - base) * 24.0
        return f"{int(h % 24):02d}:{int((h % 1) * 60):02d}"

    assert d.durmuhurta1.split("-")[0] == _start(adj.durmuhurta[0].start)
    assert d.varjya1.split("-")[0] == _start(adj.varjya[0].start)
