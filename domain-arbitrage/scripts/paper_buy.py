#!/usr/bin/env python
"""Open a stratified cohort of paper positions.

Samples across score bands AND buyer-depth bands, so the cohort can measure
both precision (did our picks sell?) and recall (did the names we passed on
sell too?), and can tell buyer depth apart from opportunity score.

Always dry-run it first and read the warnings. A confounded cohort will not
become informative by waiting.

Usage:
    python scripts/paper_buy.py --size 200 --cohort 2026Q3 --dry-run
    python scripts/paper_buy.py --size 200 --cohort 2026Q3
    python scripts/paper_buy.py --health --cohort 2026Q3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.db.base import session_scope                       # noqa: E402
from app.services.paper_portfolio import PaperPortfolioError  # noqa: E402
from app.services.paper_sampler import cohort_health, draw_sample  # noqa: E402


def _print_plan(result) -> None:
    plan = result.plan
    print(f"cohort {plan.cohort!r}  |  run {plan.run_id}  |  "
          f"{plan.eligible} eligible domain(s)")
    if plan.banding:
        print(f"banding: {plan.banding.kind}  score edges "
              f"{[round(e, 1) for e in plan.banding.score_edges] or 'n/a'}  "
              f"depth edges {plan.banding.depth_edges or 'n/a'}")
    if plan.reachability.get("missing_components"):
        print(f"score ceiling: {plan.reachability['final_score_ceiling']:.0f}/100 "
              f"({plan.reachability['raw_points_unavailable']:.0f} raw points "
              f"unreachable: "
              f"{', '.join(plan.reachability['missing_components'])})")
    print(f"{'stratum':<34s} {'avail':>6s} {'want':>5s} {'got':>5s}")
    for cell in sorted(plan.cells, key=lambda c: c.stratum):
        if cell.available == 0 and cell.requested == 0:
            continue
        print(f"  {cell.stratum:<32s} {cell.available:>6d} "
              f"{cell.requested:>5d} {cell.sampled:>5d}")
    print(f"\n{'DRY RUN - ' if result.dry_run else ''}"
          f"{len(result.opened)} position(s), {len(result.skipped)} skipped")

    recs: dict[str, int] = {}
    for entry in result.opened:
        recs[entry["recommendation"]] = recs.get(entry["recommendation"], 0) + 1
    if recs:
        print(f"by recommendation: {dict(sorted(recs.items()))}")
    if plan.warnings:
        print("\nWARNINGS")
        for warning in plan.warnings:
            print(f"  ! {warning}")
    for skipped in result.skipped[:10]:
        print(f"  skipped {skipped['domain']}: {skipped['reason']}")


def _print_health(health) -> None:
    print(f"cohort {health.cohort or '(all)'}: {health.verdict}")
    print(f"  by score band:  {health.by_score_band}")
    print(f"  by depth band:  {health.by_depth_band}")
    print(f"  by recommendation: {health.by_recommendation}")
    print(f"  score bands with depth variation: "
          f"{health.score_bands_with_depth_variation or 'NONE'}")
    print(f"  confounded: {health.confounded}   "
          f"recall measurable: {health.can_measure_recall}")
    for warning in health.warnings:
        print(f"  ! {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--size", type=int, default=200)
    parser.add_argument("--cohort", default="default",
                        help="label for this sampling batch")
    parser.add_argument("--run-id", type=int, default=None)
    parser.add_argument("--seed", type=int, default=0,
                        help="sampling is deterministic given this seed")
    parser.add_argument("--max-price", type=float, default=None)
    parser.add_argument("--banding", choices=("quantile", "absolute"),
                        default="quantile",
                        help="quantile bands come from the corpus's own score "
                             "distribution and are always fillable; absolute "
                             "bands use a fixed 0-100 scale whose top may be "
                             "unreachable when data sources are missing")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--health", action="store_true",
                        help="report on an existing cohort instead of sampling")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    with session_scope() as session:
        if args.health:
            health = cohort_health(session, args.cohort if args.cohort != "default"
                                   else None)
            print(json.dumps(health.to_dict(), indent=2) if args.json
                  else _print_health(health) or "")
            return 0
        try:
            result = draw_sample(session, size=args.size, cohort=args.cohort,
                                 run_id=args.run_id, seed=args.seed,
                                 max_price=args.max_price,
                                 banding=args.banding, dry_run=args.dry_run)
        except PaperPortfolioError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if args.dry_run:
            session.rollback()

        if args.json:
            print(json.dumps(result.to_dict(), indent=2, default=str))
        else:
            _print_plan(result)
            if not args.dry_run:
                print()
                _print_health(cohort_health(session, args.cohort))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
