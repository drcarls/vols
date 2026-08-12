from conftest import fixtures_serp

from questa_scout.collectors.serp import FixtureBackend
from questa_scout.dashboard import render_dashboard
from questa_scout.models import Company
from questa_scout.pipeline import run


def _reports():
    companies = [
        Company(name="Cascade Health Partners", naics_code="621111", employees=900),
        Company(name="TinyShop LLC", naics_code="448140", employees=15),
    ]
    return run(companies, FixtureBackend(fixtures_serp()), check_web=False)


def test_dashboard_is_self_contained_html():
    html = render_dashboard(_reports())
    assert html.lstrip().lower().startswith("<!doctype html>")
    assert "<title>Prospect Scout for Questa</title>" in html
    # no external asset references (CSP would block them)
    assert 'src="http' not in html and 'href="http' not in html
    # no unfilled format braces leaked into the markup body
    assert "{r.fit_score" not in html


def test_dashboard_renders_a_card_per_prospect():
    reports = _reports()
    html = render_dashboard(reports)
    assert html.count('class="card"') == len(reports)
    assert "Cascade Health Partners" in html
    # the top prospect's headline finding code should surface
    assert "AI_SHADOW_RISK" in html
