"""Command line entry point: collect | analyze | report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import analyze as A
from .collect import collect_all
from .markets import RETAILERS, SC_MARKETS
from .report import render_report


def _load(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        sys.exit(f"No observations at {path}. Run `collect` first.")
    return json.loads(p.read_text())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="milk-pricing",
                                 description="Walmart SC milk price analysis")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="pull Instacart milk data via Bright Data")
    c.add_argument("--retailers", nargs="*", default=None)
    c.add_argument("--zips", nargs="*", default=None)
    c.add_argument("--keyword", default="milk")
    c.add_argument("--out", default="data")
    c.add_argument("--sleep", type=float, default=1.0)

    a = sub.add_parser("analyze", help="run the pricing analysis")
    a.add_argument("--input", default="data/observations.json")
    a.add_argument("--fat", default="whole",
                   choices=["whole", "2%", "1%", "skim"])
    a.add_argument("--json", action="store_true", help="emit raw JSON")

    r = sub.add_parser("report", help="write the markdown briefing")
    r.add_argument("--input", default="data/observations.json")
    r.add_argument("--out", default="reports/sc_milk_pricing.md")
    r.add_argument("--fat", default="whole")

    sub.add_parser("markets", help="show the SC coverage universe")

    args = ap.parse_args(argv)

    if args.cmd == "markets":
        print(f"{len(SC_MARKETS)} markets, "
              f"{sum(len(m.zips) for m in SC_MARKETS)} ZIPs, "
              f"{len(RETAILERS)} retailers")
        for m in SC_MARKETS:
            print(f"  {m.name:<14} {m.region:<16} {', '.join(m.zips)}")
        print("\nRetailers:")
        for x in RETAILERS:
            print(f"  {x.name:<14} {x.channel:<14} {x.slug}")
        return 0

    if args.cmd == "collect":
        collect_all(args.retailers, args.zips, args.keyword,
                    out_dir=args.out, sleep=args.sleep)
        return 0

    obs = _load(args.input)

    if args.cmd == "analyze":
        out = {
            "coverage": A.coverage_report(obs),
            "markets": A.market_table(obs, fat=args.fat),
            "walmart_dispersion": A.walmart_zone_dispersion(obs, fat=args.fat),
            "recommendations": A.recommendations(obs, fat=args.fat),
        }
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(render_report(obs, fat=args.fat))
        return 0

    if args.cmd == "report":
        text = render_report(obs, fat=args.fat)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text)
        print(f"wrote {args.out}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
