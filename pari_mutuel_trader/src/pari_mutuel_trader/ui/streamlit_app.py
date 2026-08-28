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

    st.subheader("Equity Curve, Before and After Tax")
    eq = pd.Series(state.get("equity_curve", {}), dtype=float)
    at = pd.Series(state.get("after_tax_curve", {}), dtype=float)
    if not eq.empty:
        curves = pd.DataFrame({"pre-tax": eq})
        if not at.empty:
            curves["after tax"] = at
        curves.index = pd.to_datetime(curves.index)
        st.line_chart(curves)
        metrics = state.get("metrics", {})
        c_a, c_b, c_c = st.columns(3)
        c_a.metric("CAGR", f"{metrics.get('CAGR', 0):.2%}")
        c_b.metric("CAGR after tax", f"{metrics.get('CAGR_after_tax', 0):.2%}",
                   f"{-metrics.get('tax_drag_annual', 0):.2%}")
        c_c.metric("Short-term share of tax", f"{metrics.get('short_term_share_of_tax', 0):.0%}")

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

    review = state.get("position_review", {})
    if review:
        st.header("Position Review (IV15 / IV8, after tax)")
        st.json(review.get("summary", {}))

        decisions = pd.DataFrame(review.get("decisions", []))
        if not decisions.empty:
            decisions["notes"] = decisions["notes"].apply(lambda n: " | ".join(n))
            display = decisions[[
                "symbol", "action", "zone", "price", "iv15", "iv8", "implied_return",
                "current_weight", "target_weight", "shares_to_sell", "after_tax_price",
                "required_replacement_return", "add_level", "house_money", "notes",
            ]]
            st.dataframe(display, use_container_width=True)

            st.subheader("Prospective Return vs Hurdle")
            chart = decisions.set_index("symbol")[["implied_return", "required_replacement_return"]]
            st.bar_chart(chart)

        plan = review.get("redeploy_plan", {})
        if plan:
            st.subheader("Redeploy Plan")
            c3, c4, c5 = st.columns(3)
            c3.metric("Harvested after tax", f"{plan.get('harvested_after_tax', 0):,.0f}")
            c4.metric("Tax paid", f"{plan.get('tax_paid', 0):,.0f}")
            c5.metric("Unallocated", f"{plan.get('undeployed', 0):,.0f}")
            st.dataframe(pd.DataFrame(plan.get("allocations", [])))

    st.subheader("Config Used")
    st.json(state.get("config", {}))


if __name__ == "__main__":
    main()
