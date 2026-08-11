from __future__ import annotations

import argparse
import os
import platform
import sys
from importlib import metadata
from pathlib import Path

from pari_mutuel_trader.config import load_yaml


def print_python_banner():
    print(f"Python executable: {sys.executable}")


def cmd_build_features(args):
    from pari_mutuel_trader.data.loaders import load_features
    from pari_mutuel_trader.data.features import build_features

    print_python_banner()
    cfg = load_yaml(args.config)
    data_cfg = cfg["data"]
    raw = load_features(data_cfg["features_path"])
    feat = build_features(raw)

    # Geopolitical sleeve: populate geo_signal from live events (Kalshi prob vs instrument premium).
    geo_path = data_cfg.get("geopolitical_path")
    if geo_path and Path(geo_path).exists():
        from pari_mutuel_trader.data.geopolitical import resolve_events, attach_geo_signal
        events = resolve_events(geo_path)  # Kalshi prob (live -> local -> static)
        feat = attach_geo_signal(feat, events)
        psrc = {e.get("prob_source", "static") for e in events}
        qsrc = {e.get("premium_source", "static") for e in events}
        print(f"geo sleeve: attached geo_signal for {len(events)} events (prob: {sorted(psrc)}; premium: {sorted(qsrc)})")

    out = Path(data_cfg["features_path"])
    out.parent.mkdir(parents=True, exist_ok=True)
    feat.to_parquet(out)
    print(f"features saved: {out}")


def cmd_backtest(args):
    from pari_mutuel_trader.data.loaders import load_features
    from pari_mutuel_trader.data.features import build_features
    from pari_mutuel_trader.backtest.engine import run_backtest

    print_python_banner()
    cfg = load_yaml(args.config)
    feat = load_features(cfg["data"]["features_path"])
    if "ret_20d" not in feat.columns:
        feat = build_features(feat)
    result = run_backtest(feat, cfg)
    print(result.metrics)


def cmd_wfo(args):
    from pari_mutuel_trader.data.loaders import load_features
    from pari_mutuel_trader.data.features import build_features
    from pari_mutuel_trader.backtest.walk_forward import run_wfo

    print_python_banner()
    wfoc = load_yaml(args.config)
    base = load_yaml(wfoc["base_config"])
    feat = load_features(base["data"]["features_path"])
    if "ret_20d" not in feat.columns:
        feat = build_features(feat)
    res = run_wfo(feat, base, wfoc["wfo"])
    print(res)


def cmd_paper(args):
    from pari_mutuel_trader.data.loaders import load_features
    from pari_mutuel_trader.data.features import build_features
    from pari_mutuel_trader.paper.runner import run_paper

    print_python_banner()
    cfg = load_yaml(args.config)
    feat = load_features(cfg["data"]["features_path"])
    if "ret_20d" not in feat.columns:
        feat = build_features(feat)
    payload = run_paper(feat, cfg, cfg["data"]["state_path"])
    print({"saved": cfg["data"]["state_path"], "metrics": payload["metrics"]})


