#!/usr/bin/env python
"""Time a full 10,000-domain run against the success criterion.

The stated criterion for the MVP is: given a CSV of 10,000 domains, return a
ranked table with a defensible explanation for every number. This script
measures ingest, scoring, ranking and report generation separately so a
regression shows up in the right stage.

Runs against a throwaway database so it cannot disturb real data.

Usage:
    python scripts/generate_test_csv.py 10000 data/load_test_SYNTHETIC.csv
    python scripts/load_test.py
"""

from __future__ import annotations

import os
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CSV = ROOT / "data" / "load_test_SYNTHETIC.csv"
os.environ["DATABASE_URL"] = f"sqlite:///{ROOT / 'data' / 'load_test.db'}"
os.environ.setdefault("ALLOW_FIXTURE_DATA", "true")

from app.db.base import session_scope           # noqa: E402
from app.db.init_db import reset_db             # noqa: E402
from app.services.ingest import ingest_csv      # noqa: E402
from app.services.pipeline import run_pipeline  # noqa: E402
from app.services.portfolio import build_portfolio  # noqa: E402
from app.services.report import build_report    # noqa: E402


def main() -> int:
    if not CSV.exists():
        print(f"error: {CSV} not found. Run scripts/generate_test_csv.py first.",
              file=sys.stderr)
        return 1

    reset_db()

    started = time.time()
    with session_scope() as session:
        ingest = ingest_csv(session, CSV, source_label="load_test")
    ingest_seconds = time.time() - started
    print(f"ingest      {ingest.rows_accepted:>6,} rows   {ingest_seconds:6.1f}s")

    started = time.time()
    with session_scope() as session:
        run = run_pipeline(session)
    print(f"pipeline    {run.domains_scored:>6,} scored {time.time() - started:6.1f}s")

    started = time.time()
    with session_scope() as session:
        report = build_report(session, limit=50)
    print(f"report      {len(report.entries):>6,} rows   {time.time() - started:6.1f}s")

    started = time.time()
    with session_scope() as session:
        portfolio = build_portfolio(session, budget=10_000, scenario="balanced")
    print(f"portfolio   {len(portfolio.holdings):>6,} picks  {time.time() - started:6.1f}s")

    peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(f"peak memory {peak_mb:>6.0f} MB")
    print()
    print(f"recommendations: {report.summary['by_recommendation']}")
    print(f"data gaps:       {run.data_gaps}")
    print()
    print(f"{'#':>4} {'domain':34s} {'price':>8s} {'retail':>10s} {'P24m':>6s} "
          f"{'buyers':>6s} {'maxbid':>8s} {'score':>6s}  rec")
    for entry in report.entries[:10]:
        price = f"${entry.asking_price:,.0f}" if entry.asking_price else "-"
        print(f"{entry.rank:>4} {entry.domain:34s} {price:>8s} "
              f"${entry.retail_mid:>9,.0f} {entry.prob_sale_24m:>5.1%} "
              f"{entry.buyer_count:>6} ${entry.recommended_max_bid or 0:>7,.0f} "
              f"{entry.opportunity_score:>6.1f}  {entry.recommendation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
