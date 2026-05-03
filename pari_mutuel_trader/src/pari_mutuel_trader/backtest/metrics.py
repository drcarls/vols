from __future__ import annotations

import numpy as np
import pandas as pd


def drawdown(equity: pd.Series) -> pd.Series:
    return equity / equity.cummax() - 1.0


def sharpe(r: pd.Series, periods: int = 52) -> float:
    if r.std(ddof=0) == 0:
        return 0.0
    return float(np.sqrt(periods) * r.mean() / r.std(ddof=0))


def sortino(r: pd.Series, periods: int = 52) -> float:
    d = r[r < 0]
    if d.std(ddof=0) == 0:
        return 0.0
    return float(np.sqrt(periods) * r.mean() / d.std(ddof=0))


def summarize(equity: pd.Series, turnover_avg: float, rebalances: int, avg_holdings: float) -> dict:
    returns = equity.pct_change().dropna()
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-6)
    cagr = float(equity.iloc[-1] ** (1 / years) - 1)
    dd = drawdown(equity)
    mdd = float(dd.min())
    monthly = returns.resample("ME").sum()
    calmar = float(cagr / abs(mdd)) if mdd != 0 else 0.0
    return {
        "CAGR": cagr,
        "Sharpe": sharpe(returns),
        "Sortino": sortino(returns),
        "MaxDrawdown": mdd,
        "Calmar": calmar,
        "monthly_returns": monthly.to_dict(),
        "worst_month": float(monthly.min()) if not monthly.empty else 0.0,
        "turnover": float(turnover_avg),
        "rebalance_count": int(rebalances),
        "average_holdings": float(avg_holdings),
    }
