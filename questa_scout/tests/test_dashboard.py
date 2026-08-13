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


def test_dashboard_renders_an_expandable_row_per_prospect():
    reports = _reports()
    html = render_dashboard(reports)
    assert html.count('class="row"') == len(reports)
    assert "Cascade Health Partners" in html
    # interactive affordances present
    assert 'id="theme"' in html and 'data-filter="genai"' in html
    assert 'class="detail"' in html


def test_dashboard_shows_the_live_queries_as_evidence():
    html = render_dashboard(_reports())
    # the actual SERP queries behind the signals are surfaced in the evidence
    assert "site:linkedin.com/jobs" in html
    assert "site:linkedin.com/in" in html
    # the pre-sales angle (talking point) is rendered
    assert "Angle" in html
