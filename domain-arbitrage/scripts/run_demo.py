#!/usr/bin/env python
"""End-to-end demonstration on the bundled example data.

This uses SYNTHETIC example companies and keywords. It exists to show the
pipeline working, not to produce a real opportunity list. Every buyer it finds
is tagged FIXTURE.

Usage:
    python scripts/run_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Set before importing app modules: settings are read at import time.
os.environ.setdefault("ALLOW_FIXTURE_DATA", "true")
os.environ.setdefault("KEYWORD_PROVIDER", "csv")
os.environ.setdefault("KEYWORD_CSV_PATH",
                      str(ROOT / "data" / "examples" / "keywords_EXAMPLE_SYNTHETIC.csv"))

from app.db.base import session_scope                 # noqa: E402
from app.db.init_db import reset_db                   # noqa: E402
from app.services.ingest import ingest_csv            # noqa: E402
from app.services.paper_portfolio import open_position  # noqa: E402
from app.services.pipeline import run_pipeline        # noqa: E402
from app.services.portfolio import build_portfolio    # noqa: E402
from app.services.report import build_report, render_text  # noqa: E402

EXAMPLE_CSV = ROOT / "data" / "examples" / "domains_example.csv"


def main() -> int:
    print("!" * 78)
    print("DEMO MODE - the company and keyword files used here are SYNTHETIC.")
    print("Nothing in this output is evidence about a real company or market.")
    print("!" * 78)
    print()

    reset_db()
    with session_scope() as session:
        report = ingest_csv(session, EXAMPLE_CSV, source_label="example")
    print(f"Imported {report.rows_accepted}/{report.rows_received} rows "
          f"({report.rows_rejected} rejected, {report.rows_duplicate} duplicate)")
    for warning in report.warnings:
        print(f"  ! {warning}")
    print()

    with session_scope() as session:
        run = run_pipeline(session)
    print(f"Scored {run.domains_scored} domains in {run.duration_seconds}s")
    print(f"Data gaps: {run.data_gaps}")
    print()

    with session_scope() as session:
        print(render_text(build_report(session, limit=5), limit=5))
        print()

        for scenario in ("conservative", "balanced", "aggressive"):
            portfolio = build_portfolio(session, budget=10_000, scenario=scenario)
            print(f"PORTFOLIO [{scenario}] budget $10,000: "
                  f"{len(portfolio.holdings)} holding(s), "
                  f"${portfolio.total_invested:,.0f} invested, "
                  f"expected 24m profit ${portfolio.total_expected_profit_24m:,.0f}")
            for holding in portfolio.holdings:
                print(f"    {holding.domain:32s} ${holding.price:>8,.0f}  "
                      f"score {holding.opportunity_score:>5.1f}  "
                      f"{holding.recommendation}")
        print()

        top = build_report(session, limit=3).entries
        for entry in top:
            open_position(session, entry.domain, status="PAPER_BUY",
                          notes="opened by run_demo.py")
        print(f"Opened {len(top)} paper position(s). Their predictions are now "
              f"frozen; record outcomes with POST /api/paper/observations.")

    print()
    print("Start the API with:  uvicorn app.main:app --reload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
