from __future__ import annotations

import numpy as np
import pandas as pd

FORWARD_HORIZONS = (20, 60, 120)


def forward_returns(features: pd.DataFrame, horizons=FORWARD_HORIZONS) -> pd.DataFrame:
    """Trailing-safe forward returns per horizon, aligned to the (date, symbol) index."""
    close = features["close"]
    out = {}
    for h in horizons:
        ahead = close.groupby(level="symbol").shift(-h)
        out[f"fwd_{h}d"] = ahead / close - 1.0
    return pd.DataFrame(out, index=features.index)


def selected_panel(features: pd.DataFrame, holdings_history: dict, signal: str) -> pd.DataFrame:
    """One row per (rebalance date, selected symbol) with its IV reading and forwards.

    The selection comes from a baseline backtest's own holdings, so the study asks
    exactly the intended question: within the names this sleeve already wants, does
    the IV reading order what happens next?
    """
    fwd = forward_returns(features)
    rows = []
    for day, holdings in holdings_history.items():
        stamp = pd.Timestamp(day)
        if stamp not in features.index.get_level_values("date"):
            continue
        frame = features.xs(stamp, level="date")
        forwards = fwd.xs(stamp, level="date")
        for symbol in holdings:
            if symbol not in frame.index or signal not in frame.columns:
                continue
            row = {"date": stamp, "symbol": symbol, "signal": float(frame.loc[symbol, signal])}
            for column in forwards.columns:
                row[column] = float(forwards.loc[symbol, column]) if symbol in forwards.index else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def bucket_by_signal(panel: pd.DataFrame, buckets: int = 5, min_per_date: int = 10) -> pd.DataFrame:
    """Assign each name a within-date bucket, cheapest last.

    Bucketing inside the date avoids comparing a cheap name in one month against an
    expensive one in another, which would measure the market rather than the signal.
    Falls back to terciles when a date is too thin to cut five ways.
    """
    if panel.empty:
        return panel.assign(bucket=pd.Series(dtype=float))

    def cut(group: pd.DataFrame) -> pd.Series:
        n = len(group)
        k = buckets if n >= min_per_date else 3
        if n < k or group["signal"].nunique() < k:
            return pd.Series(np.nan, index=group.index)
        return pd.qcut(group["signal"].rank(method="first"), k, labels=range(1, k + 1)).astype(float)

    pieces = [cut(group) for _, group in panel.groupby("date")]
    bucket = pd.concat(pieces).reindex(panel.index) if pieces else pd.Series(np.nan, index=panel.index)
    out = panel.copy()
    out["bucket"] = bucket.astype(float)
    return out


def bucket_returns(panel: pd.DataFrame, horizons=FORWARD_HORIZONS) -> pd.DataFrame:
    """Mean forward return per IV bucket. Bucket 1 is the most expensive."""
    if panel.empty or panel["bucket"].isna().all():
        return pd.DataFrame()
    columns = [f"fwd_{h}d" for h in horizons]
    table = panel.groupby("bucket")[columns].mean()
    table["n"] = panel.groupby("bucket").size()
    return table


def monotonicity(table: pd.DataFrame, column: str) -> dict:
    """How well the bucket ordering lines up with subsequent return.

    `spearman` is the rank correlation between bucket number and mean return, so +1
    means cheap beats expensive in a perfectly ordered staircase. `spread` is the
    cheapest bucket minus the most expensive.
    """
    if table.empty or column not in table:
        return {"spearman": float("nan"), "spread": float("nan"), "buckets": 0}
    means = table[column].dropna()
    if len(means) < 2:
        return {"spearman": float("nan"), "spread": float("nan"), "buckets": len(means)}
    order = pd.Series(means.index, index=means.index, dtype=float)
    return {
        "spearman": float(order.rank().corr(means.rank())),
        "spread": float(means.iloc[-1] - means.iloc[0]),
        "buckets": int(len(means)),
    }


def conditional_study(
    features: pd.DataFrame,
    holdings_history: dict,
    signals: list[str],
    buckets: int = 5,
) -> dict:
    """Section 2: forward returns by IV bucket within an existing sleeve's picks."""
    out = {}
    for signal in signals:
        panel = bucket_by_signal(selected_panel(features, holdings_history, signal), buckets)
        table = bucket_returns(panel)
        out[signal] = {
            "table": table,
            "monotonicity": {f"fwd_{h}d": monotonicity(table, f"fwd_{h}d") for h in FORWARD_HORIZONS},
            "observations": int(len(panel)),
        }
    return out


def momentum_iv_grid(features: pd.DataFrame, holdings_history: dict,
                     momentum_col: str = "ret_60d", iv_change_col: str = "iv8_chg_3m") -> pd.DataFrame:
    """Section 7: the 2x2 of price momentum against the direction of intrinsic value."""
    fwd = forward_returns(features)
    rows = []
    for day, holdings in holdings_history.items():
        stamp = pd.Timestamp(day)
        if stamp not in features.index.get_level_values("date"):
            continue
        frame = features.xs(stamp, level="date")
        forwards = fwd.xs(stamp, level="date")
        present = [s for s in holdings if s in frame.index]
        if len(present) < 4:
            continue
        sub = frame.loc[present]
        strong = sub[momentum_col] >= sub[momentum_col].median()
        rising = sub[iv_change_col] > 0
        for symbol in present:
            rows.append({
                "momentum": "strong" if strong[symbol] else "weak",
                "intrinsic_value": "rising" if rising[symbol] else "falling",
                **{c: (float(forwards.loc[symbol, c]) if symbol in forwards.index else np.nan)
                   for c in forwards.columns},
            })
    panel = pd.DataFrame(rows)
    if panel.empty:
        return panel
    grid = panel.groupby(["momentum", "intrinsic_value"])[list(fwd.columns)].mean()
    grid["n"] = panel.groupby(["momentum", "intrinsic_value"]).size()
    return grid
