import types

from pari_mutuel_trader import cli
from pari_mutuel_trader.data import kalshi


def test_discover_maps_known_theme(monkeypatch, capsys):
    monkeypatch.setattr(kalshi, "list_events", lambda **k: [
        {"event_ticker": "KXFED-26", "title": "Will the Fed cut rates in March?", "category": "Economics"},
        {"event_ticker": "KXSB-26", "title": "Who wins the Super Bowl?", "category": "Sports"},
        {"event_ticker": "KXHOR-26", "title": "Iran closes the Strait of Hormuz", "category": "World"},
    ])
    args = types.SimpleNamespace(category=None, max=1200, limit=40)
    cli.cmd_discover(args)
    out = capsys.readouterr().out
    assert "mapped to a tradeable instrument: 2" in out
    assert "no instrument (skip): 1" in out
    assert "FED_CUT" in out and "IRAN_HORMUZ" in out
    assert "KXSB-26" not in out  # sports event has no instrument, is skipped


def test_discover_handles_empty_feed(monkeypatch, capsys):
    monkeypatch.setattr(kalshi, "list_events", lambda **k: [])
    args = types.SimpleNamespace(category="Economics", max=1200, limit=40)
    cli.cmd_discover(args)
    out = capsys.readouterr().out
    assert "no Kalshi events returned" in out
