"""Buyer, comparable, valuation, probability and decision tables."""

from __future__ import annotations

import datetime as _dt

from sqlalchemy import (JSON, Boolean, Float, ForeignKey, Index, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UtcDateTime
from app.provenance import utcnow


class PipelineRun(Base):
    """One execution of the scoring pipeline.

    Every downstream score points at a run, and the run records the exact
    scoring-config stamp and provider set used. That is what makes an old
    prediction reproducible.
    """

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)
    finished_at: Mapped[_dt.datetime | None] = mapped_column(UtcDateTime, default=None)
    status: Mapped[str] = mapped_column(String(32), default="running")
    scoring_config_stamp: Mapped[str] = mapped_column(String(64), default="")
    features_version: Mapped[str] = mapped_column(String(32), default="")
    providers: Mapped[dict] = mapped_column(JSON, default=dict)
    domains_scored: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    data_gaps: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, default=None)


class BuyerCandidate(Base):
    """A company that could rationally want this domain.

    INTEGRITY RULE: rows here are only ever created from a company record that
    already existed in some source (a provider response, an uploaded company
    file). The *match* is derived by this system; the *company* never is. A row
    whose provenance is FIXTURE came from synthetic example data and is not
    evidence of anything.
    """

    __tablename__ = "buyer_candidates"
    __table_args__ = (
        UniqueConstraint("domain_id", "company_domain", "match_type",
                         name="uq_buyer_domain_company_match"),
        Index("ix_buyer_domain_score", "domain_id", "buyer_value_score"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"),
                                           index=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("pipeline_runs.id"), default=None)

    company_name: Mapped[str] = mapped_column(String(512))
    company_domain: Mapped[str | None] = mapped_column(String(255), default=None)
    reason_for_match: Mapped[str] = mapped_column(Text, default="")
    match_type: Mapped[str] = mapped_column(String(64), default="unknown")
    match_score: Mapped[float] = mapped_column(Float, default=0.0)          # 0..100
    company_size_estimate: Mapped[str | None] = mapped_column(String(64), default=None)
    employee_count: Mapped[int | None] = mapped_column(Integer, default=None)
    funding_if_known: Mapped[float | None] = mapped_column(Float, default=None)
    funding_currency: Mapped[str | None] = mapped_column(String(8), default=None)
    last_funding_date: Mapped[_dt.datetime | None] = mapped_column(UtcDateTime, default=None)
    industry: Mapped[str | None] = mapped_column(String(255), default=None)
    buyer_value_score: Mapped[float] = mapped_column(Float, default=0.0)    # 0..100
    evidence_url: Mapped[str | None] = mapped_column(Text, default=None)

    provenance: Mapped[str] = mapped_column(String(16), default="MISSING", index=True)
    source: Mapped[str] = mapped_column(String(128), default="unknown")
    retrieved_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    llm_rationale: Mapped[str | None] = mapped_column(Text, default=None)


class ComparableSale(Base):
    """A recorded domain sale. OBSERVED price evidence.

    Ships EMPTY. Load real sales (e.g. a NameBio export) via
    ``scripts/load_comparables.py``. The valuation engine reports
    ``comparables_available: false`` rather than inventing a comp set.
    """

    __tablename__ = "comparable_sales"
    __table_args__ = (
        UniqueConstraint("domain", "sale_date", "venue", name="uq_comp_sale"),
        Index("ix_comp_tld_words", "tld", "word_count"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    sld: Mapped[str] = mapped_column(String(255), default="")
    tld: Mapped[str] = mapped_column(String(64), default="", index=True)
    sale_price: Mapped[float] = mapped_column(Float)
    sale_date: Mapped[_dt.datetime | None] = mapped_column(UtcDateTime, default=None, index=True)
    venue: Mapped[str | None] = mapped_column(String(128), default=None)
    length: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    words: Mapped[list] = mapped_column(JSON, default=list)
    category: Mapped[str | None] = mapped_column(String(128), default=None, index=True)
    keyword_features: Mapped[dict] = mapped_column(JSON, default=dict)

    provenance: Mapped[str] = mapped_column(String(16), default="OBSERVED")
    source: Mapped[str] = mapped_column(String(128), default="unknown")
    evidence_url: Mapped[str | None] = mapped_column(Text, default=None)
    retrieved_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)


class ComparableMatch(Base):
    """Which comps were used for which domain, and why. Makes comp-based
    valuation auditable rather than a black box."""

    __tablename__ = "comparable_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"),
                                           index=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("pipeline_runs.id"), default=None)
    comparable_id: Mapped[int] = mapped_column(ForeignKey("comparable_sales.id",
                                                          ondelete="CASCADE"))
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
    similarity_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    weight: Mapped[float] = mapped_column(Float, default=0.0)


