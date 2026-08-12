from conftest import fixtures_serp

from presales_scout.collectors.ciso import FixtureBackend
from presales_scout.models import Company
from presales_scout.pipeline import run


def test_ranking_prioritizes_in_scope_weak_no_ciso():
    companies = [
        # In NIS2 scope, no visible CISO (no fixture) -> should rank top.
        Company(name="Hot Prospect AB", sni_code="49410", employees=200, domain=None),
        # Out of NIS2 scope -> should rank bottom despite no CISO.
        Company(name="Cold Corp AB", sni_code="70220", employees=500, domain=None),
    ]
    reports = run(companies, FixtureBackend(fixtures_serp()), check_email=False)
    assert reports[0].company.name == "Hot Prospect AB"
    assert reports[0].fit_score > reports[-1].fit_score
    assert reports[-1].company.name == "Cold Corp AB"


def test_visible_ciso_scores_lower_than_missing():
    backend = FixtureBackend(fixtures_serp())
    reports = run(
        [
            Company(name="Nordfrakt Logistik AB", sni_code="49410", employees=180),
            Company(name="No Ciso AB", sni_code="49410", employees=180),
        ],
        backend,
        check_email=False,
    )
    by_name = {r.company.name: r for r in reports}
    assert by_name["No Ciso AB"].fit_score > by_name["Nordfrakt Logistik AB"].fit_score