def cmd_discover(args):
    """Enumerate what Kalshi is pricing and map each event to a tradeable exposed instrument.

    Prints Kalshi events (optionally filtered by category), tagging those whose title matches a known
    exposure theme with the theme + instruments they map to. The matched rows are ready to paste into
    configs/geopolitical.yaml (event + kalshi_ticker). This is the "more things to price" discovery
    step from docs/mining-kalshi-for-instruments.md.
    """
    from pari_mutuel_trader.data.kalshi import list_events
    from pari_mutuel_trader.data.geopolitical import DEFAULT_EXPOSURE_MAP

    # Keyword -> exposure-map event. First hit wins; keeps discovery honest about what maps.
    KEYWORDS = [
        ("hormuz", "IRAN_HORMUZ"), ("iran", "IRAN_HORMUZ"), ("strait", "IRAN_HORMUZ"),
        ("red sea", "RED_SEA"), ("houthi", "RED_SEA"), ("suez", "RED_SEA"),
        ("taiwan", "TAIWAN"), ("tsmc", "TAIWAN"),
        ("rare earth", "RARE_EARTH"), ("rare-earth", "RARE_EARTH"),
        ("defense", "REARM"), ("nato", "REARM"), ("rearm", "REARM"), ("military spend", "REARM"),
        ("venezuela", "VENEZUELA"), ("guyana", "VENEZUELA"),
        ("fed hike", "FED_HIKE"), ("rate hike", "FED_HIKE"), ("raise rates", "FED_HIKE"),
        ("fed cut", "FED_CUT"), ("rate cut", "FED_CUT"), ("lower rates", "FED_CUT"),
        ("cpi", "CPI_HOT"), ("inflation", "CPI_HOT"),
        ("recession", "RECESSION"), ("gdp", "RECESSION"),
        ("tariff", "TARIFFS"), ("trade war", "TARIFFS"),
        ("drug pric", "DRUG_PRICING"), ("medicare", "DRUG_PRICING"),
        ("fda", "FDA_APPROVAL"), ("approv", "FDA_APPROVAL"),
        ("hurricane", "MAJOR_HURRICANE"), ("storm", "MAJOR_HURRICANE"),
        ("bitcoin", "CRYPTO_RALLY"), ("btc", "CRYPTO_RALLY"), ("ethereum", "CRYPTO_RALLY"),
    ]

    def match(title: str) -> str | None:
        t = (title or "").lower()
        for kw, ev in KEYWORDS:
            if kw in t:
                return ev
        return None

    events = list_events(category=args.category, max_events=args.max)
    if not events:
        print("no Kalshi events returned (no network/keys, or category empty). "
              "The sleeve still runs on static config; discovery just needs the public feed.")
        return

    mapped, unmapped = [], 0
    for e in events:
        ev = match(e.get("title"))
        if ev:
            mapped.append((e, ev))
        else:
            unmapped += 1

    cats = sorted({(e.get("category") or "?") for e in events})
    print(f"Kalshi events: {len(events)} (categories: {', '.join(cats)})")
    print(f"mapped to a tradeable instrument: {len(mapped)}  |  no instrument (skip): {unmapped}\n")
    if not mapped:
        print("none of these titles matched a known exposure theme — "
              "extend DEFAULT_EXPOSURE_MAP / KEYWORDS to price a new one.")
        return
    print(f"{'EVENT_TICKER':<28} {'THEME':<16} INSTRUMENTS")
    print("-" * 78)
    for e, ev in mapped[: args.limit]:
        names = ", ".join(sorted(DEFAULT_EXPOSURE_MAP.get(ev, {}), key=str))
        tick = (e.get("event_ticker") or "?")[:27]
        print(f"{tick:<28} {ev:<16} {names}")
    if len(mapped) > args.limit:
        print(f"\n... {len(mapped) - args.limit} more mapped (raise --limit to see them).")
    print("\nPaste a row into configs/geopolitical.yaml as:")
    print("  - {event: <THEME>, kalshi_ticker: <a market ticker under EVENT_TICKER>, prob: 0.0, premium: 0.0}")
    print("Then `build-features` resolves prob (Kalshi) and premium (vol) automatically.")


def cmd_doctor(_args):
    print_python_banner()
    print(f"Python version: {platform.python_version()}")
    for pkg in ["numpy", "pandas", "pyyaml", "fastapi", "streamlit"]:
        try:
            print(f"{pkg}: {metadata.version(pkg)}")
        except Exception:
            print(f"{pkg}: not installed")

    for path in ["configs/default.yaml", "configs/wfo.yaml", "data/raw", "data/processed", "data/state"]:
        print(f"exists {path}: {Path(path).exists()}")

    print(f"TIINGO_API_KEY present: {bool(os.getenv('TIINGO_API_KEY'))}")
    print(f"FRED_API_KEY present: {bool(os.getenv('FRED_API_KEY'))}")
    print(f"KALSHI_API_KEY present: {bool(os.getenv('KALSHI_API_KEY'))}")
    sample_exists = Path("data/processed/features.parquet").exists() or Path("data/processed/features.csv").exists()
    print(f"sample data exists: {sample_exists}")
    print("next: python -m pari_mutuel_trader.cli backtest --config configs/default.yaml")


def main():
    p = argparse.ArgumentParser("pari_mutuel_trader")
    sp = p.add_subparsers(dest="cmd", required=True)

    b = sp.add_parser("build-features")
    b.add_argument("--config", default="configs/default.yaml")
    b.set_defaults(fn=cmd_build_features)

    bt = sp.add_parser("backtest")
    bt.add_argument("--config", default="configs/default.yaml")
    bt.set_defaults(fn=cmd_backtest)

    wf = sp.add_parser("wfo")
    wf.add_argument("--config", default="configs/wfo.yaml")
    wf.set_defaults(fn=cmd_wfo)

    pr = sp.add_parser("paper-run")
    pr.add_argument("--config", default="configs/default.yaml")
    pr.set_defaults(fn=cmd_paper)

    dc = sp.add_parser("discover", help="enumerate what Kalshi prices and map to tradeable instruments")
    dc.add_argument("--category", default=None, help="filter Kalshi category (e.g. Economics, Politics)")
    dc.add_argument("--max", type=int, default=1200, help="max Kalshi events to scan")
    dc.add_argument("--limit", type=int, default=40, help="max mapped rows to print")
    dc.set_defaults(fn=cmd_discover)

    d = sp.add_parser("doctor")
    d.set_defaults(fn=cmd_doctor)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
