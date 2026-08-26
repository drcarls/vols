#!/usr/bin/env python
"""Resolve paper positions against observed sale data.

Records SOLD for positions that appear in the sales export. Does NOT mark
anything unsold: a domain missing from a public feed may simply have sold
privately, and counting that as a failure biases the measured sale rate
downward.

To resolve positions whose horizon has elapsed, use --close-window. That marks
them CENSORED unless you also pass --observation-complete, which asserts that a
sale of any of these domains would have reached you.

Expected CSV columns: domain, sale_price, sale_date, venue, evidence_url
(only `domain` is required).

Usage:
    python scripts/reconcile_outcomes.py sales_2026Q3.csv --source namebio
    python scripts/reconcile_outcomes.py sales.csv --dry-run
    python scripts/reconcile_outcomes.py --close-window --horizon-months 24
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.db.base import session_scope                          # noqa: E402
from app.services.paper_portfolio import performance           # noqa: E402
from app.services.reconcile import (close_observation_window,  # noqa: E402
                                    read_sales, reconcile)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path", type=Path, nargs="?", default=None)
    parser.add_argument("--source", default="sales_export")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--close-window", action="store_true",
                        help="resolve positions whose horizon has elapsed")
    parser.add_argument("--horizon-months", type=int, default=24)
    parser.add_argument("--observation-complete", action="store_true",
                        help="assert that a sale WOULD have reached you over "
                             "this period; without it, positions are CENSORED "
                             "rather than marked UNSOLD")
    args = parser.parse_args()

    if not args.csv_path and not args.close_window:
        parser.error("give a sales CSV, or --close-window, or both")

    with session_scope() as session:
        payload: dict = {}

        if args.csv_path:
            if not args.csv_path.exists():
                print(f"error: {args.csv_path} not found", file=sys.stderr)
                return 1
            sales, problems = read_sales(args.csv_path)
            report = reconcile(session, sales, source=args.source,
                               dry_run=args.dry_run)
            report.sales_unparseable = len(problems)
            report.problems = problems[:20]
            payload["reconcile"] = report.to_dict()
            if not args.json:
                print(f"read {report.sales_read} sale(s), "
                      f"{len(problems)} unparseable")
                print(f"matched {report.matched} open position(s); "
                      f"{report.unmatched_sales} sale(s) matched nothing; "
                      f"{report.open_positions_after} position(s) still open")
                for entry in report.resolved[:15]:
                    predicted = entry["predicted_retail_value"]
                    observed = entry["observed_price"]
                    ratio = (f"{observed / predicted:.2f}x predicted"
                             if predicted and observed else "no price")
                    print(f"  SOLD {entry['domain']:<32s} "
                          f"{('$%s' % f'{observed:,.0f}') if observed else '-':>10s} "
                          f"({ratio}, was {entry['recommendation']})")
                for warning in report.warnings:
                    print(f"  ! {warning}")

        if args.close_window:
            closed = close_observation_window(
                session, horizon_months=args.horizon_months,
                observation_was_complete=args.observation_complete,
                source=args.source, dry_run=args.dry_run)
            payload["close_window"] = closed.to_dict()
            if not args.json:
                print(f"\ncensored {closed.censored}, "
                      f"marked unsold {closed.marked_unsold}, "
                      f"left open {closed.left_open}")
                for warning in closed.warnings:
                    print(f"  ! {warning}")

        if args.dry_run:
            session.rollback()
        else:
            session.flush()
            payload["performance"] = performance(session).to_dict()

        if args.json:
            print(json.dumps(payload, indent=2, default=str))
        elif "performance" in payload:
            perf = payload["performance"]
            print(f"\nperformance: {perf['resolved']} resolved, "
                  f"{perf['sold']} sold")
            for note in perf["notes"]:
                print(f"  ! {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
