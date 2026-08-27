"""Stratified sampling and outcome reconciliation.

Two properties in this file matter more than the rest:

  * the cohort must include names the model rated PASS and AVOID, or it can
    never be falsified;
  * a domain absent from a sales export must never be recorded as unsold.
"""

import datetime as _dt

import pytest
from sqlalchemy import select

from app.models.paper import PaperPosition
from app.services import paper_sampler as sampler
from app.services import reconcile as rec
from app.services.paper_portfolio import (TESTABLE_OUTCOMES, PaperPortfolioError,
                                          open_position, performance)


# --------------------------------------------------------------------------
# banding
# --------------------------------------------------------------------------

ABSOLUTE = sampler.Banding(kind="absolute")


@pytest.mark.parametrize("score,expected", [
    (0.0, "score_00_30"), (29.9, "score_00_30"), (30.0, "score_30_45"),
    (54.9, "score_45_55"), (55.0, "score_55_65"), (99.0, "score_65_plus"),
])
def test_absolute_score_banding(score, expected):
    assert ABSOLUTE.score_band(score) == expected


@pytest.mark.parametrize("count,expected", [
    (0, "buyers_0"), (1, "buyers_1_2"), (2, "buyers_1_2"),
    (3, "buyers_3_9"), (9, "buyers_3_9"), (10, "buyers_10_plus"), (900, "buyers_10_plus"),
])
def test_absolute_depth_banding(count, expected):
    assert ABSOLUTE.depth_band(count) == expected


def test_zero_buyers_is_its_own_band_in_both_modes():
    """'No identifiable buyer' is a different state, not just a low count."""
    assert ABSOLUTE.depth_band(0) != ABSOLUTE.depth_band(1)
    quantile = sampler.build_banding([1.0, 2.0, 3.0, 4.0], [0, 1, 4, 9])
    assert quantile.depth_band(0) == "buyers_0"
    assert quantile.depth_band(1) != "buyers_0"


# --------------------------------------------------------------------------
# quantile banding - the fix for unreachable absolute bands
# --------------------------------------------------------------------------

def test_quantile_bands_are_all_populated_by_construction():
    """The failure absolute banding has: a band nothing can ever fall into."""
    scores = [float(i) for i in range(100)]        # nothing above 99
    depths = [i % 7 for i in range(100)]
    banding = sampler.build_banding(scores, depths, score_bins=5)
    occupied = {banding.score_band(s) for s in scores}
    assert len(occupied) == 5, "every quantile band must contain something"


def test_quantile_bands_adapt_to_a_compressed_score_range():
    """With missing data sources the top of the 0-100 scale is unreachable."""
    compressed = [float(i) / 10 for i in range(200, 540)]   # 20.0 .. 53.9
    banding = sampler.build_banding(compressed, [1] * len(compressed))
    occupied = {banding.score_band(s) for s in compressed}
    assert len(occupied) == 5
    # The same corpus under absolute banding leaves two bands empty.
    absolute_occupied = {ABSOLUTE.score_band(s) for s in compressed}
    assert "score_65_plus" not in absolute_occupied
    assert "score_55_65" not in absolute_occupied


def test_quantile_band_labels_carry_their_edges():
    """Two cohorts from different corpora must not share an ambiguous label."""
    a = sampler.build_banding([float(i) for i in range(100)], [1] * 100)
    b = sampler.build_banding([float(i) for i in range(1000)], [1] * 1000)
    assert a.score_band(50.0) != b.score_band(50.0) or a.score_edges == b.score_edges
    assert any(char.isdigit() for char in a.score_band(50.0))


def test_lumpy_distributions_collapse_bands_rather_than_emptying_them():
    banding = sampler.build_banding([5.0] * 50 + [9.0] * 50, [1] * 100,
                                    score_bins=5)
    occupied = {banding.score_band(s) for s in [5.0] * 50 + [9.0] * 50}
    assert 1 <= len(occupied) <= 2, "ties must collapse, not produce empty bands"


def test_absolute_banding_is_still_available():
    banding = sampler.build_banding([10.0, 50.0, 90.0], [0, 5, 20],
                                    kind="absolute")
    assert banding.kind == "absolute"
    assert banding.score_band(90.0) == "score_65_plus"


# --------------------------------------------------------------------------
# score reachability
# --------------------------------------------------------------------------

