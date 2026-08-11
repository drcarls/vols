"""Fetch a real daily price panel from Yahoo for the sleeve's exposed universe + liquid peers.

Writes data/processed/features_real.parquet with (date, symbol) MultiIndex and ret_1d/close/volume/
adv_usd — the raw columns build_features() expands. Stdlib urllib only. Best-effort per symbol; a
symbol that fails or has no history is skipped (logged), so a short-history name (COIN, ZIM, MP) just
starts later and the engine zero-fills its early rows.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

# Exposed names across DEFAULT_EXPOSURE_MAP + enough liquid peers to fill top_k.
UNIVERSE = [
    # energy / tankers / airlines (Iran, Red Sea, Venezuela, CPI)
    "XOM", "CVX", "COP", "OXY", "EOG", "SLB", "FRO", "STNG", "INSW", "DHT",
    "DAL", "LUV", "UAL", "VLO", "XLE",
    # shipping
    "ZIM", "MATX", "FDX",
    # semis (Taiwan)
    "NVDA", "AMD", "AVGO", "TSM", "ASML", "QCOM", "MU",
    # rare earth / materials
    "MP", "ALB", "UEC", "FCX", "X", "NUE",
    # defense (rearm)
    "LMT", "RTX", "NOC", "GD", "LHX", "HII",
    # rates / macro ETFs + banks
    "KRE", "JPM", "TLT", "GLD", "XLU", "XLP", "XLY", "XLI", "HYG", "ARKK",
    # policy-exposed (tariffs, drug pricing)
    "GM", "NKE", "FXI", "EWW", "PFE", "MRK", "LLY", "CVS", "UNH", "NVO",
    # insurance (hurricane) + crypto
    "ALL", "TRV", "RNR", "COIN", "MSTR", "MARA",
    # broad anchors
    "AAPL", "MSFT", "SPY",
]


def fetch(sym: str, p1: int, p2: int, timeout: float = 15.0):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?period1={p1}&period2={p2}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    res = data["chart"]["result"][0]
    ts = res["timestamp"]
    q = res["indicators"]["quote"][0]
    df = pd.DataFrame({
        "date": pd.to_datetime(ts, unit="s").normalize(),
        "symbol": sym,
        "close": q["close"],
        "volume": q["volume"],
    }).dropna(subset=["close"])
    return df


def main():
    p1, p2 = 1514764800, 1786000000  # 2018-01-01 .. ~2026-08
    frames, skipped = [], []
    for i, s in enumerate(UNIVERSE):
        try:
            df = fetch(s, p1, p2)
            if len(df) < 200:
                skipped.append((s, f"only {len(df)} rows"))
                continue
            frames.append(df)
            print(f"[{i+1}/{len(UNIVERSE)}] {s}: {len(df)} rows")
        except Exception as e:
            skipped.append((s, str(e)[:60]))
            print(f"[{i+1}/{len(UNIVERSE)}] {s}: FAIL {e}")
        time.sleep(0.15)
    if not frames:
        print("no data fetched"); sys.exit(1)
    panel = pd.concat(frames, ignore_index=True).sort_values(["symbol", "date"])
    panel["ret_1d"] = panel.groupby("symbol")["close"].pct_change().fillna(0.0)
    panel["adv_usd"] = panel["close"] * panel["volume"].fillna(0.0)
    panel = panel.set_index(["date", "symbol"]).sort_index()
    out = Path("data/processed/features_real.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(out)
    print(f"\nsaved {out}: {len(panel)} rows, {panel.index.get_level_values('symbol').nunique()} symbols, "
          f"{panel.index.get_level_values('date').min().date()}..{panel.index.get_level_values('date').max().date()}")
    if skipped:
        print("skipped:", skipped)


if __name__ == "__main__":
    main()
