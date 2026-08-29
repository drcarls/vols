from __future__ import annotations

import pandas as pd


def turnover(old_w: pd.Series, new_w: pd.Series) -> float:
    idx = old_w.index.union(new_w.index)
    a = old_w.reindex(idx, fill_value=0.0)
    b = new_w.reindex(idx, fill_value=0.0)
    return float(0.5 * (a - b).abs().sum())


def should_rebalance(old_w: pd.Series, new_w: pd.Series, threshold: float) -> bool:
    idx = old_w.index.union(new_w.index)
    a = old_w.reindex(idx, fill_value=0.0)
    b = new_w.reindex(idx, fill_value=0.0)
    return bool((a - b).abs().max() > threshold)


def apply_liquidity_filter(frame: pd.DataFrame, min_adv: float) -> pd.DataFrame:
    if "adv_usd" not in frame.columns:
        return frame
    return frame[frame["adv_usd"] >= min_adv]


def apply_quality_filter(frame: pd.DataFrame, min_durability: float) -> pd.DataFrame:
    """Drop names whose franchise is not durable enough to be worth buying weak.

    This is a gate, not a tilt. Buying a fallen price is only a strategy when the
    business behind it is going to still be there; below the threshold a discount
    is just a discount.
    """
    if not min_durability or "durability" not in frame.columns:
        return frame
    return frame[frame["durability"] >= min_durability]
