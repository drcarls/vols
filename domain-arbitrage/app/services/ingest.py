"""CSV ingestion.

Required columns: ``domain``. Everything else is optional, because a closeout
feed and a marketplace export do not carry the same fields, and demanding them
would mean inventing them.

Rows that cannot be normalised are REJECTED WITH A REASON and reported back,
never silently dropped and never coerced into something valid-looking.
"""

from __future__ import annotations

import datetime as _dt
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import Domain, ImportBatch, Listing
from app.provenance import utcnow
from app.services.normalize import NormalizationError, normalize_domain

REQUIRED_COLUMNS = {"domain"}
KNOWN_COLUMNS = {
    "domain", "asking_price", "source", "auction_end_date", "current_bid",
    "bid_count", "traffic", "registrar", "expiration_date", "listing_type",
}


@dataclass
class IngestReport:
    batch_id: int | None = None
    rows_received: int = 0
    rows_accepted: int = 0
    rows_rejected: int = 0
    rows_duplicate: int = 0
    new_domains: int = 0
    rejections: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unknown_columns: list[str] = field(default_factory=list)
    missing_optional_columns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def _parse_price(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().replace("$", "").replace(",", "").replace("USD", "").strip()
    if not text or text.lower() in {"nan", "none", "na", "n/a", "-", ""}:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _parse_int(value: Any) -> int | None:
    price = _parse_price(value)
    return int(price) if price is not None else None


def _parse_date(value: Any) -> _dt.datetime | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "na", "n/a", "-"}:
        return None
    try:
        ts = pd.to_datetime(text, utc=True, errors="raise")
    except (ValueError, TypeError):
        return None
    return ts.to_pydatetime()


def _clean(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def read_csv(source: str | Path | bytes | io.IOBase) -> pd.DataFrame:
    """Read a domain CSV, normalising column names to lowercase snake case."""
    if isinstance(source, bytes):
        source = io.BytesIO(source)
    df = pd.read_csv(source, dtype=str, keep_default_na=False, na_values=[""])
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def ingest_dataframe(session: Session, df: pd.DataFrame, *, filename: str,
                     source_label: str | None = None) -> IngestReport:
    """Normalise, deduplicate and persist a batch of listings."""
    report = IngestReport(rows_received=len(df))

    missing_required = REQUIRED_COLUMNS - set(df.columns)
    if missing_required:
        raise ValueError(
            f"CSV is missing required column(s): {', '.join(sorted(missing_required))}. "
            f"Found: {', '.join(df.columns)}")

    report.unknown_columns = sorted(set(df.columns) - KNOWN_COLUMNS)
    report.missing_optional_columns = sorted(KNOWN_COLUMNS - set(df.columns))
    if report.unknown_columns:
        report.warnings.append(
            f"Unrecognised column(s) kept on the raw row but not mapped: "
            f"{', '.join(report.unknown_columns)}")
    if report.missing_optional_columns:
        report.warnings.append(
            f"Optional column(s) absent - the corresponding fields will be "
            f"MISSING, not defaulted: {', '.join(report.missing_optional_columns)}")

    batch = ImportBatch(filename=filename, source_label=source_label,
                        rows_received=len(df))
    session.add(batch)
    session.flush()
    report.batch_id = batch.id

    # Existing domains, fetched once rather than per row.
    existing: dict[str, Domain] = {
        d.name: d for d in session.execute(select(Domain)).scalars()
    }
    seen_in_batch: set[str] = set()
    now = utcnow()
    new_listings: list[Listing] = []

    for idx, row in df.iterrows():
        raw_domain = row.get("domain")
        try:
            norm = normalize_domain(raw_domain)
        except NormalizationError as exc:
            report.rows_rejected += 1
            report.rejections.append(
                {"row": int(idx) + 2, "domain": _clean(raw_domain),
                 "reason": str(exc)})
            continue

        if norm.name in seen_in_batch:
            report.rows_duplicate += 1
            continue
        seen_in_batch.add(norm.name)

        domain = existing.get(norm.name)
        if domain is None:
            domain = Domain(name=norm.name, sld=norm.sld, tld=norm.tld,
                            is_idn=norm.is_idn, unicode_name=norm.unicode_name,
                            first_seen_at=now, last_seen_at=now)
            session.add(domain)
            session.flush()
            existing[norm.name] = domain
            report.new_domains += 1
        else:
            domain.last_seen_at = now

        # Previous listings for this domain are no longer current.
        for prior in domain.listings:
            prior.is_current = False

        raw_row = {k: _clean(v) for k, v in row.items()}
        new_listings.append(Listing(
            domain_id=domain.id,
            batch_id=batch.id,
            asking_price=_parse_price(row.get("asking_price")),
            current_bid=_parse_price(row.get("current_bid")),
            bid_count=_parse_int(row.get("bid_count")),
            source=_clean(row.get("source")) or (source_label or "unknown"),
            listing_type=_clean(row.get("listing_type")),
            auction_end_date=_parse_date(row.get("auction_end_date")),
            expiration_date=_parse_date(row.get("expiration_date")),
            registrar=_clean(row.get("registrar")),
            traffic=_parse_price(row.get("traffic")),
            raw_row=raw_row,
            observed_at=now,
            is_current=True,
        ))
        report.rows_accepted += 1

    session.add_all(new_listings)

    priced = sum(1 for listing in new_listings if listing.effective_price is not None)
    if priced < len(new_listings):
        report.warnings.append(
            f"{len(new_listings) - priced} accepted listing(s) have no asking "
            f"price or current bid; ROI cannot be computed for them and they "
            f"will be reported with price MISSING.")

    batch.rows_accepted = report.rows_accepted
    batch.rows_rejected = report.rows_rejected
    batch.rows_duplicate = report.rows_duplicate
    batch.warnings = report.warnings
    session.flush()
    return report


def ingest_csv(session: Session, source: str | Path | bytes, *,
               filename: str | None = None,
               source_label: str | None = None) -> IngestReport:
    df = read_csv(source)
    name = filename or (str(source) if isinstance(source, (str, Path)) else "upload.csv")
    return ingest_dataframe(session, df, filename=name, source_label=source_label)
