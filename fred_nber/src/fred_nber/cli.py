"""Command-line entry point: pull open FRED/NBER yields -> tidy spread CSV.

    fred-nber pull --out spreads_long.csv          # default catalog (fr, de, consols)
    fred-nber pull --catalog series.yaml --out spreads_long.csv
    fred-nber plan                                 # print the series, no network

Then run the falsification test on real, keyless data:

    fred-nber pull --out spreads_long.csv && crisis-lag run spreads_long.csv
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .catalog import Catalog, default_catalog, load_catalog
from .client import fetch_series
from .spreads import coverage, to_spread_rows, write_long_csv


def _load_catalog(args) -> Catalog:
    return load_catalog(args.catalog) if args.catalog else default_catalog()


def _cmd_plan(args: argparse.Namespace) -> int:
    cat = _load_catalog(args)
    print("# FRED/NBER pull plan (keyless)")
    print(f"benchmark: {cat.benchmark.series:<10} {cat.benchmark.fred_id:<24} "
          f"{cat.benchmark.label}  [{cat.benchmark.coverage}]")
    for s in cat.issuers:
        print(f"  issuer:  {s.series:<10} {s.fred_id:<24} {s.label}  [{s.coverage}]")
    return 0


def _cmd_pull(args: argparse.Namespace) -> int:
    cat = _load_catalog(args)
    print(f"fetching benchmark {cat.benchmark.fred_id} …", file=sys.stderr)
    bench = fetch_series(cat.benchmark.fred_id)
    all_rows = []
    for s in cat.issuers:
        print(f"fetching {s.series} {s.fred_id} …", file=sys.stderr)
        issuer = fetch_series(s.fred_id)
        rows = to_spread_rows(
            s.series, issuer, bench, fred_id=s.fred_id, benchmark_id=cat.benchmark.fred_id
        )
        all_rows.extend(rows)
        n_i, n_b, n_o = coverage(issuer, bench)
        print(f"  {s.series:<10} issuer_months={n_i} benchmark_months={n_b} "
              f"overlap={n_o} spreads={len(rows)}", file=sys.stderr)
    n = write_long_csv(all_rows, args.out)
    print(f"wrote {n} rows -> {args.out}", file=sys.stderr)
    return 0 if n else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fred-nber",
        description="Pull keyless FRED/NBER sovereign yields and emit the crisis_lag spread CSV.",
    )
    sub = p.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--catalog", help="YAML series catalog (defaults built-in)")

    pull = sub.add_parser("pull", parents=[common], help="fetch, build spreads, write CSV")
    pull.add_argument("--out", default="spreads_long.csv", help="output tidy long CSV")
    pull.set_defaults(func=_cmd_pull)

    plan = sub.add_parser("plan", parents=[common], help="print the series plan; no network")
    plan.set_defaults(func=_cmd_plan)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
