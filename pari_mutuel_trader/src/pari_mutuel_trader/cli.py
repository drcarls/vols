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
    from pari_mutuel_trader.data.loaders import load_features, generate_sample_fundamentals
    from pari_mutuel_trader.data.features import build_features
    from pari_mutuel_trader.valuation.features import attach_valuation, load_fundamentals
    from pari_mutuel_trader.valuation.sell_rules import SellPolicy

    print_python_banner()
    cfg = load_yaml(args.config)
    data_cfg = cfg["data"]
    raw = load_features(data_cfg["features_path"])
    feat = build_features(raw)

    fundamentals_path = data_cfg.get("fundamentals_path")
    policy = SellPolicy.from_config(cfg.get("valuation"))
    if fundamentals_path and Path(fundamentals_path).exists():
        fundamentals = load_fundamentals(fundamentals_path)
        covered = set(feat.index.get_level_values("symbol")) & set(fundamentals)
        if covered:
            feat = attach_valuation(feat, fundamentals, policy)
            print(f"valuation attached for {len(covered)} symbols from {fundamentals_path}")
        else:
            feat = attach_valuation(feat, generate_sample_fundamentals(feat), policy)
            print(f"{fundamentals_path} covers none of this universe; using sample fundamentals")
    elif fundamentals_path:
        feat = attach_valuation(feat, generate_sample_fundamentals(feat), policy)
        print("no fundamentals file; using sample fundamentals")

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


def cmd_review_positions(args):
    import json
    from datetime import datetime

    from pari_mutuel_trader.valuation.book import run_review

    print_python_banner()
    as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date() if args.as_of else None
    payload = run_review(args.positions, as_of=as_of)

    if args.json:
        print(json.dumps(payload, indent=2))
        return

    summary = payload["summary"]
    print(f"\nBook review as of {summary['as_of']}")
    print(f"  market value          {summary['book_market_value']:,.0f}")
    print(f"  weighted implied ret  {summary['weighted_implied_return']:.1%}")
    print(f"  actions               {summary['actions']}")

    header = "{:<8}{:<22}{:<15}{:>10}{:>10}{:>9}{:>9}{:>9}{:>11}"
    row = "{:<8}{:<22}{:<15}{:>10.2f}{:>10.2f}{:>9.1%}{:>9.1%}{:>9.1%}{:>11.2f}"
    print()
    print(header.format("symbol", "action", "zone", "IV15", "IV8", "implied", "weight", "target", "after-tax"))
    for d in payload["decisions"]:
        print(row.format(
            d["symbol"], d["action"], d["zone"], d["iv15"], d["iv8"], d["implied_return"],
            d["current_weight"], d["target_weight"], d["after_tax_price"]))

    print("\nDetail")
    for d in payload["decisions"]:
        if d["shares_to_sell"]:
            print(f"  {d['symbol']}: sell {d['shares_to_sell']:,.0f} sh -> "
                  f"{d['gross_proceeds']:,.0f} gross, {d['tax']:,.0f} tax, "
                  f"{d['after_tax_proceeds']:,.0f} net "
                  f"(replacement must earn {d['required_replacement_return']:.1%})")
        else:
            print(f"  {d['symbol']}: no trade; add level {d['add_level']:.2f}, trim level {d['trim_level']:.2f}")
        for note in d["notes"]:
            print(f"      - {note}")

    plan = payload["redeploy_plan"]
    print(f"\nRedeploy plan: {plan['harvested_after_tax']:,.0f} harvested after "
          f"{plan['tax_paid']:,.0f} of tax")
    for alloc in plan["allocations"]:
        print(f"  {alloc['symbol']}: {alloc['amount']:,.0f} ({alloc['weight']:.1%}) "
              f"priced for {alloc['implied_return']:.1%}")
    if plan["undeployed"] > 0:
        print(f"  unallocated: {plan['undeployed']:,.0f} - nothing else clears the hurdle")


