"""Tests for Muhurta daily adjuncts (Durmuhurta, Varjya, Panchaka, Chandra/Tara Bala).

Golden fixtures anchor the implementations to the reference values used while
reverse-engineering the adjuncts table:
  - Durmuhurta: weekday -> 15-muhurta index (reference DurMuhurta1 column).
  - Tara Bala: inclusive Janma -> target 9-count (Sampat/Vipat/.../Parama Mitra).
  - Regression: Drik Panchang Chennai 2026-09-16 Dur Muhurtam / Varjyam and the
    Panchaka-Rahita day list; AstroShruti Chandra Bala verdicts (New Delhi,
    Moon in Capricorn at sunrise). All values are documented in the change
    `add-muhurta-adjuncts` design/specs.
"""

import unittest
from datetime import datetime, timedelta

from typer.testing import CliRunner

from jhora.calc.muhurta import (
    ChandraBala,
    MuhurtaTask,
    Tara,
    compute_adjuncts,
    evaluate_time,
    _chandra_bala_grade_for,
    _datetime_to_jd,
    _DURMUHURTA_DAY_MUHURTA_INDEX,
    _DURMUHURTA_NIGHT_MUHURTA_INDEX,
    _durmuhurta_windows,
    _nakshatra_varjya_windows,
    _panchaka_category,
    _panchaka_category_for,
    _panchaka_segments,
    _sunrise_sunset,
    _tara_bala_for,
)
from jhora.types.nakshatra import Nakshatra
from jhora.types.rasi import Rasi

CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2707
CHENNAI_TZ = 5.5

# Sept 7 2026 is a Monday; 7 + i walks Mon..Sun.
_SEP_2026_MON = datetime(2026, 9, 7)
# Sunday = 13th (0-based index 13 -> 14th of 15), Mon = 9th ... Sat = 1st.
_WEEKDAY_ORDINAL = {0: 14, 1: 9, 2: 4, 3: 8, 4: 6, 5: 4, 6: 1}


def _local_hours(jd: float, day_start_jd: float) -> float:
    return (jd - day_start_jd) * 24.0


class TestDurmuhurtaGolden(unittest.TestCase):
    """Task 1.2 golden fixture: weekday -> 15-muhurta index for the day and night."""

    def test_weekday_maps_to_expected_muhurta(self):
        for i in range(7):
            date = _SEP_2026_MON + timedelta(days=i)
            wd = (date.weekday() + 1) % 7
            sunrise, sunset = _sunrise_sunset(date, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)
            day_span = (sunset - sunrise) / 15.0
            day_win = _durmuhurta_windows(date, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)[0]
            muhurta_idx = round((day_win.start - sunrise) / day_span)
            self.assertEqual(muhurta_idx + 1, _WEEKDAY_ORDINAL[wd],
                             f"weekday={date.strftime('%A')}")

    def test_constant_table_matches_ordinals(self):
        for wd, expected_idx in enumerate([13, 8, 3, 7, 5, 3, 0]):
            self.assertEqual(_DURMUHURTA_DAY_MUHURTA_INDEX[wd], expected_idx)
            self.assertEqual(_DURMUHURTA_NIGHT_MUHURTA_INDEX[wd], expected_idx)
            self.assertEqual(expected_idx + 1, _WEEKDAY_ORDINAL[wd])

    def test_night_window_uses_same_index_over_night_muhurtas(self):
        date = _SEP_2026_MON  # Monday -> index 8 (9th)
        sunrise, sunset = _sunrise_sunset(date, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)
        next_sunrise, _ = _sunrise_sunset(date + timedelta(days=1),
                                          CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)
        night_win = _durmuhurta_windows(date, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)[1]
        night_span = (next_sunrise - sunset) / 15.0
        idx = round((night_win.start - sunset) / night_span)
        self.assertEqual(idx + 1, 9)

    def test_two_windows_chronological(self):
        date = _SEP_2026_MON
        wins = _durmuhurta_windows(date, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)
        self.assertEqual(len(wins), 2)
        self.assertEqual({w.kind for w in wins}, {"Durmuhurta"})
        self.assertLess(wins[0].end, wins[1].start)


