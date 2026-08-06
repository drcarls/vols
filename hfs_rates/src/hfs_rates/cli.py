"""Pull HFS weekly money-market rates -> spread-over-London CSV for crisis_lag.

    hfs-rates pull --out weekly_long.csv          # download + build (needs pyxlsb)
    hfs-rates pull --workbook Interest_rates.xlsb --out weekly_long.csv

Then, at weekly resolution:

    crisis-lag run weekly_long.csv --events events.money_market.yaml
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .catalog import default_catalog
from .client import download_workbook
from .parse import grid_to_series, read_grid
from .spreads import coverage, to_spread_rows, write_long_csv


def _cmd_plan(args: argparse.Namespace) -> int:
    cat = default_catalog()
    print(f"benchmark: {cat.benchmark.label} ({cat.benchmark.country} / "
          f"{cat.benchmark.series_substr!r})")
    for s in cat.issuers:
        print(f"  issuer: {s.series:<16} {s.label} ({s.country} / {s.series_substr!r})")
    print("\nvalue = power open-market rate - London 90d bank bills, in bp, weekly.")
    return 0


def _cmd_pull(args: argparse.Namespace) -> int:
    cat = default_catalog()
    path = args.workbook or download_workbook()
    grid = read_grid(path)
    london = grid_to_series(grid, cat.benchmark.country, cat.benchmark.series_substr,
                            start_year=args.start, end_year=args.end)
    if not london:
        print("benchmark (London) column not found — aborting.", file=sys.stderr)
        return 1
    all_rows = []
    for s in cat.issuers:
        power = grid_to_series(grid, s.country, s.series_substr,
                               start_year=args.start, end_year=args.end)
        rows = to_spread_rows(s.series, power, london)
        all_rows.extend(rows)
        n_p, n_b, n_o = coverage(power, london)
        print(f"{s.series:<16} weeks={n_p:4} overlap={n_o:4} spreads={len(rows):4}",
              file=sys.stderr)
    n = write_long_csv(all_rows, args.out)
    print(f"wrote {n} rows -> {args.out}", file=sys.stderr)
    return 0 if n else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hfs-rates",
        description="HFS weekly money-market rates -> spread-over-London CSV for crisis_lag.",
    )
    sub = p.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--start", type=int, default=1900)
    common.add_argument("--end", type=int, default=1914)

    pull = sub.add_parser("pull", parents=[common], help="download+build weekly CSV")
    pull.add_argument("--workbook", help="path to Interest_rates.xlsb (else downloaded)")
    pull.add_argument("--out", default="weekly_long.csv")
    pull.set_defaults(func=_cmd_pull)

    plan = sub.add_parser("plan", parents=[common], help="print the plan; no network")
    plan.set_defaults(func=_cmd_plan)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
