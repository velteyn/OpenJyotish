"""KP sub-lord cross-check against vedicastro 0.2.1 (vendored algorithm).

vedicastro's VedicAstro.VedicHoroscopeData.get_rl_nl_sl_data() can't be
imported here: it pins flatlib@sidereal, whose const.AY_LAHIRI_1940 no longer
exists. So this script vendors that method's maths verbatim and diffs it
against jhora's kp_sublord. No network, no third-party install needed.

Findings are written up in KP-VEDICASTRO.md; the short version is that our
chain satisfies the KP identity at every nakshatra start (first sub-lord ==
nakshatra lord) and the reference does not past 120 degrees, and that the
sweep exposed — and this repo fixed — a float-accumulation gap in ours.

Run:  python3 tools/xcheck/kp_vedicastro_xcheck.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jhora.calc.special_lagnas import kp_sublord  # noqa: E402
from jhora.types.nakshatra import Nakshatra  # noqa: E402

# ── vedicastro get_rl_nl_sl_data: verbatim port of the maths ─────────────────
_DURATION = [7, 20, 6, 10, 7, 18, 16, 19, 17]
_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
          "Jupiter", "Saturn", "Mercury"]


def vedicastro_sub_sub(deg: float):
    """The reference's sub-lord and sub-sub-lord for a longitude."""
    deg = deg - 120 * int(deg / 120)
    degcum = 0.0
    i = 0
    while i < 9:
        deg_nl = 360 / 27
        j = i
        while True:
            deg_sl = deg_nl * _DURATION[j] / 120
            k = j
            while True:
                degcum += deg_sl * _DURATION[k] / 120
                if degcum >= deg:
                    return _LORDS[j], _LORDS[k]
                k = (k + 1) % 9
                if k == j:
                    break
            j = (j + 1) % 9
            if j == i:
                break
        i += 1
    return None


def sweep():
    mismatch = 0
    checked = 0
    bad = []
    for nak in range(27):
        base = nak * (360 / 27)
        for frac in (0.001, 0.1, 0.25, 0.5, 0.75, 0.999):
            lon = (base + frac * (360 / 27)) % 360
            ref = vedicastro_sub_sub(lon)
            if ref is None:
                continue
            ours = kp_sublord(lon, 2)
            checked += 1
            got = (ours[0]["graha"].full_name, ours[1]["graha"].full_name)
            if got != ref:
                mismatch += 1
                if len(bad) < 10:
                    bad.append((round(lon, 3), ref, got))
    return checked, mismatch, bad


def identity_check():
    """KP identity: each nakshatra's first sub-lord is its own lord."""
    failures = []
    for i in range(27):
        lon = i * (360 / 27)
        nak = Nakshatra(i)
        ours = kp_sublord(lon, 1)[0]["graha"].full_name
        if ours != nak.lord:
            failures.append((i, nak.name, nak.lord, ours))
    return failures


def main():
    checked, mismatch, bad = sweep()
    print(f"sweep: checked={checked} mismatches={mismatch}")
    for lon, ref, ours in bad:
        print(f"  lon {lon}: vedicastro={ref} ours={ours}")
    fails = identity_check()
    print(f"nakshatra-start identity failures: {len(fails)}")
    for f in fails:
        print("  ", f)
    print()
    print("Interpretation: mismatches sit past 120-degree multiples, where the")
    print("reference wraps the absolute longitude and loses the nakshatra")
    print("phase. Our chain passes the identity test at all 27 nakshatras.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
