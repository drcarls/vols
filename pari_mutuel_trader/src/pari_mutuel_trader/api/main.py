from __future__ import annotations

from fastapi import FastAPI
from pari_mutuel_trader.paper.state import load_state

app = FastAPI(title="pari_mutuel_trader API")
STATE_PATH = "data/state/dashboard_state.json"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/dashboard")
def dashboard():
    return load_state(STATE_PATH)


@app.get("/equity_curve")
def equity_curve():
    return {"equity_curve": load_state(STATE_PATH).get("equity_curve", {})}


@app.get("/holdings")
def holdings():
    st = load_state(STATE_PATH)
    h = st.get("holdings_history", {})
    latest = sorted(h.keys())[-1] if h else None
    return {"date": latest, "holdings": h.get(latest, {}) if latest else {}}


@app.get("/agent_weights")
def agent_weights():
    st = load_state(STATE_PATH)
    w = st.get("agent_weights_history", {})
    latest = sorted(w.keys())[-1] if w else None
    return {"date": latest, "agent_weights": w.get(latest, {}) if latest else {}}


@app.get("/attribution")
def attribution():
    return {"attribution": load_state(STATE_PATH).get("attribution", {})}


@app.get("/position_review")
def position_review():
    return load_state(STATE_PATH).get("position_review", {})


@app.get("/redeploy_plan")
def redeploy_plan():
    return load_state(STATE_PATH).get("position_review", {}).get("redeploy_plan", {})
