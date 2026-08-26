"""Portfolio construction under a budget and exposure constraints.

The problem is a knapsack with side constraints (per-domain cap, per-category
cap, quality floors). Exact optimisation is NP-hard and, more to the point,
pointless here: the inputs are uncalibrated priors, so a provably optimal
allocation of wrong numbers is not worth the compute.

So: greedy by expected profit per dollar, then a swap-improvement pass. The
method is stated in the output, along with every constraint that bound, so you
can see *why* a domain was left out rather than wondering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import OpportunityScore
from app.models.core import Domain
from app.scoring.config import ScoringConfig, get_scoring_config

SCENARIOS = ("conservative", "balanced", "aggressive")


@dataclass
class Holding:
    domain: str
    price: float
    opportunity_score: float
    expected_profit_24m: float | None
    expected_roi_24m: float | None
    prob_sale_24m: float | None
    recommended_max_bid: float | None
    buyer_count: int
    category: str | None
    recommendation: str
    efficiency: float

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PortfolioResult:
    scenario: str
    budget: float
    method: str
    constraints: dict[str, Any]
    holdings: list[Holding] = field(default_factory=list)
    total_invested: float = 0.0
    remaining_budget: float = 0.0
    total_expected_profit_24m: float = 0.0
    portfolio_expected_roi: float | None = None
    expected_sales_24m: float = 0.0
    category_exposure: dict[str, float] = field(default_factory=dict)
    excluded: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        d["holdings"] = [h.to_dict() for h in self.holdings]
        return d


def build_portfolio(session: Session, *, budget: float, scenario: str = "balanced",
                    run_id: int | None = None,
                    cfg: ScoringConfig | None = None) -> PortfolioResult:
    cfg = cfg or get_scoring_config()
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario must be one of {SCENARIOS}, got {scenario!r}")
    if budget <= 0:
        raise ValueError("budget must be positive")

    rules = cfg.get(f"portfolio.scenarios.{scenario}")
    max_per_domain = budget * float(rules["max_fraction_per_domain"])
    max_per_category = budget * float(rules["max_fraction_per_category"])
    min_score = float(rules["min_opportunity_score"])
    min_buyers = int(rules["min_buyer_count"])
    min_conf = float(rules["min_confidence"])

    result = PortfolioResult(
        scenario=scenario, budget=budget,
        method="greedy by expected profit per dollar, then swap improvement",
        constraints={
            "max_per_domain_usd": round(max_per_domain, 2),
            "max_per_category_usd": round(max_per_category, 2),
            "min_opportunity_score": min_score,
            "min_buyer_count": min_buyers,
            "min_confidence": min_conf,
        })

    if run_id is None:
        run_id = session.execute(
            select(OpportunityScore.run_id)
            .order_by(OpportunityScore.run_id.desc()).limit(1)).scalar()
    if run_id is None:
        result.warnings.append("No pipeline run has been executed yet.")
        return result

    rows = session.execute(
        select(OpportunityScore, Domain).join(Domain)
        .where(OpportunityScore.run_id == run_id)).all()

    candidates: list[Holding] = []
    for score, domain in rows:
        price = score.acquisition_price
        reasons: list[str] = []
        if price is None or price <= 0:
            reasons.append("no asking price - capital requirement unknown")
        if score.score < min_score:
            reasons.append(f"opportunity score {score.score:.1f} < {min_score}")
        if score.buyer_count < min_buyers:
            reasons.append(f"{score.buyer_count} buyer(s) < {min_buyers}")
        if score.confidence < min_conf:
            reasons.append(f"confidence {score.confidence:.2f} < {min_conf}")
        if score.expected_profit_24m is None or score.expected_profit_24m <= 0:
            reasons.append("expected 24-month profit is not positive")
        if price is not None and price > max_per_domain:
            reasons.append(
                f"price ${price:,.0f} exceeds the per-domain cap "
                f"${max_per_domain:,.0f}")
        if reasons:
            result.excluded.append({"domain": domain.name, "price": price,
                                    "score": score.score, "reasons": reasons})
            continue

        assert price is not None and score.expected_profit_24m is not None
        candidates.append(Holding(
            domain=domain.name, price=float(price),
            opportunity_score=score.score,
            expected_profit_24m=score.expected_profit_24m,
            expected_roi_24m=score.expected_roi_24m,
            prob_sale_24m=None, recommended_max_bid=score.recommended_max_bid,
            buyer_count=score.buyer_count, category=score.category,
            recommendation=score.recommendation,
            efficiency=score.expected_profit_24m / float(price)))

    if not candidates:
        result.warnings.append(
            f"No domain met the {scenario} scenario's constraints. "
            f"{len(result.excluded)} candidate(s) were excluded; see 'excluded' "
            f"for the binding constraint on each.")
        result.remaining_budget = budget
        return result

    candidates.sort(key=lambda h: (h.efficiency, h.opportunity_score), reverse=True)

    chosen: list[Holding] = []
    spent = 0.0
    per_category: dict[str, float] = {}
    for holding in candidates:
        cat = holding.category or "uncategorised"
        if spent + holding.price > budget:
            result.excluded.append({"domain": holding.domain, "price": holding.price,
                                    "score": holding.opportunity_score,
                                    "reasons": ["budget exhausted"]})
            continue
        if per_category.get(cat, 0.0) + holding.price > max_per_category:
            result.excluded.append({
                "domain": holding.domain, "price": holding.price,
                "score": holding.opportunity_score,
                "reasons": [f"category '{cat}' exposure cap "
                            f"${max_per_category:,.0f} would be exceeded"]})
            continue
        chosen.append(holding)
        spent += holding.price
        per_category[cat] = per_category.get(cat, 0.0) + holding.price

    # Swap improvement: try replacing the weakest holding with any excluded
    # candidate that fits and improves total expected profit. One pass is
    # enough at this scale and keeps the result explainable.
    improved = True
    passes = 0
    while improved and passes < 3:
        improved = False
        passes += 1
        chosen_names = {h.domain for h in chosen}
        pool = [h for h in candidates if h.domain not in chosen_names]
        for candidate in pool:
            for i, held in enumerate(sorted(chosen, key=lambda h: h.efficiency)):
                if candidate.expected_profit_24m <= held.expected_profit_24m:
                    continue
                new_spent = spent - held.price + candidate.price
                if new_spent > budget:
                    continue
                cat_new = candidate.category or "uncategorised"
                cat_old = held.category or "uncategorised"
                projected = per_category.get(cat_new, 0.0) + candidate.price
                if cat_new == cat_old:
                    projected -= held.price
                if projected > max_per_category:
                    continue
                chosen = [h for h in chosen if h.domain != held.domain] + [candidate]
                per_category[cat_old] = per_category.get(cat_old, 0.0) - held.price
                per_category[cat_new] = per_category.get(cat_new, 0.0) + candidate.price
                spent = new_spent
                improved = True
                break
            if improved:
                break

    chosen.sort(key=lambda h: h.opportunity_score, reverse=True)
    result.holdings = chosen
    result.total_invested = round(spent, 2)
    result.remaining_budget = round(budget - spent, 2)
    result.total_expected_profit_24m = round(
        sum(h.expected_profit_24m or 0.0 for h in chosen), 2)
    result.portfolio_expected_roi = (
        round(result.total_expected_profit_24m / spent, 4) if spent > 0 else None)
    result.category_exposure = {k: round(v, 2) for k, v in per_category.items() if v > 0}
    result.warnings.append(
        "Expected profit is a model output from an UNCALIBRATED scoring "
        "config. Treat this allocation as a research exercise, not advice.")
    return result
