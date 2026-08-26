"""Buyer matching - the primary signal. Every match must be explainable."""

from pathlib import Path

import pytest

from app.providers.buyer import (CompanyFileBuyerProvider, buyer_value_score,
                                 domain_weakness, _norm_name, _strip_modifiers)
from app.providers.buyer import CompanyRecord
from app.scoring.buyer_depth import summarise
from tests.conftest import EXAMPLE_COMPANIES


@pytest.fixture(scope="module")
def provider():
    p = CompanyFileBuyerProvider(Path(EXAMPLE_COMPANIES))
    p.load()
    return p


@pytest.mark.parametrize("sld,expected", [
    ("getflow", "flow"), ("myfleetanalyticshq", "fleetanalytics"),
    ("flow", "flow"), ("theapphub", "app"),
])
def test_modifier_stripping(sld, expected):
    assert _strip_modifiers(sld) == expected


def test_company_name_normalisation_drops_legal_suffixes():
    assert _norm_name("XYZ Fleet Systems, Inc.") == "xyzfleetsystems"
    assert _norm_name("Acme GmbH") == "acme"


def test_domain_weakness_scores_and_explains():
    score, reasons = domain_weakness("get-fleet-analytics-hq.io")
    assert score == 100.0
    assert any(".io" in r for r in reasons)
    assert any("hyphen" in r for r in reasons)
    assert domain_weakness("fleetanalytics.com") == (0.0, [])
    assert domain_weakness(None) == (0.0, [])


def test_exact_alternate_tld_is_the_strongest_match(provider):
    result = provider.find_buyers("fleetanalytics.com", "fleetanalytics", "com",
                                  ["fleet", "analytics"])
    top = result.candidates[0]
    assert top.match_type == "exact_alt_tld"
    assert top.match_score >= 95
    assert "fleetanalytics.io" == top.company_domain


def test_modifier_variant_is_found(provider):
    result = provider.find_buyers("fleetanalytics.com", "fleetanalytics", "com",
                                  ["fleet", "analytics"])
    types = {c.match_type for c in result.candidates}
    assert "modifier_stripped" in types


def test_every_candidate_has_a_reason_and_a_source(provider):
    result = provider.find_buyers("berlinroofing.com", "berlinroofing", "com",
                                  ["berlin", "roofing"])
    assert result.candidates
    for candidate in result.candidates:
        assert candidate.reason_for_match
        assert candidate.source
        assert 0 <= candidate.match_score <= 100
        assert 0 <= candidate.buyer_value_score <= 100


def test_the_current_owner_is_not_proposed_as_a_buyer(provider):
    result = provider.find_buyers("fleetanalytics.io", "fleetanalytics", "io",
                                  ["fleet", "analytics"])
    assert all(c.company_domain != "fleetanalytics.io" for c in result.candidates)


def test_a_company_appears_once_at_its_best_match(provider):
    result = provider.find_buyers("berlinroofing.com", "berlinroofing", "com",
                                  ["berlin", "roofing"])
    domains = [c.company_domain for c in result.candidates]
    assert len(domains) == len(set(domains))


def test_unmatched_domain_returns_a_searched_empty_result(provider):
    result = provider.find_buyers("zzqqxx.com", "zzqqxx", "com", ["zzqqxx"])
    assert result.candidates == []
    assert result.searched is True
    assert result.is_missing is False
    assert summarise(result).missing is False


def test_buyer_value_score_is_zero_confidence_without_economics():
    bare = CompanyRecord(company_name="Nameless Co", company_domain="x.com")
    score, confidence, basis = buyer_value_score(bare)
    assert score == 0.0
    assert confidence == 0.0
    assert "no economic data" in basis


def test_buyer_value_rises_with_size():
    small = CompanyRecord("A", "a.com", employee_count=5)
    large = CompanyRecord("B", "b.com", employee_count=5000)
    assert buyer_value_score(large)[0] > buyer_value_score(small)[0]


def test_depth_value_discounts_unknown_economics(provider):
    result = provider.find_buyers("fleetanalytics.com", "fleetanalytics", "com",
                                  ["fleet", "analytics"])
    depth = summarise(result)
    assert depth.count > 0
    assert depth.depth_value > 0
    assert 0.0 <= depth.economic_coverage <= 1.0
    assert depth.strong_count <= depth.count