def test_reachability_deducts_missing_component_weights():
    components = {
        "a": {"weight": 0.20, "status": "MISSING"},
        "b": {"weight": 0.30, "status": "OK"},
        "c": {"weight": 0.50, "status": "OK"},
    }
    ceiling = sampler.reachable_score_ceiling(components, confidence=0.8)
    assert ceiling["missing_components"] == ["a"]
    assert ceiling["raw_points_unavailable"] == pytest.approx(20.0)
    assert ceiling["raw_score_ceiling"] == pytest.approx(80.0)
    assert ceiling["final_score_ceiling"] == pytest.approx(64.0)


def test_reachability_is_full_when_nothing_is_missing():
    components = {"a": {"weight": 1.0, "status": "OK"}}
    ceiling = sampler.reachable_score_ceiling(components, confidence=1.0)
    assert ceiling["raw_score_ceiling"] == pytest.approx(100.0)
    assert ceiling["missing_components"] == []


def test_plan_explains_an_unreachable_ceiling(scored_db):
    """The example corpus has no comparable sales, so points are unreachable."""
    result = sampler.draw_sample(scored_db, size=10, cohort="t1", dry_run=True)
    reach = result.plan.reachability
    assert "comparable_confidence" in reach["missing_components"]
    assert reach["raw_score_ceiling"] < 100
    assert any("unreachable because" in w for w in result.plan.warnings)
    assert any("missing data source, not a shortage" in w
               for w in result.plan.warnings)


# --------------------------------------------------------------------------
# allocation
# --------------------------------------------------------------------------

def test_allocation_is_even_when_supply_allows():
    cells = {f"c{i}": list(range(50)) for i in range(4)}
    allocation = sampler._allocate(cells, 40)
    assert sum(allocation.values()) == 40
    assert set(allocation.values()) == {10}


def test_allocation_spills_demand_from_thin_cells_to_deep_ones():
    cells = {"thin": [1, 2], "deep": list(range(100))}
    allocation = sampler._allocate(cells, 20)
    assert allocation["thin"] == 2, "a thin cell contributes all it has"
    assert allocation["deep"] == 18
    assert sum(allocation.values()) == 20


def test_allocation_cannot_exceed_supply():
    cells = {"a": [1, 2], "b": [3]}
    allocation = sampler._allocate(cells, 100)
    assert allocation == {"a": 2, "b": 1}


# --------------------------------------------------------------------------
# sampling
# --------------------------------------------------------------------------

def test_sample_opens_positions_tagged_with_cohort_and_stratum(scored_db):
    result = sampler.draw_sample(scored_db, size=12, cohort="t1")
    assert len(result.opened) == 12
    positions = scored_db.execute(select(PaperPosition)).scalars().all()
    assert len(positions) == 12
    for position in positions:
        assert position.sample_cohort == "t1"
        assert position.sample_stratum
        assert "|" in position.sample_stratum


def test_sample_spans_more_than_one_stratum(scored_db):
    result = sampler.draw_sample(scored_db, size=12, cohort="t1")
    strata = {e["stratum"] for e in result.opened}
    assert len(strata) >= 2, "a single-stratum cohort cannot compare anything"


def test_sample_includes_the_control_group(scored_db):
    """Without PASS/AVOID names, recall is unmeasurable and the score is
    unfalsifiable."""
    result = sampler.draw_sample(scored_db, size=20, cohort="t1")
    statuses = {e["status"] for e in result.opened}
    assert "PAPER_PASS" in statuses
    recommendations = {e["recommendation"] for e in result.opened}
    assert recommendations & {"PASS", "AVOID"}


def test_status_follows_the_models_own_recommendation(scored_db):
    result = sampler.draw_sample(scored_db, size=20, cohort="t1")
    for entry in result.opened:
        assert entry["status"] == sampler.STATUS_BY_RECOMMENDATION[
            entry["recommendation"]]


def test_sampling_is_deterministic_given_a_seed(scored_db):
    first = sampler.draw_sample(scored_db, size=10, cohort="a", seed=42,
                                dry_run=True)
    second = sampler.draw_sample(scored_db, size=10, cohort="b", seed=42,
                                 dry_run=True)
    assert [e["domain"] for e in first.opened] == [e["domain"] for e in second.opened]


