"""Narayana-family dasa variants: Lagnamsaka and Padanaathaamsa.

Both share the Narayana progression, period-length and antardasa rules
(``NarayanaDasa``); they differ only in the **seed sign**:

- **Lagnamsaka** seeds from the **lagna** sign — the dasa of the lagna itself.
- **Padanaathaamsa** seeds from the sign occupied by the **lord of the Arudha
  Lagna** (pada = arudha, natha = lord, amsa = sign): the dispositor of the AL.

Reference grounding (local RE, 2026-09-22): the binary builders at ``0x414d30``
(Lagnamsaka) and ``0x4151f0`` (Padanaathaamsa) are Narayana-family seed
variants. Padanaathaamsa reads a chart sign field, takes its sign-lord from the
sign-lord table, and seeds from the lord's sign — exactly the rule implemented
here. Lagnamsaka reads the lagna sign; the chart-derived strength table it then
consults is not reproduced (see ``REFERENCE.md``).

Mainstream source: Sanjay Rath, *Narayana Dasa* (Sagar / Sagittarius
Publications), chapters "Lagnamsaka Dasa" and "Padanadhamsa Dasa".
"""

from jhora.calc.arudha import bhava_arudha
from jhora.dasas.narayana import NarayanaDasa, _LORD_NAME_TO_GRAHA
from jhora.types.rasi import Rasi


class LagnamsakaDasa(NarayanaDasa):
    """Narayana-family dasa seeded from the lagna sign."""

    system_name = "lagnamsaka"

    def _seed_rasi(self, lagna_rasi: Rasi, planets, chart, opts) -> Rasi:
        return lagna_rasi


class PadanaathaamsaDasa(NarayanaDasa):
    """Narayana-family dasa seeded from the lord of the Arudha Lagna."""

    system_name = "padanaathaamsa"

    def _seed_rasi(self, lagna_rasi: Rasi, planets, chart, opts) -> Rasi:
        arudha_lagna = bhava_arudha(1, chart["lagna_lon"], planets)
        lord = _LORD_NAME_TO_GRAHA.get(arudha_lagna.lord)
        return Rasi.from_longitude(planets[lord]["longitude"])
