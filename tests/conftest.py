"""Shared fixtures and test data."""

from datetime import datetime
from typing import Dict, Tuple

import pytest

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.charts.varga import VargaChartComputer
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.varga import VargaLevel, VargaVariant


# Reference birth chart (1970-04-04 17:48:20 +0530, Chennai)
# Used throughout the project for testing
REF_BIRTH = dict(
    year=1970, month=4, day=4,
    hour=17 + 48/60 + 20/3600,
    lat=13.08, lon=80.27,
    tz="+0530", ayanamsa="lahiri",
)


def approx(val: float, ref: float, eps: float = 0.5) -> bool:
    """Check if val is within eps of ref."""
    return abs(val - ref) < eps


@pytest.fixture(scope="session")
def ref_chart() -> ChartData:
    """Build the reference chart once per session."""
    builder = ChartBuilder()
    return builder.build(**REF_BIRTH)


@pytest.fixture(scope="session")
def ref_navamsa(ref_chart):
    """Pre-compute navamsa positions for reference chart."""
    comp = VargaChartComputer()
    return comp.compute(ref_chart, VargaLevel.D_9, VargaVariant.DEFAULT)


# Expected rasi positions (approximate, sidereal Lahiri)
# Used as smoke-test references; exact values vary by ephemeris version
EXPECTED_RASI: Dict[Graha, Tuple[str, float, str]] = {
    Graha.SUN:     ("Pisces", 21.1, "neutral"),
    Graha.MOON:    ("Pisces", 1.9, "neutral"),
    Graha.MARS:    ("Aries", 3.6, "moolatrikona"),
    Graha.MERCURY: ("Aries", 8.2, "neutral"),
    Graha.JUPITER: ("Aries", 26.8, "neutral"),
    Graha.VENUS:   ("Libra", 9.7, "moolatrikona"),
    Graha.SATURN:  ("Aries", 15.1, "debilitated"),
    Graha.RAHU:    ("Aquarius", 18.1, "node"),
    Graha.KETU:    ("Leo", 11.6, "node"),
}

# Expected navamsa rasi for each planet (D-9 default, from sidereal chart)
EXPECTED_NAVAMSA: Dict[Graha, str] = {
    Graha.SUN:     "Capricorn",
    Graha.MOON:    "Cancer",
    Graha.MARS:    "Taurus",
    Graha.MERCURY: "Gemini",
    Graha.JUPITER: "Sagittarius",
    Graha.VENUS:   "Sagittarius",
    Graha.SATURN:  "Leo",
    Graha.RAHU:    "Cancer",
    Graha.KETU:    "Scorpio",
}
