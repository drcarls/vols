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
    bond_quote_audit,
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
    print("\nRaw bond-quote audit across the closure (prices, points of par):")
    print(f"  {'sovereign':<24}{'Jun2':>7}{'Jun3':>7}{'Aug5':>7}{'Sep1':>7}  flags")
    for a in bond_quote_audit(args.bonds or BONDS):
        flags = []
        if a.exdiv_flag:
            flags.append("Jun3=EX-DIV")
        if not a.genuine:
            flags.append("post-closure NOT genuine (" + a.reason.split("—")[0].strip() + ")")
        def f(x):
            return f"{x:.2f}" if x is not None else "—"
        print(f"  {a.sovereign:<24}{f(a.clean_pre):>7}{f(a.exdiv_pre):>7}"
              f"{f(a.post_stale):>7}{f(a.post_sept):>7}  {'; '.join(flags)}")
    print("\nVerdict: the Jun2/Jun3-vs-Aug5/Sep1 cross-section is UNINTERPRETABLE — the "
          "June-3 baseline is ex-dividend and the post-closure quotes are nominal "
          "(belligerent bonds 'rise' during the war). The earlier ~2% reading is withdrawn.")
    print("\nBut the pre-closure decline IS observable — the weekly (text) vintage, "
          "15 Jun -> 31 Jul 1914 (clean = to last unflagged quote):")
    from .july1914 import war_week_bond_decline
    for w in war_week_bond_decline(args.bonds or BONDS):
        if not w.quotes:
            continue
        q = " ".join(f"{d.strftime('%m-%d')}={p:.1f}{'*' if fl else ''}" for d, p, fl in w.quotes)
        tail = f"  ->{w.pct_clean:+.1f}%" if w.pct_clean is not None else ""
        if w.final_flagged and w.final_price is not None:
            tail += f" [31Jul {w.final_price:.1f} footnoted]"
        print(f"  {w.sovereign:<22}{q}{tail}")
    print("  (* = flagged: ex-dividend or footnote; clean decline stops at the last unflagged quote)")
    print("The whole European sovereign complex fell ~2.5-6% in the final trading weeks — a\n"
          "broad war repricing, visible until the market shut. The IDENTIFIED premium is what's\n"
          "unestimable (regime truncated by closure), not the reaction, which is right here.")
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


def _cmd_kokovtsov(args: argparse.Namespace) -> int:
    """Did Russian short rates move around Kokovtsov's dismissal (Feb 1914)?"""
    from .kokovtsov import format_result, kokovtsov_test

    print(format_result(kokovtsov_test(args.short or SHORT, args.bonds or BONDS)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="war-premia", description="Reproduce/extend Carls (2005).")
    p.add_argument("--short", help="path to stinterestrates.xls")
    p.add_argument("--bonds", help="path to longtermbonds.xls")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("reproduce", help="Tables 3-7").set_defaults(func=_cmd_reproduce)
    sub.add_parser("july1914", help="the extension").set_defaults(func=_cmd_july1914)
    sub.add_parser("russia", help="St Petersburg bank-rate premium").set_defaults(func=_cmd_russia)
    sub.add_parser("kokovtsov", help="the Kokovtsov dismissal event test (Feb 1914)").set_defaults(func=_cmd_kokovtsov)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
