from conftest import fixtures_serp

from presales_scout.collectors.ciso import FixtureBackend, detect_ciso
from presales_scout.collectors.ciso.brightdata_serp import parse_serp_json
from presales_scout.models import Company


def _backend():
    return FixtureBackend(fixtures_serp())


def test_parse_serp_json_normalizes():
    raw = '{"organic": [{"link": "https://x", "title": "T", "description": "D"}]}'
    results = parse_serp_json(raw)
    assert len(results) == 1
    assert results[0].link == "https://x"
    assert results[0].snippet == "D"


def test_detect_visible_ciso():
    sig = detect_ciso(Company(name="Nordfrakt Logistik AB"), _backend())
    assert sig.status == "visible"
    assert sig.confidence >= 0.8
    assert not sig.verify_recommended
    leaders = [p for p in sig.people if p.role_tier == "leader"]
    assert leaders and leaders[0].name == "Anna Svensson"


def test_detect_uncertain_when_only_analyst():
    sig = detect_ciso(Company(name="Sverige Elnat AB"), _backend())
    assert sig.status == "uncertain"
    assert sig.verify_recommended


def test_detect_none_found_for_unknown_company():
    sig = detect_ciso(Company(name="Totally Unknown AB"), _backend())
    assert sig.status == "none_found"
    assert sig.verify_recommended
    assert sig.people == []
