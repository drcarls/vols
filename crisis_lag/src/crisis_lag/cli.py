"""Command-line entry point for the falsification test.

    crisis-lag run spreads_long.csv                 # default events + verdict
    crisis-lag run spreads_long.csv --events e.yaml  # custom event spec
    crisis-lag run spreads_long.csv --measure material --band 6 10

Prints the per-crisis lag table and the verdict. Non-zero exit if the verdict is
FALSIFIED, so it can gate a build.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .events import DEFAULT_EVENTS, load_events
from .lag import measure_all
from .report import FALSIFIED, adjudicate, format_table, format_verdict
from .series import load_long_csv


def _cmd_run(args: argparse.Namespace) -> int:
    events = load_events(args.events) if args.events else DEFAULT_EVENTS
    series = load_long_csv(args.data)
    results = measure_all(series, events, z_threshold=args.z)
    verdict = adjudicate(
        results,
        band_lo_weeks=args.band[0],
        band_hi_weeks=args.band[1],
        falsify_floor_weeks=args.floor,
        lag_measure=args.measure,
    )
    print(format_table(results, lag_measure=args.measure))
    print()
    print(format_verdict(verdict))
    return 2 if verdict.verdict == FALSIFIED else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="crisis-lag",
        description="Onset->peak-stress lag test for the pre-1914 crises.",
    )
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="measure lags and adjudicate")
    r.add_argument("data", help="tidy long CSV: date,series,value")
    r.add_argument("--events", help="YAML event spec (defaults to built-in crises)")
    r.add_argument("--measure", choices=["peak", "material"], default="peak")
    r.add_argument("--z", type=float, default=2.0, help="z threshold for 'material' stress")
    r.add_argument(
        "--band", nargs=2, type=float, default=[6.0, 10.0],
        metavar=("LO", "HI"), help="predicted lag band in weeks",
    )
    r.add_argument("--floor", type=float, default=2.0, help="falsification floor (weeks)")
    r.set_defaults(func=_cmd_run)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
