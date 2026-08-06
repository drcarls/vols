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


def _cmd_warrisk(args: argparse.Namespace) -> int:
    import datetime

    from .warrisk import war_risk_series, write_long_csv

    disputes = _disputes(args)
    start = datetime.date(args.start, 1, 1)
    end = datetime.date(args.end, 12, 31)
    pts = war_risk_series(disputes, start, end, step_days=args.step,
                          both_sides=not args.any_side)
    if args.out:
        n = write_long_csv(pts, args.out)
        print(f"wrote {n} rows ({len(pts)} weeks) -> {args.out}", file=sys.stderr)
    lit = [p for p in pts if p.max_hostlev > 0]
    print(f"weeks with active great-power confrontation: {len(lit)}/{len(pts)}",
          file=sys.stderr)
    return 0


def _cmd_capratio(args: argparse.Namespace) -> int:
    from .capability import capability_series, milex_ratio, parse_nmc, write_long_csv
    from .client import download_nmc

    path = args.nmc or download_nmc(args.cache)
    nmc = parse_nmc(path)
    series = capability_series(nmc, args.start, args.end, exclude_italy=args.exclude_italy)
    print(f"year  capratio(A/E)  parity  alliance_share  milex_Ger/UK   [Italy "
          f"{'excluded' if args.exclude_italy else 'included'}]", file=sys.stderr)
    for cy in series:
        mg = milex_ratio(nmc, 255, 200, cy.year)
        print(f"{cy.year}   {cy.capratio:.3f}          {cy.parity:.3f}   "
              f"{cy.alliance_share:.3f}           "
              f"{mg:.3f}" if mg else f"{cy.year}   {cy.capratio:.3f}", file=sys.stderr)
    if args.out:
        n = write_long_csv(nmc, args.out, start=args.start, end=args.end,
                           exclude_italy=args.exclude_italy)
        print(f"wrote {n} rows -> {args.out}", file=sys.stderr)
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

    wr = sub.add_parser("warrisk", parents=[common],
                        help="emit a continuous great-power war-risk series")
    wr.add_argument("--out", help="output tidy long CSV")
    wr.add_argument("--start", type=int, default=1900)
    wr.add_argument("--end", type=int, default=1914)
    wr.add_argument("--step", type=int, default=7, help="grid step in days (default weekly)")
    wr.add_argument("--any-side", action="store_true",
                    help="count any dispute a great power is in (default: great power BOTH sides)")
    wr.set_defaults(func=_cmd_warrisk)

    cr = sub.add_parser("capratio", help="Entente/Alliance capability ratio from NMC")
    cr.add_argument("--nmc", help="path to NMC abridged CSV (else downloaded)")
    cr.add_argument("--cache", default=".", help="dir to cache the NMC CSV")
    cr.add_argument("--out", help="output tidy long CSV")
    cr.add_argument("--start", type=int, default=1900)
    cr.add_argument("--end", type=int, default=1914)
    cr.add_argument("--exclude-italy", action="store_true",
                    help="drop Italy from the Alliance (it stayed neutral in 1914)")
    cr.set_defaults(func=_cmd_capratio)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
