"""Emit a crisis_lag events YAML with objective COW-MID onset dates.

    cow-mid events --out events.mid.yaml      # download MID, write the event spec
    cow-mid show                              # list the mapped disputes + gaps

Then run either data leg on objective onsets:

    crisis-lag run fred_nber/data/fred_spreads_long.csv --events events.mid.yaml
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .client import download_mid5
from .crises import CRISIS_MAPPINGS, build_events, unmapped
from .parse import load_disputes


def _disputes(args):
    if args.mida and args.midb:
        return load_disputes(args.mida, args.midb)
    mida, midb = download_mid5(args.cache)
    return load_disputes(mida, midb)


def _emit_yaml(events: List[dict]) -> str:
    try:
        import yaml
        return yaml.safe_dump({"events": events}, sort_keys=False, allow_unicode=True)
    except Exception:  # minimal fallback if PyYAML absent
        lines = ["events:"]
        for e in events:
            lines.append(f"  - name: {e['name']}")
            for k, v in e.items():
                if k != "name":
                    lines.append(f"    {k}: {v!r}")
        return "\n".join(lines) + "\n"


def _cmd_events(args: argparse.Namespace) -> int:
    disputes = _disputes(args)
    events = build_events(disputes)
    text = _emit_yaml(events)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {len(events)} events -> {args.out}", file=sys.stderr)
    else:
        print(text)
    gaps = unmapped(disputes)
    if gaps:
        print(f"no objective MID onset for: {', '.join(gaps)}", file=sys.stderr)
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    disputes = _disputes(args)
    for m in CRISIS_MAPPINGS:
        if m.dispnum and m.dispnum in disputes:
            d = disputes[m.dispnum]
            a = "+".join(d.names(d.side_a)); b = "+".join(d.names(d.side_b))
            print(f"{m.name:<16} MID {m.dispnum:<5} onset={d.onset} "
                  f"hostlev={d.hostlev}({d.hostlev_label}) series={m.series} | {a} vs {b}")
        else:
            print(f"{m.name:<16} (no great-power MID) series={m.series}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cow-mid",
        description="COW MID -> objective crisis_lag onset dates + hostility.",
    )
    sub = p.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--cache", default=".", help="dir to cache MID CSVs")
    common.add_argument("--mida", help="path to MIDA 5.0.csv (skip download)")
    common.add_argument("--midb", help="path to MIDB 5.0.csv (skip download)")

    ev = sub.add_parser("events", parents=[common], help="emit crisis_lag events YAML")
    ev.add_argument("--out", help="output YAML path (else stdout)")
    ev.set_defaults(func=_cmd_events)

    sh = sub.add_parser("show", parents=[common], help="list mapped disputes")
    sh.set_defaults(func=_cmd_show)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
