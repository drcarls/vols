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


def generate_sample_fundamentals(features: pd.DataFrame, seed: int = 11) -> dict:
    """Plausible per-symbol assumptions for the sample universe.

    Quality is spread across the universe so the dislocated-quality gate has both
    franchises and commodities to sort between, and each symbol carries a mid-sample
    revision so value can move independently of price.
    """
    from datetime import timedelta

    from pari_mutuel_trader.valuation.features import Revision
    from pari_mutuel_trader.valuation.intrinsic import ValuationInputs
    from pari_mutuel_trader.valuation.quality import QualityProfile

    rng = np.random.default_rng(seed)
    dates = features.index.get_level_values("date").unique().sort_values()
    start, midpoint = dates[0].date(), dates[len(dates) // 2].date()

    out = {}
    for symbol in sorted(features.index.get_level_values("symbol").unique()):
        first_close = float(features.xs(symbol, level="symbol")["close"].iloc[0])
        moat = float(rng.uniform(0.15, 0.95))
        roic = float(0.08 + moat * rng.uniform(0.10, 0.30))
        stability = float(np.clip(moat + rng.normal(0, 0.12), 0.05, 0.95))
        growth = float(rng.uniform(0.03, 0.18))
        # Anchor owner earnings so prices start scattered around intrinsic value.
        earnings = first_close * float(rng.uniform(0.03, 0.09))

        def revision(on, scale):
            return Revision(
                on,
                ValuationInputs(
                    owner_earnings_ps=earnings * scale,
                    growth=growth,
                    quality=QualityProfile(moat=moat, roic=roic, roic_stability=stability),
                ),
            )

        out[symbol] = [
            revision(start - timedelta(days=1), 1.0),
            revision(midpoint, float(rng.uniform(0.75, 1.35))),
        ]
    return out
