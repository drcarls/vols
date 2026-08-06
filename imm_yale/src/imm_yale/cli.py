"""Command-line entry point: pull IMM yields, build spreads, emit the tidy CSV.

    imm-yale pull --start 1904 --end 1914 --out spreads_long.csv
    imm-yale pull --catalogue securities.yaml --out spreads_long.csv
    imm-yale plan                      # print the queries without touching network

The output CSV is exactly what ``crisis-lag run`` consumes:

    imm-yale pull --out spreads_long.csv && crisis-lag run spreads_long.csv
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .client import IMMClient, Query
from .config import Catalogue, catalogue_series, default_catalogue, load_catalogue
from .parse import parse_response, rows_to_yields
from .series import merge_series, spreads_to_points, write_long_csv
from .spread import YieldSeries, coverage, to_spreads


def _security_query(sec, start: int, end: int) -> Query:
    if sec.security_id:
        return Query(start_year=start, end_year=end, security_ids=[sec.security_id])
    return Query(start_year=start, end_year=end, name_exact=sec.name_query)


def _pull_yields(client: IMMClient, sec, start: int, end: int) -> "tuple[YieldSeries, str]":
    """Fetch and parse one security's monthly yields; return (yields, status)."""
    resp = client.fetch(_security_query(sec, start, end))
    parsed = parse_response(resp)
    if parsed.status != "ok":
        return {}, parsed.status
    return rows_to_yields(parsed.rows), "ok"


def _cmd_plan(args: argparse.Namespace) -> int:
    cat = load_catalogue(args.catalogue) if args.catalogue else default_catalogue()
    print(f"# IMM pull plan  {args.start}-{args.end}")
    print(f"benchmark: {cat.benchmark.label}  <- {cat.benchmark.name_query or cat.benchmark.security_id}")
    for sec in cat.issuers:
        sel = sec.security_id or f"name~{sec.name_query!r}"
        print(f"  {sec.series:<16} {sec.label:<28} <- {sel}")
    print("\nEach becomes one POST to alldatadispstocksall.php returning the "
          "Var7 £-s-d yield; spreads = issuer_yield - benchmark_yield (bp).")
    return 0


def _cmd_pull(args: argparse.Namespace) -> int:
    cat = load_catalogue(args.catalogue) if args.catalogue else default_catalogue()
    client = IMMClient(sleep=args.sleep)

    bench_yields, bstatus = _pull_yields(client, cat.benchmark, args.start, args.end)
    if bstatus != "ok":
        print(f"benchmark {cat.benchmark.label}: no data ({bstatus}).", file=sys.stderr)
    all_points = []
    for sec in cat.issuers:
        yields, status = _pull_yields(client, sec, args.start, args.end)
        n_i, n_b, n_o = coverage(yields, bench_yields)
        spreads = to_spreads(yields, bench_yields)
        pts = spreads_to_points(
            sec.series, spreads, security_id=sec.security_id,
            benchmark_id=cat.benchmark.security_id,
        )
        all_points.append(pts)
        print(f"{sec.series:<16} status={status:<10} "
              f"issuer_months={n_i} benchmark_months={n_b} overlap={n_o} "
              f"spreads={len(spreads)}", file=sys.stderr)

    merged = merge_series(*all_points)
    n = write_long_csv(merged, args.out)
    print(f"wrote {n} rows -> {args.out}", file=sys.stderr)
    if n == 0:
        print("No spreads produced — the IMM query backend returned no rows "
              "(see RECON.md). Nothing to run crisis-lag on.", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="imm-yale",
        description="Pull IMM sovereign yields and emit the tidy spread CSV for crisis_lag.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--start", type=int, default=1904, help="start year")
    common.add_argument("--end", type=int, default=1914, help="end year")
    common.add_argument("--catalogue", help="YAML securities catalogue (defaults built-in)")

    pull = sub.add_parser("pull", parents=[common], help="fetch, build spreads, write CSV")
    pull.add_argument("--out", default="spreads_long.csv", help="output tidy long CSV")
    pull.add_argument("--sleep", type=float, default=4.0, help="seconds between requests")
    pull.set_defaults(func=_cmd_pull)

    plan = sub.add_parser("plan", parents=[common], help="print the query plan; no network")
    plan.set_defaults(func=_cmd_plan)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
