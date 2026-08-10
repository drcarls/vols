import pandas as pd
from pytest import approx

from pari_mutuel_trader.agents.geopolitical import GeopoliticalAgent
from pari_mutuel_trader.data.geopolitical import build_geo_signal, attach_geo_signal
from pari_mutuel_trader.agents import build_v1_agents


def test_agent_neutral_when_column_absent():
    df = pd.DataFrame({"ret_1d": [0.0, 0.0]}, index=["AAA", "BBB"])
    out = GeopoliticalAgent().compute_signal(df)
    assert (out == 0.0).all()
    assert list(out.index) == ["AAA", "BBB"]


def test_agent_reads_geo_signal_column():
    df = pd.DataFrame({"geo_signal": [0.4, -0.2, 0.0]}, index=["AAA", "BBB", "CCC"])
    out = GeopoliticalAgent().compute_signal(df)
    assert out.tolist() == [0.4, -0.2, 0.0]


def test_edge_tilts_beneficiary_up_and_victim_down():
    emap = {"E": {"AAA": 1.0, "BBB": -1.0}}
    events = [{"event": "E", "prob": 0.6, "premium": 0.2}]  # edge = +0.4
    sig = build_geo_signal(["AAA", "BBB", "CCC"], events, emap)
    assert sig["AAA"] == approx(0.4)   # beneficiary tilted long
    assert sig["BBB"] == approx(-0.4)  # victim tilted away
    assert sig["CCC"] == 0.0     # unexposed


def test_zero_edge_when_odds_equal_premium():
    emap = {"E": {"AAA": 1.0}}
    events = [{"event": "E", "prob": 0.3, "premium": 0.3}]  # edge = 0 -> no tilt
    sig = build_geo_signal(["AAA", "BBB"], events, emap)
    assert (sig == 0.0).all()


def test_no_events_is_neutral():
    sig = build_geo_signal(["AAA", "BBB"], [], {"E": {"AAA": 1.0}})
    assert (sig == 0.0).all()


def test_attach_broadcasts_across_dates():
    idx = pd.MultiIndex.from_product(
        [pd.to_datetime(["2026-01-01", "2026-01-08"]), ["AAA", "BBB"]],
        names=["date", "symbol"],
    )
    df = pd.DataFrame({"close": [1, 2, 3, 4]}, index=idx)
    emap = {"E": {"AAA": 1.0}}
    out = attach_geo_signal(df, [{"event": "E", "prob": 0.5, "premium": 0.1}], emap)  # edge 0.4
    assert "geo_signal" in out.columns
    aaa = out.xs("AAA", level="symbol")["geo_signal"]
    bbb = out.xs("BBB", level="symbol")["geo_signal"]
    assert aaa.round(6).eq(0.4).all()
    assert (bbb == 0.0).all()


def test_sleeve_registered_in_factory():
    names = {a.name for a in build_v1_agents()}
    assert "geopolitical" in names
