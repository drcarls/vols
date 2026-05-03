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

    d = sp.add_parser("doctor")
    d.set_defaults(fn=cmd_doctor)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