def test_different_seeds_draw_different_samples(scored_db):
    first = sampler.draw_sample(scored_db, size=10, cohort="a", seed=1, dry_run=True)
    second = sampler.draw_sample(scored_db, size=10, cohort="b", seed=99, dry_run=True)
    assert [e["domain"] for e in first.opened] != [e["domain"] for e in second.opened]


def test_dry_run_writes_nothing(scored_db):
    result = sampler.draw_sample(scored_db, size=10, cohort="t1", dry_run=True)
    assert len(result.opened) == 10
    assert scored_db.execute(select(PaperPosition)).scalars().all() == []


def test_domains_without_a_price_are_never_sampled(scored_db):
    """A position with no entry cost could never have its ROI evaluated."""
    result = sampler.draw_sample(scored_db, size=30, cohort="t1", dry_run=True)
    assert all(e["asking_price"] and e["asking_price"] > 0 for e in result.opened)


def test_max_price_is_respected(scored_db):
    result = sampler.draw_sample(scored_db, size=30, cohort="t1", max_price=500,
                                 dry_run=True)
    assert result.opened
    assert all(e["asking_price"] <= 500 for e in result.opened)


def test_already_open_positions_are_excluded(scored_db):
    open_position(scored_db, "berlinroofing.com")
    result = sampler.draw_sample(scored_db, size=30, cohort="t1", dry_run=True)
    assert "berlinroofing.com" not in {e["domain"] for e in result.opened}


def test_oversized_request_is_reported_not_silently_truncated(scored_db):
    result = sampler.draw_sample(scored_db, size=10_000, cohort="t1", dry_run=True)
    assert result.plan.planned < 10_000
    assert any("could be allocated" in w for w in result.plan.warnings)


def test_sampling_rejects_a_bad_size(scored_db):
    with pytest.raises(PaperPortfolioError):
        sampler.draw_sample(scored_db, size=0, cohort="t1")


def test_sampling_without_a_run_is_rejected(db):
    with pytest.raises(PaperPortfolioError, match="no completed pipeline run"):
        sampler.draw_sample(db, size=5, cohort="t1")


def test_quantile_sampling_leaves_no_empty_score_band(scored_db):
    """Under absolute banding this corpus left two bands unfillable."""
    result = sampler.draw_sample(scored_db, size=20, cohort="t1", dry_run=True)
    filled = [c for c in result.plan.cells if c.requested > 0]
    assert filled
    assert not any("does not span the score range" in w
                   for w in result.plan.warnings)
    assert result.plan.banding.kind == "quantile"


def test_banding_choice_is_recorded_on_the_plan(scored_db):
    result = sampler.draw_sample(scored_db, size=10, cohort="t1",
                                 banding="absolute", dry_run=True)
    assert result.plan.banding.kind == "absolute"
    assert all(c.score_band.startswith("score_") for c in result.plan.cells)


def test_invalid_banding_is_rejected(scored_db):
    with pytest.raises(PaperPortfolioError, match="banding"):
        sampler.draw_sample(scored_db, size=5, cohort="t1", banding="nonsense")


# --------------------------------------------------------------------------
# cohort health
# --------------------------------------------------------------------------

def test_cohort_health_reports_structure(scored_db):
    sampler.draw_sample(scored_db, size=20, cohort="t1")
    health = sampler.cohort_health(scored_db, "t1")
    assert health.positions == 20
    assert health.by_score_band and health.by_depth_band
    assert health.by_recommendation
    assert health.verdict


def test_cohort_health_detects_depth_variation_within_score_bands(scored_db):
    sampler.draw_sample(scored_db, size=25, cohort="t1")
    health = sampler.cohort_health(scored_db, "t1")
    assert health.score_bands_with_depth_variation
    assert health.confounded is False


def test_cohort_health_flags_a_confounded_hand_picked_cohort(scored_db):
    """Hand-picking only the top names is the failure mode this guards."""
    from app.models.analysis import OpportunityScore
    from app.models.core import Domain

    top = scored_db.execute(
        select(OpportunityScore, Domain).join(Domain)
        .order_by(OpportunityScore.score.desc()).limit(3)).all()
    for score, domain in top:
        open_position(scored_db, domain.name, sample_cohort="handpicked",
                      sample_stratum=sampler.Banding(kind="absolute").stratum(
                          score.score, score.buyer_count))
    health = sampler.cohort_health(scored_db, "handpicked")
    assert health.can_measure_recall is False
    assert any("cannot falsify" in w for w in health.warnings)


