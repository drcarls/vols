"""Walk-forward + full-period backtest of the geopolitical/macro sleeve on the REAL universe.

Three configurations, reported side by side:

  A. BASELINE      geo_signal = 0, macro_regime = 0  (geo & macro agents neutral)
  B. STATIC TILT   today's events held constant across 2018-2026 (NO event-timing hindsight;
                   only assumes the exposure DIRECTIONS are structural)
  C. DATED EVENTS  each theme turned on at the dates its episode actually happened
                   (hindsight-placed -> an ILLUSTRATION of the resolution channel, not a forecast)

For each: full-period metrics (Sharpe/CAGR/MaxDD), the geopolitical agent's cumulative attribution
and final hedge weight (did the learner keep it?), and the walk-forward mean OOS score.
"""
from __future__ import annotations

import pandas as pd

from pari_mutuel_trader.config import load_yaml
from pari_mutuel_trader.data.loaders import load_features
from pari_mutuel_trader.data.features import build_features
from pari_mutuel_trader.data.geopolitical import (
    build_geo_signal, build_macro_regime, DEFAULT_EXPOSURE_MAP, MACRO_REGIME_SIGN,
)
from pari_mutuel_trader.backtest.engine import run_backtest
from pari_mutuel_trader.backtest.walk_forward import run_wfo

FEAT = "data/processed/features_real.parquet"

# --- today's live events (the static book), matching configs/geopolitical.example.yaml ---
STATIC_EVENTS = [
    {"event": "IRAN_HORMUZ", "prob": 0.12, "premium": 0.41},  # OVX elevated -> ~0 edge today
    {"event": "RED_SEA", "prob": 0.55, "premium": 0.35},
    {"event": "TAIWAN", "prob": 0.08, "premium": 0.05},
    {"event": "RARE_EARTH", "prob": 0.40, "premium": 0.20},
    {"event": "REARM", "prob": 0.70, "premium": 0.40},
]

# --- dated timeline: (start, end, event, prob, premium). Dates are the real episode windows
# (hindsight-placed) -> Run C is a resolution-channel illustration, NOT out-of-sample. ---
TIMELINE = [
    # Rearmament: durable theme from the 2022 invasion onward.
    ("2022-02-24", "2026-12-31", "REARM", 0.70, 0.40),
    # Energy shock around the invasion (also lifts tankers, hurts airlines).
    ("2022-02-24", "2022-12-31", "IRAN_HORMUZ", 0.35, 0.20),
    # Red Sea / Bab-el-Mandeb reroute.
    ("2023-12-15", "2024-06-30", "RED_SEA", 0.55, 0.30),
    # China rare-earth / critical-mineral export controls escalate.
    ("2023-07-01", "2026-12-31", "RARE_EARTH", 0.40, 0.20),
    # Taiwan: persistent low-grade chip-trim insurance.
    ("2021-01-01", "2026-12-31", "TAIWAN", 0.08, 0.05),
    # Macro regime: 2022-23 hiking cycle (risk-off) then 2024- easing (risk-on).
    ("2022-03-16", "2023-07-26", "FED_HIKE", 0.85, 0.30),
    ("2024-09-18", "2026-12-31", "FED_CUT", 0.60, 0.10),
]


def attach_static(feat: pd.DataFrame) -> pd.DataFrame:
    syms = feat.index.get_level_values("symbol").unique()
    sig = build_geo_signal(syms, STATIC_EVENTS)
    regime = build_macro_regime(STATIC_EVENTS)
    out = feat.copy()
    out["geo_signal"] = out.index.get_level_values("symbol").map(sig).astype(float).fillna(0.0)
    out["macro_regime"] = float(regime)
    return out