def cmd_review_account(args):
    import json
    from datetime import datetime

    from pari_mutuel_trader.account import run_account_review

    print_python_banner()
    as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date() if args.as_of else None
    payload = run_account_review(args.account, as_of=as_of)

    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print(f"\nAccount review as of {payload['as_of']}")
    total = payload["allocation_total"]
    print(f"  allocation total {total:.0%}" + ("" if abs(total - 1.0) < 1e-9 else "  <- does not sum to 100%"))

    print("\nSleeves")
    for sleeve in payload["sleeves"]:
        wrapper = "" if sleeve["tax_status"] == "taxable" else f"  [{sleeve['tax_status']}]"
        print(f"  {sleeve['name']:<20}{sleeve['kind']:<16}{sleeve['allocation']:>6.0%}  "
              f"{sleeve['holdings']:>3d} holdings{wrapper}")
        for d in sleeve.get("decisions", []):
            if d["action"] != "hold":
                print(f"      {d['symbol']:<8}{d['action']:<22}{d['zone']:<15}"
                      f"{d['current_weight']:>7.1%} -> {d['target_weight']:.1%}")
        if sleeve.get("note"):
            print(f"      ({sleeve['note']})")

    print("\nBest opportunities across the account")
    for c in payload["opportunity_set"]:
        print(f"  {c['symbol']:<8}priced for {c['implied_return']:.1%}")

    breaches = payload["look_through_breaches"]
    print(f"\nLook-through breaches ({len(breaches)})")
    for b in breaches:
        contributors = ", ".join(f"{k} {v:.1%}" for k, v in sorted(b["sleeves"].items()))
        print(f"  {b['symbol']:<8}{b['account_weight']:>7.2%} against a {b['limit']:.2%} ceiling "
              f"(+{b['excess']:.2%})  [{contributors}]")

    conflicts = payload["wash_sale_conflicts"]
    print(f"\nCross-sleeve wash sales ({len(conflicts)})")
    for c in conflicts:
        tail = (f"loss permanently lost - washed into {', '.join(c['retirement_sleeves'])}, "
                "where no basis adjustment is available"
                if c["severity"] == "permanent"
                else f"loss deferred into the replacement lot's basis, within {c['window_days']} days")
        print(f"  {c['symbol']:<8}sold at a loss by {', '.join(c['sold_at_loss_by'])}; "
              f"held or bought by {', '.join(c['held_or_bought_by'])}")
        print(f"          {tail}")
    if not breaches and not conflicts:
        print("  nothing flagged")


def cmd_evaluate(args):
    import copy

    from pari_mutuel_trader.backtest.evaluate import compare, evaluate_variants

    print_python_banner()
    base = load_yaml(args.config)

    def variant(**sections):
        c = copy.deepcopy(base)
        for section, values in sections.items():
            c[section] = {**c.get(section, {}), **values}
        return c

    plain = ["momentum", "low_vol", "house"]
    variants = {
        "baseline": variant(learning={"agents": plain},
                            portfolio={"min_durability": 0.0},
                            valuation={"enabled": False}),
        "quality gate": variant(learning={"agents": plain}, valuation={"enabled": False}),
        "valuation agent": variant(learning={"agents": ["valuation", "low_vol", "house"]},
                                   portfolio={"min_durability": 0.0},
                                   valuation={"enabled": False}),
        "dislocation agent": variant(learning={"agents": ["dislocated_quality", "low_vol", "house"]},
                                     portfolio={"min_durability": 0.0},
                                     valuation={"enabled": False}),
        "full sleeve": variant(),
    }

    seeds = list(range(args.seeds))
    print(f"\n{len(variants)} variants x {len(seeds)} seeds, reversion={args.reversion}")
    print("(reversion 0 is a random walk: nothing should help, and a variant that "
          "does is a bug or an overfit)")
    frame = evaluate_variants(variants, seeds, reversion=args.reversion,
                              days=args.days, n_symbols=args.symbols)
    result = compare(frame, "baseline", args.metric)
    print()
    print(result.to_string(float_format=lambda v: f"{v:+.4f}"))
    if args.csv:
        frame.to_csv(args.csv, index=False)
        print(f"\nper-seed results: {args.csv}")


def cmd_doctor(_args):
    print_python_banner()
    print(f"Python version: {platform.python_version()}")
    for pkg in ["numpy", "pandas", "pyyaml", "fastapi", "streamlit"]:
        try:
            print(f"{pkg}: {metadata.version(pkg)}")
        except Exception:
            print(f"{pkg}: not installed")

    for path in ["configs/default.yaml", "configs/wfo.yaml", "configs/positions.example.yaml",
                 "configs/account.example.yaml", "configs/dislocated_quality.yaml",
                 "configs/fundamentals.example.yaml", "data/raw", "data/processed", "data/state"]:
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

    rv = sp.add_parser("review-positions")
    rv.add_argument("--positions", default="configs/positions.example.yaml")
    rv.add_argument("--as-of", dest="as_of", default=None, help="YYYY-MM-DD; defaults to today")
    rv.add_argument("--json", action="store_true")
    rv.set_defaults(fn=cmd_review_positions)

    ra = sp.add_parser("review-account")
    ra.add_argument("--account", default="configs/account.example.yaml")
    ra.add_argument("--as-of", dest="as_of", default=None, help="YYYY-MM-DD; defaults to the account file")
    ra.add_argument("--json", action="store_true")
    ra.set_defaults(fn=cmd_review_account)

    ev = sp.add_parser("evaluate")
    ev.add_argument("--config", default="configs/dislocated_quality.yaml")
    ev.add_argument("--seeds", type=int, default=12)
    ev.add_argument("--reversion", type=float, default=0.0,
                    help="daily pull of price toward value; 0 is the null world")
    ev.add_argument("--days", type=int, default=800)
    ev.add_argument("--symbols", type=int, default=80)
    ev.add_argument("--metric", default="CAGR")
    ev.add_argument("--csv", default=None)
    ev.set_defaults(fn=cmd_evaluate)

    d = sp.add_parser("doctor")
    d.set_defaults(fn=cmd_doctor)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
