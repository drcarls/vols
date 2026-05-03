from __future__ import annotations

import pandas as pd
import streamlit as st
from pari_mutuel_trader.paper.state import load_state

STATE_PATH = "data/state/dashboard_state.json"


def main():
    st.set_page_config(page_title="pari_mutuel_trader", layout="wide")
    st.title("Pari-Mutuel Trader V1")
    state = load_state(STATE_PATH)

    st.subheader("Summary Metrics")
    st.json(state.get("metrics", {}))

    st.subheader("Equity Curve")
    eq = pd.Series(state.get("equity_curve", {}), dtype=float)
    if not eq.empty:
        eq.index = pd.to_datetime(eq.index)
        st.line_chart(eq)

    st.subheader("Drawdown")
    dd = pd.Series(state.get("drawdown_curve", {}), dtype=float)
    if not dd.empty:
        dd.index = pd.to_datetime(dd.index)
        st.area_chart(dd)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Current Holdings")
        hist = state.get("holdings_history", {})
        latest = sorted(hist.keys())[-1] if hist else None
        st.dataframe(pd.DataFrame(list(hist.get(latest, {}).items()), columns=["symbol", "weight"]))
    with c2:
        st.subheader("Agent Weights Over Time")
        wh = state.get("agent_weights_history", {})
        if wh:
            df = pd.DataFrame(wh).T
            st.line_chart(df)

    st.subheader("Attribution")
    st.json(state.get("attribution", {}))

    st.subheader("Recent Rebalance Trades")
    st.dataframe(pd.DataFrame(state.get("rebalance_trades", [])))

    st.subheader("Config Used")
    st.json(state.get("config", {}))


if __name__ == "__main__":
    main()
