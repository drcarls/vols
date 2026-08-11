import json

from pari_mutuel_trader.data.resolution import apply_resolution_trigger, load_state, save_state
from pari_mutuel_trader.data.geopolitical import build_geo_signal


def _ev(prob, ticker="KX", event="IRAN_HORMUZ", premium=0.1):
    return {"event": event, "kalshi_ticker": ticker, "prob": prob, "premium": premium}


def test_watching_when_odds_below_activation():
    evs, state = apply_resolution_trigger([_ev(0.30)], {}, "2026-01-01", activate_at=0.5)
    assert evs[0]["resolution_state"] == "watching"
    assert evs[0]["resolution_decay"] == 0.0
    assert state == {}  # nothing recorded until it resolves


def test_activates_when_odds_cross():
    evs, state = apply_resolution_trigger([_ev(0.62)], {}, "2026-02-24", activate_at=0.5)
    assert evs[0]["resolution_state"] == "active"
    assert evs[0]["resolution_decay"] == 1.0  # full tilt at the catalyst
    assert state["IRAN_HORMUZ"]["activated_on"] == "2026-02-24"


def test_decays_after_activation():
    state = {"IRAN_HORMUZ": {"activated_on": "2026-02-24", "peak_prob": 0.62}}
    # 8 weeks later, half_life 8 -> decay ~0.5
    evs, _ = apply_resolution_trigger([_ev(0.55)], state, "2026-04-21", half_life_weeks=8.0)
    assert evs[0]["resolution_state"] == "active"
    assert abs(evs[0]["resolution_decay"] - 0.5) < 0.03


def test_deactivates_when_odds_collapse():
    state = {"IRAN_HORMUZ": {"activated_on": "2026-02-24", "peak_prob": 0.62}}
    evs, new_state = apply_resolution_trigger([_ev(0.20)], state, "2026-05-01", deactivate_at=0.35)
    assert evs[0]["resolution_state"] == "watching"
    assert evs[0]["resolution_decay"] == 0.0
    assert "IRAN_HORMUZ" not in new_state  # resolution reversed -> cleared


def test_structural_event_without_ticker_untouched():
    # REARM has no kalshi_ticker -> trigger leaves it alone (behaves as before, decay defaults 1.0)
    evs, _ = apply_resolution_trigger([{"event": "REARM", "prob": 0.7, "premium": 0.4}], {}, "2026-01-01")
    assert "resolution_decay" not in evs[0]


def test_decay_gates_the_geo_signal():
    # resolution_decay flows into build_geo_signal's edge: watching -> zero tilt
    watching = [{"event": "IRAN_HORMUZ", "prob": 0.62, "premium": 0.1, "resolution_decay": 0.0}]
    sig = build_geo_signal(["XOM"], watching)
    assert sig["XOM"] == 0.0
    active = [{"event": "IRAN_HORMUZ", "prob": 0.62, "premium": 0.1, "resolution_decay": 1.0}]
    sig2 = build_geo_signal(["XOM"], active)
    assert sig2["XOM"] > 0.0


def test_state_round_trip(tmp_path):
    p = tmp_path / "res.json"
    save_state(str(p), {"E": {"activated_on": "2026-02-24", "peak_prob": 0.6}})
    assert load_state(str(p))["E"]["peak_prob"] == 0.6
    assert json.loads(p.read_text())["E"]["activated_on"] == "2026-02-24"
