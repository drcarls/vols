"""Reproduce the paper's tables and run the July-1914 extension.

    war-premia reproduce                # Tables 3-7 on the mirrored NW short rates
    war-premia july1914                 # feasibility + the one observable bond change
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from neal_weidenmier.load import load_short_rates, to_series_map

from .july1914 import (
    bond_feasibility,
    crisis_bond_change,
    short_rate_feasibility,
)
from .run import format_table, run_crisis
from .warweeks import CRISES

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SHORT = os.path.join(_ROOT, "neal_weidenmier", "data", "stinterestrates.xls")
BONDS = os.path.join(_ROOT, "neal_weidenmier", "data", "longtermbonds.xls")


def _cmd_reproduce(args: argparse.Namespace) -> int:
    smap = to_series_map(load_short_rates(args.short or SHORT))
    for c in CRISES:
        print(format_table(c, run_crisis(smap, c)))
        print()
    return 0


def _cmd_july1914(args: argparse.Namespace) -> int:
    for feas in (short_rate_feasibility(args.short or SHORT), bond_feasibility(args.bonds or BONDS)):
        print(f"[{feas.asset}] estimable={feas.estimable}: {feas.reason}")
    print("\nOne observable: sovereign long-bond price change across the closure "
          "(1914-06-03 -> 1914-08-05) — a distorted lower bound, not a premium:")
    changes = crisis_bond_change(args.bonds or BONDS)
    for ch in changes:
        print(f"  {ch.label:<22} {ch.pre:8.3f} -> {ch.post:8.3f}   {ch.pct:+.1f}%")
    worst = min((c.pct for c in changes), default=float("nan"))
    print("\nTwo readings, both required:")
    print("  ORDERING (smaller point): belligerents fall most, Consols least "
          "(-0.3%) — the paper's haven cross-section.")
    print(f"  MAGNITUDE (larger point, Ferguson): the worst fall is only {worst:+.1f}% "
          "— on the outbreak of a world war, almost nothing.")
    print("  The market did not price the war. The ordering rides on a trivially small shock.")
    return 0


def _cmd_russia(args: argparse.Namespace) -> int:
    """Full-sample bank-rate premia for the belligerent capitals, incl. Russia."""
    from .warweeks import get_crisis
    smap = to_series_map(load_short_rates(args.short or SHORT))
    res = {r.city: r for r in run_crisis(smap, get_crisis("full"))}
    print("Full-sample war-risk premium on the BANK (official discount) rate:")
    print(f"{'capital':<16}{'beta':>8}{'t':>7}")
    for city, label in [("petersburg_bank", "St Petersburg"), ("berlin_bank", "Berlin"),
                        ("paris_bank", "Paris"), ("vienna_bank", "Vienna"),
                        ("london_bank", "London")]:
        r = res.get(city)
        if r:
            print(f"{label:<16}{r.single.beta:>8.2f}{r.single.t_stat:>7.2f}")
    print("\nRussia (St Petersburg) is available here for the first time — the paper "
          "lacked it. Its premium is ~0 because the State Bank rate was administered "
          "and sticky, unlike the Reichsbank's; only a market rate would carry the "
          "signal, and NW's St Petersburg open-market series ends in 1900.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="war-premia", description="Reproduce/extend Carls (2005).")
    p.add_argument("--short", help="path to stinterestrates.xls")
    p.add_argument("--bonds", help="path to longtermbonds.xls")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("reproduce", help="Tables 3-7").set_defaults(func=_cmd_reproduce)
    sub.add_parser("july1914", help="the extension").set_defaults(func=_cmd_july1914)
    sub.add_parser("russia", help="St Petersburg bank-rate premium").set_defaults(func=_cmd_russia)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
