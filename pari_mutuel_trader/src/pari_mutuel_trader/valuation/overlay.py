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


def zone_caps(frame: pd.DataFrame, policy: SellPolicy) -> pd.Series | None:
    """Per-symbol weight ceiling implied by where the price sits against IV15/IV8."""
    if not has_valuation(frame):
        return None
    ceilings = {
        SPRING_LOADED: policy.conviction_weight,
        FAIR: policy.core_weight,
        RICH: 0.5 * (policy.core_weight + policy.house_money_weight),
        EXPENSIVE: policy.house_money_weight,
    }
    return zones_from_frame(frame, policy.rich_band).map(ceilings).astype(float)


def apply_valuation_caps(weights: pd.Series, caps: pd.Series | None, default_cap: float) -> pd.Series:
    """Clip target weights to their valuation ceilings and renormalize."""
    if caps is None or weights.empty:
        return weights
    limits = caps.reindex(weights.index).fillna(default_cap)
    capped = weights.clip(upper=limits)
    total = float(capped.sum())
    return capped / total if total > 0 else capped
