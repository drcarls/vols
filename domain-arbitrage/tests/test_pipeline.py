"""End-to-end: import -> score -> rank, and the stage separation that makes it
auditable."""

import pytest
from sqlalchemy import select

from app.models.analysis import (BuyerCandidate, OpportunityScore, PipelineRun,
                                 SaleProbability, Valuation)
from app.models.core import Domain, DomainFeatures, Enrichment, Listing
from app.services.ingest import ingest_csv
from tests.conftest import EXAMPLE_CSV


def test_ingest_accepts_the_example_file(db):
    report = ingest_csv(db, EXAMPLE_CSV, source_label="test")
    assert report.rows_received == 30
    assert report.rows_accepted == 30
    assert report.rows_rejected == 0
    assert report.new_domains == 30


def test_ingest_rejects_bad_rows_with_reasons_and_keeps_the_good_ones(db):
    csv = (b"domain,asking_price,source\n"
           b"good.com,100,auction\n"
           b"nodots,50,auction\n"
           b"bad_domain.com,50,auction\n"
           b"GOOD.com,120,auction\n")
    report = ingest_csv(db, csv, filename="mixed.csv")
    assert report.rows_accepted == 1
    assert report.rows_rejected == 2
    assert report.rows_duplicate == 1
    reasons = {r["reason"] for r in report.rejections}
    assert any("TLD" in r for r in reasons)
    assert any("invalid label" in r for r in reasons)


def test_ingest_requires_the_domain_column(db):
    with pytest.raises(ValueError, match="missing required column"):
        ingest_csv(db, b"name,price\nfoo.com,10\n", filename="bad.csv")


def test_missing_optional_columns_are_warned_not_defaulted(db):
    report = ingest_csv(db, b"domain\nexample.com\n", filename="minimal.csv")
    assert report.rows_accepted == 1
    assert "asking_price" in report.missing_optional_columns
    assert any("MISSING, not defaulted" in w for w in report.warnings)
    listing = db.execute(select(Listing)).scalar_one()
    assert listing.asking_price is None
    assert listing.effective_price is None


def test_reimporting_supersedes_the_previous_listing(db):
    ingest_csv(db, b"domain,asking_price\nexample.com,100\n", filename="a.csv")
    ingest_csv(db, b"domain,asking_price\nexample.com,80\n", filename="b.csv")
    listings = db.execute(select(Listing).order_by(Listing.id)).scalars().all()
    assert len(listings) == 2
    assert listings[0].is_current is False
    assert listings[1].is_current is True
    assert listings[1].asking_price == 80
    assert db.execute(select(Domain)).scalars().all().__len__() == 1


def test_every_stage_writes_its_own_row(scored_db):
    run = scored_db.execute(select(PipelineRun)).scalar_one()
    assert run.status == "complete"
    assert run.domains_scored == 30
    for model in (DomainFeatures, Valuation, SaleProbability, OpportunityScore):
        count = len(scored_db.execute(select(model)).scalars().all())
        assert count == 30, f"{model.__name__} should have one row per domain"


def test_run_records_its_provider_set_and_config(scored_db):
    run = scored_db.execute(select(PipelineRun)).scalar_one()
    assert run.scoring_config_stamp
    assert "keyword" in run.providers and "buyer" in run.providers
    assert any("UNCALIBRATED" in w for w in run.warnings)


def test_ranking_is_dense_and_ordered(scored_db):
    rows = scored_db.execute(
        select(OpportunityScore).order_by(OpportunityScore.rank)).scalars().all()
    assert [r.rank for r in rows] == list(range(1, len(rows) + 1))
    scores = [r.score for r in rows]
    assert scores == sorted(scores, reverse=True)


def test_every_score_is_reproducible_from_stored_components(scored_db):
    for score in scored_db.execute(select(OpportunityScore)).scalars():
        total = sum(c["contribution"] for c in score.components.values())
        assert total == pytest.approx(score.raw_score, abs=0.05)
        assert score.explanation["component_ranking"]
        assert score.config_stamp


def test_missing_data_is_recorded_rather_than_omitted(scored_db):
    provenances = {e.provenance for e in scored_db.execute(select(Enrichment)).scalars()}
    assert "MISSING" in provenances, \
        "fields we could not source must still be written, marked MISSING"


def test_buyers_carry_provenance_and_a_reason(scored_db):
    buyers = scored_db.execute(select(BuyerCandidate)).scalars().all()
    assert buyers
    for buyer in buyers:
        assert buyer.company_name
        assert buyer.reason_for_match
        assert buyer.match_type
        assert buyer.provenance in {"OBSERVED", "FIXTURE", "LLM_INFERRED"}


def test_scoring_is_deterministic_across_runs(scored_db):
    from app.services.pipeline import run_pipeline

    first = {s.domain_id: s.score for s in
             scored_db.execute(select(OpportunityScore)).scalars()}
    second_run = run_pipeline(scored_db)
    second = {s.domain_id: s.score for s in scored_db.execute(
        select(OpportunityScore).where(
            OpportunityScore.run_id == second_run.run_id)).scalars()}
    assert first == second
