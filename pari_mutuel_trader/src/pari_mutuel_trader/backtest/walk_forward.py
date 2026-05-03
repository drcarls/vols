from __future__ import annotations

from copy import deepcopy
import pandas as pd

from pari_mutuel_trader.backtest.engine import run_backtest


def score(metrics: dict) -> float:
    return metrics["Sharpe"] - 0.8 * abs(metrics["MaxDrawdown"]) - 0.15 * metrics["turnover"]


def stable(metrics: dict, min_holdings: int) -> bool:
    return metrics["MaxDrawdown"] >= -0.25 and metrics["average_holdings"] >= min_holdings and metrics["rebalance_count"] >= 3


def run_wfo(features: pd.DataFrame, base_config: dict, wfo_cfg: dict) -> dict:
    dates = pd.to_datetime(sorted(features.index.get_level_values("date").unique()))
    train_days = int(wfo_cfg["train_years"] * 252)
    test_days = int(wfo_cfg["test_months"] * 21)
    step_days = int(wfo_cfg["step_months"] * 21)

    grids = []
    for k in wfo_cfg["top_k_grid"]:
        for t in wfo_cfg["temperature_grid"]:
            for e in wfo_cfg["hedge_eta_grid"]:
                c = deepcopy(base_config)
                c["portfolio"]["top_k"] = k
                c["learning"]["temperature"] = t
                c["learning"]["hedge_eta"] = e
                grids.append(c)

    segments, oos_scores = [], []
    best_cfg, best_mean = deepcopy(base_config), float("-inf")
    i = train_days
    while i + test_days < len(dates):
        tr = dates[i - train_days:i]
        te = dates[i:i + test_days]
        train_df = features.loc[features.index.get_level_values("date").isin(tr)]
        test_df = features.loc[features.index.get_level_values("date").isin(te)]

        local_best, local_score = deepcopy(base_config), float("-inf")
        for cfg in grids:
            m = run_backtest(train_df, cfg).metrics
            if stable(m, min_holdings=cfg["portfolio"]["min_holdings"]):
                s = score(m)
                if s > local_score:
                    local_score, local_best = s, deepcopy(cfg)

        oos_m = run_backtest(test_df, local_best).metrics
        oos_s = score(oos_m) if stable(oos_m, min_holdings=local_best["portfolio"]["min_holdings"]) else float("-inf")
        oos_scores.append(oos_s)
        segments.append({"test_start": str(te[0].date()), "test_end": str(te[-1].date()), "score": oos_s, "config": local_best})

        mean_s = sum(oos_scores) / len(oos_scores)
        if mean_s > best_mean:
            best_mean = mean_s
            best_cfg = deepcopy(local_best)
        i += step_days

    return {"best_config": best_cfg, "segments": segments, "mean_oos_score": best_mean}
