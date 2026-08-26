"""Data-integrity rules.

These are the tests that matter most. The system's entire value depends on
never converting missing information into invented information, so the rules
are enforced here rather than left to reviewer vigilance.
"""

from app.providers.base import KeywordMetrics
from app.providers.buyer import NullBuyerProvider
from app.providers.keyword import NullKeywordProvider
from app.provenance import Provenance, derived, missing, observed
from app.scoring.buyer_depth import summarise


def test_null_keyword_provider_reports_missing_not_zero():
    metrics = NullKeywordProvider().fetch("example.com", ["example"])
    assert set(metrics.missing_fields()) == set(KeywordMetrics.__dataclass_fields__)
    for name in KeywordMetrics.__dataclass_fields__:
        field = getattr(metrics, name)
        assert field.value is None
        assert field.provenance is Provenance.MISSING
        assert field.confidence == 0.0


def test_null_buyer_provider_distinguishes_unsearched_from_empty():
    result = NullBuyerProvider().find_buyers("example.com", "example", "com", [])
    assert result.candidates == []
    assert result.searched is False
    assert result.is_missing is True

    depth = summarise(result)
    assert depth.missing is True, "not searching must not read as zero buyers"
    assert depth.count == 0


def test_searched_but_empty_is_not_missing():
    from app.providers.base import BuyerSearchResult
    result = BuyerSearchResult(candidates=[], provenance=Provenance.OBSERVED,
                               source="test", searched=True,
                               note="looked and found nobody")
    depth = summarise(result)
    assert depth.missing is False, "a completed search with no hits is a finding"
    assert depth.count == 0


def test_sourced_values_carry_full_provenance():
    value = observed(12.5, "test.source", confidence=0.9,
                     evidence_url="https://example.invalid/evidence")
    payload = value.to_dict()
    for key in ("value", "provenance", "source", "retrieved_at", "confidence",
                "evidence_url"):
        assert key in payload
    assert payload["provenance"] == "OBSERVED"


def test_missing_value_requires_an_explicit_fallback():
    value = missing("test.source", "no data")
    assert value.is_missing is True
    assert value.or_else(7) == 7
    assert derived(3, "test").or_else(7) == 3


def test_fixture_data_is_labelled_and_off_by_default():
    # Check the field default rather than an instance: the test environment
    # deliberately enables fixtures, so an instance would read that back.
    from app.config import Settings
    assert Settings.model_fields["allow_fixture_data"].default is False

    from app.providers.buyer import ExampleFixtureBuyerProvider
    from app.services.providers_registry import EXAMPLE_COMPANY_FILE
    provider = ExampleFixtureBuyerProvider(EXAMPLE_COMPANY_FILE)
    result = provider.find_buyers("fleetanalytics.com", "fleetanalytics", "com",
                                  ["fleet", "analytics"])
    assert result.candidates, "fixture file should match the example domains"
    for candidate in result.candidates:
        assert candidate.provenance is Provenance.FIXTURE


def test_fixture_provider_is_not_selected_without_the_flag(monkeypatch):
    from app.config import get_settings
    from app.services import providers_registry

    get_settings.cache_clear()
    monkeypatch.setenv("ALLOW_FIXTURE_DATA", "false")
    monkeypatch.delenv("BUYER_COMPANY_CSV_PATH", raising=False)
    try:
        providers = providers_registry.build_providers()
        assert providers.buyer.available is False
        assert any("BUYER DATA MISSING" in w for w in providers.warnings)
    finally:
        get_settings.cache_clear()


def test_missing_keyword_data_never_becomes_a_number(scored_db):
    """A domain with no keyword row must show MISSING, not an imputed value."""
    from sqlalchemy import select

    from app.models.core import Domain, Enrichment

    domain = scored_db.execute(
        select(Domain).where(Domain.name == "harborlogistics.com")).scalar_one()
    rows = {e.field: e for e in scored_db.execute(
        select(Enrichment).where(Enrichment.domain_id == domain.id)).scalars()}
    cpc = rows.get("cpc_usd")
    assert cpc is not None, "the absence itself must be recorded"
    assert cpc.provenance == "MISSING"
    assert cpc.value_num is None
