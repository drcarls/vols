"""Daily opportunity report.

Renders the ranked table plus, for each name, the numbers a decision actually
needs: what it costs, what the model thinks it is worth, how likely it is to
sell, who might buy it, and the most you should pay. Every figure comes from a
stored column - the report formats data, it does not compute new estimates.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analysis import (BuyerCandidate, OpportunityScore, PipelineRun,
                                 SaleProbability, Valuation)
from app.models.core import Domain, Listing
from app.provenance import utcnow


@dataclass
class ReportEntry:
    rank: int
    domain: str
    recommendation: str
    opportunity_score: float
    confidence: float
    asking_price: float | None
    listing_type: str | None
    auction_end_date: str | None
    recommended_max_bid: float | None
    retail_low: float
    retail_mid: float
    retail_high: float
    wholesale_mid: float
    strategic_high: float | None
    prob_sale_12m: float
    prob_sale_24m: float
    prob_sale_36m: float
    expected_holding_months: float
    expected_profit_24m: float | None
    expected_roi_24m: float | None
    buyer_count: int
    top_buyers: list[dict[str, Any]]
    category: str | None
    valuation_confidence: float
    data_gaps: list[str]
    top_reasons: list[str]
    risks: list[str]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class OpportunityReport:
    generated_at: str
    run_id: int
    scoring_config: str
    calibrated: bool
    entries: list[ReportEntry] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        d["entries"] = [e.to_dict() for e in self.entries]
        return d


def _iso(value: _dt.datetime | None) -> str | None:
    return value.isoformat() if value else None


def build_report(session: Session, *, run_id: int | None = None, limit: int = 25,
                 min_score: float | None = None,
                 recommendations: list[str] | None = None) -> OpportunityReport:
    if run_id is None:
        run_id = session.execute(
            select(PipelineRun.id).where(PipelineRun.status == "complete")
            .order_by(PipelineRun.id.desc()).limit(1)).scalar()
    if run_id is None:
        return OpportunityReport(generated_at=utcnow().isoformat(), run_id=-1,
                                 scoring_config="", calibrated=False,
                                 warnings=["No completed pipeline run exists."])

    run = session.get(PipelineRun, run_id)
    query = (select(OpportunityScore, Domain, Valuation, SaleProbability)
             .join(Domain, Domain.id == OpportunityScore.domain_id)
             .join(Valuation, (Valuation.domain_id == OpportunityScore.domain_id) &
                   (Valuation.run_id == OpportunityScore.run_id))
             .join(SaleProbability,
                   (SaleProbability.domain_id == OpportunityScore.domain_id) &
                   (SaleProbability.run_id == OpportunityScore.run_id))
             .where(OpportunityScore.run_id == run_id))
    if min_score is not None:
        query = query.where(OpportunityScore.score >= min_score)
    if recommendations:
        query = query.where(OpportunityScore.recommendation.in_(recommendations))
    rows = session.execute(
        query.order_by(OpportunityScore.score.desc()).limit(limit)).all()

    # Fetch listings and buyers for the whole page in two queries rather than
    # two per row.
    page_ids = [domain.id for _, domain, _, _ in rows]
    listings_by_domain: dict[int, Listing] = {}
    if page_ids:
        for listing in session.execute(
                select(Listing).where(Listing.domain_id.in_(page_ids),
                                      Listing.is_current.is_(True))
                .order_by(Listing.observed_at)).scalars():
            listings_by_domain[listing.domain_id] = listing
    buyers_by_domain: dict[int, list[BuyerCandidate]] = {}
    if page_ids:
        for buyer in session.execute(
                select(BuyerCandidate).where(BuyerCandidate.domain_id.in_(page_ids))
                .order_by(BuyerCandidate.match_score.desc())).scalars():
            buyers_by_domain.setdefault(buyer.domain_id, []).append(buyer)

    entries: list[ReportEntry] = []
    for score, domain, valuation, probability in rows:
        listing = listings_by_domain.get(domain.id)
        buyers = buyers_by_domain.get(domain.id, [])[:5]
        explanation = score.explanation or {}
        entries.append(ReportEntry(
            rank=score.rank or 0, domain=domain.name,
            recommendation=score.recommendation,
            opportunity_score=score.score, confidence=round(score.confidence, 3),
            asking_price=score.acquisition_price,
            listing_type=listing.listing_type if listing else None,
            auction_end_date=_iso(listing.auction_end_date) if listing else None,
            recommended_max_bid=score.recommended_max_bid,
            retail_low=valuation.retail_value_low,
            retail_mid=valuation.retail_value_mid,
            retail_high=valuation.retail_value_high,
            wholesale_mid=valuation.wholesale_value_mid,
            strategic_high=valuation.strategic_value_high,
            prob_sale_12m=probability.prob_sale_12m,
            prob_sale_24m=probability.prob_sale_24m,
            prob_sale_36m=probability.prob_sale_36m,
            expected_holding_months=probability.expected_holding_months,
            expected_profit_24m=score.expected_profit_24m,
            expected_roi_24m=score.expected_roi_24m,
            buyer_count=score.buyer_count,
            top_buyers=[{"company_name": b.company_name,
                         "company_domain": b.company_domain,
                         "match_type": b.match_type,
                         "match_score": b.match_score,
                         "buyer_value_score": b.buyer_value_score,
                         "reason": b.reason_for_match,
                         "provenance": b.provenance,
                         "evidence_url": b.evidence_url} for b in buyers],
            category=score.category,
            valuation_confidence=valuation.confidence,
            data_gaps=list(score.data_gaps or []),
            top_reasons=list(explanation.get("top_reasons", [])),
            risks=list(explanation.get("risks", []))))

    # Summary counts are aggregated in SQL. Loading every score row to count
    # them in Python costs seconds on a 10,000-domain run and buys nothing.
    by_rec = {rec: int(n) for rec, n in session.execute(
        select(OpportunityScore.recommendation, func.count(OpportunityScore.id))
        .where(OpportunityScore.run_id == run_id)
        .group_by(OpportunityScore.recommendation)).all()}
    scored_total = int(session.execute(
        select(func.count(OpportunityScore.id))
        .where(OpportunityScore.run_id == run_id)).scalar() or 0)
    with_buyers = int(session.execute(
        select(func.count(OpportunityScore.id))
        .where(OpportunityScore.run_id == run_id,
               OpportunityScore.buyer_count > 0)).scalar() or 0)
    positive_ev = int(session.execute(
        select(func.count(OpportunityScore.id))
        .where(OpportunityScore.run_id == run_id,
               OpportunityScore.expected_profit_24m > 0)).scalar() or 0)

    report = OpportunityReport(
        generated_at=utcnow().isoformat(), run_id=run_id,
        scoring_config=run.scoring_config_stamp if run else "",
        calibrated=False, entries=entries,
        summary={
            "domains_scored": scored_total,
            "by_recommendation": dict(sorted(by_rec.items())),
            "with_buyers": with_buyers,
            "positive_expected_profit": positive_ev,
            "data_gaps": (run.data_gaps if run else {}),
        },
        warnings=list(run.warnings) if run else [])
    return report


def render_text(report: OpportunityReport, limit: int = 10) -> str:
    """Plain-text daily report, for a terminal or an email."""
    lines: list[str] = []
    lines.append("=" * 78)
    lines.append("TODAY'S TOP DOMAIN OPPORTUNITIES")
    lines.append(f"generated {report.generated_at}  |  run {report.run_id}  |  "
                 f"scoring config {report.scoring_config}")
    lines.append("=" * 78)
    if report.warnings:
        lines.append("")
        lines.append("DATA AND MODEL WARNINGS")
        for w in report.warnings:
            lines.append(f"  ! {w}")
    lines.append("")
    s = report.summary
    lines.append(f"Scored {s.get('domains_scored', 0)} domain(s); "
                 f"{s.get('positive_expected_profit', 0)} have positive expected "
                 f"profit; {s.get('with_buyers', 0)} have at least one identified buyer.")
    lines.append(f"Recommendations: {s.get('by_recommendation', {})}")
    lines.append("")

    if not report.entries:
        lines.append("No domains matched the report filters.")
        return "\n".join(lines)

    for entry in report.entries[:limit]:
        lines.append("-" * 78)
        price = f"${entry.asking_price:,.0f}" if entry.asking_price is not None else "MISSING"
        lines.append(f"{entry.rank}. {entry.domain}   [{entry.recommendation}]  "
                     f"score {entry.opportunity_score:.0f}/100 "
                     f"(confidence {entry.confidence:.0%})")
        lines.append(f"    Asking / current: {price}"
                     + (f"   auction ends {entry.auction_end_date[:10]}"
                        if entry.auction_end_date else ""))
        if entry.recommended_max_bid is not None:
            lines.append(f"    Maximum recommended bid: ${entry.recommended_max_bid:,.0f}")
        lines.append(f"    Retail value: ${entry.retail_low:,.0f} - "
                     f"${entry.retail_high:,.0f} (mid ${entry.retail_mid:,.0f}, "
                     f"valuation confidence {entry.valuation_confidence:.0f}/100)")
        lines.append(f"    Sale probability: 12m {entry.prob_sale_12m:.1%}  "
                     f"24m {entry.prob_sale_24m:.1%}  36m {entry.prob_sale_36m:.1%}  "
                     f"(expected hold {entry.expected_holding_months:.0f} months)")
        if entry.expected_profit_24m is not None:
            roi = (f"{entry.expected_roi_24m:.0%}"
                   if entry.expected_roi_24m is not None else "n/a")
            lines.append(f"    Expected 24m profit: ${entry.expected_profit_24m:,.0f}"
                         f"   expected ROI: {roi}")
        lines.append(f"    Credible buyers: {entry.buyer_count}")
        for b in entry.top_buyers[:3]:
            tag = "" if b["provenance"] == "OBSERVED" else f" [{b['provenance']}]"
            lines.append(f"      - {b['company_name']}{tag} "
                         f"({b['company_domain'] or 'no domain'}) "
                         f"fit {b['match_score']:.0f}/100 - {b['match_type']}")
        if entry.top_reasons:
            lines.append("    Why it ranks here:")
            for r in entry.top_reasons[:5]:
                lines.append(f"      + {r}")
        if entry.risks:
            lines.append("    Risks:")
            for r in entry.risks[:4]:
                lines.append(f"      - {r}")
        if entry.data_gaps:
            lines.append(f"    MISSING DATA: {', '.join(entry.data_gaps)}")
    lines.append("-" * 78)
    return "\n".join(lines)
