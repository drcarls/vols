from __future__ import annotations

import pandas as pd

from pari_mutuel_trader.valuation.intrinsic import EXPENSIVE, FAIR, RICH, SPRING_LOADED
from pari_mutuel_trader.valuation.sell_rules import SellPolicy

IV_COLUMNS = ("discount_to_iv15", "premium_to_iv8")


def has_valuation(frame: pd.DataFrame) -> bool:
    return all(c in frame.columns for c in IV_COLUMNS)


def zones_from_frame(frame: pd.DataFrame, rich_band: float = 0.15) -> pd.Series:
    """Map the IV columns of a feature frame onto valuation zones."""
    discount = frame["discount_to_iv15"].fillna(0.0)
    premium = frame["premium_to_iv8"].fillna(0.0)
    zone = pd.Series(FAIR, index=frame.index, dtype=object)
    zone[premium > 0] = RICH
    zone[premium > rich_band] = EXPENSIVE
    zone[discount >= 0] = SPRING_LOADED
    return zone


def zone_ceilings(policy: SellPolicy, natural_weight: float | None = None) -> dict[str, float]:
    """Weight ceiling per zone.

    Absolute ceilings are portfolio percentages and suit a concentrated book. In a
    diversified sleeve they are the wrong units: at 25 equal-weighted names the
    natural position is 4%, so every ceiling above that is inert and the overlay
    only ever shaves the expensive bucket. Relative sizing scales the ceilings off
    the natural position instead, so they bind at any breadth.
    """
    if policy.sizing == "relative":
        if not natural_weight:
            raise ValueError("relative sizing needs the sleeve's natural weight")
        return {zone: natural_weight * mult for zone, mult in policy.zone_multiples.items()}
    return {
        SPRING_LOADED: policy.conviction_weight,
        FAIR: policy.core_weight,
        RICH: 0.5 * (policy.core_weight + policy.house_money_weight),
        EXPENSIVE: policy.house_money_weight,
    }


def zone_caps(
    frame: pd.DataFrame, policy: SellPolicy, natural_weight: float | None = None
) -> pd.Series | None:
    """Per-symbol weight ceiling implied by where the price sits against IV15/IV8."""
    if not has_valuation(frame):
        return None
    ceilings = zone_ceilings(policy, natural_weight)
    return zones_from_frame(frame, policy.rich_band).map(ceilings).astype(float)


def apply_valuation_caps(weights: pd.Series, caps: pd.Series | None, default_cap: float) -> pd.Series:
    """Clip target weights to their valuation ceilings and renormalize."""
    if caps is None or weights.empty:
        return weights
    limits = caps.reindex(weights.index).fillna(default_cap)
    capped = weights.clip(upper=limits)
    total = float(capped.sum())
    return capped / total if total > 0 else capped
