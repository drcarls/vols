from __future__ import annotations

import pandas as pd


def select_universe(prob: pd.Series, top_k: int, min_holdings: int) -> pd.Series:
    n = max(top_k, min_holdings)
    return prob.sort_values(ascending=False).head(n)


def build_weights(selected_prob: pd.Series, mode: str, vol: pd.Series | None, max_weight: float) -> pd.Series:
    if selected_prob.empty:
        return selected_prob
    if mode == "equal_weight":
        w = pd.Series(1.0 / len(selected_prob), index=selected_prob.index)
    elif mode == "probability_weight":
        w = selected_prob / selected_prob.sum()
    elif mode == "volatility_adjusted":
        if vol is None:
            raise ValueError("vol required for volatility_adjusted")
        inv = 1 / vol.reindex(selected_prob.index).clip(lower=1e-6)
        w = inv / inv.sum()
    else:
        raise ValueError(f"Unknown weighting mode: {mode}")

    w = w.clip(upper=max_weight)
    return w / w.sum()
