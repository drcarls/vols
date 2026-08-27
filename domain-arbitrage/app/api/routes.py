"""HTTP API.

Route design follows the pipeline stages, so the URL structure mirrors the
data flow: import -> run -> domains -> report -> portfolio -> paper -> analysis.

Two conventions worth knowing:

  * ``/api/domains/{name}`` returns the FULL audit trail for one domain -
    listing, features, enrichments with provenance, buyers with evidence,
    comparables used, valuation walk, probability terms, and the score
    decomposition. That endpoint is the answer to "defend this number".
  * Anything derived from synthetic fixture data is flagged in ``warnings``
    on the response, not buried in a field somewhere.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analysis import sensitivity as sensitivity_mod
from app.analysis.signal_power import analyse as analyse_signals
from app.config import get_settings
from app.db.base import get_db
from app.models.analysis import (BuyerCandidate, ComparableMatch,
                                 ComparableSale, OpportunityScore, PipelineRun,
                                 SaleProbability, Valuation)
from app.models.core import Domain, DomainFeatures, Enrichment, ImportBatch, Listing
from app.models.paper import PaperPosition
from app.schemas.api import (CloseWindowRequest, IngestResponse,
                             ObservationRequest, PaperPositionRequest,
                             PortfolioRequest, RankedResponse, RankedRow,
                             RunRequest, RunResponse, SampleRequest)
from app.scoring.config import get_scoring_config
from app.services import paper_portfolio as paper_svc
from app.services import paper_sampler as sampler
from app.services import reconcile as reconcile_svc
from app.services import portfolio as portfolio_svc
from app.services import report as report_svc
from app.services.ingest import ingest_csv
from app.services.pipeline import run_pipeline
from app.services.providers_registry import build_providers

router = APIRouter(prefix="/api")


def _latest_run_id(db: Session) -> int | None:
    return db.execute(select(PipelineRun.id).where(PipelineRun.status == "complete")
                      .order_by(PipelineRun.id.desc()).limit(1)).scalar()


# --------------------------------------------------------------------------
# health and configuration
# --------------------------------------------------------------------------

@router.get("/health")
def health() -> dict[str, Any]:
    cfg = get_scoring_config()
    providers = build_providers()
    return {
        "status": "ok",
        "scoring_config": cfg.stamp,
        "calibrated": cfg.calibrated,
        "calibration_warning": cfg.calibration_note,
        "providers": providers.describe(),
    }


@router.get("/config")
def config() -> dict[str, Any]:
    """The full scoring configuration, so weights are inspectable at runtime."""
    cfg = get_scoring_config()
    s = get_settings()
    return {
        "stamp": cfg.stamp, "version": cfg.version, "calibrated": cfg.calibrated,
        "calibration_note": cfg.calibration_note,
        "config": cfg.raw,
        "runtime": {
            "keyword_provider": s.keyword_provider,
            "buyer_provider": s.buyer_provider,
            "llm_provider": s.llm_provider,
            "allow_fixture_data": s.allow_fixture_data,
            "database_url": s.database_url.split("://", 1)[0] + "://...",
        },
    }


# --------------------------------------------------------------------------
# import
# --------------------------------------------------------------------------

@router.post("/import", response_model=IngestResponse)
async def import_csv(file: UploadFile = File(...),
                     source_label: str | None = Query(default=None),
                     db: Session = Depends(get_db)) -> IngestResponse:
    """Upload a CSV of domains. Required column: ``domain``."""
    payload = await file.read()
    try:
        report = ingest_csv(db, payload, filename=file.filename or "upload.csv",
                            source_label=source_label)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return IngestResponse(**report.to_dict())


@router.get("/batches")
def list_batches(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.execute(select(ImportBatch).order_by(ImportBatch.id.desc())).scalars().all()
    return [{"id": b.id, "filename": b.filename, "source_label": b.source_label,
             "rows_received": b.rows_received, "rows_accepted": b.rows_accepted,
             "rows_rejected": b.rows_rejected, "rows_duplicate": b.rows_duplicate,
             "created_at": b.created_at.isoformat(), "warnings": b.warnings}
            for b in rows]


# --------------------------------------------------------------------------
# pipeline
# --------------------------------------------------------------------------

@router.post("/pipeline/run", response_model=RunResponse)
def trigger_run(request: RunRequest | None = None,
                db: Session = Depends(get_db)) -> RunResponse:
    """Score every imported domain (or a subset) and persist all stages."""
    domain_ids = request.domain_ids if request else None
    report = run_pipeline(db, domain_ids=domain_ids)
    db.commit()
    return RunResponse(**report.to_dict())


@router.get("/runs")
def list_runs(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.execute(select(PipelineRun).order_by(PipelineRun.id.desc())).scalars().all()
    return [{"id": r.id, "started_at": r.started_at.isoformat(),
             "finished_at": r.finished_at.isoformat() if r.finished_at else None,
             "status": r.status, "domains_scored": r.domains_scored,
             "scoring_config_stamp": r.scoring_config_stamp,
             "features_version": r.features_version, "providers": r.providers,
             "data_gaps": r.data_gaps, "warnings": r.warnings} for r in rows]


# --------------------------------------------------------------------------
# ranked results
# --------------------------------------------------------------------------

@router.get("/domains", response_model=RankedResponse)
def ranked_domains(run_id: int | None = None, limit: int = Query(50, ge=1, le=1000),
                   offset: int = Query(0, ge=0),
                   min_score: float | None = None,
                   recommendation: str | None = None,
                   category: str | None = None,
                   min_buyers: int | None = None,
                   max_price: float | None = None,
                   db: Session = Depends(get_db)) -> RankedResponse:
    """The ranked table. This is the primary deliverable of the system."""
    run_id = run_id or _latest_run_id(db)
    if run_id is None:
        return RankedResponse(run_id=-1, total=0, offset=offset, limit=limit,
                              rows=[], warnings=["No completed pipeline run exists."])

    base = (select(OpportunityScore, Domain, Valuation, SaleProbability)
            .join(Domain, Domain.id == OpportunityScore.domain_id)
            .join(Valuation, (Valuation.domain_id == OpportunityScore.domain_id) &
                  (Valuation.run_id == OpportunityScore.run_id))
            .join(SaleProbability,
                  (SaleProbability.domain_id == OpportunityScore.domain_id) &
                  (SaleProbability.run_id == OpportunityScore.run_id))
            .where(OpportunityScore.run_id == run_id))
    if min_score is not None:
        base = base.where(OpportunityScore.score >= min_score)
    if recommendation:
        base = base.where(OpportunityScore.recommendation == recommendation.upper())
    if category:
        base = base.where(OpportunityScore.category == category)
    if min_buyers is not None:
        base = base.where(OpportunityScore.buyer_count >= min_buyers)
    if max_price is not None:
        base = base.where(OpportunityScore.acquisition_price <= max_price)

    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = db.execute(base.order_by(OpportunityScore.score.desc())
                      .offset(offset).limit(limit)).all()

    run = db.get(PipelineRun, run_id)
    return RankedResponse(
        run_id=run_id, total=int(total), offset=offset, limit=limit,
        warnings=list(run.warnings) if run else [],
        rows=[RankedRow(
            rank=s.rank, domain=d.name, asking_price=s.acquisition_price,
            retail_value_low=v.retail_value_low, retail_value_mid=v.retail_value_mid,
            retail_value_high=v.retail_value_high, prob_sale_24m=p.prob_sale_24m,
            buyer_count=s.buyer_count, recommended_max_bid=s.recommended_max_bid,
            expected_profit_24m=s.expected_profit_24m,
            expected_roi_24m=s.expected_roi_24m, opportunity_score=s.score,
            confidence=round(s.confidence, 3), recommendation=s.recommendation,
            category=s.category, data_gaps=list(s.data_gaps or []))
            for s, d, v, p in rows])


@router.get("/domains/{name}")
def domain_detail(name: str, run_id: int | None = None,
                  db: Session = Depends(get_db)) -> dict[str, Any]:
    """Complete audit trail for one domain: every input to every number."""
    domain = db.execute(select(Domain).where(Domain.name == name.lower())).scalar_one_or_none()
    if domain is None:
        raise HTTPException(status_code=404, detail=f"domain {name!r} not imported")

    run_id = run_id or _latest_run_id(db)
    score = db.execute(select(OpportunityScore).where(
        OpportunityScore.domain_id == domain.id,
        OpportunityScore.run_id == run_id)).scalar_one_or_none()
    valuation = db.execute(select(Valuation).where(
        Valuation.domain_id == domain.id, Valuation.run_id == run_id)).scalar_one_or_none()
    probability = db.execute(select(SaleProbability).where(
        SaleProbability.domain_id == domain.id,
        SaleProbability.run_id == run_id)).scalar_one_or_none()
    features = db.execute(select(DomainFeatures).where(
        DomainFeatures.domain_id == domain.id)
        .order_by(DomainFeatures.computed_at.desc())).scalars().first()
    listings = db.execute(select(Listing).where(Listing.domain_id == domain.id)
                          .order_by(Listing.observed_at.desc())).scalars().all()
    enrichments = db.execute(select(Enrichment).where(
        Enrichment.domain_id == domain.id)).scalars().all()
    buyers = db.execute(select(BuyerCandidate).where(
        BuyerCandidate.domain_id == domain.id)
        .order_by(BuyerCandidate.match_score.desc())).scalars().all()
    comp_matches = db.execute(
        select(ComparableMatch, ComparableSale)
        .join(ComparableSale, ComparableSale.id == ComparableMatch.comparable_id)
        .where(ComparableMatch.domain_id == domain.id)
        .order_by(ComparableMatch.similarity.desc())).all()
    positions = db.execute(select(PaperPosition).where(
        PaperPosition.domain_id == domain.id)).scalars().all()

    return {
        "domain": {"name": domain.name, "sld": domain.sld, "tld": domain.tld,
                   "is_idn": domain.is_idn, "unicode_name": domain.unicode_name,
                   "first_seen_at": domain.first_seen_at.isoformat(),
                   "last_seen_at": domain.last_seen_at.isoformat()},
        "listings": [{"asking_price": l.asking_price, "current_bid": l.current_bid,
                      "effective_price": l.effective_price, "bid_count": l.bid_count,
                      "source": l.source, "listing_type": l.listing_type,
                      "auction_end_date": l.auction_end_date.isoformat() if l.auction_end_date else None,
                      "expiration_date": l.expiration_date.isoformat() if l.expiration_date else None,
                      "registrar": l.registrar, "traffic": l.traffic,
                      "is_current": l.is_current,
                      "observed_at": l.observed_at.isoformat(),
                      "raw_row": l.raw_row} for l in listings],
        "features": ({k: v for k, v in features.__dict__.items()
                      if not k.startswith("_") and k != "computed_at"}
                     | {"computed_at": features.computed_at.isoformat()}
                     if features else None),
        "enrichments": [{"field": e.field, "value": e.value_num if e.value_num is not None
                         else (e.value_text if e.value_text is not None else e.value_json),
                         "provenance": e.provenance, "source": e.source,
                         "retrieved_at": e.retrieved_at.isoformat(),
                         "confidence": e.confidence, "evidence_url": e.evidence_url,
                         "note": e.note} for e in enrichments],
        "buyers": [{"company_name": b.company_name, "company_domain": b.company_domain,
                    "reason_for_match": b.reason_for_match, "match_type": b.match_type,
                    "match_score": b.match_score,
                    "company_size_estimate": b.company_size_estimate,
                    "employee_count": b.employee_count,
                    "funding_if_known": b.funding_if_known,
                    "industry": b.industry,
                    "buyer_value_score": b.buyer_value_score,
                    "evidence_url": b.evidence_url, "provenance": b.provenance,
                    "source": b.source, "confidence": b.confidence} for b in buyers],
        "comparables_used": [{"domain": c.domain, "sale_price": c.sale_price,
                              "sale_date": c.sale_date.isoformat() if c.sale_date else None,
                              "venue": c.venue, "similarity": m.similarity,
                              "weight": m.weight,
                              "similarity_breakdown": m.similarity_breakdown,
                              "evidence_url": c.evidence_url}
                             for m, c in comp_matches],
        "valuation": ({"wholesale": [valuation.wholesale_value_low,
                                     valuation.wholesale_value_mid,
                                     valuation.wholesale_value_high],
                       "retail": [valuation.retail_value_low,
                                  valuation.retail_value_mid,
                                  valuation.retail_value_high],
                       "strategic_value_high": valuation.strategic_value_high,
                       "confidence": valuation.confidence,
                       "method": valuation.method,
                       "config_stamp": valuation.config_stamp,
                       "comparables_available": valuation.comparables_available,
                       "comparable_stats": valuation.comparable_stats,
                       "walk": valuation.components,
                       "data_gaps": valuation.data_gaps} if valuation else None),
        "probability": ({"prob_sale_12m": probability.prob_sale_12m,
                         "prob_sale_24m": probability.prob_sale_24m,
                         "prob_sale_36m": probability.prob_sale_36m,
                         "annual_hazard": probability.annual_hazard,
                         "expected_holding_months": probability.expected_holding_months,
                         "base_log_odds": probability.base_log_odds,
                         "terms": probability.terms, "model": probability.model,
                         "confidence": probability.confidence,
                         "data_gaps": probability.data_gaps} if probability else None),
        "opportunity": ({"rank": score.rank, "score": score.score,
                         "raw_score": score.raw_score,
                         "confidence": score.confidence,
                         "recommendation": score.recommendation,
                         "economics": {
                             "acquisition_price": score.acquisition_price,
                             "capital_required": score.capital_required,
                             "gross_spread": score.gross_spread,
                             "multiple_on_cost": score.multiple_on_cost,
                             "expected_sale_value_24m": score.expected_sale_value_24m,
                             "expected_profit_24m": score.expected_profit_24m,
                             "expected_roi_24m": score.expected_roi_24m,
                             "annualized_opportunity_score": score.annualized_opportunity_score,
                             "recommended_max_bid": score.recommended_max_bid,
                             "estimated_renewal_costs_24m": score.estimated_renewal_costs_24m,
                             "expected_transaction_costs": score.expected_transaction_costs},
                         "components": score.components,
                         "explanation": score.explanation,
                         "config_stamp": score.config_stamp,
                         "data_gaps": score.data_gaps} if score else None),
        "paper_positions": [{"id": p.id, "status": p.status,
                             "date_seen": p.date_seen.isoformat(),
                             "outcome": p.outcome, "outcome_price": p.outcome_price}
                            for p in positions],
    }


@router.get("/domains/{name}/explain", response_class=PlainTextResponse)
def explain(name: str, run_id: int | None = None,
            db: Session = Depends(get_db)) -> str:
    """Human-readable defence of a domain's score."""
    detail = domain_detail(name, run_id, db)
    opp = detail.get("opportunity")
    if not opp:
        return f"{name} has not been scored."
    exp = opp["explanation"]
    lines = [f"{name} - opportunity score {opp['score']:.1f}/100 "
             f"[{opp['recommendation']}]",
             f"scoring config {opp['config_stamp']} (UNCALIBRATED)", ""]
    lines.append("COMPONENT CONTRIBUTIONS (weighted sum -> raw score "
                 f"{opp['raw_score']:.1f}, confidence-adjusted to {opp['score']:.1f})")
    for c in exp.get("component_ranking", []):
        lines.append(f"  {c['component']:<24s} value {c['value']:>6} "
                     f"x weight {c['weight']:<5} = {c['contribution']:>6}  "
                     f"[{c['status']}]")
        lines.append(f"      {c['why']}")
    lines.append("")
    lines.append("VALUATION WALK")
    walk = exp.get("valuation_walk", {})
    base = walk.get("base", {})
    lines.append(f"  base: ${base.get('value', 0):,.0f} ({base.get('basis','')})")
    for key, value in walk.items():
        if isinstance(value, dict) and "multiplier" in value:
            lines.append(f"  x {value['multiplier']:<6} {key:<22s} {value['basis']}")
    lines.append(f"  = retail mid ${detail['valuation']['retail'][1]:,.0f}")
    lines.append("")
    lines.append("PROBABILITY TERMS (log-odds)")
    for term, data in exp.get("probability_terms", {}).items():
        lines.append(f"  {term:<24s} z={str(data.get('z')):>8s} "
                     f"coef={data.get('coefficient')} "
                     f"contribution={data.get('contribution')} [{data.get('status')}]")
        lines.append(f"      {data.get('note','')}")
    lines.append("")
    if exp.get("risks"):
        lines.append("RISKS")
        for r in exp["risks"]:
            lines.append(f"  - {r}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

@router.get("/report")
def report(run_id: int | None = None, limit: int = Query(25, ge=1, le=200),
           min_score: float | None = None,
           db: Session = Depends(get_db)) -> dict[str, Any]:
    return report_svc.build_report(db, run_id=run_id, limit=limit,
                                   min_score=min_score).to_dict()


@router.get("/report/text", response_class=PlainTextResponse)
def report_text(run_id: int | None = None, limit: int = Query(10, ge=1, le=100),
                db: Session = Depends(get_db)) -> str:
    built = report_svc.build_report(db, run_id=run_id, limit=limit)
    return report_svc.render_text(built, limit=limit)


# --------------------------------------------------------------------------
# portfolio
# --------------------------------------------------------------------------

@router.post("/portfolio")
def portfolio(request: PortfolioRequest,
              db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        result = portfolio_svc.build_portfolio(
            db, budget=request.budget, scenario=request.scenario,
            run_id=request.run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.to_dict()


# --------------------------------------------------------------------------
# paper portfolio
# --------------------------------------------------------------------------

@router.post("/paper/positions")
def open_paper_position(request: PaperPositionRequest,
                        db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        position = paper_svc.open_position(db, request.domain, status=request.status,
                                           run_id=request.run_id, notes=request.notes)
    except paper_svc.PaperPortfolioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return {"id": position.id, "domain": position.domain_name,
            "status": position.status, "date_seen": position.date_seen.isoformat(),
            "asking_price": position.asking_price,
            "predicted_retail_value": position.predicted_retail_value,
            "predicted_sale_probability_24m": position.predicted_sale_probability_24m,
            "opportunity_score": position.opportunity_score,
            "recommended_max_bid": position.recommended_max_bid,
            "config_stamp": position.config_stamp,
            "signal_snapshot": position.signal_snapshot}


@router.get("/paper/positions")
def list_paper_positions(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.execute(select(PaperPosition)
                      .order_by(PaperPosition.date_seen.desc())).scalars().all()
    return [{"id": p.id, "domain": p.domain_name, "status": p.status,
             "date_seen": p.date_seen.isoformat(), "asking_price": p.asking_price,
             "predicted_retail_value": p.predicted_retail_value,
             "predicted_sale_probability_24m": p.predicted_sale_probability_24m,
             "opportunity_score": p.opportunity_score,
             "recommendation": p.recommendation,
             "recommended_max_bid": p.recommended_max_bid,
             "outcome": p.outcome, "outcome_price": p.outcome_price,
             "outcome_date": p.outcome_date.isoformat() if p.outcome_date else None,
             "config_stamp": p.config_stamp,
             "observations": len(p.observations)} for p in rows]


@router.post("/paper/observations")
def add_observation(request: ObservationRequest,
                    db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        obs = paper_svc.record_observation(
            db, request.position_id, event_type=request.event_type,
            sold=request.sold, observed_price=request.observed_price,
            listing_price=request.listing_price, venue=request.venue,
            bid_count=request.bid_count, source=request.source,
            evidence_url=request.evidence_url, note=request.note)
    except paper_svc.PaperPortfolioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    position = db.get(PaperPosition, request.position_id)
    return {"id": obs.id, "position_id": obs.position_id,
            "event_type": obs.event_type, "observed_at": obs.observed_at.isoformat(),
            "position_outcome": position.outcome if position else None,
            "warning": (None if request.evidence_url else
                        "No evidence_url supplied. This outcome cannot be "
                        "independently verified later.")}


@router.post("/paper/sample")
def sample_positions(request: SampleRequest,
                     db: Session = Depends(get_db)) -> dict[str, Any]:
    """Open a stratified cohort of paper positions.

    Samples across score bands AND buyer-depth bands so the cohort can measure
    recall as well as precision, and can tell buyer depth apart from the score
    it contributes to. Defaults to a dry run - read the plan's warnings before
    committing, because a confounded cohort never becomes informative.
    """
    try:
        result = sampler.draw_sample(
            db, size=request.size, cohort=request.cohort, run_id=request.run_id,
            seed=request.seed, max_price=request.max_price,
            banding=request.banding, dry_run=request.dry_run)
    except paper_svc.PaperPortfolioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if request.dry_run:
        db.rollback()
    else:
        db.commit()
    payload = result.to_dict()
    if not request.dry_run:
        payload["health"] = sampler.cohort_health(db, request.cohort).to_dict()
    return payload


@router.get("/paper/cohorts/{cohort}/health")
def cohort_health(cohort: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Can this cohort answer the question it was drawn for?

    Structural check, independent of outcomes. Worth running the day a cohort
    is drawn rather than eighteen months later.
    """
    return sampler.cohort_health(db, None if cohort == "all" else cohort).to_dict()


@router.post("/paper/reconcile")
async def reconcile_outcomes(file: UploadFile = File(...),
                             source: str = Query(default="sales_export"),
                             dry_run: bool = Query(default=True),
                             db: Session = Depends(get_db)) -> dict[str, Any]:
    """Record SOLD for open positions appearing in a sales export.

    Positive evidence only. Positions absent from the file are left open: a
    public feed covers part of the market, so absence is not evidence of a
    failure to sell.
    """
    payload = await file.read()
    sales, problems = reconcile_svc.read_sales(payload)
    report = reconcile_svc.reconcile(db, sales, source=source, dry_run=dry_run)
    report.sales_unparseable = len(problems)
    report.problems = problems[:50]
    if dry_run:
        db.rollback()
    else:
        db.commit()
    return report.to_dict()


@router.post("/paper/close-window")
def close_window(request: CloseWindowRequest,
                 db: Session = Depends(get_db)) -> dict[str, Any]:
    """Resolve positions whose modelled horizon has elapsed.

    Marks them CENSORED unless ``observation_was_complete`` asserts that a sale
    would have reached you. Censored positions are excluded from every
    statistic, which loses power - the correct trade against counting invisible
    sales as failures.
    """
    report = reconcile_svc.close_observation_window(
        db, horizon_months=request.horizon_months,
        observation_was_complete=request.observation_was_complete,
        source=request.source, dry_run=request.dry_run)
    if request.dry_run:
        db.rollback()
    else:
        db.commit()
    return report.to_dict()


@router.get("/paper/performance")
def paper_performance(db: Session = Depends(get_db)) -> dict[str, Any]:
    return paper_svc.performance(db).to_dict()


# --------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------

@router.get("/analysis/signal-power")
def signal_power(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Which signals actually predict resale? Including 'we don't know yet'."""
    return analyse_signals(db).to_dict()


@router.get("/analysis/sensitivity")
def sensitivity(run_id: int | None = None,
                include_ablations: bool = True,
                db: Session = Depends(get_db)) -> dict[str, Any]:
    """Which conclusions survive being wrong about the priors?

    Sweeps each prior across a grid and ablates each ranking component, then
    reports rank stability and level movement SEPARATELY. A stable ranking can
    be acted on before calibration even though every dollar figure is a guess;
    an unstable one cannot.

    Expensive on a large corpus - it re-scores the cohort once per grid point.
    """
    return sensitivity_mod.analyse(
        db, run_id=run_id, include_ablations=include_ablations).to_dict()


@router.get("/analysis/sensitivity/text", response_class=PlainTextResponse)
def sensitivity_text(run_id: int | None = None,
                     include_ablations: bool = True,
                     db: Session = Depends(get_db)) -> str:
    report = sensitivity_mod.analyse(db, run_id=run_id,
                                     include_ablations=include_ablations)
    return sensitivity_mod.render_text(report)


@router.get("/analysis/coverage")
def coverage(run_id: int | None = None,
             db: Session = Depends(get_db)) -> dict[str, Any]:
    """Data completeness: what fraction of domains have each field, by provenance."""
    run_id = run_id or _latest_run_id(db)
    total = db.execute(select(func.count(Domain.id))).scalar() or 0
    rows = db.execute(
        select(Enrichment.field, Enrichment.provenance, func.count(Enrichment.id))
        .group_by(Enrichment.field, Enrichment.provenance)).all()
    by_field: dict[str, dict[str, int]] = {}
    for field, provenance, count in rows:
        by_field.setdefault(field, {})[provenance] = int(count)

    buyer_rows = db.execute(
        select(BuyerCandidate.provenance, func.count(BuyerCandidate.id))
        .group_by(BuyerCandidate.provenance)).all()
    comps_total = db.execute(select(func.count(ComparableSale.id))).scalar() or 0

    run = db.get(PipelineRun, run_id) if run_id else None
    return {
        "domains": total,
        "run_id": run_id,
        "enrichment_by_field": by_field,
        "buyer_candidates_by_provenance": {p: int(c) for p, c in buyer_rows},
        "comparable_sales_loaded": int(comps_total),
        "run_data_gaps": run.data_gaps if run else {},
        "warnings": run.warnings if run else [],
    }
