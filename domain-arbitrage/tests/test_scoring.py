"""Valuation, probability and decision arithmetic."""

import math

import pytest

from app.providers.base import KeywordMetrics
from app.scoring import opportunity as opp
from app.scoring import probability as prob
from app.scoring import valuation as val
from app.scoring.buyer_depth import BuyerDepth
from app.scoring.comparables import ComparableStats
from app.scoring.config import get_scoring_config
from app.scoring.features import extract_features


@pytest.fixture(scope="module")
def cfg():
    return get_scoring_config()


def _depth(count: int, max_value: float = 60.0) -> BuyerDepth:
    return BuyerDepth(missing=False, searched=True, count=count,
                      strong_count=count // 3, total_found=count,
                      depth_value=count * 0.4, max_buyer_value=max_value,
                      mean_match_score=70.0, economic_coverage=0.8)


NO_KEYWORDS = KeywordMetrics.all_missing("test", "none")
NO_COMPS = ComparableStats(available=False, count=0)


def test_config_weights_sum_to_one(cfg):
    assert cfg.validate() == []
    assert math.isclose(sum(cfg.get("opportunity.weights").values()), 1.0)


def test_config_is_marked_uncalibrated(cfg):
    assert cfg.calibrated is False
    assert "UNCALIBRATED" in cfg.calibration_note


def test_valuation_decomposes_into_its_multipliers(cfg):
    features = extract_features("fleetanalytics", "com")
    result = val.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10), NO_COMPS)
    base = result.components["base"]["value"]
    product = base
    for name, entry in result.components.items():
        if isinstance(entry, dict) and "multiplier" in entry:
            product *= entry["multiplier"]
    # Tolerance is 1e-3 rather than exact because the stored multipliers are
    # rounded to four decimals for legibility in the audit trail. The walk must
    # reconstruct the value to well within display precision.
    assert product == pytest.approx(result.components["heuristic_retail_mid"], rel=1e-3)


def test_valuation_ranges_are_ordered(cfg):
    features = extract_features("fleetanalytics", "com")
    r = val.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10), NO_COMPS)
    assert r.retail_value_low < r.retail_value_mid < r.retail_value_high
    assert r.wholesale_value_low < r.wholesale_value_mid < r.wholesale_value_high
    assert r.wholesale_value_mid < r.retail_value_mid


def test_missing_buyer_data_lowers_confidence_without_moving_the_multiplier(cfg):
    features = extract_features("fleetanalytics", "com")
    known = val.estimate(cfg, "com", features, NO_KEYWORDS, _depth(0), NO_COMPS)
    unknown = val.estimate(cfg, "com", features, NO_KEYWORDS,
                           BuyerDepth(missing=True, searched=False), NO_COMPS)
    assert unknown.components["buyer_depth"]["multiplier"] == 1.0
    assert unknown.confidence < known.confidence
    assert "buyer_depth" in unknown.data_gaps


def test_more_buyers_raises_value_and_probability(cfg):
    features = extract_features("fleetanalytics", "com")
    values, probs = [], []
    for n in (0, 1, 5, 20, 50):
        v = val.estimate(cfg, "com", features, NO_KEYWORDS, _depth(n), NO_COMPS)
        p = prob.estimate(cfg, "com", features, NO_KEYWORDS, _depth(n), NO_COMPS,
                          "logistics", 1000.0, v.retail_value_mid)
        values.append(v.retail_value_mid)
        probs.append(p.prob_sale_24m)
    assert values == sorted(values)
    assert probs == sorted(probs)


def test_strategic_value_is_missing_without_a_strong_buyer(cfg):
    features = extract_features("fleetanalytics", "com")
    weak = val.estimate(cfg, "com", features, NO_KEYWORDS, _depth(5, max_value=10.0),
                        NO_COMPS)
    strong = val.estimate(cfg, "com", features, NO_KEYWORDS,
                          _depth(5, max_value=90.0), NO_COMPS)
    assert weak.strategic_value_high is None
    assert strong.strategic_value_high is not None


def test_probability_terms_sum_to_the_log_odds(cfg):
    features = extract_features("fleetanalytics", "com")
    r = prob.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10), NO_COMPS,
                      "logistics", 1000.0, 8000.0)
    total = r.base_log_odds + sum(t["contribution"] for t in r.terms.values())
    reconstructed = 1.0 / (1.0 + math.exp(-total))
    clamped = min(max(reconstructed, cfg.get("probability.min_annual_probability")),
                  cfg.get("probability.max_annual_probability"))
    assert r.annual_hazard == pytest.approx(clamped, abs=1e-4)


def test_probabilities_are_monotonic_in_horizon(cfg):
    features = extract_features("fleetanalytics", "com")
    r = prob.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10), NO_COMPS,
                      "logistics", 1000.0, 8000.0)
    assert r.prob_sale_12m <= r.prob_sale_24m <= r.prob_sale_36m
    assert 0.0 <= r.prob_sale_36m <= 1.0


