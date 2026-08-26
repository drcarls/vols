"""Valuation engine: wholesale, retail and strategic value.

    retail_mid = base(tld) * PRODUCT(multipliers)   [then blended with comps]

Multiplicative and flat by design. There is no interaction term, no learned
weight and no ensemble, because in V0 there is nothing to learn from - and a
model whose structure you cannot read is a model you cannot audit.

Every multiplier is recorded with its input value, so the output decomposes:

    2500 (com base)
      x 1.05 (length 17)
      x 0.50 (3 words)
      x 1.30 (all dictionary words)
      x 1.00 (commercial intent: MISSING)
      x 1.42 (buyer depth 18)
    = 2425

Confidence is a separate axis from value. A high valuation built on missing
keyword and buyer data gets a low confidence, and the ranking layer discounts
it. Ranges widen as confidence falls, so the output stops pretending to a
precision it does not have.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.providers.base import KeywordMetrics
from app.scoring.buyer_depth import BuyerDepth
from app.scoring.comparables import ComparableStats
from app.scoring.config import ScoringConfig
from app.scoring.features import DomainFeatureSet


@dataclass
class ValuationResult:
    wholesale_value_low: float
    wholesale_value_mid: float
    wholesale_value_high: float
    retail_value_low: float
    retail_value_mid: float
    retail_value_high: float
    strategic_value_high: float | None
    confidence: float                       # 0..100
    method: str
    components: dict[str, Any] = field(default_factory=dict)
    comparables_available: bool = False
    comparable_stats: dict[str, Any] = field(default_factory=dict)
    data_gaps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def _record(components: dict, name: str, multiplier: float, basis: str,
            inputs: Any) -> float:
    components[name] = {"multiplier": round(multiplier, 4), "basis": basis,
                        "input": inputs}
    return multiplier


def estimate(cfg: ScoringConfig, tld: str, features: DomainFeatureSet,
             keywords: KeywordMetrics, buyers: BuyerDepth,
             comps: ComparableStats) -> ValuationResult:
    """Produce wholesale / retail / strategic estimates for one domain."""
    v = cfg.section("valuation")
    components: dict[str, Any] = {}
    gaps: list[str] = []

    # ---- base ------------------------------------------------------------
    base = float(cfg.tld_value("valuation.retail_base_usd_by_tld", tld))
    components["base"] = {"value": base, "basis": f"retail base for .{tld}"}

    mult = 1.0

    # ---- structural multipliers -----------------------------------------
    m = v["multipliers"]

    length_m = ScoringConfig.interpolate_table(m["length"]["by_length"],
                                               features.sld_length)
    length_m = max(m["length"]["min"], min(m["length"]["max"], length_m))
    mult *= _record(components, "length", length_m,
                    "shorter names command a premium",
                    {"sld_length": features.sld_length})

    wc_table = m["word_count"]["by_count"]
    wc_m = float(wc_table.get(features.word_count, m["word_count"]["default"]))
    mult *= _record(components, "word_count", wc_m,
                    "one- and two-word names are far more liquid",
                    {"word_count": features.word_count})

    if features.all_words_dictionary:
        dict_m = float(m["dictionary"]["all_words_dictionary"])
        dict_basis = "every token is a dictionary word"
    elif features.dictionary_word_count > 0:
        dict_m = float(m["dictionary"]["some_words_dictionary"])
        dict_basis = "some tokens are dictionary words"
    else:
        dict_m = float(m["dictionary"]["no_words_dictionary"])
        dict_basis = "no recognised dictionary words"
    mult *= _record(components, "dictionary", dict_m, dict_basis,
                    {"dictionary_word_count": features.dictionary_word_count})

    if features.has_hyphen:
        mult *= _record(components, "hyphen_penalty", float(m["defects"]["hyphen"]),
                        "hyphenated names carry a large retail discount",
                        {"hyphen_count": features.hyphen_count})
    if features.has_digit:
        mult *= _record(components, "digit_penalty", float(m["defects"]["digit"]),
                        "digits create dictation ambiguity",
                        {"digit_count": features.digit_count})

    brand_m = ScoringConfig.lerp(m["brandability"]["at_score_0"],
                                 m["brandability"]["at_score_100"],
                                 features.brandability / 100.0)
    mult *= _record(components, "brandability", brand_m,
                    "brandable names reach more buyer types",
                    {"brandability": features.brandability})

    # ---- commercial intent (may be MISSING) -----------------------------
    ci = keywords.commercial_intent
    if ci.is_missing:
        ci_m = float(m["commercial_intent"]["missing_data_multiplier"])
        mult *= _record(components, "commercial_intent", ci_m,
                        "NO KEYWORD DATA - multiplier forced to neutral, "
                        "confidence penalised instead",
                        {"commercial_intent": None})
        gaps.append("commercial_intent")
    else:
        ci_m = ScoringConfig.lerp(m["commercial_intent"]["at_score_0"],
                                  m["commercial_intent"]["at_score_100"],
                                  float(ci.value) / 100.0)
        mult *= _record(components, "commercial_intent", ci_m,
                        "advertiser spend evidences commercial value",
                        {"commercial_intent": ci.value, "source": ci.source})

    # ---- buyer depth (the hypothesis under test) ------------------------
    bd = m["buyer_depth"]
    if buyers.missing:
        bd_m = float(bd["missing_data_multiplier"])
        mult *= _record(components, "buyer_depth", bd_m,
                        "NO BUYER SEARCH PERFORMED - multiplier forced to "
                        "neutral, confidence penalised instead",
                        {"buyer_count": None})
        gaps.append("buyer_depth")
    else:
        depth_table = {0: bd["at_depth_0"], 1: bd["at_depth_1"],
                       5: bd["at_depth_5"], 20: bd["at_depth_20"],
                       50: bd["at_depth_50"]}
        bd_m = min(float(bd["max"]),
                   ScoringConfig.interpolate_table(depth_table, buyers.count))
        mult *= _record(components, "buyer_depth", bd_m,
                        "identifiable end buyers are what makes retail value real",
                        {"buyer_count": buyers.count,
                         "strong_count": buyers.strong_count,
                         "depth_value": buyers.depth_value})

    heuristic_mid = base * mult
    components["heuristic_retail_mid"] = round(heuristic_mid, 2)
    components["total_multiplier"] = round(mult, 4)

    # ---- comparable-sales blend -----------------------------------------
    import math

    retail_mid = heuristic_mid
    if comps.available and comps.weighted_median and comps.weighted_median > 0:
        max_w = float(v["comparables"]["max_blend_weight"])
        blend_w = max_w * comps.confidence
        # Blend in log space: value distributions are multiplicative, so an
        # arithmetic average of $500 and $50,000 would be meaningless.
        retail_mid = math.exp((1 - blend_w) * math.log(max(1.0, heuristic_mid))
                              + blend_w * math.log(max(1.0, comps.weighted_median)))
        components["comparable_blend"] = {
            "weight": round(blend_w, 4),
            "comparable_weighted_median": comps.weighted_median,
            "comparable_count": comps.count,
            "comparable_confidence": comps.confidence,
            "heuristic_before_blend": round(heuristic_mid, 2),
            "basis": "log-space blend; comps capped at "
                     f"{max_w:.0%} weight even at full confidence",
        }
    else:
        gaps.append("comparable_sales")
        components["comparable_blend"] = {
            "weight": 0.0,
            "basis": comps.note or "no comparable sales available",
        }

    # ---- confidence ------------------------------------------------------
    # Starts at a deliberately modest ceiling: this model is uncalibrated, so
    # even a fully-enriched domain should not report high confidence.
    confidence = 0.55
    if "commercial_intent" in gaps:
        confidence -= float(m["commercial_intent"]["missing_data_confidence_penalty"])
    if "buyer_depth" in gaps:
        confidence -= float(m["buyer_depth"]["missing_data_confidence_penalty"])
    if comps.available:
        confidence += 0.35 * comps.confidence
    if features.segmentation_confidence < 0.5:
        confidence -= 0.08
        gaps.append("word_segmentation_uncertain")
    if not buyers.missing and buyers.economic_coverage < 0.5:
        confidence -= 0.05
        gaps.append("buyer_economics_partial")
    confidence = max(0.05, min(0.95, confidence))

    # ---- ranges ----------------------------------------------------------
    r = v["ranges"]
    low_ratio = ScoringConfig.lerp(r["low_ratio_at_low_confidence"],
                                   r["low_ratio_at_high_confidence"], confidence)
    high_ratio = ScoringConfig.lerp(r["high_ratio_at_low_confidence"],
                                    r["high_ratio_at_high_confidence"], confidence)
    retail_low = retail_mid * low_ratio
    retail_high = retail_mid * high_ratio

    ws_ratio = float(v["wholesale_ratio_of_retail"])
    ws_spread = float(v["wholesale_range_spread"])
    wholesale_mid = retail_mid * ws_ratio
    wholesale_low = wholesale_mid * (1.0 - ws_spread)
    wholesale_high = wholesale_mid * (1.0 + ws_spread)

    # ---- strategic value -------------------------------------------------
    strategic: float | None = None
    st = v["strategic"]
    if buyers.missing:
        components["strategic"] = {"basis": "no buyer search performed",
                                   "value": None}
    elif buyers.max_buyer_value >= float(st["min_buyer_value_score"]):
        strategic = retail_high * float(st["multiple_of_retail_high"])
        components["strategic"] = {
            "basis": f"strongest identified buyer scores "
                     f"{buyers.max_buyer_value:.0f}/100 on economic weight",
            "multiple_of_retail_high": st["multiple_of_retail_high"],
            "value": round(strategic, 2)}
    else:
        components["strategic"] = {
            "basis": f"no buyer clears the economic threshold "
                     f"({st['min_buyer_value_score']}); strongest is "
                     f"{buyers.max_buyer_value:.0f}",
            "value": None}

    return ValuationResult(
        wholesale_value_low=round(wholesale_low, 2),
        wholesale_value_mid=round(wholesale_mid, 2),
        wholesale_value_high=round(wholesale_high, 2),
        retail_value_low=round(retail_low, 2),
        retail_value_mid=round(retail_mid, 2),
        retail_value_high=round(retail_high, 2),
        strategic_value_high=round(strategic, 2) if strategic else None,
        confidence=round(confidence * 100.0, 2),
        method=f"heuristic_v0/{cfg.version}",
        components=components,
        comparables_available=comps.available,
        comparable_stats=comps.to_dict(),
        data_gaps=sorted(set(gaps)),
    )
