"""South Indian chart: signs occupy fixed cells, Aries top row 2nd column,
running clockwise to Pisces in the top-left corner."""
from jhora.types.rasi import Rasi
from jhora.ui.chart_widget import _SOUTH_INDIAN_GRID

# Perimeter cells of the 4x4 grid, clockwise starting at (0, 1).
_CLOCKWISE_FROM_ARIES = [
    (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 3),
    (3, 2), (3, 1), (3, 0), (2, 0), (1, 0), (0, 0),
]


def _cell_of():
    return {rasi: (row, col) for row, col, rasi in _SOUTH_INDIAN_GRID}


def test_every_rasi_once_on_perimeter():
    cells = [(r, c) for r, c, _ in _SOUTH_INDIAN_GRID]
    assert len(_SOUTH_INDIAN_GRID) == 12
    assert set(_cell_of()) == set(Rasi)
    assert sorted(cells) == sorted(_CLOCKWISE_FROM_ARIES)


def test_fixed_anchor_cells():
    cell = _cell_of()
    assert cell[Rasi.PISCES] == (0, 0)
    assert cell[Rasi.ARIES] == (0, 1)
    assert cell[Rasi.GEMINI] == (0, 3)
    assert cell[Rasi.VIRGO] == (3, 3)
    assert cell[Rasi.SAGITTARIUS] == (3, 0)


def test_zodiac_runs_clockwise():
    rasi_at = {(r, c): rasi for r, c, rasi in _SOUTH_INDIAN_GRID}
    order = [rasi_at[pos] for pos in _CLOCKWISE_FROM_ARIES]
    assert order == [Rasi(i) for i in range(12)]
