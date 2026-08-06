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
    for ch in crisis_bond_change(args.bonds or BONDS):
        print(f"  {ch.label:<22} {ch.pre:8.3f} -> {ch.post:8.3f}   {ch.pct:+.1f}%")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="war-premia", description="Reproduce/extend Carls (2005).")
    p.add_argument("--short", help="path to stinterestrates.xls")
    p.add_argument("--bonds", help="path to longtermbonds.xls")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("reproduce", help="Tables 3-7").set_defaults(func=_cmd_reproduce)
    sub.add_parser("july1914", help="the extension").set_defaults(func=_cmd_july1914)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
