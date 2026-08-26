"""Re-scoring fidelity and the sensitivity harness.

The load-bearing test in this file is ``test_baseline_rescore_reproduces_stored_scores``.
If a re-score under the original config does not reproduce the stored numbers
exactly, then every sweep result is measuring reconstruction error rather than
config sensitivity, and the whole analysis is worthless.
"""

import pytest
from sqlalchemy import select

from app.analysis import sensitivity as sens
from app.analysis.rescore import load_stage_inputs, rescore, rescore_one
from app.models.analysis import OpportunityScore, PipelineRun
from app.scoring.config import (get_scoring_config, renormalised_weights,
                                with_overrides)


@pytest.fixture
def run_id(scored_db):
    return scored_db.execute(
        select(PipelineRun.id).order_by(PipelineRun.id.desc())).scalar()


# --------------------------------------------------------------------------
# config variants
# --------------------------------------------------------------------------

def test_overrides_do_not_mutate_the_shared_config():
    cfg = get_scoring_config()
    before = cfg.get("probability.base_annual_sell_through")
    variant = with_overrides(cfg, {"probability.base_annual_sell_through": 0.09})
    assert variant.get("probability.base_annual_sell_through") == 0.09
    assert cfg.get("probability.base_annual_sell_through") == before
    assert variant.stamp != cfg.stamp, "a variant must be distinguishable"


def test_overrides_reject_unknown_paths():
    cfg = get_scoring_config()
    with pytest.raises(KeyError):
        with_overrides(cfg, {"probability.no_such_key": 1})
    with pytest.raises(KeyError):
        with_overrides(cfg, {"no_such_section.key": 1})


@pytest.mark.parametrize("weight", [0.0, 0.05, 0.15, 0.35, 1.0])
def test_renormalised_weights_always_sum_to_one(weight):
    cfg = get_scoring_config()
    if weight == 1.0:
        pytest.skip("a weight of 1.0 leaves nothing to rescale")
    weights = renormalised_weights(cfg, "buyer_depth", weight)
    assert weights["buyer_depth"] == pytest.approx(weight)
    assert sum(weights.values()) == pytest.approx(1.0, abs=1e-9)
    variant = with_overrides(cfg, {"opportunity.weights": weights})
    assert variant.validate() == []


def test_renormalisation_preserves_relative_order_of_other_weights():
    cfg = get_scoring_config()
    original = cfg.get("opportunity.weights")
    adjusted = renormalised_weights(cfg, "buyer_depth", 0.30)
    others = [k for k in original if k != "buyer_depth"]
    original_order = sorted(others, key=lambda k: original[k])
    adjusted_order = sorted(others, key=lambda k: adjusted[k])
    assert original_order == adjusted_order


def test_renormalised_weights_rejects_unknown_component():
    with pytest.raises(KeyError):
        renormalised_weights(get_scoring_config(), "not_a_component", 0.1)


# --------------------------------------------------------------------------
# re-score fidelity
# --------------------------------------------------------------------------

def test_baseline_rescore_reproduces_stored_scores(scored_db, run_id):
    """Without this, every sweep number is reconstruction noise."""
    inputs = load_stage_inputs(scored_db, run_id)
    assert inputs
    rows = rescore(get_scoring_config(), inputs)

    stored = {s.domain_id: s for s in scored_db.execute(
        select(OpportunityScore).where(OpportunityScore.run_id == run_id)).scalars()}
    assert len(rows) == len(stored)
    for row in rows:
        original = stored[row.domain_id]
        assert row.score == pytest.approx(original.score, abs=1e-9)
        assert row.raw_score == pytest.approx(original.raw_score, abs=1e-9)
        assert row.recommendation == original.recommendation
        assert row.buyer_count == original.buyer_count
        if original.expected_profit_24m is not None:
            assert row.expected_profit_24m == pytest.approx(
                original.expected_profit_24m, abs=0.01)


def test_rescore_preserves_missing_keyword_data(scored_db, run_id):
    """Reconstruction must not upgrade an absence into a value."""
    inputs = load_stage_inputs(scored_db, run_id)
    without_keywords = [i for i in inputs
                        if i.keywords.commercial_intent.is_missing]
    assert without_keywords, "the example corpus has domains with no keyword row"
    for item in without_keywords:
        assert item.keywords.cpc_usd.is_missing
        assert item.keywords.commercial_intent.value is None


def test_rescore_returns_rows_in_score_order(scored_db, run_id):
    rows = rescore(get_scoring_config(), load_stage_inputs(scored_db, run_id))
    assert [r.score for r in rows] == sorted((r.score for r in rows), reverse=True)


def test_rescore_reacts_to_the_base_rate(scored_db, run_id):
    inputs = load_stage_inputs(scored_db, run_id)
    cfg = get_scoring_config()
    low = rescore_one(with_overrides(
        cfg, {"probability.base_annual_sell_through": 0.005}), inputs[0])
    high = rescore_one(with_overrides(
        cfg, {"probability.base_annual_sell_through": 0.06}), inputs[0])
    assert high.prob_sale_24m > low.prob_sale_24m
    assert high.recommended_max_bid > low.recommended_max_bid


def test_rescore_writes_nothing(scored_db, run_id):
    before = len(scored_db.execute(select(OpportunityScore)).scalars().all())
    sens.analyse(scored_db, run_id=run_id)
    after = len(scored_db.execute(select(OpportunityScore)).scalars().all())
    assert before == after, "analysis must never be mistaken for a prediction"


