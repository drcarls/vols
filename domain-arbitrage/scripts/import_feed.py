#!/usr/bin/env python
"""Import a third-party domain listing export.

Marketplaces each use different column headers. This proposes a mapping onto
the canonical schema and PRINTS IT before importing, because a wrong column
mapping is the most dangerous error available here: map a renewal price or an
appraisal onto `asking_price` and every downstream number is wrong while
looking entirely plausible.

Always run it without --yes first and read the mapping.

Usage:
    python scripts/import_feed.py auctions.csv --source-label godaddy
    python scripts/import_feed.py auctions.csv --source-label godaddy --yes
    python scripts/import_feed.py feed.csv --map "Price=asking_price" --yes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.db.base import session_scope                       # noqa: E402
from app.db.init_db import init_db                          # noqa: E402
from app.services.feed_mapping import (parse_overrides,      # noqa: E402
                                       propose_mapping)
from app.services.ingest import ingest_dataframe, read_csv  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--source-label", default=None,
                        help="where this inventory came from, e.g. 'godaddy'")
    parser.add_argument("--map", action="append", default=[], metavar="SRC=FIELD",
                        help="force a column mapping; repeatable")
    parser.add_argument("--yes", action="store_true",
                        help="import after showing the mapping")
    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"error: {args.csv_path} not found", file=sys.stderr)
        return 1

    try:
        overrides = parse_overrides(args.map)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    frame = read_csv(args.csv_path)
    proposal = propose_mapping(list(frame.columns))
    print(f"{args.csv_path}: {len(frame)} row(s), {len(frame.columns)} column(s)")
    print(proposal.describe())
    if overrides:
        print("explicit overrides:")
        for source, canonical in overrides.items():
            print(f"  {source:<28s} -> {canonical}")

    if not args.yes:
        print("\nDry run. Re-run with --yes to import, or correct the mapping "
              "with --map SRC=FIELD.")
        return 0

    if proposal.looks_like_sales_history and not overrides:
        print("\nRefusing to import: this looks like a completed-sales export. "
              "Load it with scripts/load_comparables.py, or force the mapping "
              "with --map if you are sure.", file=sys.stderr)
        return 1

    init_db()
    with session_scope() as session:
        report = ingest_dataframe(
            session, frame, filename=args.csv_path.name,
            source_label=args.source_label,
            column_mapping={**proposal.mapping, **overrides})

    print(f"\nimported {report.rows_accepted}/{report.rows_received} row(s) "
          f"({report.rows_rejected} rejected, {report.rows_duplicate} duplicate, "
          f"{report.new_domains} new)")
    for warning in report.warnings:
        print(f"  ! {warning}")
    for rejection in report.rejections[:10]:
        print(f"  row {rejection['row']}: {rejection['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
