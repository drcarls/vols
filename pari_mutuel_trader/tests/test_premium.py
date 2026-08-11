from pari_mutuel_trader.data import premium
from pari_mutuel_trader.data.geopolitical import resolve_events


def test_normalized_premium_midrange():
    assert premium.normalized_premium(60.0, 25.0, 95.0) == (60 - 25) / (95 - 25)


def test_normalized_premium_clips():
    assert premium.normalized_premium(200.0, 25.0, 100.0) == 1.0
    assert premium.normalized_premium(10.0, 25.0, 100.0) == 0.0
    assert premium.normalized_premium(None, 25.0, 100.0) is None


def test_resolve_premiums_from_vol(monkeypatch):
    monkeypatch.setattr(premium, "fetch_vol", lambda *a, **k: 60.0)  # OVX 60 in [25,100] -> 0.4667
    ev = premium.resolve_premiums([{"event": "IRAN_HORMUZ", "prob": 0.5, "premium": 0.2}])
    assert abs(ev[0]["premium"] - (60 - 25) / (100 - 25)) < 1e-9
    assert ev[0]["premium_source"] == "vol:^OVX"


def test_resolve_premiums_keeps_static_when_no_vol(monkeypatch):
    monkeypatch.setattr(premium, "fetch_vol", lambda *a, **k: None)
    ev = premium.resolve_premiums([{"event": "IRAN_HORMUZ", "prob": 0.5, "premium": 0.2}])
    assert ev[0]["premium"] == 0.2  # unchanged


def test_resolve_premiums_static_event_untouched(monkeypatch):
    monkeypatch.setattr(premium, "fetch_vol", lambda *a, **k: 30.0)
    ev = premium.resolve_premiums([{"event": "REARM", "prob": 0.7, "premium": 0.4}])  # no vol source
    assert ev[0]["premium"] == 0.4


def test_resolve_events_wires_both(monkeypatch, tmp_path):
    from pari_mutuel_trader.data import kalshi
    monkeypatch.setattr(kalshi, "fetch_market_prob", lambda *a, **k: 0.6)
    monkeypatch.setattr(premium, "fetch_vol", lambda *a, **k: 62.5)  # -> (62.5-25)/75 = 0.5
    f = tmp_path / "g.yaml"
    f.write_text("events:\n  - event: IRAN_HORMUZ\n    kalshi_ticker: T\n    prob: 0.1\n    premium: 0.9\n")
    ev = resolve_events(str(f))
    assert ev[0]["prob"] == 0.6
    assert abs(ev[0]["premium"] - 0.5) < 1e-9
