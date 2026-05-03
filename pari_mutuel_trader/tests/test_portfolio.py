import pandas as pd
from pari_mutuel_trader.portfolio.construction import build_weights


def test_probability_weight():
    s = pd.Series([0.5, 0.3, 0.2], index=["a", "b", "c"])
    w = build_weights(s, mode="probability_weight", vol=None, max_weight=0.8)
    assert abs(float(w.sum()) - 1.0) < 1e-9
