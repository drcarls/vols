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


def generate_valuation_universe(
    days: int = 800,
    n_symbols: int = 80,
    seed: int = 42,
    reversion: float = 0.0,
    dispersion: float = 0.45,
    drift: float = 0.0002,
    vol: float = 0.018,
):
    """A test world where value exists independently of price.

    Fundamentals are drawn first and prices are anchored to them, which is the only
    way to ask whether a valuation signal helps: if owner earnings are derived from
    the price history, "cheap" just means "has fallen" and any edge is circular.

    `reversion` is the daily pull of price toward intrinsic value. At 0 the world is
    a pure random walk and no valuation signal can help - that is the null the
    strategy has to fail. Above 0 there is a real effect to find.

    Returns the raw feature frame and the fundamentals that generated it.
    """
    from datetime import timedelta

    from pari_mutuel_trader.valuation.features import Revision
    from pari_mutuel_trader.valuation.intrinsic import ValuationInputs, intrinsic_value
    from pari_mutuel_trader.valuation.quality import QualityProfile

    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2019-01-01", periods=days)
    syms = [f"STK{i:03d}" for i in range(n_symbols)]
    midpoint = days // 2

    moat = rng.uniform(0.15, 0.95, n_symbols)
    roic = 0.08 + moat * rng.uniform(0.10, 0.30, n_symbols)
    stability = np.clip(moat + rng.normal(0, 0.12, n_symbols), 0.05, 0.95)
    growth = rng.uniform(0.03, 0.18, n_symbols)
    earnings = rng.uniform(0.5, 12.0, n_symbols)
    revision_shock = rng.uniform(0.75, 1.35, n_symbols)

    def inputs_for(i, scale):
        return ValuationInputs(
            owner_earnings_ps=float(earnings[i] * scale),
            growth=float(growth[i]),
            quality=QualityProfile(float(moat[i]), float(roic[i]), float(stability[i])),
        )

    fundamentals, iv_early, iv_late = {}, np.empty(n_symbols), np.empty(n_symbols)
    for i, symbol in enumerate(syms):
        early, late = inputs_for(i, 1.0), inputs_for(i, revision_shock[i])
        iv_early[i] = intrinsic_value(early, 0.15)
        iv_late[i] = intrinsic_value(late, 0.15)
        fundamentals[symbol] = [
            Revision(dates[0].date() - timedelta(days=1), early),
            Revision(dates[midpoint].date(), late),
        ]

    # Price starts scattered around value, then walks - pulled toward it or not.
    log_price = np.log(iv_early) + rng.normal(0.0, dispersion, n_symbols)
    shocks = rng.normal(drift, vol, (days, n_symbols))
    closes = np.empty((days, n_symbols))
    for t in range(days):
        target = np.log(iv_early if t < midpoint else iv_late)
        log_price = log_price + shocks[t] + reversion * (target - log_price)
        closes[t] = np.exp(log_price)

    close = pd.DataFrame(closes, index=dates, columns=syms)
    ret = close.pct_change().fillna(0.0)
    frame = pd.DataFrame({
        "ret_1d": ret.stack(),
        "close": close.stack(),
    })
    frame.index.names = ["date", "symbol"]
    frame = frame.sort_index()
    frame["volume"] = rng.integers(50_000, 2_000_000, len(frame))
    frame["adv_usd"] = frame["close"] * frame["volume"]
    return frame, fundamentals
