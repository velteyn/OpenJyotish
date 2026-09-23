"""Narayana-family dasa variants: Lagnamsaka and Padanaathaamsa.

Both share the Narayana progression, period-length and antardasa rules
(``NarayanaDasa``); they differ only in the **seed sign**:

- **Lagnamsaka** seeds from the **lagna** sign — the dasa of the lagna itself.
- **Padanaathaamsa** seeds from the sign occupied by the **lord of the Arudha
  Lagna** (pada = arudha, natha = lord, amsa = sign): the dispositor of the AL.

Rule implemented here: Padanaathaamsa reads the chart's Arudha Lagna,
takes its sign-lord from the sign-lord table, and seeds from the lord's
sign; Lagnamsaka seeds from the lagna sign — the Narayana-family seed
variants as taught in the mainstream source below.

Mainstream source: Sanjay Rath, *Narayana Dasa* (Sagar / Sagittarius
Publications), chapters "Lagnamsaka Dasa" and "Padanadhamsa Dasa".
"""

from jhora.calc.arudha import bhava_arudha
from jhora.calc.jaimini_strength import chart_signs_lons, stronger_rasi
from jhora.dasas.narayana import NarayanaDasa, _LORD_NAME_TO_GRAHA
from jhora.types.rasi import Rasi


class LagnamsakaDasa(NarayanaDasa):
    """Narayana-family dasa seeded from the stronger of the lagna and its 7th.

    The reference resolves the lagna/7th seed through its sign-strength
    ladder (the "satya-peetha" rule); ``stronger_rasi`` reproduces that
    exactly.
    """

    system_name = "lagnamsaka"

    def _seed_rasi(self, lagna_rasi: Rasi, planets, chart, opts) -> Rasi:
        signs, lons = chart_signs_lons(chart)
        seventh = (lagna_rasi.value + 6) % 12
        return Rasi(stronger_rasi(lagna_rasi.value, seventh, signs, lons))


class PadanaathaamsaDasa(NarayanaDasa):
    """Narayana-family dasa seeded from the lord of the Arudha Lagna."""

    system_name = "padanaathaamsa"

    def _seed_rasi(self, lagna_rasi: Rasi, planets, chart, opts) -> Rasi:
        arudha_lagna = bhava_arudha(1, chart["lagna_lon"], planets)
        lord = _LORD_NAME_TO_GRAHA.get(arudha_lagna.lord)
        return Rasi.from_longitude(planets[lord]["longitude"])
