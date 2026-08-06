"""Robustness of the cause-or-cover signal to the choice of neutral benchmark.

The Netherlands is not a *far* neutral — it borders Germany and would price
invasion risk in a European war. Genuine far neutrals are the US, Sweden,
Switzerland (money market) and the US (bond). If the finance-as-constraint signal
is real it should survive whichever neutral we subtract; if it depends on the
neutral, it is at the noise floor. This runs the neutral-benchmark percentile for
each power against several neutrals and shows the scatter.

    python neutral_robustness.py
"""

from __future__ import annotations

import datetime
import importlib.util
import os
import sys

import cause_or_cover as cc

_HERE = os.path.dirname(os.path.abspath(__file__))
SHORT = os.path.join(_HERE, "..", "neal_weidenmier", "data", "stinterestrates.xls")
BONDS = os.path.join(_HERE, "..", "neal_weidenmier", "data", "longtermbonds.xls")

# crisis -> (climbing-down power series, onset)
ONSETS = {
    "Morocco/Fr": ("france", "1905-03-31"),
    "Bosnia/Ru": ("russia", "1908-10-06"),
    "Agadir/Ge": ("germany", "1911-07-01"),
    "Balkans/Au": ("austria_hungary", "1912-10-08"),
}


def _load_builder():
    spec = importlib.util.spec_from_file_location("b", os.path.join(_HERE, "build_nw_spreads.py"))
    b = importlib.util.module_from_spec(spec)
    sys.path.insert(0, _HERE)
    spec.loader.exec_module(b)
    return b


def money_market_table(window: int = 180):
    sys.path.insert(0, os.path.join(_HERE, "..", "neal_weidenmier", "src"))
    from neal_weidenmier.load import load_short_rates

    obs = load_short_rates(SHORT)
    def S(city, rt):
        return [(o.date, o.value) for o in obs if o.city == city and o.rate_type == rt]

    powers = {"germany": ("Berlin", "Open Mkt"), "france": ("Paris", "Open Mkt"),
              "austria_hungary": ("Vienna", "Open Mkt"), "russia": ("Petersburg", "Bank")}
    neutrals = {"Amsterdam(near)": ("Amsterdam", "Open Mkt"), "Switzerland": ("Geneva", "Market"),
                "Sweden": ("Stockholm", "Market"), "US(call)": ("New York", "call")}
    out = {}
    for nname, (nc, nr) in neutrals.items():
        neut = S(nc, nr)
        row = {}
        for crisis, (pser, od) in ONSETS.items():
            _e, p, _n = cc.neutral_benchmark_check({pser: S(*powers[pser]), "dutch": neut}, pser, od, window)
            row[crisis] = p
        out[nname] = row
    return out


def bond_table(window: int = 270):
    b = _load_builder()
    data = b._text_dates_and_prices(BONDS)
    import xlrd
    from neal_weidenmier.load import true_date
    wb = xlrd.open_workbook(BONDS); sh = wb.sheet_by_name("YIELDS")

    def dt(r):
        c = sh.cell(r, 0)
        if c.ctype == 3:
            try:
                return true_date(xlrd.xldate.xldate_as_datetime(c.value, wb.datemode).date())
            except Exception:
                return None
        if c.ctype == 1 and "/" in str(c.value):
            try:
                return datetime.datetime.strptime(c.value.strip(), "%d/%m/%Y").date()
            except ValueError:
                return None
        return None

    def ycol(col):
        return [(dt(r), sh.cell_value(r, col)) for r in range(6, sh.nrows)
                if dt(r) and isinstance(sh.cell_value(r, col), (int, float)) and sh.cell_value(r, col) != ""]

    neutrals = {"Dutch": ycol(26), "US-bond": ycol(23), "Italian": ycol(24)}
    pow_cols = {"russia": (15, 4.0), "germany": (28, 3.0), "austria_hungary": (24, 4.0), "france": (7, 3.0)}
    powyield = {p: [(d, coup / data[d][col] * 100) for d in sorted(data) if data[d].get(col)]
                for p, (col, coup) in pow_cols.items()}
    out = {}
    for nname, neut in neutrals.items():
        row = {}
        for crisis, (pser, od) in ONSETS.items():
            _e, p, _n = cc.neutral_benchmark_check({pser: powyield[pser], "dutch": neut}, pser, od, window)
            row[crisis] = p
        out[nname] = row
    return out


def _print(title, table):
    print(title)
    print(f"  {'neutral':<16}" + "".join(f"{c:>12}" for c in ONSETS))
    for nname, row in table.items():
        print(f"  {nname:<16}" + "".join(f"{(f'{row[c]:.0f}%' if row[c] is not None else '—'):>12}" for c in ONSETS))
    print()


def main() -> int:
    _print("MONEY-MARKET cause-or-cover percentile @180d, by neutral:", money_market_table())
    _print("BOND cause-or-cover percentile @270d, by neutral:", bond_table())
    print("Robust across neutrals: France = calm in the money market (low everywhere);")
    print("Austria = repriced in bonds (high vs every bond neutral). Everything else scatters")
    print("-> the per-country signal is at the noise floor; do not claim it per country.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
