"""Planetary hours (Hora) — sequence, continuity and current-hora."""

from datetime import datetime, timedelta

from jhora.calc.hora import (
    CHALDEAN, WEEKDAY_LORD, hora_slots, current_hora,
)
from jhora.types.graha import Graha

LAT, LON, TZ = 12.97, 77.59, 5.5


def test_first_hora_is_the_weekday_lord():
    # 2026-09-22 is a Tuesday (day lord Mars).
    slots = hora_slots(datetime(2026, 9, 22), LAT, LON, TZ)
    assert len(slots) == 24
    assert slots[0].lord == Graha.MARS
    assert slots[0].part == "Day"


def test_chaldean_sequence():
    slots = hora_slots(datetime(2026, 9, 22), LAT, LON, TZ)  # Tuesday
    start = CHALDEAN.index(Graha.MARS)
    for i, slot in enumerate(slots):
        assert slot.lord == CHALDEAN[(start + i) % 7]


def test_day_and_night_are_twelve_each_and_contiguous():
    slots = hora_slots(datetime(2026, 9, 22), LAT, LON, TZ)
    assert sum(s.part == "Day" for s in slots) == 12
    assert sum(s.part == "Night" for s in slots) == 12
    for a, b in zip(slots, slots[1:]):
        assert a.end == b.start


def test_next_day_first_hora_wraps_to_the_next_lord():
    slots = hora_slots(datetime(2026, 9, 22), LAT, LON, TZ)  # Tuesday
    wed = hora_slots(datetime(2026, 9, 23), LAT, LON, TZ)    # Wednesday
    assert slots[-1].end == wed[0].start
    assert wed[0].lord == WEEKDAY_LORD[3] == Graha.MERCURY


def test_current_hora_contains_the_moment():
    moment = datetime(2026, 9, 22, 12, 0)
    slot = current_hora(moment, LAT, LON, TZ)
    assert slot is not None
    assert slot.start <= moment < slot.end


def test_pre_sunrise_belongs_to_previous_night():
    # 03:30 on the 23rd falls in the 22nd's night horas.
    moment = datetime(2026, 9, 23, 3, 30)
    slot = current_hora(moment, LAT, LON, TZ)
    assert slot is not None
    assert slot.part == "Night"
    assert slot.start >= datetime(2026, 9, 22, 18, 0)
