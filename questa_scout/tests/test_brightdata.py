import pytest

from questa_scout.collectors.serp import BrightDataSerpBackend, parse_serp_json
from questa_scout.collectors.serp.query import build_jobs_query, build_governance_query


def test_requires_token():
    with pytest.raises(ValueError):
        BrightDataSerpBackend("")


def test_google_url_carries_query_and_geo():
    b = BrightDataSerpBackend("tok", zone="serp")
    url = b._google_url(build_jobs_query("Acme Inc"), "us", "en")
    assert "google.com/search" in url
    assert "gl=us" in url and "hl=en" in url
    assert "brd_json=1" in url
    assert "Acme+Inc" in url  # company name url-encoded into q


def test_parse_serp_json_normalizes_both_shapes():
    payload = {"organic": [
        {"link": "https://www.linkedin.com/in/x", "title": "X - Chief Privacy Officer - Acme", "description": "d"},
    ]}
    out = parse_serp_json(payload)
    assert len(out) == 1
    assert out[0].link.endswith("/in/x")
    assert "Chief Privacy Officer" in out[0].title


def test_governance_and_jobs_queries_differ():
    assert "linkedin.com/in" in build_governance_query("Acme")
    assert "linkedin.com/jobs" in build_jobs_query("Acme")
