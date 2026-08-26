"""Decision layer: arbitrage arithmetic, ranking score and recommendation.

Three things happen here, kept apart on purpose:

  1. **Economics** - pure arithmetic on the valuation and probability outputs.
     Expected value, expected profit, ROI, maximum bid. No judgement, no
     weights; you can check every line with a calculator.
  2. **Ranking** - a weighted sum of nine normalised components, every one of
     which is stored with its raw value, weight and contribution. "Why did A
     rank above B" is answered by subtracting the two component vectors.
  3. **Recommendation** - the score plus hard gates. A high score built on a
     negative expected profit does not become a BUY.

The confidence adjustment is what stops the ranking rewarding ignorance: a
domain with no keyword data and no buyer search can post a flattering raw score
because nothing contradicted it, so the raw score is multiplied down by how
much of it rested on actual data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.scoring.buyer_depth import BuyerDepth
from app.scoring.comparables import ComparableStats
from app.scoring.config import ScoringConfig
from app.scoring.features import DomainFeatureSet
from app.scoring.probability import (CATEGORY_LIQUIDITY,
                                     DEFAULT_CATEGORY_LIQUIDITY,
                                     ProbabilityResult)
from app.scoring.valuation import ValuationResult

RECOMMENDATIONS = ("STRONG_BUY", "BUY", "WATCH", "PASS", "AVOID")


@dataclass
class Economics:
    acquisition_price: float | None
    capital_required: float | None
    gross_spread: float | None
    multiple_on_cost: float | None
    expected_sale_value_24m: float | None
    estimated_renewal_costs_24m: float
    expected_transaction_costs: float | None
    expected_profit_24m: float | None
    expected_roi_24m: float | None
    annualized_opportunity_score: float | None
    recommended_max_bid: float | None
    assumptions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class OpportunityResult:
    score: float
    raw_score: float
    confidence: float
    recommendation: str
    components: dict[str, Any]
    explanation: dict[str, Any]
    economics: Economics

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        d["economics"] = self.economics.to_dict()
        return d


# --------------------------------------------------------------------------
# 1. economics - arithmetic only
# --------------------------------------------------------------------------

def compute_economics(cfg: ScoringConfig, asking_price: float | None,
                      valuation: ValuationResult,
                      probability: ProbabilityResult) -> Economics:
    econ = cfg.section("economics")
    renewal = float(econ["annual_renewal_cost_usd"])
    txn_rate = float(econ["transaction_cost_rate"])
    transfer = float(econ["transfer_cost_usd"])
    mos = float(econ["margin_of_safety"])
    residual_ratio = float(econ.get("unsold_residual_ratio_of_wholesale", 0.0))

    retail_mid = valuation.retail_value_mid
    p24 = probability.prob_sale_24m

    # Expected sale value: probability-weighted, not the headline retail number.
    expected_sale_value = p24 * retail_mid

    # The unsold branch is not worthless. A name that fails to reach an end user
    # within the horizon can usually be liquidated into the investor market at
    # a fraction of modelled wholesale. Excluding this understates every
    # opportunity by roughly the same amount, which would distort the ranking as
    # well as the level.
    residual_value = (1.0 - p24) * valuation.wholesale_value_mid * residual_ratio
    expected_terminal_value = expected_sale_value + residual_value

    # Renewals accrue whether or not the domain sells; two years at the horizon.
    renewals_24m = renewal * 2.0

    # Transaction costs are only paid on a sale, so they are probability-weighted.
    expected_txn = p24 * (retail_mid * txn_rate) + p24 * transfer

    assumptions = {
        "horizon_months": 24,
        "annual_renewal_cost_usd": renewal,
        "renewals_charged": 2,
        "transaction_cost_rate": txn_rate,
        "transaction_costs_are_probability_weighted": True,
        "transfer_cost_usd": transfer,
        "margin_of_safety": mos,
        "cost_of_capital_annual": econ["cost_of_capital_annual"],
        "unsold_residual_ratio_of_wholesale": residual_ratio,
        "residual_value_if_unsold": round(residual_value, 2),
        "expected_terminal_value": round(expected_terminal_value, 2),
        "note": ("expected_sale_value = P(sale within 24m) x retail_value_mid. "
                 "expected_terminal_value adds (1 - P) x wholesale_mid x "
                 f"{residual_ratio} for the unsold branch. Both retail and "
                 "wholesale are UNCALIBRATED model outputs, not observations."),
    }

    if asking_price is None or asking_price <= 0:
        return Economics(
            acquisition_price=asking_price, capital_required=None,
            gross_spread=None, multiple_on_cost=None,
            expected_sale_value_24m=round(expected_sale_value, 2),
            estimated_renewal_costs_24m=round(renewals_24m, 2),
            expected_transaction_costs=round(expected_txn, 2),
            expected_profit_24m=None, expected_roi_24m=None,
            annualized_opportunity_score=None,
            recommended_max_bid=round(max(0.0,
                (expected_terminal_value - expected_txn - renewals_24m) * mos), 2),
            assumptions=assumptions | {"price_status": "MISSING - no asking "
                                       "price in the listing; ROI not computable"})

    capital = asking_price + renewals_24m
    gross_spread = retail_mid - asking_price
    multiple = retail_mid / asking_price
    expected_profit = (expected_terminal_value - asking_price - renewals_24m
                       - expected_txn)
    expected_roi = expected_profit / capital if capital > 0 else None

    holding_years = max(0.25, probability.expected_holding_months / 12.0)
    conf = valuation.confidence / 100.0
    annualized = ((expected_profit * conf) / capital / holding_years
                  if capital > 0 else None)

    # Maximum bid: what the expected value supports, discounted by the margin of
    # safety. Explicitly NOT derived from retail value, which would be bidding
    # against a price we have only a probability of ever achieving.
    max_bid = max(0.0, (expected_terminal_value - expected_txn - renewals_24m) * mos)

    return Economics(
        acquisition_price=round(asking_price, 2),
        capital_required=round(capital, 2),
        gross_spread=round(gross_spread, 2),
        multiple_on_cost=round(multiple, 3),
        expected_sale_value_24m=round(expected_sale_value, 2),
        estimated_renewal_costs_24m=round(renewals_24m, 2),
        expected_transaction_costs=round(expected_txn, 2),
        expected_profit_24m=round(expected_profit, 2),
        expected_roi_24m=round(expected_roi, 4) if expected_roi is not None else None,
        annualized_opportunity_score=round(annualized, 4) if annualized is not None else None,
        recommended_max_bid=round(max_bid, 2),
        assumptions=assumptions,
    )


# --------------------------------------------------------------------------
# 2. ranking components
# --------------------------------------------------------------------------

def _norm_0_100(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return max(0.0, min(100.0, (value - low) / (high - low) * 100.0))


def compute_components(cfg: ScoringConfig, features: DomainFeatureSet,
                       buyers: BuyerDepth, comps: ComparableStats,
                       valuation: ValuationResult, probability: ProbabilityResult,
                       economics: Economics, commercial_intent: float | None,
                       tld: str, category: str | None) -> dict[str, dict]:
    """Each component normalised to 0..100, with the reason it took that value."""
    import math

    o = cfg.section("opportunity")
    comp: dict[str, dict] = {}

    # valuation gap - how many multiples of cost the modelled retail is
    if economics.multiple_on_cost is None:
        comp["valuation_gap"] = {"value": 0.0, "status": "MISSING",
                                 "why": "no asking price, so no gap computable"}
    else:
        full = float(o["valuation_gap_multiple_for_full_marks"])
        v = _norm_0_100(math.log10(max(1.0, economics.multiple_on_cost)),
                        0.0, math.log10(full))
        comp["valuation_gap"] = {
            "value": round(v, 2), "status": "OK",
            "why": f"modelled retail is {economics.multiple_on_cost:.1f}x the "
                   f"asking price ({full:.0f}x scores 100)"}

    # capital efficiency - expected ROI over the horizon
    if economics.expected_roi_24m is None:
        comp["capital_efficiency"] = {"value": 0.0, "status": "MISSING",
                                      "why": "expected ROI not computable"}
    else:
        scale = float(o["roi_scale_for_full_marks"])
        v = _norm_0_100(economics.expected_roi_24m, -0.5, scale)
        comp["capital_efficiency"] = {
            "value": round(v, 2), "status": "OK",
            "why": f"expected 24-month ROI {economics.expected_roi_24m:.0%} "
                   f"({scale:.0%} scores 100)"}

    # sale probability
    v = _norm_0_100(probability.prob_sale_24m, 0.0, 0.40)
    comp["sale_probability"] = {
        "value": round(v, 2), "status": "OK",
        "why": f"modelled 24-month sale probability "
               f"{probability.prob_sale_24m:.1%} (40% scores 100)"}

    # buyer depth - the hypothesis under test
    if buyers.missing:
        comp["buyer_depth"] = {"value": 0.0, "status": "MISSING",
                               "why": "no buyer search was performed"}
        comp["buyer_quality"] = {"value": 0.0, "status": "MISSING",
                                 "why": "no buyer search was performed"}
    else:
        v = _norm_0_100(math.log10(buyers.count + 1), 0.0, math.log10(51))
        comp["buyer_depth"] = {
            "value": round(v, 2), "status": "OK",
            "why": f"{buyers.count} credible buyer(s) identified, "
                   f"{buyers.strong_count} at identity level (50 scores 100)"}
        comp["buyer_quality"] = {
            "value": round(buyers.max_buyer_value, 2), "status": "OK",
            "why": f"strongest buyer scores {buyers.max_buyer_value:.0f}/100 "
                   f"on economic weight; economics known for "
                   f"{buyers.economic_coverage:.0%} of buyers"}

    # commercial intent
    if commercial_intent is None:
        comp["commercial_intent"] = {"value": 0.0, "status": "MISSING",
                                     "why": "no keyword data source configured"}
    else:
        comp["commercial_intent"] = {
            "value": round(commercial_intent, 2), "status": "OK",
            "why": f"commercial intent {commercial_intent:.0f}/100 from CPC "
                   f"and advertiser competition"}

    # comparable confidence
    if not comps.available:
        comp["comparable_confidence"] = {"value": 0.0, "status": "MISSING",
                                         "why": "no comparable sales loaded"}
    else:
        comp["comparable_confidence"] = {
            "value": round(comps.confidence * 100.0, 2), "status": "OK",
            "why": f"{comps.count} comparable(s), mean similarity "
                   f"{comps.mean_similarity:.2f}, dispersion "
                   f"{comps.dispersion_ratio}"}

    # brandability
    comp["brandability"] = {
        "value": round(features.brandability, 2), "status": "OK",
        "why": f"brandability {features.brandability:.0f}/100 "
               f"(pronounceability {features.pronounceability:.0f}, "
               f"{features.word_count} word(s))"}

    # liquidity - TLD and category
    tld_liq = float(cfg.tld_value("probability.tld_liquidity", tld))
    cat_liq = (CATEGORY_LIQUIDITY.get(category, DEFAULT_CATEGORY_LIQUIDITY)
               if category else None)
    if cat_liq is None:
        liquidity = tld_liq * 100.0
        why = f".{tld} liquidity {tld_liq}; category unknown"
    else:
        liquidity = (0.6 * tld_liq + 0.4 * cat_liq) * 100.0
        why = f".{tld} liquidity {tld_liq}, category '{category}' liquidity {cat_liq}"
    comp["liquidity"] = {"value": round(liquidity, 2), "status": "OK", "why": why}

    return comp


def score_from_components(cfg: ScoringConfig, components: dict[str, dict],
                          valuation_confidence: float,
                          probability_confidence: float) -> tuple[float, float, float, dict]:
    """Weighted sum, then a confidence adjustment.

    Returns ``(final_score, raw_score, confidence, enriched_components)``.
    """
    o = cfg.section("opportunity")
    weights = o["weights"]
    enriched: dict[str, dict] = {}
    raw = 0.0
    for name, weight in weights.items():
        entry = dict(components.get(name, {"value": 0.0, "status": "MISSING",
                                           "why": "component not computed"}))
        contribution = float(entry.get("value", 0.0)) * float(weight)
        entry["weight"] = float(weight)
        entry["contribution"] = round(contribution, 3)
        enriched[name] = entry
        raw += contribution

    # Confidence: valuation confidence, probability data coverage, and the
    # fraction of ranking components that actually had data.
    present = sum(1 for e in enriched.values() if e.get("status") == "OK")
    coverage = present / len(weights)
    confidence = (0.45 * (valuation_confidence / 100.0)
                  + 0.25 * probability_confidence
                  + 0.30 * coverage)

    floor = float(o["confidence_floor"])
    final = raw * (floor + (1.0 - floor) * confidence)
    return round(final, 2), round(raw, 2), round(confidence, 4), enriched


# --------------------------------------------------------------------------
# 3. recommendation
# --------------------------------------------------------------------------

def recommend(cfg: ScoringConfig, score: float, economics: Economics,
              buyers: BuyerDepth) -> tuple[str, list[str]]:
    """Score plus hard gates. Returns (recommendation, gate messages)."""
    r = cfg.section("recommendation")
    gates: list[str] = []

    if economics.expected_profit_24m is not None and \
            economics.expected_profit_24m <= float(r["avoid_if_expected_profit_below"]):
        gates.append(
            f"expected 24-month profit is "
            f"${economics.expected_profit_24m:,.0f} - negative expected value "
            f"at the asking price")
        return "AVOID", gates

    if score >= float(r["strong_buy_min_score"]):
        base = "STRONG_BUY"
    elif score >= float(r["buy_min_score"]):
        base = "BUY"
    elif score >= float(r["watch_min_score"]):
        base = "WATCH"
    else:
        base = "PASS"

    if base in ("STRONG_BUY", "BUY"):
        roi = economics.expected_roi_24m
        if roi is None:
            gates.append("expected ROI not computable (no asking price)")
            base = "WATCH"
        elif roi < float(r["min_expected_roi_for_buy"]):
            gates.append(f"expected ROI {roi:.0%} is below the "
                         f"{float(r['min_expected_roi_for_buy']):.0%} floor for a buy")
            base = "WATCH"
        if buyers.missing:
            gates.append("no buyer search was performed, so buyer depth is "
                         "unknown rather than zero")
            base = "WATCH"
        elif buyers.count < int(r["min_buyers_for_buy"]):
            gates.append(f"only {buyers.count} credible buyer(s), below the "
                         f"minimum of {r['min_buyers_for_buy']}")
            base = "WATCH"
    return base, gates


# --------------------------------------------------------------------------
# explanation layer
# --------------------------------------------------------------------------

def build_explanation(domain: str, components: dict[str, dict],
                      economics: Economics, valuation: ValuationResult,
                      probability: ProbabilityResult, buyers: BuyerDepth,
                      features: DomainFeatureSet, category: str | None,
                      gates: list[str], cfg: ScoringConfig) -> dict[str, Any]:
    """Human-readable account of the score, generated from stored numbers.

    Deterministic prose assembled from the component table - not an LLM
    narration of a number it cannot see. The LLM may add colour later, but the
    reasons here are the actual arithmetic.
    """
    ranked = sorted(components.items(),
                    key=lambda kv: kv[1].get("contribution", 0.0), reverse=True)
    reasons = [f"{kv[1]['why']} (contributes {kv[1]['contribution']:.1f} points)"
               for kv in ranked[:5] if kv[1].get("status") == "OK"
               and kv[1].get("contribution", 0) > 0]

    risks: list[str] = []
    if buyers.missing:
        risks.append("Buyer depth is UNKNOWN - no buyer data source was "
                     "configured, so the central signal is absent.")
    elif buyers.count == 0:
        risks.append("No credible end buyer was identified. Retail value has "
                     "no identified route to a purchaser.")
    elif buyers.count < 3:
        risks.append(f"Only {buyers.count} credible buyer(s) - a narrow market "
                     f"means sale timing depends on very few decisions.")
    if buyers.economic_coverage < 0.5 and not buyers.missing and buyers.count:
        risks.append(f"Economic data is available for only "
                     f"{buyers.economic_coverage:.0%} of identified buyers, so "
                     f"buyer quality is weakly evidenced.")
    if not valuation.comparables_available:
        risks.append("No comparable sales were available; the valuation rests "
                     "entirely on the heuristic prior.")
    if "commercial_intent" in valuation.data_gaps:
        risks.append("No keyword data (search volume / CPC), so commercial "
                     "intent could not be evidenced.")
    if features.word_count >= 3:
        risks.append(f"{features.word_count}-word name - long names have "
                     f"materially thinner resale demand.")
    if features.has_hyphen or features.has_digit:
        risks.append("Hyphen or digit in the name is a large, well-documented "
                     "retail discount.")
    if probability.expected_holding_months > 30:
        risks.append(f"Expected holding period is "
                     f"{probability.expected_holding_months:.0f} months, which "
                     f"ties up capital for a long time.")
    risks.extend(gates)

    return {
        "domain": domain,
        "category": category,
        "top_reasons": reasons,
        "risks": risks,
        "component_ranking": [
            {"component": k, "value": v.get("value"), "weight": v.get("weight"),
             "contribution": v.get("contribution"), "status": v.get("status"),
             "why": v.get("why")}
            for k, v in ranked],
        "valuation_walk": valuation.components,
        "probability_terms": probability.terms,
        "economics_assumptions": economics.assumptions,
        "model_status": {
            "scoring_config": cfg.stamp,
            "calibrated": cfg.calibrated,
            "warning": cfg.calibration_note,
        },
    }
