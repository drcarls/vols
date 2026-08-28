from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from pari_mutuel_trader.agents import build_v1_agents
from pari_mutuel_trader.learning.aggregation import softmax, pari_mutuel_aggregate
from pari_mutuel_trader.learning.hedge import hedge_update
from pari_mutuel_trader.portfolio.construction import build_weights, select_universe
from pari_mutuel_trader.portfolio.constraints import apply_liquidity_filter, should_rebalance, turnover
from pari_mutuel_trader.portfolio.lots import LotLedger
from pari_mutuel_trader.portfolio.tax_aware import SeasoningPolicy, apply_holds, seasoning_holds
from pari_mutuel_trader.backtest.metrics import summarize
from pari_mutuel_trader.valuation.overlay import apply_valuation_caps, zone_caps
from pari_mutuel_trader.valuation.sell_rules import SellPolicy
from pari_mutuel_trader.valuation.tax import TaxProfile


@dataclass
class BacktestResult:
    metrics: dict
    equity_curve: pd.Series
    drawdown_curve: pd.Series
    holdings_history: dict
    agent_weights_history: dict
    attribution: dict
    rebalance_trades: list
    after_tax_curve: pd.Series
    realized_sales: list


def run_backtest(features: pd.DataFrame, config: dict) -> BacktestResult:
    agents = build_v1_agents()
    dates = sorted(features.index.get_level_values("date").unique())
    all_symbols = sorted(features.index.get_level_values("symbol").unique())

    port_cfg = config["portfolio"]
    learn_cfg = config["learning"]
    risk_cfg = config["risk"]
    val_cfg = config.get("valuation", {}) or {}
    val_policy = SellPolicy.from_config(val_cfg)
    valuation_on = bool(val_cfg.get("enabled", False))
    tax_cfg = config.get("tax", {}) or {}
    tax_profile = TaxProfile(**{k: float(v) for k, v in tax_cfg.items() if k in TaxProfile.__dataclass_fields__})
    seasoning = SeasoningPolicy.from_config(config.get("tax_aware"))
    min_rebalances = int(config["backtest"].get("min_rebalances", 3))

    current = pd.Series(0.0, index=all_symbols)
    ledger = LotLedger(method=seasoning.lot_method, wash_sales=seasoning.wash_sales)
    weights = {a.name: 1.0 / len(agents) for a in agents}
    equity = [1.0]
    eq_dates = [pd.Timestamp(dates[0])]
    after_tax = [1.0]
    tax_multiplier = 1.0
    turns = []
    rebalance_count = 0
    holdings_history, weight_history = {}, {}
    attribution = {a.name: 0.0 for a in agents}
    rebalance_trades = []
    realized_sales = []
    blocked = 0

    for i in range(1, len(dates)):
        d0, d1 = dates[i - 1], dates[i]
        frame0 = features.xs(d0, level="date")
        frame1 = features.xs(d1, level="date")

        if i % 5 == 0:
            as_of = pd.Timestamp(d1).date()
            liquid = apply_liquidity_filter(frame0, min_adv=port_cfg.get("min_adv", 0.0))
            # An agent with no data to vote on is dropped rather than allowed to cast
            # a flat vote, which would only dilute the agents that do have a view.
            active = [a for a in agents if not a.abstains(liquid)] or agents
            probs = {a.name: softmax(a.compute_signal(liquid), learn_cfg["temperature"]) for a in active}
            pooled = pari_mutuel_aggregate(probs, {a.name: weights[a.name] for a in active})
            selected = select_universe(pooled, port_cfg["top_k"], port_cfg["min_holdings"])
            target = build_weights(selected, port_cfg.get("weighting", "equal_weight"), liquid.get("vol_20d"), port_cfg["max_stock_weight"])

            if valuation_on:
                natural = 1.0 / len(target) if len(target) else None
                target = apply_valuation_caps(target, zone_caps(liquid, val_policy, natural), port_cfg["max_stock_weight"])

            prices = frame0["close"]
            holds = seasoning_holds(target, current, ledger, prices, pooled, seasoning, as_of, keep_rank=int(seasoning.keep_multiple * port_cfg["top_k"]))
            target = apply_holds(target, current, holds)

            if should_rebalance(current[current > 0], target, port_cfg["rebalance_threshold"]):
                previous = current[current > 0]
                t = turnover(previous, target)
                # Building the book from cash is not turnover - there is nothing yet
                # to turn over - so the cap applies only once the sleeve is invested.
                initial_build = previous.empty
                if not initial_build and t > port_cfg["turnover_cap"]:
                    blocked += 1
                else:
                    updated = pd.Series(0.0, index=all_symbols)
                    updated.loc[target.index] = target.values

                    tax_fraction = 0.0
                    for symbol in set(previous.index).union(target.index):
                        delta = float(updated.get(symbol, 0.0) - current.get(symbol, 0.0))
                        price = float(prices.get(symbol, 0.0))
                        if delta < -1e-12:
                            sales = ledger.sell(symbol, -delta, price, as_of, tax_profile)
                            realized_sales.extend(sales)
                            tax_fraction += sum(s.tax for s in sales)
                        elif delta > 1e-12:
                            tax_fraction += ledger.buy(symbol, delta, price, as_of)
                    tax_multiplier *= 1.0 - tax_fraction

                    current = updated
                    if not initial_build:
                        turns.append(t)  # the initial build is exempt, so it is not averaged in
                    rebalance_count += 1
                    holdings_history[str(as_of)] = target.to_dict()
                    weight_history[str(as_of)] = dict(weights)
                    rebalance_trades.append({
                        "date": str(as_of),
                        "turnover": float(t),
                        "added": list(set(target.index) - set(previous.index)),
                        "removed": list(set(previous.index) - set(target.index)),
                        "deferred_for_seasoning": sorted(holds),
                        "tax_drag": float(tax_fraction),
                    })

        ret = frame1["ret_1d"].reindex(current.index).fillna(0.0)
        port_ret = float((current * ret).sum())
        equity.append(equity[-1] * (1 + port_ret))
        after_tax.append(equity[-1] * tax_multiplier)
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
    after_tax_curve = pd.Series(after_tax, index=eq_dates, name="after_tax_equity")
    dd_curve = equity_curve / equity_curve.cummax() - 1.0
    avg_holdings = float(sum(len(x) for x in holdings_history.values()) / len(holdings_history)) if holdings_history else 0.0
    turnover_avg = float(sum(turns) / len(turns)) if turns else 0.0
    metrics = summarize(equity_curve, turnover_avg=turnover_avg, rebalances=rebalance_count, avg_holdings=avg_holdings)

    after_tax_metrics = summarize(after_tax_curve, turnover_avg=turnover_avg, rebalances=rebalance_count, avg_holdings=avg_holdings)
    realized_tax = float(sum(s.tax for s in realized_sales))
    short_term_tax = float(sum(s.tax for s in realized_sales if not s.long_term))
    metrics["CAGR_after_tax"] = after_tax_metrics["CAGR"]
    metrics["tax_drag_annual"] = float(metrics["CAGR"] - after_tax_metrics["CAGR"])
    metrics["realized_tax"] = realized_tax
    metrics["short_term_share_of_tax"] = float(short_term_tax / realized_tax) if realized_tax else 0.0
    metrics["deferred_for_seasoning"] = int(sum(len(t["deferred_for_seasoning"]) for t in rebalance_trades))
    metrics["blocked_by_turnover_cap"] = int(blocked)
    metrics["wash_sale_disallowed"] = float(ledger.disallowed_loss)

    if metrics["MaxDrawdown"] < risk_cfg["max_drawdown_limit"]:
        metrics["risk_flag"] = "max_drawdown_breach"
    if rebalance_count < min_rebalances:
        metrics["risk_flag"] = "too_few_rebalances"
    if avg_holdings < port_cfg["min_holdings"]:
        metrics["risk_flag"] = "insufficient_holdings"
    if turnover_avg > port_cfg["turnover_cap"]:
        metrics["risk_flag"] = "excessive_turnover"

    metrics["current_holdings"] = current[current > 0].to_dict()

    return BacktestResult(
        metrics, equity_curve, dd_curve, holdings_history, weight_history,
        attribution, rebalance_trades, after_tax_curve, realized_sales,
    )