class Valuation(Base):
    """Wholesale / retail / strategic value estimates. ESTIMATED."""

    __tablename__ = "valuations"
    __table_args__ = (UniqueConstraint("domain_id", "run_id", name="uq_valuation_run"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"),
                                           index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("pipeline_runs.id"), index=True)

    wholesale_value_low: Mapped[float | None] = mapped_column(Float, default=None)
    wholesale_value_mid: Mapped[float | None] = mapped_column(Float, default=None)
    wholesale_value_high: Mapped[float | None] = mapped_column(Float, default=None)
    retail_value_low: Mapped[float | None] = mapped_column(Float, default=None)
    retail_value_mid: Mapped[float | None] = mapped_column(Float, default=None)
    retail_value_high: Mapped[float | None] = mapped_column(Float, default=None)
    strategic_value_high: Mapped[float | None] = mapped_column(Float, default=None)

    confidence: Mapped[float] = mapped_column(Float, default=0.0)           # 0..100
    method: Mapped[str] = mapped_column(String(64), default="heuristic_v0")
    config_stamp: Mapped[str] = mapped_column(String(64), default="")
    provenance: Mapped[str] = mapped_column(String(16), default="ESTIMATED")

    # Full multiplicative decomposition: base, each multiplier, comp blend.
    components: Mapped[dict] = mapped_column(JSON, default=dict)
    comparables_available: Mapped[bool] = mapped_column(Boolean, default=False)
    comparable_stats: Mapped[dict] = mapped_column(JSON, default=dict)
    data_gaps: Mapped[list] = mapped_column(JSON, default=list)
    computed_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)


class SaleProbability(Base):
    """Probability of sale over 12 / 24 / 36 months. ESTIMATED."""

    __tablename__ = "sale_probabilities"
    __table_args__ = (UniqueConstraint("domain_id", "run_id", name="uq_prob_run"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"),
                                           index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("pipeline_runs.id"), index=True)

    prob_sale_12m: Mapped[float] = mapped_column(Float, default=0.0)
    prob_sale_24m: Mapped[float] = mapped_column(Float, default=0.0)
    prob_sale_36m: Mapped[float] = mapped_column(Float, default=0.0)
    annual_hazard: Mapped[float] = mapped_column(Float, default=0.0)
    expected_holding_months: Mapped[float] = mapped_column(Float, default=0.0)

    base_log_odds: Mapped[float] = mapped_column(Float, default=0.0)
    terms: Mapped[dict] = mapped_column(JSON, default=dict)   # driver -> {z, coef, contribution}
    model: Mapped[str] = mapped_column(String(64), default="logodds_heuristic_v0")
    config_stamp: Mapped[str] = mapped_column(String(64), default="")
    provenance: Mapped[str] = mapped_column(String(16), default="ESTIMATED")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    data_gaps: Mapped[list] = mapped_column(JSON, default=list)
    computed_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)


class OpportunityScore(Base):
    """The decision layer: ranking score, economics and recommendation."""

    __tablename__ = "opportunity_scores"
    __table_args__ = (
        UniqueConstraint("domain_id", "run_id", name="uq_score_run"),
        Index("ix_score_run_score", "run_id", "score"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"),
                                           index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("pipeline_runs.id"), index=True)

    score: Mapped[float] = mapped_column(Float, default=0.0)          # 0..100, confidence-adjusted
    raw_score: Mapped[float] = mapped_column(Float, default=0.0)      # before confidence adjustment
    rank: Mapped[int | None] = mapped_column(Integer, default=None, index=True)
    recommendation: Mapped[str] = mapped_column(String(16), default="PASS")

    # Economics. All arithmetic, all reproducible from stored inputs.
    acquisition_price: Mapped[float | None] = mapped_column(Float, default=None)
    gross_spread: Mapped[float | None] = mapped_column(Float, default=None)
    multiple_on_cost: Mapped[float | None] = mapped_column(Float, default=None)
    expected_sale_value_24m: Mapped[float | None] = mapped_column(Float, default=None)
    expected_profit_24m: Mapped[float | None] = mapped_column(Float, default=None)
    expected_roi_24m: Mapped[float | None] = mapped_column(Float, default=None)
    annualized_opportunity_score: Mapped[float | None] = mapped_column(Float, default=None)
    recommended_max_bid: Mapped[float | None] = mapped_column(Float, default=None)
    capital_required: Mapped[float | None] = mapped_column(Float, default=None)
    estimated_renewal_costs_24m: Mapped[float | None] = mapped_column(Float, default=None)
    expected_transaction_costs: Mapped[float | None] = mapped_column(Float, default=None)

    components: Mapped[dict] = mapped_column(JSON, default=dict)   # name -> {value, weight, contribution}
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)  # reasons, risks, assumptions
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    category: Mapped[str | None] = mapped_column(String(128), default=None, index=True)
    buyer_count: Mapped[int] = mapped_column(Integer, default=0)
    config_stamp: Mapped[str] = mapped_column(String(64), default="")
    data_gaps: Mapped[list] = mapped_column(JSON, default=list)
    computed_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)


class LlmCacheEntry(Base):
    """Content-addressed LLM response cache. Keeps cost bounded and makes runs
    reproducible: same prompt + same model => same stored JSON."""

    __tablename__ = "llm_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    cache_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    model: Mapped[str] = mapped_column(String(128))
    task: Mapped[str] = mapped_column(String(64), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    response_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)
    tokens_in: Mapped[int | None] = mapped_column(Integer, default=None)
    tokens_out: Mapped[int | None] = mapped_column(Integer, default=None)