# --------------------------------------------------------------------------
# rank statistics
# --------------------------------------------------------------------------

@pytest.mark.parametrize("xs,ys,expected", [
    ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], 1.0),
    ([1, 2, 3, 4, 5], [5, 4, 3, 2, 1], -1.0),
])
def test_kendall_tau_endpoints(xs, ys, expected):
    assert sens.kendall_tau(xs, ys) == pytest.approx(expected)


def test_kendall_tau_single_adjacent_swap():
    assert sens.kendall_tau([1, 2, 3, 4], [1, 2, 4, 3]) == pytest.approx(0.6667, abs=1e-4)


def test_kendall_tau_needs_two_points():
    assert sens.kendall_tau([1], [1]) is None
    assert sens.kendall_tau([], []) is None


def test_identical_rankings_compare_as_identical(scored_db, run_id):
    rows = rescore(get_scoring_config(), load_stage_inputs(scored_db, run_id))
    stability = sens.compare_rankings(rows, rows)
    assert all(v == 1.0 for v in stability.top_k_overlap.values())
    assert stability.kendall_tau_top == pytest.approx(1.0)
    assert stability.max_rank_shift == 0
    assert stability.entered_top25 == [] and stability.left_top25 == []


def test_reversed_ranking_compares_as_opposite(scored_db, run_id):
    rows = rescore(get_scoring_config(), load_stage_inputs(scored_db, run_id))
    stability = sens.compare_rankings(rows, list(reversed(rows)))
    assert stability.kendall_tau_top == pytest.approx(-1.0)
    assert stability.spearman_full == pytest.approx(-1.0)


# --------------------------------------------------------------------------
# the harness
# --------------------------------------------------------------------------

def test_analysis_produces_sweeps_and_ablations(scored_db, run_id):
    report = sens.analyse(scored_db, run_id=run_id)
    assert report.run_id == run_id
    assert report.domains == 30
    assert report.calibrated is False
    assert {s.parameter for s in report.sweeps} == set(sens.DEFAULT_GRIDS)
    assert len(report.ablations) == 9
    assert len(report.weight_gaps) == 9
    assert report.verdict


def test_every_sweep_contains_its_baseline_point(scored_db, run_id):
    report = sens.analyse(scored_db, run_id=run_id, include_ablations=False)
    for sweep in report.sweeps:
        baselines = [p for p in sweep.points if p.is_baseline]
        assert len(baselines) == 1, f"{sweep.parameter} lost its baseline point"
        stability = baselines[0].stability
        assert all(v == 1.0 for v in stability.top_k_overlap.values()), \
            "the baseline point must compare identically against itself"


def test_small_corpus_is_flagged(scored_db, run_id):
    report = sens.analyse(scored_db, run_id=run_id, include_ablations=False)
    assert any("indicative at best" in w for w in report.warnings)


def test_corpus_dependence_is_always_warned(scored_db, run_id):
    report = sens.analyse(scored_db, run_id=run_id, include_ablations=False)
    assert any("property of THIS corpus" in w for w in report.warnings)


def test_missing_data_components_are_diagnosed_as_such_not_as_useless(scored_db, run_id):
    """The example corpus has no comparable sales, so comparable_confidence is
    constant. That must read as a missing source, never as a dead component."""
    report = sens.analyse(scored_db, run_id=run_id)
    comps = next(a for a in report.ablations if a.component == "comparable_confidence")
    assert comps.coverage == 0.0
    assert comps.influence == pytest.approx(0.0)
    assert comps.diagnosis.startswith("NO DATA")
    assert "says nothing about its value" in comps.diagnosis


def test_weight_gaps_sum_consistently(scored_db, run_id):
    report = sens.analyse(scored_db, run_id=run_id)
    shares = [g.effective_share for g in report.weight_gaps
              if g.effective_share is not None]
    if shares:
        assert sum(shares) == pytest.approx(1.0, abs=1e-3)
    assert sum(g.configured_share for g in report.weight_gaps) == pytest.approx(1.0)


def test_ablating_a_component_changes_nothing_when_it_is_constant(scored_db, run_id):
    report = sens.analyse(scored_db, run_id=run_id)
    for ablation in report.ablations:
        if ablation.coverage == 0.0:
            assert ablation.influence == pytest.approx(0.0)


def test_render_text_covers_every_section(scored_db, run_id):
    text = sens.render_text(sens.analyse(scored_db, run_id=run_id))
    for heading in ("SENSITIVITY AND ABLATION ANALYSIS", "VERDICT", "SWEEP",
                    "COMPONENT ABLATION",
                    "CONFIGURED WEIGHT vs MEASURED INFLUENCE"):
        assert heading in text


def test_analysis_of_an_empty_database_is_graceful(db):
    report = sens.analyse(db)
    assert report.run_id == -1
    assert report.domains == 0
    assert "No completed pipeline run" in report.verdict


def test_api_endpoints(scored_db):
    from fastapi.testclient import TestClient

    from app.main import app
    client = TestClient(app)

    body = client.get("/api/analysis/sensitivity").json()
    assert body["domains"] == 30
    assert body["sweeps"] and body["ablations"] and body["weight_gaps"]
    assert body["verdict"]

    text = client.get("/api/analysis/sensitivity/text").text
    assert "COMPONENT ABLATION" in text

    quick = client.get("/api/analysis/sensitivity?include_ablations=false").json()
    assert quick["ablations"] == []