def test_cohort_health_on_an_empty_cohort(scored_db):
    health = sampler.cohort_health(scored_db, "nothing-here")
    assert health.positions == 0
    assert "No positions" in health.verdict


# --------------------------------------------------------------------------
# reconciliation
# --------------------------------------------------------------------------

def _sales_csv(*rows: str) -> bytes:
    header = "domain,sale_price,sale_date,venue,evidence_url\n"
    return (header + "\n".join(rows)).encode()


def test_read_sales_parses_and_reports_bad_rows():
    sales, problems = rec.read_sales(_sales_csv(
        "example.com,5000,2027-01-15,Sedo,https://example.invalid/1",
        "nodots,100,2027-01-15,Sedo,",
    ))
    assert len(sales) == 1
    assert sales[0].domain == "example.com"
    assert sales[0].sale_price == 5000.0
    assert sales[0].sale_date.year == 2027
    assert len(problems) == 1


def test_read_sales_normalises_domains():
    sales, _ = rec.read_sales(_sales_csv("HTTPS://WWW.Example.com/x,100,,,"))
    assert sales[0].domain == "example.com"


def test_reconcile_resolves_only_the_domains_present(scored_db):
    sampler.draw_sample(scored_db, size=10, cohort="t1")
    names = [p.domain_name for p in
             scored_db.execute(select(PaperPosition)).scalars()]
    sales, _ = rec.read_sales(_sales_csv(
        f"{names[0]},7000,2027-02-01,Sedo,https://example.invalid/1"))

    report = rec.reconcile(scored_db, sales, source="test")
    assert report.matched == 1
    resolved = scored_db.execute(select(PaperPosition).where(
        PaperPosition.domain_name == names[0])).scalar_one()
    assert resolved.outcome == "SOLD"
    assert resolved.outcome_price == 7000.0


def test_reconcile_never_marks_absent_domains_unsold(scored_db):
    """The integrity rule: a public feed covers part of the market, so absence
    is not evidence of a failure to sell."""
    sampler.draw_sample(scored_db, size=10, cohort="t1")
    names = [p.domain_name for p in
             scored_db.execute(select(PaperPosition)).scalars()]
    sales, _ = rec.read_sales(_sales_csv(f"{names[0]},7000,,,"))
    rec.reconcile(scored_db, sales, source="test")

    others = scored_db.execute(select(PaperPosition).where(
        PaperPosition.domain_name != names[0])).scalars().all()
    assert others
    assert all(p.outcome is None for p in others)
    assert any("absence is not evidence" in w for w in
               rec.reconcile(scored_db, [], source="test").warnings)


def test_reconcile_dry_run_writes_nothing(scored_db):
    sampler.draw_sample(scored_db, size=6, cohort="t1")
    name = scored_db.execute(select(PaperPosition)).scalars().first().domain_name
    sales, _ = rec.read_sales(_sales_csv(f"{name},7000,,,"))
    report = rec.reconcile(scored_db, sales, source="test", dry_run=True)
    assert report.matched == 1
    assert all(p.outcome is None for p in
               scored_db.execute(select(PaperPosition)).scalars())


def test_reconcile_counts_sales_matching_nothing(scored_db):
    sampler.draw_sample(scored_db, size=5, cohort="t1")
    sales, _ = rec.read_sales(_sales_csv("some-unrelated-name.com,5000,,,"))
    report = rec.reconcile(scored_db, sales, source="test")
    assert report.matched == 0
    assert report.unmatched_sales == 1


def test_reconcile_warns_about_missing_evidence(scored_db):
    sampler.draw_sample(scored_db, size=5, cohort="t1")
    name = scored_db.execute(select(PaperPosition)).scalars().first().domain_name
    sales, _ = rec.read_sales(_sales_csv(f"{name},7000,,,"))
    report = rec.reconcile(scored_db, sales, source="test")
    assert any("evidence_url" in w for w in report.warnings)


# --------------------------------------------------------------------------
# closing the observation window
# --------------------------------------------------------------------------

FUTURE = _dt.datetime(2030, 1, 1, tzinfo=_dt.timezone.utc)


