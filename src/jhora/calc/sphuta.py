"""Sphutas — Prasna Marga auspicious-point longitudes.

Pure functions of explicit longitudes (degrees, any sidereal frame as long
as inputs share it); all results modulo 360. Formulas per Prasna Marga
Chapter V (B.V. Raman lineage); Beeja/Kshetra planet sets per standard
teaching. Proven against a worked JHora-lineage example (see tests).

Gulika is passed in (temporal upagrahas), never computed here, keeping this
module free of ephemeris and of Gulika-convention questions.
"""

from typing import Dict


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
    }
