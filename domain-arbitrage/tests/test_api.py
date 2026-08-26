"""HTTP surface. Checks that the API exposes the audit trail, not just scores."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import EXAMPLE_CSV


@pytest.fixture
def client(scored_db):
    return TestClient(app)


def test_health_declares_the_calibration_status(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["calibrated"] is False
    assert "UNCALIBRATED" in body["calibration_warning"]
    assert "providers" in body


def test_config_endpoint_exposes_every_weight(client):
    body = client.get("/api/config").json()
    weights = body["config"]["opportunity"]["weights"]
    assert sum(weights.values()) == pytest.approx(1.0)
    assert body["config"]["probability"]["base_annual_sell_through"] > 0


def test_ranked_table_has_the_columns_the_brief_asked_for(client):
    body = client.get("/api/domains?limit=5").json()
    assert body["total"] == 30
    row = body["rows"][0]
    for key in ("rank", "domain", "asking_price", "retail_value_mid",
                "prob_sale_24m", "buyer_count", "recommended_max_bid",
                "opportunity_score", "recommendation"):
        assert key in row
    assert body["warnings"], "data-source warnings must travel with the results"


def test_ranked_table_filters(client):
    high = client.get("/api/domains?min_score=45").json()
    assert all(r["opportunity_score"] >= 45 for r in high["rows"])
    cheap = client.get("/api/domains?max_price=500").json()
    assert all(r["asking_price"] <= 500 for r in cheap["rows"])
    buyers = client.get("/api/domains?min_buyers=2").json()
    assert all(r["buyer_count"] >= 2 for r in buyers["rows"])


def test_domain_detail_returns_the_whole_audit_trail(client):
    body = client.get("/api/domains/berlinroofing.com").json()
    for section in ("domain", "listings", "features", "enrichments", "buyers",
                    "comparables_used", "valuation", "probability", "opportunity"):
        assert section in body
    assert body["valuation"]["walk"]["base"]["value"] > 0
    assert body["probability"]["terms"]
    assert body["opportunity"]["components"]
    assert body["opportunity"]["explanation"]["component_ranking"]
    # Provenance travels with every enriched field.
    for enrichment in body["enrichments"]:
        assert enrichment["provenance"] in {"OBSERVED", "DERIVED", "ESTIMATED",
                                            "LLM_INFERRED", "FIXTURE", "MISSING"}
        assert enrichment["source"]
        assert enrichment["retrieved_at"]


def test_unknown_domain_returns_404(client):
    assert client.get("/api/domains/not-imported.com").status_code == 404


def test_explain_endpoint_is_readable(client):
    text = client.get("/api/domains/berlinroofing.com/explain").text
    assert "COMPONENT CONTRIBUTIONS" in text
    assert "VALUATION WALK" in text
    assert "PROBABILITY TERMS" in text
    assert "UNCALIBRATED" in text


def test_report_endpoints(client):
    body = client.get("/api/report?limit=3").json()
    assert len(body["entries"]) == 3
    assert body["summary"]["domains_scored"] == 30
    text = client.get("/api/report/text?limit=2").text
    assert "TODAY'S TOP DOMAIN OPPORTUNITIES" in text
    assert "Maximum recommended bid" in text


def test_portfolio_endpoint(client):
    body = client.post("/api/portfolio",
                       json={"budget": 5000, "scenario": "aggressive"}).json()
    assert body["total_invested"] <= 5000
    assert body["constraints"]["min_opportunity_score"] is not None
    assert body["warnings"]


def test_portfolio_rejects_a_bad_budget(client):
    assert client.post("/api/portfolio", json={"budget": -1}).status_code == 422


def test_paper_position_lifecycle(client):
    opened = client.post("/api/paper/positions",
                         json={"domain": "berlinroofing.com"}).json()
    assert opened["config_stamp"]
    assert opened["signal_snapshot"]["buyer_depth_count"] >= 0

    listed = client.get("/api/paper/positions").json()
    assert len(listed) == 1

    observation = client.post("/api/paper/observations", json={
        "position_id": opened["id"], "event_type": "SOLD", "sold": True,
        "observed_price": 5000}).json()
    assert observation["position_outcome"] == "SOLD"
    assert "evidence_url" in (observation["warning"] or ""), \
        "an outcome without evidence must be flagged"


def test_signal_power_endpoint_is_honest_about_no_data(client):
    body = client.get("/api/analysis/signal-power").json()
    assert body["sufficient_data"] is False
    assert "UNDETERMINED" in body["verdict"]


def test_coverage_endpoint_reports_gaps(client):
    body = client.get("/api/analysis/coverage").json()
    assert body["domains"] == 30
    assert body["comparable_sales_loaded"] == 0
    assert "cpc_usd" in body["enrichment_by_field"]
    assert body["run_data_gaps"]


def test_import_endpoint_round_trip(db):
    client = TestClient(app)
    with open(EXAMPLE_CSV, "rb") as fh:
        response = client.post("/api/import",
                               files={"file": ("domains.csv", fh, "text/csv")})
    assert response.status_code == 200
    assert response.json()["rows_accepted"] == 30

    run = client.post("/api/pipeline/run", json={})
    assert run.status_code == 200
    assert run.json()["domains_scored"] == 30


def test_import_rejects_a_file_without_the_domain_column(db):
    client = TestClient(app)
    response = client.post("/api/import",
                           files={"file": ("bad.csv", b"name\nfoo.com\n", "text/csv")})
    assert response.status_code == 400
    assert "domain" in response.json()["detail"]


def test_dashboard_renders_with_its_warning_banner(client):
    html = client.get("/").text
    assert "UNCALIBRATED" in html
    assert "berlinroofing.com" in html
