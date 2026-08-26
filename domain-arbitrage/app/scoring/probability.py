"""Probability-of-sale model.

Transparent log-odds:

    logit(p_annual) = logit(base_rate) + SUM_i (coefficient_i * z_i)

Each ``z_i`` is a bounded driver, roughly centred on zero and scaled to
[-1, +1], so a coefficient reads directly as "moves the log-odds by this much
between a bad and a good domain on this axis". Every term is stored with its
z, coefficient and contribution, so a probability can be taken apart into "the
buyer depth added +0.9, the four-word length took away -0.3".

Why this shape and not a learned model: with zero outcome data, a fitted model
would be fitting noise. The log-odds form was chosen because it is the form a
logistic regression will take once the paper portfolio has enough resolved
outcomes to fit one - at which point ``coefficients`` in the YAML get replaced
by fitted values and nothing else in the codebase changes.

MISSING drivers contribute z=0 (no evidence either way) and are listed in
``data_gaps``, rather than being imputed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from app.providers.base import KeywordMetrics
from app.scoring.buyer_depth import BuyerDepth
from app.scoring.comparables import ComparableStats
from app.scoring.config import ScoringConfig
from app.scoring.features import DomainFeatureSet

# Category liquidity priors, 0..1. Ordinal guesses about how actively domains in
# each category trade. Hand-set; listed here rather than in the YAML because
# they are a property of the taxonomy, which also lives in code.
CATEGORY_LIQUIDITY: dict[str, float] = {
    "software": 0.8, "ai": 0.8, "data": 0.75, "finance": 0.8, "crypto": 0.7,
    "cybersecurity": 0.7, "marketing": 0.7, "ecommerce": 0.7, "health": 0.65,
    "insurance": 0.65, "real_estate": 0.65, "hr": 0.6, "logistics": 0.6,
    "legal": 0.6, "education": 0.55, "travel": 0.55, "energy": 0.55,
    "biotech": 0.5, "telecom": 0.5, "media": 0.5, "food": 0.5, "gaming": 0.5,
    "fashion": 0.5, "automotive": 0.5, "construction": 0.45, "sports": 0.45,
    "manufacturing": 0.4, "home_services": 0.4, "events": 0.35,
    "agriculture": 0.35, "pets": 0.35, "nonprofit": 0.2,
}
DEFAULT_CATEGORY_LIQUIDITY = 0.4


@dataclass
class ProbabilityResult:
    prob_sale_12m: float
    prob_sale_24m: float
    prob_sale_36m: float
    annual_hazard: float
    expected_holding_months: float
    base_log_odds: float
    terms: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    data_gaps: list[str] = field(default_factory=list)
    model: str = "logodds_heuristic_v0"

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def _logit(p: float) -> float:
    p = min(1 - 1e-9, max(1e-9, p))
    return math.log(p / (1 - p))


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _centred(value: float, low: float, high: float) -> float:
    """Map ``value`` from [low, high] onto [-1, +1], clamped."""
    if high <= low:
        return 0.0
    t = (value - low) / (high - low)
    return max(-1.0, min(1.0, 2.0 * t - 1.0))


def estimate(cfg: ScoringConfig, tld: str, features: DomainFeatureSet,
             keywords: KeywordMetrics, buyers: BuyerDepth,
             comps: ComparableStats, category: str | None,
             asking_price: float | None,
             retail_value_mid: float | None) -> ProbabilityResult:
    """Annual sale hazard and cumulative 12/24/36-month probabilities."""
    p = cfg.section("probability")
    coef = p["coefficients"]
    terms: dict[str, Any] = {}
    gaps: list[str] = []

    base_rate = float(p["base_annual_sell_through"])
    log_odds = _logit(base_rate)

    contributions: list[float] = []

    def add(name: str, z: float | None, note: str) -> None:
        """Record one driver. ``z=None`` means MISSING -> contributes nothing."""
        c = float(coef[name])
        if z is None:
            terms[name] = {"z": None, "coefficient": c, "contribution": 0.0,
                           "status": "MISSING", "note": note}
            gaps.append(name)
            return
        z = max(-1.0, min(1.0, z))
        contribution = c * z
        terms[name] = {"z": round(z, 4), "coefficient": c,
                       "contribution": round(contribution, 4),
                       "status": "OK", "note": note}
        contributions.append(contribution)

    # --- buyer depth: the hypothesis under test --------------------------
    if buyers.missing:
        add("buyer_depth", None, "no buyer search performed")
        add("buyer_quality", None, "no buyer search performed")
    else:
        # 0 buyers -> -1, ~10 buyers -> ~0, 50+ -> +1. Log scale because the
        # step from 0 to 3 buyers matters far more than 40 to 43.
        z_depth = _centred(math.log10(buyers.count + 1), 0.0, math.log10(51))
        add("buyer_depth", z_depth,
            f"{buyers.count} credible buyer(s), {buyers.strong_count} identity-level")
        add("buyer_quality", _centred(buyers.max_buyer_value, 20.0, 85.0),
            f"strongest buyer economic score {buyers.max_buyer_value:.0f}/100")

    # --- commercial intent -----------------------------------------------
    ci = keywords.commercial_intent
    if ci.is_missing:
        add("commercial_intent", None, "no keyword data source")
    else:
        add("commercial_intent", _centred(float(ci.value), 15.0, 75.0),
            f"commercial intent {float(ci.value):.0f}/100")

    # --- name quality -----------------------------------------------------
    add("brandability", _centred(features.brandability, 30.0, 85.0),
        f"brandability {features.brandability:.0f}/100")

    liq = cfg.tld_value("probability.tld_liquidity", tld)
    add("tld_liquidity", _centred(float(liq), 0.1, 1.0), f".{tld} liquidity {liq}")

    # Shortness: 6 chars -> +1, 20 chars -> -1.
    add("length_penalty", _centred(-features.sld_length, -20.0, -6.0),
        f"{features.sld_length}-character second-level name")

    add("word_count_penalty", _centred(-features.word_count, -4.0, -1.0),
        f"{features.word_count} word(s)")

    # --- price relative to modelled retail --------------------------------
    if asking_price and retail_value_mid and asking_price > 0:
        ratio = retail_value_mid / asking_price
        # 1x -> -1 (no room), 20x -> +1 (lots of room to price attractively)
        add("price_vs_retail", _centred(math.log10(max(0.1, ratio)),
                                        0.0, math.log10(20.0)),
            f"modelled retail is {ratio:.1f}x the asking price")
    else:
        add("price_vs_retail", None, "asking price or retail value unavailable")

    # --- comparables and category ----------------------------------------
    if comps.available:
        add("comparable_frequency", _centred(math.log10(comps.count + 1),
                                             0.0, math.log10(26)),
            f"{comps.count} comparable sale(s) found")
    else:
        add("comparable_frequency", None, "no comparable sales loaded")

    if category:
        cl = CATEGORY_LIQUIDITY.get(category, DEFAULT_CATEGORY_LIQUIDITY)
        add("category_liquidity", _centred(cl, 0.2, 0.8),
            f"category '{category}' liquidity prior {cl}")
    else:
        add("category_liquidity", None, "category could not be determined")

    log_odds += sum(contributions)
    hazard = _sigmoid(log_odds)
    hazard = max(float(p["min_annual_probability"]),
                 min(float(p["max_annual_probability"]), hazard))

    # Multi-year rollup. Independent annual hazards with a decay: the pool of
    # unsold names gets worse each year because the best ones already sold.
    decay = float(p["hazard_decay_per_year"])
    h1 = hazard
    h2 = hazard * decay
    h3 = hazard * decay * decay
    p12 = h1
    p24 = 1.0 - (1 - h1) * (1 - h2)
    p36 = 1.0 - (1 - h1) * (1 - h2) * (1 - h3)

    # Expected holding period, capped at the 36-month modelling horizon. A
    # domain that probably never sells is reported at the cap, not at infinity.
    HORIZON_MONTHS = 36.0
    expected_months = (12 * h1 * 0.5 + 24 * (p24 - p12) + 36 * (p36 - p24)
                       + HORIZON_MONTHS * (1 - p36))

    # Confidence: how much of the model actually had data behind it.
    driver_count = len(coef)
    known = driver_count - len(gaps)
    confidence = round(known / driver_count, 3)

    return ProbabilityResult(
        prob_sale_12m=round(p12, 4),
        prob_sale_24m=round(p24, 4),
        prob_sale_36m=round(p36, 4),
        annual_hazard=round(hazard, 4),
        expected_holding_months=round(expected_months, 1),
        base_log_odds=round(_logit(base_rate), 4),
        terms=terms,
        confidence=confidence,
        data_gaps=sorted(set(gaps)),
        model=f"logodds_heuristic_v0/{cfg.version}",
    )