def test_missing_drivers_contribute_nothing_and_are_listed(cfg):
    features = extract_features("fleetanalytics", "com")
    r = prob.estimate(cfg, "com", features, NO_KEYWORDS,
                      BuyerDepth(missing=True, searched=False), NO_COMPS,
                      None, None, 8000.0)
    for name in ("buyer_depth", "commercial_intent", "category_liquidity"):
        assert r.terms[name]["status"] == "MISSING"
        assert r.terms[name]["contribution"] == 0.0
        assert name in r.data_gaps


def test_economics_arithmetic_is_reproducible_by_hand(cfg):
    features = extract_features("fleetanalytics", "com")
    valuation = val.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10), NO_COMPS)
    probability = prob.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10),
                                NO_COMPS, "logistics", 1000.0,
                                valuation.retail_value_mid)
    econ = opp.compute_economics(cfg, 1000.0, valuation, probability)

    p24 = probability.prob_sale_24m
    retail = valuation.retail_value_mid
    renewals = cfg.get("economics.annual_renewal_cost_usd") * 2
    txn_rate = cfg.get("economics.transaction_cost_rate")
    residual_ratio = cfg.get("economics.unsold_residual_ratio_of_wholesale")

    expected_sale = p24 * retail
    residual = (1 - p24) * valuation.wholesale_value_mid * residual_ratio
    expected_txn = p24 * retail * txn_rate
    profit = expected_sale + residual - 1000.0 - renewals - expected_txn

    # Stored figures are rounded to cents and probabilities to four decimals,
    # so recomputation matches to display precision rather than to the bit.
    assert econ.expected_sale_value_24m == pytest.approx(expected_sale, abs=0.02)
    assert econ.expected_profit_24m == pytest.approx(profit, abs=0.02)
    assert econ.gross_spread == pytest.approx(retail - 1000.0, abs=0.02)
    assert econ.multiple_on_cost == pytest.approx(retail / 1000.0, rel=1e-3)


def test_max_bid_is_below_expected_value_by_the_margin_of_safety(cfg):
    features = extract_features("fleetanalytics", "com")
    valuation = val.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10), NO_COMPS)
    probability = prob.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10),
                                NO_COMPS, "logistics", 1000.0,
                                valuation.retail_value_mid)
    econ = opp.compute_economics(cfg, 1000.0, valuation, probability)
    assert econ.recommended_max_bid < valuation.retail_value_mid
    mos = cfg.get("economics.margin_of_safety")
    gross = (econ.assumptions["expected_terminal_value"]
             - econ.expected_transaction_costs - econ.estimated_renewal_costs_24m)
    assert econ.recommended_max_bid == pytest.approx(gross * mos, abs=0.02)


def test_negative_expected_profit_forces_avoid(cfg):
    features = extract_features("fleetanalytics", "com")
    valuation = val.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10), NO_COMPS)
    probability = prob.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10),
                                NO_COMPS, "logistics", 500_000.0,
                                valuation.retail_value_mid)
    econ = opp.compute_economics(cfg, 500_000.0, valuation, probability)
    recommendation, gates = opp.recommend(cfg, 99.0, econ, _depth(10))
    assert recommendation == "AVOID"
    assert gates


def test_unknown_buyers_cannot_produce_a_buy(cfg):
    features = extract_features("fleetanalytics", "com")
    unknown = BuyerDepth(missing=True, searched=False)
    valuation = val.estimate(cfg, "com", features, NO_KEYWORDS, unknown, NO_COMPS)
    probability = prob.estimate(cfg, "com", features, NO_KEYWORDS, unknown,
                                NO_COMPS, None, 10.0, valuation.retail_value_mid)
    econ = opp.compute_economics(cfg, 10.0, valuation, probability)
    recommendation, gates = opp.recommend(cfg, 95.0, econ, unknown)
    assert recommendation not in ("BUY", "STRONG_BUY")
    assert any("buyer search" in g for g in gates)


def test_component_contributions_sum_to_the_raw_score(cfg):
    features = extract_features("fleetanalytics", "com")
    valuation = val.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10), NO_COMPS)
    probability = prob.estimate(cfg, "com", features, NO_KEYWORDS, _depth(10),
                                NO_COMPS, "logistics", 1000.0,
                                valuation.retail_value_mid)
    econ = opp.compute_economics(cfg, 1000.0, valuation, probability)
    components = opp.compute_components(cfg, features, _depth(10), NO_COMPS,
                                        valuation, probability, econ, None,
                                        "com", "logistics")
    score, raw, confidence, enriched = opp.score_from_components(
        cfg, components, valuation.confidence, probability.confidence)
    assert sum(e["contribution"] for e in enriched.values()) == pytest.approx(raw, abs=0.05)
    assert score <= raw, "confidence adjustment can only discount"
    assert 0.0 <= confidence <= 1.0
