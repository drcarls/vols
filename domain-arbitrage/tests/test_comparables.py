"""Comparable-sales selection and statistics."""

import pytest

from app.scoring.comparables import (CompRecord, MIN_SIMILARITY, analyse,
                                     similarity, weighted_median)


def _comp(i, price, tld="com", words=None, wc=2, length=14, category="logistics",
          cpc=None):
    return CompRecord(id=i, domain=f"comp{i}.{tld}", sale_price=price, tld=tld,
                      word_count=wc, length=length, category=category,
                      words=words or ["fleet", "analytics"], cpc=cpc,
                      venue="TestVenue")


def test_no_comps_reports_unavailable_not_zero():
    stats = analyse("com", ["fleet", "analytics"], 14, 2, "logistics", None, [])
    assert stats.available is False
    assert stats.count == 0
    assert stats.confidence == 0.0
    assert stats.median is None
    assert "no comparable sales" in stats.note


def test_similarity_rewards_matching_tld_and_category():
    same = similarity("com", ["fleet", "analytics"], 14, 2, "logistics", None,
                      _comp(1, 5000))[0]
    other_tld = similarity("com", ["fleet", "analytics"], 14, 2, "logistics", None,
                           _comp(2, 5000, tld="xyz"))[0]
    assert same > other_tld


def test_similarity_breakdown_names_every_dimension():
    _, breakdown = similarity("com", ["fleet", "analytics"], 14, 2, "logistics",
                              None, _comp(1, 5000))
    assert {"tld", "category", "token_overlap"} <= set(breakdown)
    # Weights renormalise to 1 across whichever dimensions had data on both
    # sides; they are stored rounded to four decimals.
    assert sum(v["weight"] for v in breakdown.values()) == pytest.approx(1.0, abs=1e-3)


def test_dissimilar_sales_are_excluded():
    far = CompRecord(id=9, domain="unrelated.xyz", sale_price=900_000, tld="xyz",
                     word_count=1, length=40, category="pets", words=["pets"])
    stats = analyse("com", ["fleet", "analytics"], 14, 2, "logistics", None, [far])
    assert stats.available is False


def test_weighted_median_resists_one_outlier():
    prices = [1000.0, 1100.0, 1200.0, 1300.0, 500_000.0]
    weights = [1.0, 1.0, 1.0, 1.0, 0.05]
    assert weighted_median(prices, weights) < 2000.0


def test_statistics_are_ordered_and_complete():
    comps = [_comp(i, price) for i, price in
             enumerate([1000, 2000, 3000, 4000, 5000, 6000], start=1)]
    stats = analyse("com", ["fleet", "analytics"], 14, 2, "logistics", None, comps)
    assert stats.available is True
    assert stats.count == 6
    assert stats.minimum <= stats.p25 <= stats.median <= stats.p75 <= stats.maximum
    assert 0.0 < stats.confidence <= 1.0
    assert stats.mean_similarity >= MIN_SIMILARITY
    assert len(stats.used) == 6
    assert all("breakdown" in u for u in stats.used)


def test_confidence_falls_with_a_small_or_scattered_set():
    tight = [_comp(i, 3000 + i * 50) for i in range(1, 9)]
    scattered = [_comp(i, 100 * (10 ** (i % 4))) for i in range(1, 9)]
    tight_stats = analyse("com", ["fleet", "analytics"], 14, 2, "logistics", None, tight)
    scattered_stats = analyse("com", ["fleet", "analytics"], 14, 2, "logistics",
                              None, scattered)
    assert tight_stats.confidence > scattered_stats.confidence

    two = analyse("com", ["fleet", "analytics"], 14, 2, "logistics", None, tight[:2])
    assert two.confidence < tight_stats.confidence
    assert "weak evidence" in two.note


def test_comparable_blend_moves_the_valuation_toward_the_comps():
    from app.providers.base import KeywordMetrics
    from app.scoring.buyer_depth import BuyerDepth
    from app.scoring.config import get_scoring_config
    from app.scoring.features import extract_features
    from app.scoring.valuation import estimate

    cfg = get_scoring_config()
    features = extract_features("fleetanalytics", "com")
    depth = BuyerDepth(missing=False, searched=True, count=5, strong_count=2,
                       depth_value=2.0, max_buyer_value=50.0,
                       mean_match_score=70.0, economic_coverage=1.0)
    no_comps = analyse("com", features.words, 14, 2, "logistics", None, [])
    rich = [_comp(i, 60_000) for i in range(1, 13)]
    with_comps = analyse("com", features.words, 14, 2, "logistics", None, rich)

    baseline = estimate(cfg, "com", features, KeywordMetrics.all_missing("t", "n"),
                        depth, no_comps)
    blended = estimate(cfg, "com", features, KeywordMetrics.all_missing("t", "n"),
                       depth, with_comps)
    assert blended.retail_value_mid > baseline.retail_value_mid
    assert blended.comparables_available is True
    assert blended.confidence > baseline.confidence
    assert blended.components["comparable_blend"]["weight"] > 0
    # Comps never take the whole weight, however confident they are.
    assert blended.components["comparable_blend"]["weight"] <= \
        cfg.get("valuation.comparables.max_blend_weight")
