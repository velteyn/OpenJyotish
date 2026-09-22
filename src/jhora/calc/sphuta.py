"""Sphutas — Prasna Marga auspicious-point longitudes.

Pure functions of explicit longitudes (degrees, any sidereal frame as long
as inputs share it); all results modulo 360. Formulas per Prasna Marga
Chapter V (B.V. Raman lineage); Beeja/Kshetra planet sets per standard
teaching. Proven against a worked example (see tests).

Also the Yogi family: Yoga Sphuta = Sun + Moon; Tithi Sphuta = Moon − Sun;
Rahu Tithi Sphuta = Rahu − Sun; Yogi Sphuta = Yoga + 93°20' (Yogi planet =
its nakshatra lord); Avayoga Sphuta = Yogi + 186°40' (Avayogi planet = its
nakshatra lord); Sahayogi (Duplicate Yogi) = the sign lord of the Yogi point.

Gulika is passed in (temporal upagrahas), never computed here, keeping this
module free of ephemeris and of Gulika-convention questions.
"""

from typing import Dict

from jhora.types.nakshatra import Nakshatra
from jhora.types.rasi import Rasi

#: Yogi point advances seven nakshatras (93°20') past the Yoga point.
YOGI_OFFSET = 93.0 + 20.0 / 60.0
#: Avayoga point advances fourteen nakshatras (186°40') past the Yoga point.
AVAYOGI_OFFSET = 186.0 + 40.0 / 60.0


def trisphuta(lagna: float, moon: float, gulika: float) -> float:
    """Thrisphuta: Lagna + Moon + Gulika."""
    return (lagna + moon + gulika) % 360.0


def chatusphuta(trisphuta_lon: float, sun: float) -> float:
    """Chatusphuta: Thrisphuta + Sun."""
    return (trisphuta_lon + sun) % 360.0


def panchasphuta(chatusphuta_lon: float, rahu: float) -> float:
    """Panchasphuta: Chatusphuta + Rahu."""
    return (chatusphuta_lon + rahu) % 360.0


def prana_sphuta(lagna: float, gulika: float) -> float:
    """Prana Sphuta (life breath): 5 * Lagna + Gulika."""
    return (lagna * 5.0 + gulika) % 360.0


def deha_sphuta(moon: float, gulika: float) -> float:
    """Deha Sphuta (body): 8 * Moon + Gulika."""
    return (moon * 8.0 + gulika) % 360.0


def mrityu_sphuta(gulika: float, sun: float) -> float:
    """Mrityu Sphuta (death): 7 * Gulika + Sun."""
    return (gulika * 7.0 + sun) % 360.0


def beeja_sphuta(jupiter: float, venus: float, sun: float) -> float:
    """Beeja Sphuta (seed): Jupiter + Venus + Sun."""
    return (jupiter + venus + sun) % 360.0


def kshetra_sphuta(jupiter: float, moon: float, mars: float) -> float:
    """Kshetra Sphuta (field): Jupiter + Moon + Mars."""
    return (jupiter + moon + mars) % 360.0


def yoga_sphuta(sun: float, moon: float) -> float:
    """Yoga Sphuta: Sun + Moon (the yoga point)."""
    return (sun + moon) % 360.0


def tithi_sphuta(moon: float, sun: float) -> float:
    """Tithi Sphuta: Moon − Sun (the lunar-day longitude)."""
    return (moon - sun) % 360.0


def rahu_tithi_sphuta(rahu: float, sun: float) -> float:
    """Rahu Tithi Sphuta: Rahu − Sun."""
    return (rahu - sun) % 360.0


def yogi_sphuta(sun: float, moon: float) -> float:
    """Yogi Sphuta: the Yoga point (Sun + Moon) + 93°20' (7 nakshatras)."""
    return (sun + moon + YOGI_OFFSET) % 360.0


def avayoga_sphuta(sun: float, moon: float) -> float:
    """Avayoga Sphuta: the Yogi Sphuta + 186°40' (Yoga + 280°)."""
    return (sun + moon + YOGI_OFFSET + AVAYOGI_OFFSET) % 360.0


def yogi_planet(moon: float, sun: float) -> str:
    """Yogi planet: the lord of the nakshatra of the Yogi Sphuta."""
    return Nakshatra.from_longitude(yogi_sphuta(sun, moon))[0].lord


def avayogi_planet(moon: float, sun: float) -> str:
    """Avayogi planet: the lord of the nakshatra of the Avayoga Sphuta."""
    return Nakshatra.from_longitude(avayoga_sphuta(sun, moon))[0].lord


def sahayogi_planet(moon: float, sun: float) -> str:
    """Sahayogi (Duplicate Yogi): the sign lord of the Yogi point."""
    return Rasi.from_longitude(yogi_sphuta(sun, moon)).lord


def compute_yogi(moon: float, sun: float) -> Dict[str, str]:
    """The Yogi / Avayogi / Sahayogi planets (Prasna Marga)."""
    return {
        "Yogi": yogi_planet(moon, sun),
        "Avayogi": avayogi_planet(moon, sun),
        "Sahayogi": sahayogi_planet(moon, sun),
    }


def compute_sphutas(lagna: float, sun: float, moon: float, mars: float,
                    jupiter: float, venus: float, rahu: float,
                    gulika: float) -> Dict[str, float]:
    """All nine Sphutas in dependency order."""
    tri = trisphuta(lagna, moon, gulika)
    chat = chatusphuta(tri, sun)
    return {
        "Trisphuta": tri,
        "Chatusphuta": chat,
        "Panchasphuta": panchasphuta(chat, rahu),
        "Prana": prana_sphuta(lagna, gulika),
        "Deha": deha_sphuta(moon, gulika),
        "Mrityu": mrityu_sphuta(gulika, sun),
        "Beeja": beeja_sphuta(jupiter, venus, sun),
        "Kshetra": kshetra_sphuta(jupiter, moon, mars),
        "Yoga": yoga_sphuta(sun, moon),
        "Tithi": tithi_sphuta(moon, sun),
        "RahuTithi": rahu_tithi_sphuta(rahu, sun),
        "Yogi": yogi_sphuta(sun, moon),
        "Avayoga": avayoga_sphuta(sun, moon),
    }
