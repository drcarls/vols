from pari_mutuel_trader.data.loaders import generate_sample_features
from pari_mutuel_trader.data.features import build_features
from pari_mutuel_trader.backtest.engine import run_backtest


def test_backtest_outputs_metrics():
    raw = generate_sample_features(days=300, n_symbols=40)
    feat = build_features(raw)
    cfg = {
        "data": {"features_path": "data/processed/features.parquet", "state_path": "data/state/dashboard_state.json"},
        "portfolio": {"top_k": 25, "min_holdings": 20, "max_stock_weight": 0.05, "turnover_cap": 0.4, "rebalance_threshold": 0.01, "weighting": "equal_weight", "min_adv": 0},
        "learning": {"temperature": 1.0, "hedge_eta": 0.03, "min_agent_weight": 0.05, "max_agent_weight": 0.5},
        "backtest": {"frequency": "weekly", "min_rebalances": 3},
        "risk": {"max_drawdown_limit": -0.25},
    }
    out = run_backtest(feat, cfg)
    assert "Sharpe" in out.metrics
