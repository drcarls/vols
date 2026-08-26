#!/usr/bin/env python
"""Load real comparable domain sales into the database.

The comparable-sales table ships EMPTY, because this repository has no licensed
sale data and inventing sale prices would corrupt the only OBSERVED price
evidence in the system.

Where to get real data:
  * NameBio (namebio.com) - CSV export of public aftermarket sales
  * DNJournal weekly sales reports
  * Sedo / GoDaddy / Afternic published sale lists
  * your own escrow records

Expected CSV columns (case-insensitive):
    domain,sale_price,sale_date,venue,category,evidence_url

``domain`` and ``sale_price`` are required. Structural features (length, word
count, words, TLD) are derived here so the comparison engine does not have to
trust the file for them.

Usage:
    python scripts/load_comparables.py path/to/namebio_export.csv --source namebio
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.base import session_scope                       # noqa: E402
from app.db.init_db import init_db                          # noqa: E402
from app.models.analysis import ComparableSale              # noqa: E402
from app.provenance import Provenance                       # noqa: E402
from app.scoring.features import extract_features           # noqa: E402
from app.services.normalize import (NormalizationError,     # noqa: E402
                                    normalize_domain)

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y",
                "%d %b %Y", "%Y-%m")


def parse_date(value: str | None) -> _dt.datetime | None:
    if not value:
        return None
    text = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return _dt.datetime.strptime(text, fmt).replace(tzinfo=_dt.timezone.utc)
        except ValueError:
            continue
    return None


def parse_price(value: str | None) -> float | None:
    if not value:
        return None
    text = str(value).replace("$", "").replace(",", "").replace("USD", "").strip()
    try:
        price = float(text)
    except ValueError:
        return None
    return price if price > 0 else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--source", default="manual_import",
                        help="Where these sales came from (recorded on every row).")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"error: {args.csv_path} not found", file=sys.stderr)
        return 1

    init_db()
    loaded = skipped = 0
    problems: list[str] = []

    with args.csv_path.open(newline="", encoding="utf-8-sig") as fh, \
            session_scope() as session:
        for line_no, raw in enumerate(csv.DictReader(fh), start=2):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
            price = parse_price(row.get("sale_price") or row.get("price"))
            try:
                norm = normalize_domain(row.get("domain", ""))
            except NormalizationError as exc:
                skipped += 1
                problems.append(f"line {line_no}: {exc}")
                continue
            if price is None:
                skipped += 1
                problems.append(f"line {line_no}: unparseable or non-positive sale_price")
                continue

            features = extract_features(norm.sld, norm.tld)
            record = ComparableSale(
                domain=norm.name, sld=norm.sld, tld=norm.tld, sale_price=price,
                sale_date=parse_date(row.get("sale_date") or row.get("date")),
                venue=row.get("venue") or row.get("marketplace") or None,
                length=features.sld_length, word_count=features.word_count,
                words=list(features.words),
                category=row.get("category") or None,
                keyword_features={k: v for k, v in (
                    ("cpc", parse_price(row.get("cpc"))),
                    ("search_volume", parse_price(row.get("search_volume"))))
                    if v is not None},
                provenance=Provenance.OBSERVED.value, source=args.source,
                evidence_url=row.get("evidence_url") or None)
            if not args.dry_run:
                session.merge(record)
            loaded += 1

        if args.dry_run:
            session.rollback()

    print(f"{'would load' if args.dry_run else 'loaded'} {loaded} comparable sale(s) "
          f"from {args.csv_path}")
    if skipped:
        print(f"skipped {skipped} row(s):")
        for problem in problems[:20]:
            print(f"  {problem}")
        if len(problems) > 20:
            print(f"  ... and {len(problems) - 20} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
