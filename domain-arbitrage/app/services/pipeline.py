"""Pipeline orchestration.

Stage order is fixed and one-directional, mirroring the separation the whole
design rests on:

    DATA -> FEATURES -> BUYERS -> COMPARABLES -> VALUATION -> PROBABILITY
         -> EXPECTED VALUE -> RANKING / DECISION

Later stages read earlier ones; nothing reads backwards. Each stage writes its
own table, so the intermediate state of any prediction survives.

A run records which providers were live. That is what lets you say six months
from now: "these 400 predictions were made with no keyword data and a fixture
buyer file, so their errors mean something different from these 90".
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Sequence

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.analysis import (BuyerCandidate, ComparableMatch,
                                 ComparableSale, OpportunityScore, PipelineRun,
                                 SaleProbability, Valuation)
from app.models.core import Domain, DomainFeatures, Enrichment, Listing
from app.providers.base import BuyerProvider, KeywordProvider
from app.provenance import utcnow
from app.scoring import comparables as comps_mod
from app.scoring import opportunity as opp_mod
from app.scoring import probability as prob_mod
from app.scoring import valuation as val_mod
from app.scoring.buyer_depth import summarise as summarise_buyers
from app.scoring.classify import classify
from app.scoring.config import ScoringConfig, get_scoring_config
from app.scoring.features import FEATURES_VERSION, extract_features
from app.services.providers_registry import ProviderSet, build_providers

log = logging.getLogger(__name__)


@dataclass
class RunReport:
    run_id: int
    domains_scored: int
    duration_seconds: float
    providers: dict[str, Any]
    data_gaps: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def _load_comparables(session: Session) -> list[comps_mod.CompRecord]:
    rows = session.execute(select(ComparableSale)).scalars().all()
    out: list[comps_mod.CompRecord] = []
    for r in rows:
        kf = r.keyword_features or {}
        out.append(comps_mod.CompRecord(
            id=r.id, domain=r.domain, sale_price=float(r.sale_price),
            tld=r.tld or "", word_count=r.word_count or 0, length=r.length or 0,
            category=r.category, words=list(r.words or []),
            cpc=kf.get("cpc"), search_volume=kf.get("search_volume"),
            sale_date=r.sale_date, venue=r.venue))
    return out


def run_pipeline(session: Session, *, domain_ids: Sequence[int] | None = None,
                 cfg: ScoringConfig | None = None,
                 providers: ProviderSet | None = None,
                 batch_size: int = 500) -> RunReport:
    """Score domains and persist every intermediate stage."""
    started = time.time()
    settings = get_settings()
    cfg = cfg or get_scoring_config()
    providers = providers or build_providers()

    run = PipelineRun(
        started_at=utcnow(), status="running",
        scoring_config_stamp=cfg.stamp, features_version=FEATURES_VERSION,
        providers=providers.describe())
    session.add(run)
    session.flush()

    warnings: list[str] = list(providers.warnings)
    if not cfg.calibrated:
        warnings.append(
            f"Scoring config {cfg.stamp} is UNCALIBRATED: {cfg.calibration_note}")

    comp_records = _load_comparables(session)
    if not comp_records:
        warnings.append(
            "No comparable sales loaded. Valuations rest entirely on the "
            "heuristic prior. Load real sales with scripts/load_comparables.py.")

    query = select(Domain)
    if domain_ids is not None:
        query = query.where(Domain.id.in_(list(domain_ids)))
    domains = session.execute(query).scalars().all()

    gap_counts: dict[str, int] = {}
    scored = 0

    for start in range(0, len(domains), batch_size):
        chunk = domains[start:start + batch_size]
        _score_chunk(session, run, cfg, providers, comp_records, chunk,
                     gap_counts, settings)
        scored += len(chunk)
        session.flush()
        log.info("scored %d/%d domains", scored, len(domains))

    # Rank within the run. Done in one pass at the end because rank is a
    # property of the cohort, not of a domain.
    ranked = session.execute(
        select(OpportunityScore.id)
        .where(OpportunityScore.run_id == run.id)
        .order_by(OpportunityScore.score.desc())).scalars().all()
    if ranked:
        session.execute(
            update(OpportunityScore),
            [{"id": row_id, "rank": position}
             for position, row_id in enumerate(ranked, start=1)])

    run.finished_at = utcnow()
    run.status = "complete"
    run.domains_scored = scored
    run.warnings = warnings
    run.data_gaps = gap_counts
    session.flush()

    return RunReport(run_id=run.id, domains_scored=scored,
                     duration_seconds=round(time.time() - started, 2),
                     providers=providers.describe(), data_gaps=gap_counts,
                     warnings=warnings)


def _score_chunk(session: Session, run: PipelineRun, cfg: ScoringConfig,
                 providers: ProviderSet,
                 comp_records: list[comps_mod.CompRecord],
                 domains: Sequence[Domain], gap_counts: dict[str, int],
                 settings) -> None:
    """Score one chunk of domains with batched database access.

    Per-domain round trips are what make a 10,000-row run unusable, so this
    prefetches what it needs for the whole chunk, accumulates rows in memory,
    and writes them in bulk statements at the end. The scoring logic itself is
    unchanged and still runs one domain at a time.
    """
    keyword_provider: KeywordProvider = providers.keyword
    buyer_provider: BuyerProvider = providers.buyer
    domain_ids = [d.id for d in domains]

    # ---- prefetch --------------------------------------------------------
    existing_features = {
        f.domain_id: f for f in session.execute(
            select(DomainFeatures).where(
                DomainFeatures.domain_id.in_(domain_ids),
                DomainFeatures.features_version == FEATURES_VERSION)).scalars()}
    existing_enrichments = {
        (e.domain_id, e.field, e.source): e for e in session.execute(
            select(Enrichment).where(Enrichment.domain_id.in_(domain_ids))).scalars()}

    # Current listings, fetched once. Reaching through ``domain.listings`` would
    # emit a lazy-load query per domain.
    current_listings: dict[int, Listing] = {}
    for listing in session.execute(
            select(Listing).where(Listing.domain_id.in_(domain_ids))
            .order_by(Listing.is_current, Listing.observed_at)).scalars():
        current_listings[listing.domain_id] = listing

    # Buyer and comparable matches are fully replaced on each run, so clear the
    # whole chunk in two statements rather than two per domain.
    session.execute(delete(BuyerCandidate).where(
        BuyerCandidate.domain_id.in_(domain_ids)))
    session.execute(delete(ComparableMatch).where(
        ComparableMatch.domain_id.in_(domain_ids)))

    feature_rows: list[dict] = []
    enrichment_rows: list[dict] = []
    buyer_rows: list[dict] = []
    comp_match_rows: list[dict] = []
    valuation_rows: list[dict] = []
    probability_rows: list[dict] = []
    score_rows: list[dict] = []

    for domain in domains:
        # ---- FEATURES ----------------------------------------------------
        features = extract_features(domain.sld, domain.tld)
        payload = _feature_payload(features)
        current = existing_features.get(domain.id)
        if current is None:
            feature_rows.append({"domain_id": domain.id,
                                 "features_version": FEATURES_VERSION} | payload)
        else:
            for key, value in payload.items():
                setattr(current, key, value)

        # ---- SEMANTIC CLASSIFICATION -------------------------------------
        classification = classify(domain.name, features.words, providers.llm)
        category = classification.category.value

        # ---- KEYWORD / COMMERCIAL ENRICHMENT -----------------------------
        keywords = keyword_provider.fetch(domain.name, features.words)
        if keywords.category.is_missing and not classification.category.is_missing:
            keywords.category = classification.category
        if keywords.geo_specificity.is_missing:
            keywords.geo_specificity = classification.geo_specificity
        if keywords.intent_type.is_missing:
            keywords.intent_type = classification.intent_type

        # One merged dict so a field answered by both sources is written once
        # rather than colliding on the (domain, field, source) constraint.
        _collect_enrichments(domain.id,
                             {**classification.as_records(), **keywords.as_records()},
                             existing_enrichments, enrichment_rows)

        # ---- BUYER DEPTH -------------------------------------------------
        buyer_result = buyer_provider.find_buyers(
            domain.name, domain.sld, domain.tld, features.words, category)
        for candidate in buyer_result.candidates:
            buyer_rows.append({
                "domain_id": domain.id, "run_id": run.id,
                "company_name": candidate.company_name,
                "company_domain": candidate.company_domain,
                "reason_for_match": candidate.reason_for_match,
                "match_type": candidate.match_type,
                "match_score": candidate.match_score,
                "company_size_estimate": candidate.company_size_estimate,
                "employee_count": candidate.employee_count,
                "funding_if_known": candidate.funding_if_known,
                "funding_currency": candidate.funding_currency,
                "last_funding_date": candidate.last_funding_date,
                "industry": candidate.industry,
                "buyer_value_score": candidate.buyer_value_score,
                "evidence_url": candidate.evidence_url,
                "provenance": candidate.provenance.value,
                "source": candidate.source,
                "retrieved_at": candidate.retrieved_at,
                "confidence": candidate.confidence,
                "llm_rationale": candidate.llm_rationale})
        buyers = summarise_buyers(buyer_result)

        # ---- COMPARABLES -------------------------------------------------
        cpc = None if keywords.cpc_usd.is_missing else float(keywords.cpc_usd.value)
        comp_stats = comps_mod.analyse(
            domain.tld, features.words, features.sld_length, features.word_count,
            category, cpc, comp_records)
        for used in comp_stats.used:
            comp_match_rows.append({
                "domain_id": domain.id, "run_id": run.id,
                "comparable_id": used["comparable_id"],
                "similarity": used["similarity"],
                "similarity_breakdown": used["breakdown"],
                "weight": used["weight"]})

        # ---- VALUATION ---------------------------------------------------
        valuation = val_mod.estimate(cfg, domain.tld, features, keywords,
                                     buyers, comp_stats)

        listing = current_listings.get(domain.id)
        price = listing.effective_price if listing else None

        # ---- PROBABILITY -------------------------------------------------
        probability = prob_mod.estimate(
            cfg, domain.tld, features, keywords, buyers, comp_stats, category,
            price, valuation.retail_value_mid)

        # ---- EXPECTED VALUE + DECISION -----------------------------------
        economics = opp_mod.compute_economics(cfg, price, valuation, probability)
        commercial_intent = (None if keywords.commercial_intent.is_missing
                             else float(keywords.commercial_intent.value))
        components = opp_mod.compute_components(
            cfg, features, buyers, comp_stats, valuation, probability,
            economics, commercial_intent, domain.tld, category)
        score, raw_score, confidence, enriched = opp_mod.score_from_components(
            cfg, components, valuation.confidence, probability.confidence)
        recommendation, gates = opp_mod.recommend(cfg, score, economics, buyers)
        explanation = opp_mod.build_explanation(
            domain.name, enriched, economics, valuation, probability, buyers,
            features, category, gates, cfg)

        all_gaps = sorted(set(valuation.data_gaps) | set(probability.data_gaps))
        for gap in all_gaps:
            gap_counts[gap] = gap_counts.get(gap, 0) + 1

        valuation_rows.append({
            "domain_id": domain.id, "run_id": run.id,
            "wholesale_value_low": valuation.wholesale_value_low,
            "wholesale_value_mid": valuation.wholesale_value_mid,
            "wholesale_value_high": valuation.wholesale_value_high,
            "retail_value_low": valuation.retail_value_low,
            "retail_value_mid": valuation.retail_value_mid,
            "retail_value_high": valuation.retail_value_high,
            "strategic_value_high": valuation.strategic_value_high,
            "confidence": valuation.confidence, "method": valuation.method,
            "config_stamp": cfg.stamp, "components": valuation.components,
            "comparables_available": valuation.comparables_available,
            "comparable_stats": valuation.comparable_stats,
            "data_gaps": valuation.data_gaps, "provenance": "ESTIMATED",
            "computed_at": utcnow()})

        probability_rows.append({
            "domain_id": domain.id, "run_id": run.id,
            "prob_sale_12m": probability.prob_sale_12m,
            "prob_sale_24m": probability.prob_sale_24m,
            "prob_sale_36m": probability.prob_sale_36m,
            "annual_hazard": probability.annual_hazard,
            "expected_holding_months": probability.expected_holding_months,
            "base_log_odds": probability.base_log_odds,
            "terms": probability.terms, "model": probability.model,
            "config_stamp": cfg.stamp, "confidence": probability.confidence,
            "data_gaps": probability.data_gaps, "provenance": "ESTIMATED",
            "computed_at": utcnow()})

        score_rows.append({
            "domain_id": domain.id, "run_id": run.id, "score": score,
            "raw_score": raw_score, "rank": None,
            "recommendation": recommendation,
            "acquisition_price": economics.acquisition_price,
            "gross_spread": economics.gross_spread,
            "multiple_on_cost": economics.multiple_on_cost,
            "expected_sale_value_24m": economics.expected_sale_value_24m,
            "expected_profit_24m": economics.expected_profit_24m,
            "expected_roi_24m": economics.expected_roi_24m,
            "annualized_opportunity_score": economics.annualized_opportunity_score,
            "recommended_max_bid": economics.recommended_max_bid,
            "capital_required": economics.capital_required,
            "estimated_renewal_costs_24m": economics.estimated_renewal_costs_24m,
            "expected_transaction_costs": economics.expected_transaction_costs,
            "components": enriched, "explanation": explanation,
            "confidence": confidence, "category": category,
            "buyer_count": buyers.count, "config_stamp": cfg.stamp,
            "data_gaps": all_gaps, "computed_at": utcnow()})

    # ---- bulk write ------------------------------------------------------
    for model, rows in ((DomainFeatures, feature_rows),
                        (Enrichment, enrichment_rows),
                        (BuyerCandidate, buyer_rows),
                        (ComparableMatch, comp_match_rows),
                        (Valuation, valuation_rows),
                        (SaleProbability, probability_rows),
                        (OpportunityScore, score_rows)):
        if rows:
            session.execute(insert(model), rows)


def _feature_payload(features) -> dict[str, Any]:
    return {
        "length": features.length, "sld_length": features.sld_length,
        "word_count": features.word_count, "words": list(features.words),
        "has_hyphen": features.has_hyphen, "has_digit": features.has_digit,
        "digit_count": features.digit_count, "hyphen_count": features.hyphen_count,
        "syllable_count": features.syllable_count, "vowel_ratio": features.vowel_ratio,
        "max_consonant_run": features.max_consonant_run,
        "dictionary_word_count": features.dictionary_word_count,
        "all_words_dictionary": features.all_words_dictionary,
        "is_single_dictionary_word": features.is_single_dictionary_word,
        "is_plural": features.is_plural, "prefix": features.prefix,
        "suffix": features.suffix,
        "has_generic_modifier": features.has_generic_modifier,
        "acronym_likelihood": features.acronym_likelihood,
        "segmentation_confidence": features.segmentation_confidence,
        "mean_word_zipf": features.mean_word_zipf,
        "pronounceability": features.pronounceability,
        "memorability": features.memorability,
        "spelling_ambiguity": features.spelling_ambiguity,
        "semantic_coherence": features.semantic_coherence,
        "brandability": features.brandability,
        "business_name_plausibility": features.business_name_plausibility,
        "components": features.components, "computed_at": utcnow(),
    }


def _collect_enrichments(domain_id: int, records: dict,
                         existing: dict[tuple[int, str, str], Enrichment],
                         out_rows: list[dict]) -> None:
    """Queue enrichment writes, updating in place where a row already exists.

    MISSING values are recorded too. The absence of data is a fact worth
    timestamping, and it is what makes the coverage report honest.
    """
    # Collapse within-call duplicates: two providers can legitimately answer the
    # same field, and only one row per (domain, field, source) may exist.
    deduped: dict[tuple[str, str], Any] = {}
    for field_name, sourced in records.items():
        deduped[(field_name, sourced.source)] = sourced

    for (field_name, source), sourced in deduped.items():
        value = sourced.value
        payload = {
            "value_num": float(value) if isinstance(value, (int, float))
                         and not isinstance(value, bool) else None,
            "value_text": str(value) if isinstance(value, str) else None,
            "value_json": value if isinstance(value, (dict, list)) else None,
            "provenance": sourced.provenance.value,
            "source": source,
            "retrieved_at": sourced.retrieved_at,
            "confidence": sourced.confidence,
            "evidence_url": sourced.evidence_url,
            "note": sourced.note,
        }
        current = existing.get((domain_id, field_name, source))
        if current is None:
            out_rows.append({"domain_id": domain_id, "field": field_name} | payload)
        else:
            for key, val in payload.items():
                setattr(current, key, val)
