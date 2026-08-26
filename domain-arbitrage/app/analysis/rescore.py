"""Re-score a completed run under a different scoring configuration.

The pipeline's expensive stages - feature extraction, classification, buyer
matching, comparable search - do not depend on the scoring config at all. Only
valuation, probability and the decision layer do. So a config sweep does not
need to re-run the pipeline: it reloads the stored stage inputs once and
replays the last three stages in memory.

That is what makes a sensitivity sweep affordable, and it is also the
foundation for later backtesting: "what would the model have said about these
domains under the coefficients we fitted last month?"

Nothing here writes to the database. A re-score is analysis, not a prediction,
and must never be mistaken for one.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import (BuyerCandidate, OpportunityScore, PipelineRun,
                                 Valuation)
from app.models.core import Domain, DomainFeatures, Enrichment
from app.providers.base import BuyerCandidateRecord, BuyerSearchResult, KeywordMetrics
from app.provenance import Provenance, Sourced, missing
from app.scoring import comparables as comps_mod
from app.scoring import opportunity as opp_mod
from app.scoring import probability as prob_mod
from app.scoring import valuation as val_mod
from app.scoring.buyer_depth import BuyerDepth, summarise
from app.scoring.config import ScoringConfig
from app.scoring.features import DomainFeatureSet

_KEYWORD_FIELDS = tuple(KeywordMetrics.__dataclass_fields__)


@dataclass
class StageInputs:
    """Everything the config-dependent stages need, for one domain."""

    domain_id: int
    name: str
    sld: str
    tld: str
    features: DomainFeatureSet
    keywords: KeywordMetrics
    buyers: BuyerDepth
    comps: comps_mod.ComparableStats
    category: str | None
    price: float | None


@dataclass
class ScoredRow:
    """The output of one re-score. Mirrors ``opportunity_scores`` in memory."""

    domain_id: int
    domain: str
    score: float
    raw_score: float
    confidence: float
    recommendation: str
    retail_value_mid: float
    wholesale_value_mid: float
    valuation_confidence: float
    prob_sale_24m: float
    expected_profit_24m: float | None
    expected_roi_24m: float | None
    recommended_max_bid: float | None
    acquisition_price: float | None
    buyer_count: int
    category: str | None
    components: dict[str, Any] = field(default_factory=dict)


def _features_from_row(row: DomainFeatures) -> DomainFeatureSet:
    names = set(DomainFeatureSet.__dataclass_fields__)
    return DomainFeatureSet(**{
        name: getattr(row, name) for name in names if hasattr(row, name)})


def _keywords_from_enrichments(rows: Sequence[Enrichment]) -> KeywordMetrics:
    """Rebuild KeywordMetrics, preserving MISSING as MISSING.

    A field with no stored row, or a row marked MISSING, comes back missing.
    Reconstruction must not quietly upgrade an absence into a value - that
    would make a sweep look better-evidenced than the run it replays.
    """
    by_field: dict[str, Enrichment] = {}
    for row in rows:
        # Prefer a non-MISSING row when several sources answered the same field.
        current = by_field.get(row.field)
        if current is None or (current.provenance == "MISSING"
                               and row.provenance != "MISSING"):
            by_field[row.field] = row

    values: dict[str, Sourced[Any]] = {}
    for name in _KEYWORD_FIELDS:
        row = by_field.get(name)
        if row is None or row.provenance == "MISSING":
            values[name] = missing("rescore", "not recorded on the original run")
            continue
        raw = row.value_num if row.value_num is not None else (
            row.value_text if row.value_text is not None else row.value_json)
        if raw is None:
            values[name] = missing("rescore", "stored value was null")
            continue
        values[name] = Sourced(
            value=raw, provenance=Provenance(row.provenance), source=row.source,
            retrieved_at=row.retrieved_at, confidence=row.confidence,
            evidence_url=row.evidence_url, note=row.note)
    return KeywordMetrics(**values)


def _buyers_from_rows(rows: Sequence[BuyerCandidate], *, searched: bool) -> BuyerDepth:
    """Rebuild buyer depth by replaying the same aggregation the pipeline used.

    ``searched`` comes from the run's recorded provider set. It is the
    difference between "no buyers exist" and "we never looked", and it cannot
    be inferred from an empty candidate list.
    """
    if not searched:
        return summarise(BuyerSearchResult(
            candidates=[], provenance=Provenance.MISSING, source="rescore",
            searched=False, note="buyer provider was unavailable on the "
                                 "original run"))
    candidates = [
        BuyerCandidateRecord(
            company_name=row.company_name, company_domain=row.company_domain,
            reason_for_match=row.reason_for_match, match_type=row.match_type,
            match_score=row.match_score, buyer_value_score=row.buyer_value_score,
            provenance=Provenance(row.provenance), source=row.source,
            evidence_url=row.evidence_url,
            company_size_estimate=row.company_size_estimate,
            employee_count=row.employee_count,
            funding_if_known=row.funding_if_known,
            funding_currency=row.funding_currency,
            last_funding_date=row.last_funding_date, industry=row.industry,
            confidence=row.confidence, retrieved_at=row.retrieved_at)
        for row in rows]
    provenance = candidates[0].provenance if candidates else Provenance.OBSERVED
    return summarise(BuyerSearchResult(
        candidates=candidates, provenance=provenance,
        source=(rows[0].source if rows else "rescore"), searched=True))


def _comps_from_stats(stored: dict[str, Any] | None) -> comps_mod.ComparableStats:
    if not stored:
        return comps_mod.ComparableStats(available=False, count=0,
                                         note="no comparable stats stored")
    allowed = set(comps_mod.ComparableStats.__dataclass_fields__)
    return comps_mod.ComparableStats(**{k: v for k, v in stored.items()
                                        if k in allowed})


def load_stage_inputs(session: Session, run_id: int) -> list[StageInputs]:
    """Read back everything a re-score needs, in a fixed number of queries."""
    run = session.get(PipelineRun, run_id)
    if run is None:
        raise ValueError(f"no pipeline run with id {run_id}")

    buyer_searched = bool((run.providers or {}).get("buyer", {}).get("available"))

    rows = session.execute(
        select(OpportunityScore, Domain, Valuation, DomainFeatures)
        .join(Domain, Domain.id == OpportunityScore.domain_id)
        .join(Valuation, (Valuation.domain_id == OpportunityScore.domain_id) &
              (Valuation.run_id == OpportunityScore.run_id))
        .join(DomainFeatures, DomainFeatures.domain_id == OpportunityScore.domain_id)
        .where(OpportunityScore.run_id == run_id)).all()
    if not rows:
        return []

    domain_ids = [domain.id for _, domain, _, _ in rows]

    enrichments: dict[int, list[Enrichment]] = defaultdict(list)
    buyers: dict[int, list[BuyerCandidate]] = defaultdict(list)
    # Chunked so a large run stays well under the bound-parameter limit.
    for start in range(0, len(domain_ids), 500):
        chunk = domain_ids[start:start + 500]
        for row in session.execute(
                select(Enrichment).where(Enrichment.domain_id.in_(chunk))).scalars():
            enrichments[row.domain_id].append(row)
        for row in session.execute(
                select(BuyerCandidate).where(
                    BuyerCandidate.domain_id.in_(chunk))).scalars():
            buyers[row.domain_id].append(row)

    inputs: list[StageInputs] = []
    for score, domain, valuation, features_row in rows:
        inputs.append(StageInputs(
            domain_id=domain.id, name=domain.name, sld=domain.sld, tld=domain.tld,
            features=_features_from_row(features_row),
            keywords=_keywords_from_enrichments(enrichments[domain.id]),
            buyers=_buyers_from_rows(buyers[domain.id], searched=buyer_searched),
            comps=_comps_from_stats(valuation.comparable_stats),
            category=score.category,
            # The acquisition price is taken from the stored score rather than
            # re-read from the listing, so a re-score replays the economics the
            # original prediction actually saw.
            price=score.acquisition_price))
    return inputs


def rescore_one(cfg: ScoringConfig, item: StageInputs) -> ScoredRow:
    """Replay valuation -> probability -> decision for one domain."""
    valuation = val_mod.estimate(cfg, item.tld, item.features, item.keywords,
                                 item.buyers, item.comps)
    probability = prob_mod.estimate(
        cfg, item.tld, item.features, item.keywords, item.buyers, item.comps,
        item.category, item.price, valuation.retail_value_mid)
    economics = opp_mod.compute_economics(cfg, item.price, valuation, probability)
    commercial_intent = (None if item.keywords.commercial_intent.is_missing
                         else float(item.keywords.commercial_intent.value))
    components = opp_mod.compute_components(
        cfg, item.features, item.buyers, item.comps, valuation, probability,
        economics, commercial_intent, item.tld, item.category)
    score, raw_score, confidence, enriched = opp_mod.score_from_components(
        cfg, components, valuation.confidence, probability.confidence)
    recommendation, _gates = opp_mod.recommend(cfg, score, economics, item.buyers)

    return ScoredRow(
        domain_id=item.domain_id, domain=item.name, score=score,
        raw_score=raw_score, confidence=confidence, recommendation=recommendation,
        retail_value_mid=valuation.retail_value_mid,
        wholesale_value_mid=valuation.wholesale_value_mid,
        valuation_confidence=valuation.confidence,
        prob_sale_24m=probability.prob_sale_24m,
        expected_profit_24m=economics.expected_profit_24m,
        expected_roi_24m=economics.expected_roi_24m,
        recommended_max_bid=economics.recommended_max_bid,
        acquisition_price=economics.acquisition_price,
        buyer_count=item.buyers.count, category=item.category,
        components=enriched)


def rescore(cfg: ScoringConfig, inputs: Sequence[StageInputs]) -> list[ScoredRow]:
    """Re-score a whole cohort, highest score first."""
    rows = [rescore_one(cfg, item) for item in inputs]
    rows.sort(key=lambda r: r.score, reverse=True)
    return rows
