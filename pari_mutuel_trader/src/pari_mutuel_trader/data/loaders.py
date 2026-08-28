from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def load_features(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.exists():
        if p.suffix == ".parquet":
            return pd.read_parquet(p)
        if p.suffix == ".csv":
            df = pd.read_csv(p, parse_dates=["date"])
            return df.set_index(["date", "symbol"]).sort_index()
    return generate_sample_features()


def generate_sample_features(days: int = 800, n_symbols: int = 80, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2019-01-01", periods=days)
    syms = [f"STK{i:03d}" for i in range(n_symbols)]
    idx = pd.MultiIndex.from_product([dates, syms], names=["date", "symbol"])
    n = len(idx)
    df = pd.DataFrame(index=idx)
    df["ret_1d"] = rng.normal(0.0004, 0.018, n)
    # Price has to be the compounded return series, not an independent draw:
    # otherwise every price-derived feature is unrelated to the returns being
    # earned, and a cost basis taken from `close` is meaningless.
    start = pd.Series(rng.uniform(5, 300, n_symbols), index=syms)
    growth = (1.0 + df["ret_1d"]).groupby(level="symbol").cumprod()
    df["close"] = growth * start.reindex(df.index.get_level_values("symbol")).values
    df["volume"] = rng.integers(50_000, 2_000_000, n)
    df["adv_usd"] = df["close"] * df["volume"]
    return df
