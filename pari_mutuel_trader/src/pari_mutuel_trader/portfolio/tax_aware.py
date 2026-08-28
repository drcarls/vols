from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from pari_mutuel_trader.portfolio.lots import HIFO, LotLedger
from pari_mutuel_trader.valuation.tax import days_to_long_term


@dataclass
class SeasoningPolicy:
    """When a sale is worth deferring for the holding-period clock.

    The discretionary rule transplanted: do not sit in a position you are
    uncomfortable with just to reach a long-term rate, but when the case for
    selling is marginal and the clock is nearly run, let it run.
    """

    enabled: bool = True
    wait_days: int = 45
    keep_multiple: float = 2.0
    lot_method: str = HIFO
    wash_sales: bool = True

    @classmethod
    def from_config(cls, cfg: dict | None) -> "SeasoningPolicy":
        cfg = cfg or {}
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in cfg.items() if k in known})


def seasoning_holds(
    target: pd.Series,
    current: pd.Series,
    ledger: LotLedger,
    prices: pd.Series,
    pooled: pd.Series,
    policy: SeasoningPolicy,
    as_of: date,
    keep_rank: int,
) -> set[str]:
    """Names the sleeve wants to drop that are worth holding to long-term treatment.

    A name qualifies only while the case against it is weak. Once its score falls
    out of the widened keep band, conviction has gone and the clock stops being a
    reason to stay.
    """
    if not policy.enabled:
        return set()

    held = set(current[current > 0].index)
    dropping = held - set(target.index)
    if not dropping:
        return set()

    still_ranked = set(pooled.sort_values(ascending=False).head(keep_rank).index)
    holds = set()
    for symbol in dropping:
        if symbol not in still_ranked:
            continue
        price = float(prices.get(symbol, 0.0))
        if ledger.unrealized_gain(symbol, price) <= 0:
            continue  # a loss is worth realizing, not deferring
        acquired = ledger.newest_acquisition(symbol)
        remaining = days_to_long_term(acquired, as_of)
        if 0 < remaining <= policy.wait_days:
            holds.add(symbol)
    return holds


def apply_holds(target: pd.Series, current: pd.Series, holds: set[str]) -> pd.Series:
    """Re-admit deferred names at their existing weight and renormalize."""
    if not holds:
        return target
    combined = target.copy()
    for symbol in holds:
        combined.loc[symbol] = float(current.get(symbol, 0.0))
    total = float(combined.sum())
    return combined / total if total > 0 else combined
