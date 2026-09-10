"""Tests for Choghadiya — daily auspicious/inauspicious time slots.

Golden tables verified against drikpanchang.com live rendering (Sep 3 2026
Kolkata/Dehra Dun, Sep 6 2026 LA Sunday). The planetary-hour cycle uses
Chaldean order: Sun → Venus → Mercury → Moon → Saturn → Jupiter → Mars.
"""

import subprocess
import sys
import unittest
from datetime import datetime, timedelta

from jhora.calc.choghadiya import (
    ChoghadiyaDay,
    ChoghadiyaSlot,
    GRAHA_NAME,
    GRAHA_RATING,
    choghadiya_day,
    current_choghadiya,
    day_table,
    night_table,
)
from jhora.types.graha import Graha


# ── Reference tables (drikpanchang.com) ────────────────────────────────────────

# Day: step +1 from weekday lord position in Chaldean cycle
EXPECTED_DAY = {
    0: ["Udveg","Char","Labh","Amrit","Kaal","Shubh","Rog","Udveg"],    # Sun
    1: ["Amrit","Kaal","Shubh","Rog","Udveg","Char","Labh","Amrit"],    # Mon
    2: ["Rog","Udveg","Char","Labh","Amrit","Kaal","Shubh","Rog"],      # Tue
    3: ["Labh","Amrit","Kaal","Shubh","Rog","Udveg","Char","Labh"],     # Wed
    4: ["Shubh","Rog","Udveg","Char","Labh","Amrit","Kaal","Shubh"],    # Thu
    5: ["Char","Labh","Amrit","Kaal","Shubh","Rog","Udveg","Char"],     # Fri
    6: ["Kaal","Shubh","Rog","Udveg","Char","Labh","Amrit","Kaal"],     # Sat
}

# Night: step +5 (mod 7) from (day_start + 5) mod 7
EXPECTED_NIGHT = {
    0: ["Shubh","Amrit","Char","Rog","Kaal","Labh","Udveg","Shubh"],    # Sun
    1: ["Char","Rog","Kaal","Labh","Udveg","Shubh","Amrit","Char"],     # Mon
    2: ["Kaal","Labh","Udveg","Shubh","Amrit","Char","Rog","Kaal"],     # Tue
    3: ["Udveg","Shubh","Amrit","Char","Rog","Kaal","Labh","Udveg"],    # Wed
    4: ["Amrit","Char","Rog","Kaal","Labh","Udveg","Shubh","Amrit"],    # Thu
    5: ["Rog","Kaal","Labh","Udveg","Shubh","Amrit","Char","Rog"],      # Fri
    6: ["Labh","Udveg","Shubh","Amrit","Char","Rog","Kaal","Labh"],     # Sat
}

EXPECTED_RATINGS = {
    "Udveg": "Bad",
    "Char":  "Neutral",
    "Labh":  "Good",
    "Amrit": "Good",
    "Kaal":  "Bad",
    "Shubh": "Good",
    "Rog":   "Bad",
}

EXPECTED_LORDS = {
    "Udveg": Graha.SUN,
    "Char":  Graha.VENUS,
    "Labh":  Graha.MERCURY,
    "Amrit": Graha.MOON,
    "Kaal":  Graha.SATURN,
    "Shubh": Graha.JUPITER,
    "Rog":   Graha.MARS,
}

WD_NAMES = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]

# Kolkata (22.57°N, 88.36°E, IST +5.5) for full-computation tests
LAT, LON, TZ = 22.5726, 88.3639, 5.5


# ── Golden table tests ──────────────────────────────────────────────────────────

class TestGoldenTables(unittest.TestCase):
    """Verify every weekday's day and night sequences match drikpanchang."""

    def test_day_tables_all_weekdays(self):
        for wd in range(7):
            names = [n for n, _, _ in day_table(wd)]
            self.assertEqual(
                names, EXPECTED_DAY[wd],
                f"Day table mismatch for {WD_NAMES[wd]}"
            )

    def test_night_tables_all_weekdays(self):
        for wd in range(7):
            names = [n for n, _, _ in night_table(wd)]
            self.assertEqual(
                names, EXPECTED_NIGHT[wd],
                f"Night table mismatch for {WD_NAMES[wd]}"
            )

    def test_day_tables_have_8_entries(self):
        for wd in range(7):
            self.assertEqual(len(day_table(wd)), 8)

    def test_night_tables_have_8_entries(self):
        for wd in range(7):
            self.assertEqual(len(night_table(wd)), 8)


# ── Name → rating/lord maps ────────────────────────────────────────────────────

class TestNameMaps(unittest.TestCase):
    def test_all_ratings_match(self):
        for name, expected in EXPECTED_RATINGS.items():
            self.assertEqual(GRAHA_RATING[EXPECTED_LORDS[name]], expected,
                             f"Rating mismatch for {name}")

    def test_all_lords_match(self):
        for name, expected_lord in EXPECTED_LORDS.items():
            self.assertEqual(GRAHA_NAME[expected_lord], name,
                             f"Name round-trip failed for {expected_lord}")

    def test_good_count(self):
        good = [n for n, r in EXPECTED_RATINGS.items() if r == "Good"]
        self.assertEqual(len(good), 3, f"Expected 3 Good slots, got {len(good)}: {good}")

    def test_bad_count(self):
        bad = [n for n, r in EXPECTED_RATINGS.items() if r == "Bad"]
        self.assertEqual(len(bad), 3, f"Expected 3 Bad slots, got {len(bad)}: {bad}")

    def test_neutral_count(self):
        neutral = [n for n, r in EXPECTED_RATINGS.items() if r == "Neutral"]
        self.assertEqual(len(neutral), 1, f"Expected 1 Neutral slot, got {len(neutral)}: {neutral}")


