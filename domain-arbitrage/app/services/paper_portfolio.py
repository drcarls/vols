"""Paper portfolio: record predictions, later record outcomes, then score the
model against them.

The reason this exists: every valuation and probability in this system is an
uncalibrated prior. The only way to find out whether any of it has predictive
power - and specifically whether *buyer depth* has predictive power - is to
freeze predictions with a timestamp and a config version, then compare them
with what actually happened.

Nothing here may write a model output into an outcome field.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analysis import (BuyerCandidate, OpportunityScore,
                                 SaleProbability, Valuation)
from app.models.core import Domain, DomainFeatures, Enrichment
from app.models.paper import PaperObservation, PaperPosition
from app.provenance import utcnow

VALID_STATUSES = {"PAPER_BUY", "PAPER_WATCH", "PAPER_PASS", "CLOSED"}
VALID_OUTCOMES = {"SOLD", "UNSOLD", "LOST_AUCTION", "EXPIRED_UNSOLD", "UNKNOWN"}


class PaperPortfolioError(ValueError):
    pass


def _signal_snapshot(session: Session, domain: Domain, score: OpportunityScore,
                     valuation: Valuation, probability: SaleProbability) -> dict[str, Any]:
    """Freeze exactly the signals the predictive-power analysis will test.

    Stored on the position rather than recomputed later, because the feature
    code and scoring config both move. A prediction has to be judged against the
    signals that produced it, not against today's version of them.
    """
    buyers = session.execute(
        select(BuyerCandidate).where(BuyerCandidate.domain_id == domain.id)).scalars().all()
    credible = [b for b in buyers if b.match_score >= 50.0]
    enrichments = {e.field: e for e in session.execute(
        select(Enrichment).where(Enrichment.domain_id == domain.id)).scalars()}
    features = session.execute(
        select(DomainFeatures).where(DomainFeatures.domain_id == domain.id)
        .order_by(DomainFeatures.computed_at.desc())).scalars().first()

    def num(field: str) -> float | None:
        e = enrichments.get(field)
        if e is None or e.provenance == "MISSING" or e.value_num is None:
            return None
        return float(e.value_num)

    components = score.components or {}
    return {
        "buyer_depth_count": len(credible),
        "buyer_depth_strong_count": sum(1 for b in credible if b.match_score >= 78.0),
        "buyer_depth_value": round(sum((b.match_score / 100.0) *
                                       ((b.buyer_value_score / 100.0) if b.buyer_value_score > 0 else 0.25)
                                       for b in credible), 4),
        "buyer_quality_max": max((b.buyer_value_score for b in credible), default=0.0),
        "buyer_provenance": (credible[0].provenance if credible else "MISSING"),
        "search_volume": num("search_volume"),
        "cpc": num("cpc_usd"),
        "commercial_intent": num("commercial_intent"),
        "brandability": components.get("brandability", {}).get("value"),
        "length": len(domain.sld),
        "word_count": features.word_count if features else None,
        "pronounceability": features.pronounceability if features else None,
        "asking_price": score.acquisition_price,
        "retail_value_mid": valuation.retail_value_mid,
        "wholesale_value_mid": valuation.wholesale_value_mid,
        "prob_sale_24m": probability.prob_sale_24m,
        "opportunity_score": score.score,
        "expected_roi_24m": score.expected_roi_24m,
        "category": score.category,
        "tld": domain.tld,
        "data_gaps": list(score.data_gaps or []),
    }


def open_position(session: Session, domain_name: str, *,
                  status: str = "PAPER_BUY", run_id: int | None = None,
                  notes: str | None = None) -> PaperPosition:
    """Freeze the current prediction for a domain as a paper position."""
    if status not in VALID_STATUSES:
        raise PaperPortfolioError(
            f"status must be one of {sorted(VALID_STATUSES)}, got {status!r}")

    domain = session.execute(
        select(Domain).where(Domain.name == domain_name.lower())).scalar_one_or_none()
    if domain is None:
        raise PaperPortfolioError(f"domain {domain_name!r} has not been imported")

    score_q = select(OpportunityScore).where(OpportunityScore.domain_id == domain.id)
    if run_id is not None:
        score_q = score_q.where(OpportunityScore.run_id == run_id)
    score = session.execute(
        score_q.order_by(OpportunityScore.run_id.desc())).scalars().first()
    if score is None:
        raise PaperPortfolioError(
            f"domain {domain_name!r} has not been scored; run the pipeline first")

    valuation = session.execute(select(Valuation).where(
        Valuation.domain_id == domain.id,
        Valuation.run_id == score.run_id)).scalar_one()
    probability = session.execute(select(SaleProbability).where(
        SaleProbability.domain_id == domain.id,
        SaleProbability.run_id == score.run_id)).scalar_one()

    existing = session.execute(select(PaperPosition).where(
        PaperPosition.domain_id == domain.id,
        PaperPosition.outcome.is_(None))).scalars().first()
    if existing is not None:
        raise PaperPortfolioError(
            f"an unresolved paper position already exists for {domain_name!r} "
            f"(id={existing.id}); resolve it before opening another")

    position = PaperPosition(
        domain_id=domain.id, domain_name=domain.name, run_id=score.run_id,
        status=status, date_seen=utcnow(), asking_price=score.acquisition_price,
        predicted_wholesale_value=valuation.wholesale_value_mid,
        predicted_retail_value=valuation.retail_value_mid,
        predicted_retail_low=valuation.retail_value_low,
        predicted_retail_high=valuation.retail_value_high,
        predicted_sale_probability_12m=probability.prob_sale_12m,
        predicted_sale_probability_24m=probability.prob_sale_24m,
        predicted_sale_probability_36m=probability.prob_sale_36m,
        opportunity_score=score.score,
        recommended_max_bid=score.recommended_max_bid,
        expected_profit_24m=score.expected_profit_24m,
        expected_roi_24m=score.expected_roi_24m,
        recommendation=score.recommendation,
        signal_snapshot=_signal_snapshot(session, domain, score, valuation, probability),
        config_stamp=score.config_stamp, notes=notes)
    session.add(position)
    session.flush()
    return position


def record_observation(session: Session, position_id: int, *, event_type: str,
                       sold: bool | None = None, observed_price: float | None = None,
                       listing_price: float | None = None, venue: str | None = None,
                       bid_count: int | None = None, source: str = "manual",
                       evidence_url: str | None = None,
                       note: str | None = None,
                       observed_at: _dt.datetime | None = None) -> PaperObservation:
    """Record an OBSERVED fact about a position.

    Resolving observations (an auction result, a confirmed sale) also set the
    position's outcome. Everything else is history that accumulates.
    """
    position = session.get(PaperPosition, position_id)
    if position is None:
        raise PaperPortfolioError(f"no paper position with id {position_id}")

    observation = PaperObservation(
        position_id=position.id, observed_at=observed_at or utcnow(),
        event_type=event_type, sold=sold, observed_price=observed_price,
        listing_price=listing_price, venue=venue, bid_count=bid_count,
        source=source, evidence_url=evidence_url, note=note)
    session.add(observation)

    if event_type in {"SOLD", "AUCTION_RESULT"} and sold is not None:
        if sold:
            position.outcome = "SOLD"
            position.outcome_price = observed_price
            position.outcome_date = observation.observed_at
        elif event_type == "AUCTION_RESULT":
            position.outcome = "LOST_AUCTION"
            position.outcome_date = observation.observed_at
        else:
            position.outcome = "UNSOLD"
            position.outcome_date = observation.observed_at
        position.outcome_resolved_at = utcnow()
    elif event_type == "DELISTED":
        position.outcome = "EXPIRED_UNSOLD"
        position.outcome_date = observation.observed_at
        position.outcome_resolved_at = utcnow()

    session.flush()
    return observation


@dataclass
class PerformanceReport:
    """Model performance. Every figure states its own sample size, and any
    figure with no supporting data reports None rather than 0."""

    evaluated: int = 0
    paper_bought: int = 0
    resolved: int = 0
    unresolved: int = 0
    sold: int = 0
    unsold: int = 0
    lost_auction: int = 0
    observed_sale_rate: float | None = None
    mean_predicted_prob_24m: float | None = None
    calibration_gap: float | None = None
    mean_modeled_roi: float | None = None
    mean_observed_roi: float | None = None
    median_valuation_error_ratio: float | None = None
    mean_absolute_log_error: float | None = None
    false_positives: int | None = None
    false_negatives: int | None = None
    sufficient_data: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


MIN_RESOLVED_FOR_STATS = 10


def performance(session: Session) -> PerformanceReport:
    """Compare frozen predictions against observed outcomes."""
    import math
    import statistics

    report = PerformanceReport()
    report.evaluated = int(session.execute(
        select(func.count(func.distinct(OpportunityScore.domain_id)))).scalar() or 0)

    positions = session.execute(select(PaperPosition)).scalars().all()
    report.paper_bought = sum(1 for p in positions if p.status == "PAPER_BUY")

    resolved = [p for p in positions if p.outcome is not None]
    report.resolved = len(resolved)
    report.unresolved = len(positions) - len(resolved)
    report.sold = sum(1 for p in resolved if p.outcome == "SOLD")
    report.unsold = sum(1 for p in resolved
                        if p.outcome in {"UNSOLD", "EXPIRED_UNSOLD"})
    report.lost_auction = sum(1 for p in resolved if p.outcome == "LOST_AUCTION")

    if not positions:
        report.notes.append(
            "No paper positions have been opened. Mark domains PAPER_BUY to "
            "start recording predictions.")
        return report

    # Positions where the outcome is decided by whether the domain sold. Lost
    # auctions are excluded: we never held the asset, so its sale says nothing
    # about our prediction.
    testable = [p for p in resolved if p.outcome in {"SOLD", "UNSOLD",
                                                     "EXPIRED_UNSOLD"}]
    if len(testable) < MIN_RESOLVED_FOR_STATS:
        report.notes.append(
            f"Only {len(testable)} resolved position(s) with a sale/no-sale "
            f"outcome. At least {MIN_RESOLVED_FOR_STATS} are needed before any "
            f"performance statistic is meaningful; statistics are withheld "
            f"rather than reported on a sample this small.")
        return report

    report.sufficient_data = True
    sold_set = [p for p in testable if p.outcome == "SOLD"]
    report.observed_sale_rate = round(len(sold_set) / len(testable), 4)

    predicted = [p.predicted_sale_probability_24m for p in testable
                 if p.predicted_sale_probability_24m is not None]
    if predicted:
        report.mean_predicted_prob_24m = round(sum(predicted) / len(predicted), 4)
        report.calibration_gap = round(
            report.observed_sale_rate - report.mean_predicted_prob_24m, 4)

    modeled_rois = [p.expected_roi_24m for p in testable if p.expected_roi_24m is not None]
    if modeled_rois:
        report.mean_modeled_roi = round(sum(modeled_rois) / len(modeled_rois), 4)

    # Observed ROI: only computable where we know both what we would have paid
    # and what it actually fetched. Unsold positions realise -100% of capital
    # under the horizon convention (no residual is credited to an observation,
    # because a residual is a model output, not an observation).
    observed_rois: list[float] = []
    for p in testable:
        if p.asking_price is None or p.asking_price <= 0:
            continue
        if p.outcome == "SOLD" and p.outcome_price is not None:
            observed_rois.append((p.outcome_price - p.asking_price) / p.asking_price)
        elif p.outcome in {"UNSOLD", "EXPIRED_UNSOLD"}:
            observed_rois.append(-1.0)
    if observed_rois:
        report.mean_observed_roi = round(sum(observed_rois) / len(observed_rois), 4)

    # Valuation error, measured in log space because valuations span orders of
    # magnitude. Only sold positions have an observed price to compare against.
    errors = [math.log(p.outcome_price / p.predicted_retail_value)
              for p in sold_set
              if p.outcome_price and p.predicted_retail_value
              and p.outcome_price > 0 and p.predicted_retail_value > 0]
    if errors:
        report.mean_absolute_log_error = round(
            sum(abs(e) for e in errors) / len(errors), 4)
        report.median_valuation_error_ratio = round(
            math.exp(statistics.median(errors)), 4)
    else:
        report.notes.append(
            "No sold position has an observed sale price, so valuation error "
            "cannot be measured yet.")

    # A false positive is a domain we recommended buying that did not sell; a
    # false negative is one we passed on that did.
    report.false_positives = sum(
        1 for p in testable
        if p.recommendation in {"STRONG_BUY", "BUY"} and p.outcome != "SOLD")
    report.false_negatives = sum(
        1 for p in testable
        if p.recommendation in {"PASS", "AVOID"} and p.outcome == "SOLD")
    return report
