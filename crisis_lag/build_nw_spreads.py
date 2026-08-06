"""Build a tidy (date, series, value) spread CSV from the Neal-Weidenmier bonds.

Feeds the real Belle-Epoque sovereign spreads into `crisis-lag`, so the asserted
6-10 week onset->peak lag can be *measured* rather than assumed.

Stress measure = sovereign **spread over British consols**, in yield points:

    yield_X   = coupon_X / price_X * 100          (current yield; a monotone
                                                    transform of price, so peak
                                                    *timing* is exact regardless)
    spread_X  = yield_X - yield_British_consol      (isolates country risk from
                                                    the global bond level)

Prices come from the RAW sheet's weekly **text vintage** (the internally
consistent d/m/yyyy series; the sparse Excel-serial rows are a second vintage and
are excluded), decoded exactly as war_premia does. Series ids match the crisis
events: france, russia, germany, austria_hungary.

    python build_nw_spreads.py ../neal_weidenmier/data/longtermbonds.xls data/nw_spreads_long.csv
"""

from __future__ import annotations

import csv
import datetime
import sys
from typing import Dict, Optional

# RAW price columns and coupons. British consol is the benchmark.
BRITISH = ("UK consol", 3, 2.75)
COUNTRIES = {
    "france": ("French 3% rente", 7, 3.0),
    "russia": ("Russian New 4%", 15, 4.0),
    "austria_hungary": ("Austrian Gold 4%", 24, 4.0),
    "germany": ("German Imperial 3%", 28, 3.0),
}


def _text_dates_and_prices(path: str):
    """{date: {col: price}} for the weekly text vintage (d/m/yyyy rows only)."""
    import xlrd

    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_name("RAW")
    cols = [BRITISH[1]] + [c for _, c, _ in COUNTRIES.values()]
    out: Dict[datetime.date, Dict[int, float]] = {}
    for r in range(6, sh.nrows):
        c0 = sh.cell(r, 0)
        if c0.ctype != 1 or "/" not in c0.value:
            continue
        try:
            d = datetime.datetime.strptime(c0.value.strip(), "%d/%m/%Y").date()
        except ValueError:
            continue
        row: Dict[int, float] = {}
        for col in cols:
            cell = sh.cell(r, col)
            if cell.ctype == xlrd.XL_CELL_NUMBER and cell.value:
                row[col] = float(cell.value)
        out[d] = row
    return out


def build(path: str) -> list:
    data = _text_dates_and_prices(path)
    _, bcol, bcoup = BRITISH
    rows = []
    for d in sorted(data):
        prices = data[d]
        bp = prices.get(bcol)
        if not bp:
            continue
        by = bcoup / bp * 100.0
        for series, (_label, col, coup) in COUNTRIES.items():
            p = prices.get(col)
            if not p:
                continue
            spread = coup / p * 100.0 - by
            rows.append((d.isoformat(), series, round(spread, 4)))
    return rows


def main(argv) -> int:
    src = argv[1] if len(argv) > 1 else "../neal_weidenmier/data/longtermbonds.xls"
    dst = argv[2] if len(argv) > 2 else "data/nw_spreads_long.csv"
    rows = build(src)
    with open(dst, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "series", "value"])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
