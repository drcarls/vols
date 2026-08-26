"""Reconcile paper positions against observed sale data.

The integrity hazard in this module is specific and worth stating plainly:

    A domain missing from a sales export did not necessarily fail to sell.

Public sale feeds cover a fraction of the market. Private deals, brokered
transfers and marketplaces that publish nothing are all invisible. So absence
from a file is absence of evidence, not evidence of absence, and marking a
position UNSOLD because it did not appear in one export would bias the measured
sale rate downward - in exactly the direction that makes an over-pessimistic
base rate look correct.

Two operations, kept separate on purpose:

  * ``reconcile`` records SOLD for positions that DO appear. Positive evidence
    only. It never resolves anything as unsold.
  * ``close_observation_window`` marks positions CENSORED or UNSOLD, and
    requires the caller to state explicitly that the observation window was
    complete over the period in question. CENSORED is the default, because it
    is almost always the truthful answer.

Only UNSOLD counts toward the testable set. CENSORED positions are excluded
from every statistic rather than silently counted as failures.
"""

from __future__ import annotations

import csv
import datetime as _dt
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.paper import PaperPosition
from app.provenance import utcnow
from app.services.normalize import NormalizationError, normalize_domain
from app.services.paper_portfolio import record_observation

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y",
                "%d %b %Y", "%Y-%m")


@dataclass
class SaleRecord:
    """One observed sale, from a source outside this system."""

    domain: str
    sale_price: float | None
    sale_date: _dt.datetime | None
    venue: str | None
    evidence_url: str | None


@dataclass
class ReconcileReport:
    source: str
    sales_read: int = 0
    sales_unparseable: int = 0
    matched: int = 0
    already_resolved: int = 0
    unmatched_sales: int = 0
    open_positions_before: int = 0
    open_positions_after: int = 0
    resolved: list[dict[str, Any]] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def _parse_date(value: str | None) -> _dt.datetime | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return _dt.datetime.strptime(text, fmt).replace(tzinfo=_dt.timezone.utc)
        except ValueError:
            continue
    return None


def _parse_price(value: str | None) -> float | None:
    if not value:
        return None
    text = str(value).replace("$", "").replace(",", "").replace("USD", "").strip()
    try:
        price = float(text)
    except ValueError:
        return None
    return price if price > 0 else None


def read_sales(source: str | Path | bytes) -> tuple[list[SaleRecord], list[str]]:
    """Parse a sales export. Columns: domain, sale_price, sale_date, venue,
    evidence_url. Only ``domain`` is required."""
    if isinstance(source, bytes):
        handle: Any = io.StringIO(source.decode("utf-8-sig"))
    else:
        handle = Path(source).open(newline="", encoding="utf-8-sig")

    records: list[SaleRecord] = []
    problems: list[str] = []
    try:
        for line_no, raw in enumerate(csv.DictReader(handle), start=2):
            row = {(k or "").strip().lower(): (v or "").strip()
                   for k, v in raw.items()}
            try:
                norm = normalize_domain(row.get("domain", ""))
            except NormalizationError as exc:
                problems.append(f"line {line_no}: {exc}")
                continue
            records.append(SaleRecord(
                domain=norm.name,
                sale_price=_parse_price(row.get("sale_price") or row.get("price")),
                sale_date=_parse_date(row.get("sale_date") or row.get("date")),
                venue=row.get("venue") or row.get("marketplace") or None,
                evidence_url=row.get("evidence_url") or None))
    finally:
        if not isinstance(source, bytes):
            handle.close()
    return records, problems


