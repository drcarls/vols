"""Command line entry points for Phase 1.

    python -m lexmeter_fees.cli robots-audit
    python -m lexmeter_fees.cli preflight
    python -m lexmeter_fees.cli sweep --help
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

from .discovery import audit_domain
from .http import UrllibFetcher
from .politeness import Policy
from .preflight import load_preflight
from .targets import load_targets

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = ROOT / "config" / "collection_policy.yaml"
DEFAULT_TARGETS = ROOT / "config" / "targets" / "ticketing.yaml"


def cmd_robots_audit(args: argparse.Namespace) -> int:
    policy = Policy.load(args.policy)
    fetcher = UrllibFetcher(policy)
    targets = load_targets(args.targets)
    results = []

    for i, target in enumerate(targets.sweep_order()):
        if i:
            # Paced even for a single public file per host.
            time.sleep(policy.min_delay)
        audit = audit_domain(target.domain, fetcher)
        results.append({"target": target.id, **asdict(audit)})
        status = (
            f"UNREACHABLE ({audit.error})"
            if not audit.reachable
            else "CONFLICTS with checkout capture"
            if audit.conflicts_with_checkout_capture
            else "no checkout conflict"
        )
        print(f"{target.id:16} {target.domain:26} {status}", file=sys.stderr)

    Path(args.out).write_text(json.dumps(results, indent=2, default=str))
    reached = [r for r in results if r["reachable"]]
    conflicts = sum(
        1 for r in reached
        if r.get("checkout_paths_disallowed") or r.get("disallows_everything")
    )
    unreachable = len(results) - len(reached)

    print(f"\n{len(reached)}/{len(results)} reachable; written to {args.out}", file=sys.stderr)
    if reached:
        print(f"{conflicts}/{len(reached)} disallow checkout paths.", file=sys.stderr)
    if unreachable:
        # A conflict count over an empty sample is not a clean result, and saying
        # "0 conflicts" next to "20 unreachable" invites exactly that misreading.
        print(
            f"{unreachable} unreachable -- their robots.txt was NOT read, so nothing "
            "is known about what they disallow. Re-run from the collection "
            "environment before treating this audit as complete.",
            file=sys.stderr,
        )
    return 0 if reached else 1


def cmd_preflight(args: argparse.Namespace) -> int:
    pre = load_preflight(args.policy)
    if pre.certifiable:
        print("Preflight clear: captures will be certifiable.")
        return 0
    print("Captures would NOT be certifiable. Blockers:\n")
    for blocker in pre.blockers:
        print(f"  - {blocker}")
    print("\nResolve these, or pass --uncertified to collect anyway.")
    return 1


def cmd_sweep(args: argparse.Namespace) -> int:
    pre = load_preflight(args.policy)
    if not pre.certifiable and not args.uncertified:
        print("Refusing to sweep. Run `preflight` to see why, or pass --uncertified.")
        for blocker in pre.blockers:
            print(f"  - {blocker}")
        return 1
    # Live capture needs a browser context, per-target selector specs and
    # geolocated egress; none of that belongs in an ephemeral build container.
    print(
        "Live sweep must run in the collection environment: it needs Playwright, "
        "per-target SelectorSpecs, and the geolocated egress provider. "
        "See DRIP_FEE_COLLECTOR_PLAN.md Phase 1."
    )
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lexmeter-fees")
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--targets", default=str(DEFAULT_TARGETS))
    sub = parser.add_subparsers(dest="command", required=True)

    robots = sub.add_parser("robots-audit", help="fetch and classify robots.txt per target")
    robots.add_argument("--out", default="robots_audit.json")
    robots.set_defaults(func=cmd_robots_audit)

    pre = sub.add_parser("preflight", help="check whether captures would be certifiable")
    pre.set_defaults(func=cmd_preflight)

    sweep = sub.add_parser("sweep", help="run a weekly sweep")
    sweep.add_argument("--uncertified", action="store_true")
    sweep.set_defaults(func=cmd_sweep)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
