import json

from pari_mutuel_trader.data import kalshi
from pari_mutuel_trader.data.geopolitical import resolve_events


def test_implied_prob_from_last_price():
    assert kalshi.implied_prob_from_market({"last_price": 42}) == 0.42


def test_implied_prob_from_bid_ask_mid():
    assert kalshi.implied_prob_from_market({"yes_bid": 30, "yes_ask": 40}) == 0.35


def test_implied_prob_none_when_empty():
    assert kalshi.implied_prob_from_market({}) is None


def test_enrich_prefers_live(monkeypatch):
    monkeypatch.setattr(kalshi, "fetch_market_prob", lambda *a, **k: 0.5)
    ev = kalshi.enrich_events([{"event": "E", "kalshi_ticker": "T", "prob": 0.1}])
    assert ev[0]["prob"] == 0.5
    assert ev[0]["prob_source"] == "kalshi_live"


def test_enrich_falls_back_to_local(monkeypatch, tmp_path):
    monkeypatch.setattr(kalshi, "fetch_market_prob", lambda *a, **k: None)
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"T": 0.33}))
    ev = kalshi.enrich_events([{"event": "E", "kalshi_ticker": "T", "prob": 0.1}], local_path=str(f))
    assert ev[0]["prob"] == 0.33
    assert ev[0]["prob_source"] == "kalshi_local"


def test_enrich_keeps_static_when_no_feed(monkeypatch):
    monkeypatch.setattr(kalshi, "fetch_market_prob", lambda *a, **k: None)
    ev = kalshi.enrich_events([{"event": "E", "kalshi_ticker": "T", "prob": 0.1}])
    assert ev[0]["prob"] == 0.1  # unchanged; no prob_source set


def test_enrich_normalizes_percentage(monkeypatch, tmp_path):
    monkeypatch.setattr(kalshi, "fetch_market_prob", lambda *a, **k: None)
    f = tmp_path / "p.csv"
    f.write_text("ticker,prob\nT,42\n")  # stored as a percentage
    ev = kalshi.enrich_events([{"event": "E", "kalshi_ticker": "T"}], local_path=str(f))
    assert ev[0]["prob"] == 0.42


def test_load_local_probs_csv(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("ticker,prob\nT,0.7\nU,0.2\n")
    d = kalshi.load_local_probs(str(f))
    assert d["T"] == 0.7 and d["U"] == 0.2


def test_resolve_events_static_no_network(tmp_path):
    # event without kalshi_ticker -> resolve does no fetch, keeps static prob
    f = tmp_path / "g.yaml"
    f.write_text("events:\n  - event: REARM\n    prob: 0.7\n    premium: 0.4\n")
    ev = resolve_events(str(f))
    assert ev[0]["prob"] == 0.7


def test_resolve_events_uses_kalshi_when_ticker(monkeypatch, tmp_path):
    monkeypatch.setattr(kalshi, "fetch_market_prob", lambda *a, **k: 0.6)
    f = tmp_path / "g.yaml"
    f.write_text("events:\n  - event: IRAN_HORMUZ\n    kalshi_ticker: T\n    prob: 0.1\n    premium: 0.2\n")
    ev = resolve_events(str(f))
    assert ev[0]["prob"] == 0.6