class TestTaraGolden(unittest.TestCase):
    """Task 1.2 golden fixture: inclusive Janma -> target 9-count classification."""

    # count within 1..9 -> (Tara name, auspicious?)
    _TABLE = {
        1: ("Janma", False),
        2: ("Sampat", True),
        3: ("Vipat", False),
        4: ("Kshema", True),
        5: ("Pratyari", False),
        6: ("Sadhaka", True),
        7: ("Nidhana", False),
        8: ("Mitra", True),
        9: ("Parama Mitra", True),
    }

    def test_full_nine_count(self):
        janma = Nakshatra.ASVINI
        for count in range(1, 28):
            target = Nakshatra((janma.value + count - 1) % 27)
            tara, auspicious = Tara.from_janma(janma, target)
            rem = count % 9 or 9
            expected_name, expected_auspicious = self._TABLE[rem]
            self.assertEqual(tara.value, expected_name, f"count={count}")
            self.assertEqual(auspicious, expected_auspicious, f"count={count}")
            self.assertEqual(tara.auspicious, expected_auspicious)

    def test_wrap_around_counts_toward_nines(self):
        # Janma Hasta (13), target Chitra (14): inclusive count 2 -> Sampat.
        tara, auspicious = Tara.from_janma(Nakshatra.HASTA, Nakshatra.CHITRA)
        self.assertEqual(tara, Tara.SAMPAT)
        self.assertTrue(auspicious)
        # Janma Ashvini -> Revati: count 27 -> Parama Mitra.
        tara, auspicious = Tara.from_janma(Nakshatra.ASVINI, Nakshatra.REVATI)
        self.assertEqual(tara, Tara.PARAMA_MITRA)
        self.assertTrue(auspicious)
        # Janma Ashvini -> same nakshatra: count 1 -> Janma (neutral).
        tara, auspicious = Tara.from_janma(Nakshatra.ASVINI, Nakshatra.ASVINI)
        self.assertEqual(tara, Tara.JANMA)
        self.assertFalse(auspicious)

    def test_day_bala_for_missing_janma_is_unavailable(self):
        for nak in (Nakshatra.ASVINI, Nakshatra.HASTA):
            day_nak, _pada = Nakshatra.from_longitude(200.0)
            tara, auspicious = _tara_bala_for(day_nak, None)
            self.assertIsNone(tara)
            self.assertFalse(auspicious)


class TestDurmuhurtaRegression(unittest.TestCase):
    """Task 1.3: Drik Panchang Chennai 2026-09-16 'Dur Muhurtam 11:39 AM to 12:28 PM'."""

    def test_day_window_matches_drik(self):
        dt = datetime(2026, 9, 16)
        day_start_jd = _datetime_to_jd(dt.replace(hour=0, minute=0), CHENNAI_TZ)
        win = _durmuhurta_windows(dt, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)[0]
        start_h, end_h = (_local_hours(jd, day_start_jd) for jd in (win.start, win.end))
        self.assertAlmostEqual(start_h, 11 + 39 / 60, delta=12 / 60)
        self.assertAlmostEqual(end_h, 12 + 28 / 60, delta=12 / 60)


class TestVarjyaRegression(unittest.TestCase):
    """Task 1.3: Drik Panchang Chennai 2026-09-14/16 Varjyam windows."""

    # (date, Drik start hh:mm, Drik end hh:mm)
    _CASES = [
        (datetime(2026, 9, 14), 19 + 51 / 60, 21 + 33 / 60),
        (datetime(2026, 9, 16), 21 + 47 / 60, 23 + 33 / 60),
    ]

    def test_varjya_windows_match_drik(self):
        for dt, drik_start, drik_end in self._CASES:
            day_start_jd = _datetime_to_jd(dt.replace(hour=0, minute=0), CHENNAI_TZ)
            wins = _nakshatra_varjya_windows(dt, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)
            self.assertGreaterEqual(len(wins), 1, f"{dt.date()}")
            start_h = min(_local_hours(w.start, day_start_jd) for w in wins)
            end_h = max(_local_hours(w.end, day_start_jd) for w in wins)
            self.assertAlmostEqual(start_h, drik_start, delta=15 / 60, msg=f"{dt.date()}")
            self.assertAlmostEqual(end_h, drik_end, delta=15 / 60, msg=f"{dt.date()}")

    def test_no_varjya_when_crossings_outside_civil_day(self):
        # Chennai 2026-09-17: both varjya crossings fall outside the civil day.
        dt = datetime(2026, 9, 17)
        wins = _nakshatra_varjya_windows(dt, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)
        self.assertEqual(len(wins), 0)


