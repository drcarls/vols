from __future__ import annotations

from pathlib import Path

from pari_mutuel_trader.backtest.engine import run_backtest
from pari_mutuel_trader.paper.state import save_state


def run_paper(features, config: dict, state_path: str) -> dict:
    result = run_backtest(features, config)
    positions_path = config.get("data", {}).get("positions_path")
    review = {}
    if positions_path and Path(positions_path).exists():
        from pari_mutuel_trader.valuation.book import run_review

        review = run_review(positions_path)
    payload = {
        "metrics": result.metrics,
        "equity_curve": {str(k.date()): float(v) for k, v in result.equity_curve.items()},
        "drawdown_curve": {str(k.date()): float(v) for k, v in result.drawdown_curve.items()},
        "after_tax_curve": {str(k.date()): float(v) for k, v in result.after_tax_curve.items()},
        "holdings_history": result.holdings_history,
        "agent_weights_history": result.agent_weights_history,
        "attribution": result.attribution,
        "rebalance_trades": result.rebalance_trades,
        "position_review": review,
        "config": config,
    }
    save_state(state_path, payload)
    return payload