def attach_dated(feat: pd.DataFrame) -> pd.DataFrame:
    out = feat.copy()
    dates = out.index.get_level_values("date")
    syms_all = out.index.get_level_values("symbol")
    geo = pd.Series(0.0, index=out.index)
    reg = pd.Series(0.0, index=out.index)
    # Group timeline entries by date-window so we build one event-set per active window.
    for start, end, event, prob, premium in TIMELINE:
        mask = (dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))
        if not mask.any():
            continue
        ev = [{"event": event, "prob": prob, "premium": premium}]
        # name tilt
        sig = build_geo_signal(out.index.get_level_values("symbol").unique(), ev)
        geo.loc[mask] += syms_all[mask].map(sig).astype(float).fillna(0.0).values
        # macro regime (only macro events contribute)
        reg.loc[mask] += build_macro_regime(ev)
    out["geo_signal"] = geo.values
    out["macro_regime"] = reg.clip(-1.0, 1.0).values
    return out


def geo_report(feat: pd.DataFrame, cfg: dict, label: str) -> dict:
    res = run_backtest(feat, cfg)
    m = res.metrics
    geo_attr = res.attribution.get("geopolitical", 0.0)
    macro_attr = res.attribution.get("macro_regime", 0.0)
    # final hedge weight for the geo agent (last rebalance snapshot)
    wh = res.agent_weights_history
    last_w = wh[max(wh)] if wh else {}
    return {
        "run": label,
        "Sharpe": round(m.get("Sharpe", 0.0), 3),
        "CAGR": round(m.get("CAGR", 0.0), 4),
        "MaxDD": round(m.get("MaxDrawdown", 0.0), 3),
        "turnover": round(m.get("turnover", 0.0), 3),
        "geo_attr": round(geo_attr, 4),
        "macro_attr": round(macro_attr, 4),
        "geo_wt": round(last_w.get("geopolitical", float("nan")), 3),
        "macro_wt": round(last_w.get("macro_regime", float("nan")), 3),
        "flag": m.get("risk_flag", "-"),
    }


def main():
    import sys
    base = load_yaml("configs/default.yaml")
    # Benchmark config fix: the default 0.40 turnover cap blocks the cold-start ramp from cash to a
    # full 25-name book (initial turnover ~0.5), so the book never invests. Raise it enough to allow
    # the ramp; ongoing weekly turnover stays well under. Engine logic untouched.
    base["portfolio"]["turnover_cap"] = 0.60
    raw = load_features(FEAT)
    feat = build_features(raw)
    print(f"universe: {feat.index.get_level_values('symbol').nunique()} symbols, "
          f"{feat.index.get_level_values('date').min().date()}..{feat.index.get_level_values('date').max().date()}",
          flush=True)

    import copy
    conv = copy.deepcopy(base)
    conv["learning"]["use_conviction"] = True

    dated = attach_dated(feat)
    runs = [
        ("A_baseline", feat, base),
        ("B_static", attach_static(feat), base),
        ("C_dated", dated, base),
        ("C_dated+conv", dated, conv),   # same signal, conviction lever ON
    ]

    hdr = ["run", "Sharpe", "CAGR", "MaxDD", "turnover", "geo_attr", "macro_attr", "geo_wt", "macro_wt", "flag"]
    print("\n=== Full-period backtest (2018-2026) ===", flush=True)
    print(" | ".join(h.rjust(12) for h in hdr), flush=True)
    variants = {}
    for name, f, cfg in runs:
        variants[name] = f
        r = geo_report(f, cfg, name)
        print(" | ".join(str(r[h]).rjust(12) for h in hdr), flush=True)

    if "--wfo" in sys.argv:
        wfo_cfg = {"train_years": 3, "test_months": 6, "step_months": 6,
                   "top_k_grid": [25], "temperature_grid": [1.0], "hedge_eta_grid": [0.03]}
        print("\n=== Walk-forward (train 3y / test 6m / step 6m) — mean OOS score ===", flush=True)
        for name in ("A_baseline", "B_static", "C_dated"):
            try:
                res = run_wfo(variants[name], base, wfo_cfg)
                segs = res["segments"]
                scored = [s["score"] for s in segs if s["score"] > float("-inf")]
                print(f"{name:12}: mean_oos_score={res['mean_oos_score']:+.3f}  "
                      f"segments={len(segs)}  scored={len(scored)}", flush=True)
            except Exception as e:
                print(f"{name:12}: WFO failed: {e}", flush=True)


if __name__ == "__main__":
    main()
