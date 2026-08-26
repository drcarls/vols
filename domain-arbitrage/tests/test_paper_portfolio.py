"""Paper portfolio and the predictive-power analysis.

The most important assertion in this file is that statistics are WITHHELD on
small samples. A performance page that reports a confident number from six
outcomes is worse than one that reports nothing.
"""



import pytest
from sqlalchemy import select

from app.analysis.signal_power import MIN_SAMPLE, analyse as analyse_signals
from app.models.paper import PaperPosition
from app.services import paper_portfolio as paper
from app.services.portfolio import build_portfolio


def test_opening_a_position_freezes_the_prediction(scored_db):
    position = paper.open_position(scored_db, "berlinroofing.com")
    assert position.status == "PAPER_BUY"
    assert position.predicted_retail_value is not None
    assert position.predicted_sale_probability_24m is not None
    assert position.opportunity_score is not None
    assert position.recommended_max_bid is not None
    assert position.config_stamp, "the config version must be frozen with it"
    assert position.outcome is None


def test_signal_snapshot_captures_the_signals_under_test(scored_db):
    position = paper.open_position(scored_db, "berlinroofing.com")
    snapshot = position.signal_snapshot
    for key in ("buyer_depth_count", "buyer_depth_value", "buyer_quality_max",
                "brandability", "asking_price", "retail_value_mid", "tld"):
        assert key in snapshot


def test_cannot_open_two_unresolved_positions_for_one_domain(scored_db):
    paper.open_position(scored_db, "berlinroofing.com")
    with pytest.raises(paper.PaperPortfolioError, match="already exists"):
        paper.open_position(scored_db, "berlinroofing.com")


def test_unknown_domain_is_rejected(scored_db):
    with pytest.raises(paper.PaperPortfolioError, match="not been imported"):
        paper.open_position(scored_db, "never-seen.com")


def test_recording_a_sale_resolves_the_position(scored_db):
    position = paper.open_position(scored_db, "berlinroofing.com")
    paper.record_observation(scored_db, position.id, event_type="SOLD", sold=True,
                             observed_price=6500.0,
                             evidence_url="https://example.invalid/sale")
    refreshed = scored_db.get(PaperPosition, position.id)
    assert refreshed.outcome == "SOLD"
    assert refreshed.outcome_price == 6500.0
    assert refreshed.outcome_resolved_at is not None
    assert len(refreshed.observations) == 1


def test_losing_an_auction_is_distinct_from_not_selling(scored_db):
    position = paper.open_position(scored_db, "berlinroofing.com")
    paper.record_observation(scored_db, position.id, event_type="AUCTION_RESULT",
                             sold=False)
    assert scored_db.get(PaperPosition, position.id).outcome == "LOST_AUCTION"


def _resolve_many(session, count, sold_predicate):
    """Open and resolve ``count`` positions, for statistics tests."""
    from app.models.core import Domain
    names = [d.name for d in session.execute(select(Domain)).scalars()][:count]
    for index, name in enumerate(names):
        position = paper.open_position(session, name)
        sold = sold_predicate(index, position)
        paper.record_observation(
            session, position.id, event_type="SOLD", sold=sold,
            observed_price=(position.predicted_retail_value * 0.8) if sold else None,
            evidence_url="https://example.invalid/outcome")
    return names


def test_performance_withholds_statistics_on_a_small_sample(scored_db):
    _resolve_many(scored_db, 5, lambda i, p: i % 2 == 0)
    report = paper.performance(scored_db)
    assert report.sufficient_data is False
    assert report.observed_sale_rate is None
    assert report.false_positives is None
    assert any("at least" in note.lower() for note in report.notes)


def test_performance_reports_once_the_sample_is_large_enough(scored_db):
    _resolve_many(scored_db, 20, lambda i, p: i % 4 == 0)
    report = paper.performance(scored_db)
    assert report.sufficient_data is True
    assert report.resolved == 20
    assert report.observed_sale_rate == pytest.approx(0.25, abs=0.01)
    assert report.mean_predicted_prob_24m is not None
    assert report.calibration_gap is not None
    assert report.false_positives is not None and report.false_negatives is not None


def test_signal_power_reports_undetermined_before_there_is_evidence(scored_db):
    report = analyse_signals(scored_db)
    assert report.sufficient_data is False
    assert report.resolved_positions == 0
    assert "UNDETERMINED" in report.verdict
    assert report.hypothesis


def test_signal_power_evaluates_once_outcomes_exist(scored_db):
    # Make buyer depth genuinely predictive, then check the analysis notices.
    _resolve_many(scored_db, 25,
                  lambda i, p: p.signal_snapshot.get("buyer_depth_count", 0) >= 3)
    report = analyse_signals(scored_db)
    assert report.resolved_positions >= MIN_SAMPLE
    assert report.sufficient_data is True
    depth = next(r for r in report.results if r.signal == "buyer_depth_count")
    assert depth.auc is not None
    assert depth.auc > 0.5, "a signal we made predictive should score above chance"
    assert report.ranking
    assert report.verdict


def test_signal_results_carry_coverage(scored_db):
    _resolve_many(scored_db, 25, lambda i, p: i % 3 == 0)
    report = analyse_signals(scored_db)
    for result in report.results:
        assert 0.0 <= result.coverage <= 1.0
        if result.coverage < 0.5:
            assert result.note or result.auc is None


def test_portfolio_respects_the_budget_and_caps(scored_db):
    result = build_portfolio(scored_db, budget=2000, scenario="aggressive")
    assert result.total_invested <= 2000
    cap = result.constraints["max_per_domain_usd"]
    assert all(h.price <= cap for h in result.holdings)
    for category, exposure in result.category_exposure.items():
        assert exposure <= result.constraints["max_per_category_usd"] + 1e-6


def test_portfolio_scenarios_widen_monotonically(scored_db):
    counts = [len(build_portfolio(scored_db, budget=10_000, scenario=s).holdings)
              for s in ("conservative", "balanced", "aggressive")]
    assert counts[0] <= counts[1] <= counts[2]


def test_portfolio_explains_every_exclusion(scored_db):
    result = build_portfolio(scored_db, budget=10_000, scenario="conservative")
    assert result.excluded
    for excluded in result.excluded:
        assert excluded["reasons"], "an excluded domain must say which rule bound"


def test_portfolio_rejects_a_bad_budget(scored_db):
    with pytest.raises(ValueError):
        build_portfolio(scored_db, budget=0)
