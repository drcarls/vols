from pari_mutuel_trader.learning.aggregation import softmax
import pandas as pd


def test_softmax_sum_to_one():
    s = pd.Series([1.0, 2.0, 3.0], index=["a", "b", "c"])
    p = softmax(s, 1.0)
    assert abs(float(p.sum()) - 1.0) < 1e-9
