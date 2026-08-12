from conftest import fixtures_serp

from questa_scout.collectors.serp import FixtureBackend
from questa_scout.models import Company
from questa_scout.pipeline import run
from questa_scout.context_map import derive_findings


def _backend():
    return FixtureBackend(fixtures_serp())


def test_ranking_prioritizes_regulated_adopting_ungoverned():
    companies = [
        # Regulated (PHI), active AI, no visible governance owner -> top.
        Company(name="Cascade Health Partners", naics_code="621111", employees=900),
        # Not a regulated-data sector -> should rank bottom.
        Company(name="TinyShop LLC", naics_code="448140", employees=15),
    ]
    reports = run(companies, _backend(), check_web=False)
    assert reports[0].company.name == "Cascade Health Partners"
    assert reports[-1].company.name == "TinyShop LLC"
    assert reports[0].fit_score > reports[-1].fit_score


def test_governed_scores_lower_than_ungoverned_peer():
    companies = [
        Company(name="Meridian Trust Bank", naics_code="522110", employees=1200),   # has CPO
        Company(name="Ungoverned Bank", naics_code="522110", employees=1200),        # no fixture
    ]
    reports = run(companies, _backend(), check_web=False)
    by_name = {r.company.name: r for r in reports}
    assert by_name["Ungoverned Bank"].fit_score > by_name["Meridian Trust Bank"].fit_score


def test_phi_sensitivity_breaks_ties_above_consumer_pii():
    companies = [
        Company(name="PHI Co", naics_code="621111", employees=300),      # PHI, sensitivity 4
        Company(name="PII Co", naics_code="561440", employees=300),      # consumer_pii, sensitivity 2
    ]
    reports = run(companies, _backend(), check_web=False)
    by_name = {r.company.name: r for r in reports}
    # Same adoption/governance (none), so the PHI sensitivity bonus wins.
    assert by_name["PHI Co"].fit_score > by_name["PII Co"].fit_score


def test_saas_routes_to_developer_product():
    reports = run(
        [Company(name="DocuFlow Software Inc", naics_code="511210", employees=140)],
        _backend(),
        check_web=False,
    )
    assert reports[0].product == "Questa Developer (API)"


def test_findings_lead_with_shadow_ai_for_adopting_ungoverned():
    reports = run(
        [Company(name="Cascade Health Partners", naics_code="621111", employees=900)],
        _backend(),
        check_web=False,
    )
    findings = derive_findings(reports[0])
    assert findings, "expected at least one mapped finding"
    assert findings[0].finding_id == "AI_SHADOW_RISK"
    # PHI escalates severity to critical.
    assert findings[0].severity == "critical"