def reconcile(session: Session, sales: Iterable[SaleRecord], *,
              source: str = "sales_export",
              dry_run: bool = False) -> ReconcileReport:
    """Record SOLD for every open position that appears in the sales data.

    Positive evidence only. Positions absent from ``sales`` are left untouched -
    resolving them is the job of ``close_observation_window``, which forces the
    caller to be explicit about what the absence means.
    """
    report = ReconcileReport(source=source)

    open_positions = session.execute(
        select(PaperPosition).where(PaperPosition.outcome.is_(None))).scalars().all()
    report.open_positions_before = len(open_positions)
    by_domain: dict[str, list[PaperPosition]] = {}
    for position in open_positions:
        by_domain.setdefault(position.domain_name, []).append(position)

    resolved_names = {p.domain_name for p in session.execute(
        select(PaperPosition).where(PaperPosition.outcome.is_not(None))).scalars()}

    for record in sales:
        report.sales_read += 1
        matches = by_domain.get(record.domain)
        if not matches:
            if record.domain in resolved_names:
                report.already_resolved += 1
            else:
                report.unmatched_sales += 1
            continue

        for position in matches:
            if not dry_run:
                record_observation(
                    session, position.id, event_type="SOLD", sold=True,
                    observed_price=record.sale_price,
                    observed_at=record.sale_date or utcnow(),
                    venue=record.venue, source=source,
                    evidence_url=record.evidence_url,
                    note=("reconciled from a sales export"
                          if record.evidence_url is None else None))
            report.matched += 1
            report.resolved.append({
                "position_id": position.id, "domain": position.domain_name,
                "observed_price": record.sale_price,
                "predicted_retail_value": position.predicted_retail_value,
                "asking_price": position.asking_price,
                "sale_date": (record.sale_date.isoformat()
                              if record.sale_date else None),
                "evidence_url": record.evidence_url,
                "predicted_prob_24m": position.predicted_sale_probability_24m,
                "recommendation": position.recommendation})
        by_domain.pop(record.domain, None)

    report.open_positions_after = report.open_positions_before - report.matched

    without_price = sum(1 for r in report.resolved if r["observed_price"] is None)
    if without_price:
        report.warnings.append(
            f"{without_price} matched sale(s) had no price, so valuation error "
            f"cannot be measured for them - only the sale/no-sale outcome.")
    without_evidence = sum(1 for r in report.resolved if not r["evidence_url"])
    if without_evidence:
        report.warnings.append(
            f"{without_evidence} matched sale(s) had no evidence_url and cannot "
            f"be independently verified later.")
    report.warnings.append(
        "Positions absent from this export were NOT resolved. A public sales "
        "feed covers only part of the market, so absence is not evidence of a "
        "failure to sell.")
    return report


@dataclass
class CloseReport:
    censored: int = 0
    marked_unsold: int = 0
    left_open: int = 0
    positions: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def close_observation_window(session: Session, *, as_of: _dt.datetime | None = None,
                             horizon_months: int = 24,
                             observation_was_complete: bool = False,
                             source: str = "manual",
                             note: str | None = None,
                             dry_run: bool = False) -> CloseReport:
    """Resolve open positions whose horizon has elapsed.

    ``observation_was_complete`` is the caller asserting: over this whole
    period, a sale of any of these domains WOULD have reached me. That is a
    strong claim - it is false for any public sales feed - so it defaults to
    False, and without it positions are marked CENSORED rather than UNSOLD.

    CENSORED positions are excluded from every statistic. That loses power, and
    losing power is the correct trade against silently counting invisible sales
    as failures.
    """
    as_of = as_of or utcnow()
    report = CloseReport()

    open_positions = session.execute(
        select(PaperPosition).where(PaperPosition.outcome.is_(None))).scalars().all()

    for position in open_positions:
        elapsed_days = (as_of - position.date_seen).days
        if elapsed_days < horizon_months * 30:
            report.left_open += 1
            continue

        entry = {"position_id": position.id, "domain": position.domain_name,
                 "days_open": elapsed_days,
                 "outcome": "UNSOLD" if observation_was_complete else "CENSORED"}
        if not dry_run:
            if observation_was_complete:
                # A sale-status observation whose answer is "no". record_observation
                # resolves this to UNSOLD, which is in the testable set.
                record_observation(
                    session, position.id, event_type="SOLD", sold=False,
                    observed_at=as_of, source=source,
                    note=note or (f"horizon of {horizon_months} months elapsed; "
                                  f"observation window asserted complete"))
            else:
                # Censoring records that we STOPPED WATCHING, which is a fact
                # about us and not about the domain. LISTING_CHANGE is used
                # because it resolves nothing on its own; the outcome is then
                # set explicitly so this can never be mistaken for a failure
                # to sell.
                record_observation(
                    session, position.id, event_type="LISTING_CHANGE",
                    observed_at=as_of, source=source,
                    note=note or (f"horizon of {horizon_months} months elapsed; "
                                  f"observation window INCOMPLETE - censored, "
                                  f"not counted as a failure to sell"))
                position.outcome = "CENSORED"
                position.outcome_date = as_of
                position.outcome_resolved_at = utcnow()
        if observation_was_complete:
            report.marked_unsold += 1
        else:
            report.censored += 1
        report.positions.append(entry)

    if report.censored:
        report.warnings.append(
            f"{report.censored} position(s) marked CENSORED, not UNSOLD, "
            f"because observation_was_complete was not asserted. They are "
            f"excluded from every performance statistic. Pass "
            f"observation_was_complete=True only if you are confident a sale "
            f"of any of these domains would have reached you.")
    if report.marked_unsold:
        report.warnings.append(
            f"{report.marked_unsold} position(s) marked UNSOLD on the caller's "
            f"assertion that the observation window was complete. If it was "
            f"not, the measured sale rate is biased downward.")
    return report