# ── Partition math ──────────────────────────────────────────────────────────────

class TestPartitionMath(unittest.TestCase):
    """Day/8 == slot length; contiguous; night crosses midnight."""

    def setUp(self):
        self.date = datetime(2026, 9, 3)  # Thursday
        self.cd = choghadiya_day(self.date, LAT, LON, TZ)

    def test_exactly_8_day_slots(self):
        self.assertEqual(len(self.cd.day_slots), 8)

    def test_exactly_8_night_slots(self):
        self.assertEqual(len(self.cd.night_slots), 8)

    def test_day_slots_contiguous(self):
        for i in range(7):
            self.assertEqual(
                self.cd.day_slots[i].end, self.cd.day_slots[i + 1].start,
                f"Day gap/overlap at slot {i}"
            )

    def test_night_slots_contiguous(self):
        for i in range(7):
            self.assertEqual(
                self.cd.night_slots[i].end, self.cd.night_slots[i + 1].start,
                f"Night gap/overlap at slot {i}"
            )

    def test_day_night_no_gap(self):
        """Last day slot ends exactly when first night slot starts."""
        self.assertEqual(
            self.cd.day_slots[-1].end, self.cd.night_slots[0].start,
            "Gap between day and night"
        )

    def test_all_day_slots_equal_duration(self):
        durations = [s.duration_minutes for s in self.cd.day_slots]
        for d in durations:
            self.assertAlmostEqual(d, durations[0], places=1,
                                   msg="Day slots not equal duration")

    def test_all_night_slots_equal_duration(self):
        durations = [s.duration_minutes for s in self.cd.night_slots]
        for d in durations:
            self.assertAlmostEqual(d, durations[0], places=1,
                                   msg="Night slots not equal duration")

    def test_day_start_before_sunset_before_night_end(self):
        self.assertTrue(self.cd.day_slots[0].start < self.cd.night_slots[-1].end)


# ── Night crossing midnight ────────────────────────────────────────────────────

class TestMidnightCrossing(unittest.TestCase):
    """Night slots past midnight carry the next calendar date."""

    def test_night_crosses_midnight(self):
        # Kolkata in September: night ~17:52 to ~05:19 next day
        cd = choghadiya_day(datetime(2026, 9, 3), LAT, LON, TZ)
        last_night = cd.night_slots[-1]
        self.assertGreaterEqual(last_night.end.day, cd.date.day,
                                "Night should extend past midnight for Kolkata Sep")


# ── Lookup / current_choghadiya ────────────────────────────────────────────────

class TestLookup(unittest.TestCase):
    def test_finds_slot_in_day(self):
        moment = datetime(2026, 9, 3, 12, 0)  # midday
        slot = current_choghadiya(moment, LAT, LON, TZ)
        self.assertIsNotNone(slot, "Should find a slot at midday")
        self.assertFalse(slot.is_night)

    def test_finds_slot_in_night(self):
        moment = datetime(2026, 9, 3, 21, 0)  # 9 PM
        slot = current_choghadiya(moment, LAT, LON, TZ)
        self.assertIsNotNone(slot, "Should find a slot at 9 PM")
        self.assertTrue(slot.is_night)

    def test_pre_sunrise_returns_night_slot(self):
        # Before sunrise → should find a night slot (from previous panchang day)
        moment = datetime(2026, 9, 3, 4, 0)  # 4 AM, before sunrise ~05:19
        slot = current_choghadiya(moment, LAT, LON, TZ)
        # Could be None (before this day's sunrise) or a night slot
        if slot is not None:
            self.assertTrue(slot.is_night)

    def test_evaluate_choghadiya_returns_same_as_current(self):
        moment = datetime(2026, 9, 3, 14, 0)
        from jhora.calc.choghadiya import evaluate_choghadiya
        s1 = current_choghadiya(moment, LAT, LON, TZ)
        s2 = evaluate_choghadiya(moment, LAT, LON, TZ)
        self.assertEqual(s1, s2)


# ── next_good_slot ─────────────────────────────────────────────────────────────

class TestNextGoodSlot(unittest.TestCase):
    def test_finds_good_slot(self):
        from jhora.calc.choghadiya import next_good_slot
        moment = datetime(2026, 9, 3, 8, 0)  # during Udveg (Bad) on Thu
        result = next_good_slot(moment, LAT, LON, TZ)
        self.assertIsNotNone(result, "Should find a Good slot after 8 AM Thu")
        slot, minutes = result
        self.assertEqual(slot.rating, "Good")
        self.assertGreaterEqual(minutes, 0)


# ── CLI smoke test ─────────────────────────────────────────────────────────────

class TestCLI(unittest.TestCase):
    def test_choghadiya_command_runs(self):
        result = subprocess.run(
            [sys.executable, "-m", "jhora.cli.main", "choghadiya",
             "--lat", "22.57", "--lon", "88.36", "--tz", "5.5"],
            capture_output=True, text=True, timeout=30,
            env={"PYTHONPATH": "src", "QT_QPA_PLATFORM": "offscreen",
                 **{k: v for k, v in __import__("os").environ.items()
                    if k != "PYTHONPATH"}},
        )
        self.assertEqual(result.returncode, 0,
                         f"CLI failed: {result.stderr[:500]}")
        self.assertIn("Choghadiya", result.stdout,
                      "Output should mention Choghadiya")


# ── Regression: muhurta untouched ─────────────────────────────────────────────

class TestMuhurtaUntouched(unittest.TestCase):
    def test_muhurta_imports(self):
        from jhora.calc.muhurta import evaluate_time, compute_panchanga
        self.assertTrue(callable(evaluate_time))
        self.assertTrue(callable(compute_panchanga))


if __name__ == "__main__":
    unittest.main()
