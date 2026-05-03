from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from pari_mutuel_trader.agents import build_v1_agents
from pari_mutuel_trader.learning.aggregation import softmax, pari_mutuel_aggregate
from pari_mutuel_trader.learning.hedge import hedge_update
from pari_mutuel_trader.portfolio.construction import build_weights, select_universe
from pari_mutuel_trader.portfolio.constraints import apply_liquidity_filter, should_rebalance, turnover
from pari_mutuel_trader.backtest.metrics import summarize


@dataclass
class BacktestResult:
    metrics: dict
    equity_curve: pd.Series
    drawdown_curve: pd.Series
    holdings_history: dict
    agent_weights_history: dict
    attribution: dict
    rebalance_trades: list


def run_backtest(features: pd.DataFrame, config: dict) -> BacktestResult:
    agents = build_v1_agents()
    dates = sorted(features.index.get_level_values("date").unique())
    all_symbols = sorted(features.index.get_level_values("symbol").unique())

    port_cfg = config["portfolio"]
    learn_cfg = config["learning"]
    risk_cfg = config["risk"]
    min_rebalances = int(config["backtest"].get("min_rebalances", 3))

    current = pd.Series(0.0, index=all_symbols)
    weights = {a.name: 1.0 / len(agents) for a in agents}
    equity = [1.0]
    eq_dates = [pd.Timestamp(dates[0])]
    turns = []
    rebalance_count = 0
    holdings_history, weight_history = {}, {}
    attribution = {a.name: 0.0 for a in agents}
    rebalance_trades = []

    for i in range(1, len(dates)):
        d0, d1 = dates[i - 1], dates[i]
        frame0 = features.xs(d0, level="date")
        frame1 = features.xs(d1, level="date")

        if i % 5 == 0:
            liquid = apply_liquidity_filter(frame0, min_adv=port_cfg.get("min_adv", 0.0))
            probs = {}
            for a in agents:
                probs[a.name] = softmax(a.compute_signal(liquid), learn_cfg["temperature"])
            pooled = pari_mutuel_aggregate(probs, weights)
            selected = select_universe(pooled, port_cfg["top_k"], port_cfg["min_holdings"])
            target = build_weights(selected, port_cfg.get("weighting", "equal_weight"), liquid.get("vol_20d"), port_cfg["max_stock_weight"])

            if should_rebalance(current[current > 0], target, port_cfg["rebalance_threshold"]):
                t = turnover(current[current > 0], target)
                if t <= port_cfg["turnover_cap"]:
                    previous = current[current > 0]
                    current = pd.Series(0.0, index=all_symbols)
                    current.loc[target.index] = target.values
                    turns.append(t)
                    rebalance_count += 1
                    holdings_history[str(pd.Timestamp(d1).date())] = target.to_dict()
                    weight_history[str(pd.Timestamp(d1).date())] = dict(weights)
                    rebalance_trades.append({"date": str(pd.Timestamp(d1).date()), "turnover": float(t), "added": list(set(target.index)-set(previous.index)), "removed": list(set(previous.index)-set(target.index))})

        ret = frame1["ret_1d"].reindex(current.index).fillna(0.0)
        port_ret = float((current * ret).sum())
        equity.append(equity[-1] * (1 + port_ret))
        eq_dates.append(pd.Timestamp(d1))

        perf = {}
        for a in agents:
            signal = a.compute_signal(frame0)
            top = signal.nlargest(port_cfg["top_k"]).index
            a_ret = frame1.loc[frame1.index.intersection(top), "ret_1d"].mean()
            perf[a.name] = float(a_ret) if a_ret == a_ret else 0.0
            attribution[a.name] += perf[a.name]
        weights = hedge_update(weights, perf, eta=learn_cfg["hedge_eta"], min_w=learn_cfg["min_agent_weight"], max_w=learn_cfg["max_agent_weight"])

    equity_curve = pd.Series(equity, index=eq_dates, name="equity")
    dd_curve = equity_curve / equity_curve.cummax() - 1.0
    avg_holdings = float(sum(len(x) for x in holdings_history.values()) / len(holdings_history)) if holdings_history else 0.0
    turnover_avg = float(sum(turns) / len(turns)) if turns else 0.0
    metrics = summarize(equity_curve, turnover_avg=turnover_avg, rebalances=rebalance_count, avg_holdings=avg_holdings)

    if metrics["MaxDrawdown"] < risk_cfg["max_drawdown_limit"]:
        metrics["risk_flag"] = "max_drawdown_breach"
    if rebalance_count < min_rebalances:
        metrics["risk_flag"] = "too_few_rebalances"
    if avg_holdings < port_cfg["min_holdings"]:
        metrics["risk_flag"] = "insufficient_holdings"
    if turnover_avg > port_cfg["turnover_cap"]:
        metrics["risk_flag"] = "excessive_turnover"

    metrics["current_holdings"] = current[current > 0].to_dict()

    return BacktestResult(metrics, equity_curve, dd_curve, holdings_history, weight_history, attribution, rebalance_trades)