class TestPanchakaRegression(unittest.TestCase):
    """Task 1.3: Drik Panchang Chennai 2026-09-16 Panchaka-Rahita day list.

    The reference lists 13 segments from sunrise. We sample the interior midpoint of
    each and require the same category, then verify the mod-9 arithmetic directly.
    """

    # (start hh:mm, end hh:mm, category). Source: Drik 'Panchaka Rahita Muhurta
    # for the day' (Chennai, Wed 2026-09-16).
    _DRIK_SEGMENTS = [
        (5 + 58 / 60, 6 + 5 / 60, "Rahita"),
        (6 + 5 / 60, 8 + 6 / 60, "Raja"),
        (8 + 6 / 60, 8 + 59 / 60, "Rahita"),
        (8 + 59 / 60, 10 + 13 / 60, "Chora"),
        (10 + 13 / 60, 12 + 25 / 60, "Rahita"),
        (12 + 25 / 60, 14 + 32 / 60, "Roga"),
        (14 + 32 / 60, 16 + 25 / 60, "Rahita"),
        (16 + 25 / 60, 17 + 22 / 60, "Mrityu"),
        (17 + 22 / 60, 18 + 7 / 60, "Agni"),
        (18 + 7 / 60, 19 + 47 / 60, "Rahita"),
        (19 + 47 / 60, 21 + 35 / 60, "Mrityu"),
        (21 + 35 / 60, 23 + 37 / 60, "Agni"),
        (23 + 37 / 60, 1 + 49 / 60, "Rahita"),
    ]

    def test_categories_reproduce_drik_day(self):
        # Sunrise-to-midnight segment kinds must reproduce the Drik 13-segment
        # order exactly (Rahita == Drik "Good"); boundaries may shift a few minutes
        # because Drik resolves exact times while we scan on a 10-minute grid.
        segs = _panchaka_segments(datetime(2026, 9, 16), CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)
        sunrise, _sunset = _sunrise_sunset(datetime(2026, 9, 16),
                                           CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)
        kinds = []
        for w in segs:
            if w.end <= sunrise:
                continue
            kinds.append(w.kind if w.kind == "Rahita" else w.kind.split()[0])
        expected = [seg[2] for seg in self._DRIK_SEGMENTS]
        self.assertEqual(kinds, expected)

    def test_anchor_categories(self):
        # Anchors well inside both Drik and our segments: 07:30 Raja, 09:30 Chora,
        # 13:30 Roga, 21:00 Mrityu.
        for hh, mm, expected in [(7, 30, "Raja"), (9, 30, "Chora"),
                                 (13, 30, "Roga"), (21, 0, "Mrityu")]:
            dt = datetime(2026, 9, 16, hh, mm)
            name, _rahita = _panchaka_category(dt, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)
            self.assertEqual(name, expected, f"at {dt.time()}")

    def test_mod9_arithmetic_golden_table(self):
        # (tithi_no, vara_no, nak_no, lagna_no) -> (name, rahita) for every remainder.
        cases = [
            ((5, 4, 16, 3), ("Mrityu", False)),   # remainder 1
            ((5, 4, 16, 4), ("Agni", False)),     # 2
            ((5, 4, 16, 5), ("Rahita", True)),    # 3
            ((5, 4, 16, 6), ("Raja", False)),     # 4
            ((5, 4, 16, 7), ("Rahita", True)),    # 5
            ((5, 4, 16, 8), ("Chora", False)),    # 6
            ((5, 4, 16, 9), ("Rahita", True)),    # 7
            ((5, 4, 16, 10), ("Roga", False)),    # 8
            ((5, 4, 16, 11), ("Rahita", True)),   # 0
        ]
        for inputs, expected in cases:
            self.assertEqual(_panchaka_category_for(*inputs), expected, f"{inputs}")

    def test_segments_cover_day_chronologically(self):
        segs = _panchaka_segments(datetime(2026, 9, 16), CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)
        self.assertGreaterEqual(len(segs), 10)
        for prev, cur in zip(segs, segs[1:]):
            self.assertLessEqual(prev.end, cur.start)
            self.assertLess(prev.start, prev.end)
        self.assertLess(segs[-1].end - segs[0].start, 1.02)


