from __future__ import annotations

from pari_mutuel_trader.backtest.engine import run_backtest
from pari_mutuel_trader.paper.state import save_state


def run_paper(features, config: dict, state_path: str) -> dict:
    result = run_backtest(features, config)
    payload = {
        "metrics": result.metrics,
        "equity_curve": {str(k.date()): float(v) for k, v in result.equity_curve.items()},
        "drawdown_curve": {str(k.date()): float(v) for k, v in result.drawdown_curve.items()},
        "holdings_history": result.holdings_history,
        "agent_weights_history": result.agent_weights_history,
        "attribution": result.attribution,
        "rebalance_trades": result.rebalance_trades,
        "config": config,
    }
    save_state(state_path, payload)
    return payload