def test_closing_defaults_to_censoring_not_unsold(scored_db):
    sampler.draw_sample(scored_db, size=8, cohort="t1")
    report = rec.close_observation_window(scored_db, as_of=FUTURE,
                                          horizon_months=24)
    assert report.censored == 8
    assert report.marked_unsold == 0
    outcomes = {p.outcome for p in
                scored_db.execute(select(PaperPosition)).scalars()}
    assert outcomes == {"CENSORED"}


def test_censored_positions_are_excluded_from_statistics(scored_db):
    """Censoring loses power. Counting invisible sales as failures loses truth."""
    sampler.draw_sample(scored_db, size=20, cohort="t1")
    rec.close_observation_window(scored_db, as_of=FUTURE, horizon_months=24)
    assert "CENSORED" not in TESTABLE_OUTCOMES

    report = performance(scored_db)
    assert report.resolved == 20
    assert report.sufficient_data is False, \
        "20 censored positions must not be treated as 20 failures to sell"
    assert report.observed_sale_rate is None


def test_asserting_a_complete_window_yields_unsold(scored_db):
    sampler.draw_sample(scored_db, size=8, cohort="t1")
    report = rec.close_observation_window(
        scored_db, as_of=FUTURE, horizon_months=24,
        observation_was_complete=True)
    assert report.marked_unsold == 8
    assert report.censored == 0
    outcomes = {p.outcome for p in
                scored_db.execute(select(PaperPosition)).scalars()}
    assert outcomes == {"UNSOLD"}
    assert any("biased downward" in w for w in report.warnings)


def test_positions_inside_their_horizon_are_left_open(scored_db):
    sampler.draw_sample(scored_db, size=8, cohort="t1")
    report = rec.close_observation_window(scored_db, horizon_months=24)
    assert report.left_open == 8
    assert report.censored == 0
    assert all(p.outcome is None for p in
               scored_db.execute(select(PaperPosition)).scalars())


def test_full_loop_sample_reconcile_measure(scored_db):
    """Sample, resolve some as sold, close the rest, and get statistics out."""
    sampler.draw_sample(scored_db, size=20, cohort="t1")
    names = [p.domain_name for p in
             scored_db.execute(select(PaperPosition)).scalars()]
    sales, _ = rec.read_sales(_sales_csv(*[
        f"{n},4000,2027-06-01,Sedo,https://example.invalid/{i}"
        for i, n in enumerate(names[:6])]))
    rec.reconcile(scored_db, sales, source="test")
    rec.close_observation_window(scored_db, as_of=FUTURE, horizon_months=24,
                                 observation_was_complete=True)

    report = performance(scored_db)
    assert report.resolved == 20
    assert report.sold == 6
    assert report.unsold == 14
    assert report.sufficient_data is True
    assert report.observed_sale_rate == pytest.approx(0.3)
    assert report.calibration_gap is not None
    assert report.median_valuation_error_ratio is not None


def test_api_endpoints(scored_db):
    from fastapi.testclient import TestClient

    from app.main import app
    client = TestClient(app)

    dry = client.post("/api/paper/sample",
                      json={"size": 10, "cohort": "api", "dry_run": True}).json()
    assert dry["opened_count"] == 10
    assert client.get("/api/paper/positions").json() == []

    live = client.post("/api/paper/sample",
                       json={"size": 10, "cohort": "api", "dry_run": False}).json()
    assert live["opened_count"] == 10
    assert live["health"]["positions"] == 10

    health = client.get("/api/paper/cohorts/api/health").json()
    assert health["cohort"] == "api"
    assert health["positions"] == 10

    name = live["opened"][0]["domain"]
    csv = _sales_csv(f"{name},9000,2027-01-01,Sedo,https://example.invalid/1")
    resp = client.post("/api/paper/reconcile?dry_run=false&source=test",
                       files={"file": ("sales.csv", csv, "text/csv")})
    assert resp.status_code == 200
    assert resp.json()["matched"] == 1

    closed = client.post("/api/paper/close-window",
                         json={"horizon_months": 1, "dry_run": True}).json()
    assert closed["censored"] + closed["left_open"] >= 0


def test_sample_endpoint_defaults_to_dry_run(scored_db):
    from fastapi.testclient import TestClient

    from app.main import app
    client = TestClient(app)
    body = client.post("/api/paper/sample", json={"size": 5, "cohort": "x"}).json()
    assert body["dry_run"] is True
    assert client.get("/api/paper/positions").json() == []