class TestChandraBalaRegression(unittest.TestCase):
    """Task 1.3: AstroShruti Chandra Bala verdicts (New Delhi, Tue 25 Aug 2026,
    Moon in Capricorn at sunrise): rank from Janma rashi, verdicts per rashi."""

    # rasi index (0=Aries..11=Pisces) -> grade with Moon in Capricorn (rasi 9).
    _VERDICTS = [
        ChandraBala.GOOD,     # Aries    10th
        ChandraBala.NEUTRAL,  # Taurus    9th
        ChandraBala.BAD,      # Gemini    8th
        ChandraBala.GOOD,     # Cancer    7th
        ChandraBala.GOOD,     # Leo       6th
        ChandraBala.NEUTRAL,  # Virgo     5th
        ChandraBala.BAD,      # Libra     4th
        ChandraBala.GOOD,     # Scorpio   3rd
        ChandraBala.NEUTRAL,  # Sagitt.   2nd
        ChandraBala.GOOD,     # Capricorn 1st
        ChandraBala.BAD,      # Aquarius 12th
        ChandraBala.GOOD,     # Pisces   11th
    ]
    MOON_RASI = Rasi.CAPRICORN.value  # 9

    # First nakshatra whose start longitude falls in each rashi.
    _FIRST_NAK = [0, 3, 5, 7, 9, 12, 14, 16, 18, 21, 23, 25]

    def test_verdicts_per_janma_rashi(self):
        for rasi_idx, expected in enumerate(self._VERDICTS):
            janma = Nakshatra(self._FIRST_NAK[rasi_idx])
            grade = _chandra_bala_grade_for(self.MOON_RASI, janma)
            self.assertEqual(grade, expected, f"rashi={Rasi(rasi_idx).name}")

    def test_house_count_mapping(self):
        # Moon in Taurus (rasi 1). Inclusive house count = (moon - janma) % 12 + 1:
        #   Taurus janma   -> house 1  -> GOOD
        #   Aries janma    -> house 2  -> NEUTRAL
        #   Aquarius janma -> house 4  -> BAD
        self.assertEqual(
            _chandra_bala_grade_for(Rasi.TAURUS.value, Nakshatra(self._FIRST_NAK[1])),
            ChandraBala.GOOD)
        self.assertEqual(
            _chandra_bala_grade_for(Rasi.TAURUS.value, Nakshatra(self._FIRST_NAK[0])),
            ChandraBala.NEUTRAL)
        self.assertEqual(
            _chandra_bala_grade_for(Rasi.TAURUS.value, Nakshatra(self._FIRST_NAK[10])),
            ChandraBala.BAD)

    def test_unavailable_without_janma(self):
        self.assertEqual(_chandra_bala_grade_for(self.MOON_RASI, None),
                         ChandraBala.UNAVAILABLE)


