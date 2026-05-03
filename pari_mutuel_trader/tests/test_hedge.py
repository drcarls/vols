from pari_mutuel_trader.learning.hedge import hedge_update


def test_hedge_normalizes_weights():
    w = {"a": 0.5, "b": 0.5}
    p = {"a": 0.02, "b": -0.01}
    out = hedge_update(w, p, eta=0.05, min_w=0.05, max_w=0.95)
    assert abs(sum(out.values()) - 1.0) < 1e-9
