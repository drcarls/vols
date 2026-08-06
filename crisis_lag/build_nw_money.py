"""Build money-market (commercial-paper) stress series from the NW short rates.

Companion to build_nw_spreads.py (which builds long-bond spreads). The book's
financial *brake* is a mobilization-finance mechanism — armies are mobilized on
short-term borrowing, so the binding constraint bites first in the MONEY MARKET
(discount, open-market bills, call money), not in long bonds. Bonds price
solvency; commercial paper prices the immediate cost of raising cash. This emits
the commercial-paper analogues so the lag and cause-or-cover tests can be run on
the instrument that actually carries the brake, and compared to the bond version.

Two files, mirroring the bond builder:
  data/mm_spreads_long.csv : city OPEN-MARKET rate minus the London 3-mo trade
      bill (the paper's basis), rising = tightening = stress. For crisis-lag.
  data/mm_yields_long.csv  : city open-market rate + the Amsterdam open-market
      rate as the neutral money market ('dutch'), for the neutral-benchmark
      control in cause_or_cover.py.

Note the one gap: NW has no St Petersburg OPEN-MARKET rate (only the administered
bank rate, which is sticky — see the Kokovtsov analysis), so 'russia' here is the
policy rate, not a market rate, and must be read with that caveat.

    python build_nw_money.py ../neal_weidenmier/data/stinterestrates.xls
"""

from __future__ import annotations

import csv
import sys

# series id -> (city, rate_type). Open-market where NW has it; Russia only bank.
POWERS = {
    "germany": ("Berlin", "Open Mkt"),
    "france": ("Paris", "Open Mkt"),
    "austria_hungary": ("Vienna", "Open Mkt"),
    "russia": ("Petersburg", "Bank"),   # no open-market rate exists post-1900
}
NEUTRAL = ("Amsterdam", "Open Mkt")     # neutral money market
BASIS = ("London", "3 mo. Trade")        # the Rigobon-Sack basis asset


def _series(obs, city, rt):
    return {o.date: o.value for o in obs if o.city == city and o.rate_type == rt}


def build(short_path: str):
    sys.path.insert(0, "../neal_weidenmier/src")
    from neal_weidenmier.load import load_short_rates

    obs = load_short_rates(short_path)
    london = _series(obs, *BASIS)
    neutral = _series(obs, *NEUTRAL)

    spreads, yields_ = [], []
    for pid, (city, rt) in POWERS.items():
        s = _series(obs, city, rt)
        for d, v in s.items():
            yields_.append((d.isoformat(), pid, round(v, 4)))
            if d in london:
                spreads.append((d.isoformat(), pid, round(v - london[d], 4)))
    for d, v in neutral.items():
        yields_.append((d.isoformat(), "dutch", round(v, 4)))
    return sorted(spreads), sorted(yields_)


def _write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "series", "value"])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {path}")


def main(argv) -> int:
    src = argv[1] if len(argv) > 1 else "../neal_weidenmier/data/stinterestrates.xls"
    spreads, yields_ = build(src)
    _write(argv[2] if len(argv) > 2 else "data/mm_spreads_long.csv", spreads)
    _write(argv[3] if len(argv) > 3 else "data/mm_yields_long.csv", yields_)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
