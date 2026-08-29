from __future__ import annotations

import pandas as pd


def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(raw.index, pd.MultiIndex):
        raise ValueError("Expected MultiIndex (date, symbol)")
    raw = raw.sort_index()
    grouped = raw.groupby(level="symbol")
    out = raw.copy()
    out["ret_20d"] = grouped["close"].pct_change(20).fillna(0)
    out["ret_60d"] = grouped["close"].pct_change(60).fillna(0)
    out["vol_20d"] = grouped["ret_1d"].rolling(20).std().reset_index(level=0, drop=True).fillna(0.02)
    out["drawdown_60d"] = grouped["close"].transform(lambda s: s / s.rolling(60, min_periods=1).max() - 1)
    out["breakout_20d"] = grouped["close"].transform(lambda s: (s - s.rolling(20, min_periods=1).max()) / s.clip(lower=1e-6))
    out["trend_persistence"] = grouped["ret_1d"].transform(lambda s: s.rolling(20, min_periods=1).mean())
    if "news_intensity" not in out:
        out["news_intensity"] = 0.0
    if "macro_regime" not in out:
        out["macro_regime"] = 0.0
    for col in ("discount_to_iv15", "premium_to_iv8", "durability", "dislocation", "iv15", "iv8"):
        if col not in out:
            out[col] = 0.0
    cols = [
        "ret_1d", "ret_20d", "ret_60d", "vol_20d", "drawdown_60d", "breakout_20d",
        "trend_persistence", "news_intensity", "macro_regime",
        "discount_to_iv15", "premium_to_iv8", "durability", "dislocation", "iv15", "iv8",
        "adv_usd", "close"
    ]
    return out[cols].fillna(0.0)
