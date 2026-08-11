"""Lightweight odds snapshot -> append to the dated panel. Cheap always-on cron target.

Resolves each configured event's live Kalshi ``prob`` + instrument ``premium`` (and runs the
resolution trigger), then appends one row per event to ``data.odds_log_path`` — WITHOUT the full
feature build, so it is cheap to run daily/weekly. Over time this accumulates the genuine dated
``(prob, premium)`` panel needed to backtest the resolution trigger honestly.

Run:  cd pari_mutuel_trader && PYTHONPATH=src python3 scripts/log_odds.py
Cron: schedule this weekly; it is idempotent per (date, event).
"""
from __future__ import annotations

from datetime import date

from pari_mutuel_trader.config import load_yaml
from pari_mutuel_trader.data.geopolitical import resolve_events
from pari_mutuel_trader.data.odds_log import append_odds_snapshot


def main(config: str = "configs/default.yaml") -> None:
    cfg = load_yaml(config)["data"]
    geo_path = cfg.get("geopolitical_path")
    odds_path = cfg.get("odds_log_path")
    if not geo_path or not odds_path:
        print("no geopolitical_path / odds_log_path configured; nothing to log")
        return
    today = date.today().isoformat()
    events = resolve_events(
        geo_path,
        resolution_state_path=cfg.get("resolution_state_path"),
        today=today if cfg.get("resolution_state_path") else None,
    )
    n = append_odds_snapshot(events, odds_path, today)
    states = ", ".join(f"{e['event']}={e.get('resolution_state', 'static')}"
                       for e in events) or "(none)"
    print(f"{today}: logged {n} rows to {odds_path} | {states}")


if __name__ == "__main__":
    main()