class TestComputeAdjuncts(unittest.TestCase):
    def test_bundle_with_and_without_janma(self):
        dt = datetime(2026, 9, 16)
        info = compute_adjuncts(dt, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ,
                                janma_nakshatra=Nakshatra.ASVINI)
        self.assertEqual(len(info.durmuhurta), 2)
        self.assertEqual(info.chandra_bala, self._expected_chandra())
        self.assertIsNotNone(info.tara_bala)
        self.assertIn(info.tara_auspicious, (True, False))
        self.assertEqual(len(info.panchaka), len(_panchaka_segments(
            dt, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)))

        bare = compute_adjuncts(dt, CHENNAI_LAT, CHENNAI_LON, CHENNAI_TZ)
        self.assertIs(bare.chandra_bala, ChandraBala.UNAVAILABLE)
        self.assertIsNone(bare.tara_bala)
        self.assertFalse(bare.tara_auspicious)

    def _expected_chandra(self):
        # Janma Ashvini (Aries), Moon in Capricorn -> 10th -> Good.
        return ChandraBala.GOOD


class TestAdjunctScoring(unittest.TestCase):
    """Tasks 3.1/3.2: adjunct penalties/rewards change candidate scores cleanly."""

    def test_adjunct_durmuhurta_penalty_against_offset_moment(self):
        # Chennai, Tue 2026-09-15: 21:00 is inside the second Durmuhurta window
        # (20:53-21:32) while 20:30 shares its Rahita segment and all other flags.
        inside = evaluate_time(datetime(2026, 9, 15, 21, 0), CHENNAI_LAT,
                               CHENNAI_LON, CHENNAI_TZ, MuhurtaTask.GENERAL)
        offset = evaluate_time(datetime(2026, 9, 15, 20, 30), CHENNAI_LAT,
                               CHENNAI_LON, CHENNAI_TZ, MuhurtaTask.GENERAL)
        self.assertIn("Durmuhurta!", inside.score_detail)
        self.assertNotIn("Durmuhurta!", offset.score_detail)
        self.assertLess(inside.score, offset.score)
        self.assertAlmostEqual(offset.score - inside.score, 0.15, places=6)

    def test_adjunct_rahita_beats_non_rahita_neighbor(self):
        # Same day: 18:10 is inside the Roga segment (16:40-18:20) while 18:30 is
        # in the adjacent Rahita segment (18:20-21:40); all other flags are equal.
        avoid = evaluate_time(datetime(2026, 9, 15, 18, 10), CHENNAI_LAT,
                              CHENNAI_LON, CHENNAI_TZ, MuhurtaTask.GENERAL)
        good = evaluate_time(datetime(2026, 9, 15, 18, 30), CHENNAI_LAT,
                             CHENNAI_LON, CHENNAI_TZ, MuhurtaTask.GENERAL)
        self.assertIn("Roga Panchaka!", avoid.score_detail)
        self.assertNotIn("Panchaka!", good.score_detail)
        self.assertGreater(good.score, avoid.score)
        self.assertAlmostEqual(good.score - avoid.score, 0.10, places=6)


class TestMuhurtaAdjunctCLI(unittest.TestCase):
    """Tasks 4.1/4.2: --adjuncts prints the binary-style table; defaults stay clean."""

    _ARGS = ["muhurta", "2026-09-16", "10:00", "13.0827", "80.2707",
             "--tz", "+0530"]

    def test_cli_adjuncts_reports_binary_style_table(self):
        from jhora.cli.main import app

        result = CliRunner().invoke(app, self._ARGS + [
            "--adjuncts", "--janma-nakshatra", "Magha"])
        self.assertEqual(result.exit_code, 0, result.output)
        for label in ("DurMuhurta1", "DurMuhurta2", "Varjya1", "Varjya2",
                      "Sunrise", "Sunset", "Panchaka Segments",
                      "Chandra Bala:", "Tara Bala:"):
            self.assertIn(label, result.output)

    def test_cli_adjuncts_janma_ignored_without_flag(self):
        from jhora.cli.main import app

        runner = CliRunner()
        default = runner.invoke(app, self._ARGS)
        janma_only = runner.invoke(app, self._ARGS + ["--janma-nakshatra", "Magha"])
        self.assertEqual(default.exit_code, 0, default.output)
        self.assertEqual(janma_only.exit_code, 0, janma_only.output)
        self.assertEqual(janma_only.output, default.output)
        self.assertNotIn("DurMuhurta1", default.output)


if __name__ == "__main__":
    unittest.main()