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
from .model import StepKind
from .politeness import Policy
from .preflight import load_preflight
from .selectors import SpecStatus, assert_verified_before_sweep, load_specs
from .targets import load_targets

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = ROOT / "config" / "collection_policy.yaml"
DEFAULT_TARGETS = ROOT / "config" / "targets" / "ticketing.yaml"
DEFAULT_SELECTORS = ROOT / "config" / "selectors" / "ticketing.yaml"

DEFAULT_FLOW = [
    StepKind.LISTING,
    StepKind.DETAIL,
    StepKind.SELECT,
    StepKind.CHECKOUT,
    StepKind.REVIEW,
]


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
    # A sweep over an unverified spec produces noise rather than findings: a
    # selector that matches nothing reads as an absent fee, which reads as
    # compliance. Checked before the environment question, because it is the one
    # that silently corrupts results rather than loudly failing.
    specs = load_specs(args.selectors)
    tier_a = [t.id for t in load_targets(args.targets).sweep_order() if t.tier == "A"]
    pending = assert_verified_before_sweep(specs, tier_a)
    if pending and not args.allow_unverified_selectors:
        print(f"Refusing to sweep: {len(pending)}/{len(tier_a)} Tier A specs unverified.")
        print("  " + ", ".join(pending))
        print("Run `selector-status`, then author and `verify-selectors` each one.")
        return 1

    # Live capture needs a browser context and geolocated egress; neither belongs
    # in an ephemeral build container.
    print(
        "Live sweep must run in the collection environment: it needs Playwright "
        "and the geolocated egress provider. See DRIP_FEE_COLLECTOR_PLAN.md Phase 1."
    )
    return 2


def cmd_selector_status(args: argparse.Namespace) -> int:
    specs = load_specs(args.selectors)
    targets = load_targets(args.targets)
    tier_a = [t.id for t in targets.sweep_order() if t.tier == "A"]

    for target_id in tier_a:
        spec = specs.get(target_id)
        status = spec.status.value if spec else "missing"
        problems = spec.structural_problems(DEFAULT_FLOW) if spec else ["no spec"]
        note = "" if not problems else f"  <- {problems[0]}"
        print(f"{target_id:16} {status:12}{note}")

    pending = assert_verified_before_sweep(specs, tier_a)
    verified = len(tier_a) - len(pending)
    print(f"\n{verified}/{len(tier_a)} Tier A specs verified.")
    if pending:
        print(
            "A sweep over an unverified spec produces noise, not findings: a "
            "selector that matches nothing reads as an absent fee, which reads as "
            "compliance. Author these before the first sweep."
        )
    return 0 if not pending else 1


def cmd_verify_selectors(args: argparse.Namespace) -> int:
    from .authoring import load_saved_pages, verify_spec

    specs = load_specs(args.selectors)
    spec = specs.get(args.target)
    if spec is None:
        print(f"No spec for {args.target!r}.")
        return 2

    pages = load_saved_pages(args.pages)
    if not pages:
        print(
            f"No saved pages in {args.pages}. Save them first with `save-page`; "
            "authoring against saved copies keeps the tuning loop off the live site."
        )
        return 2

    report = verify_spec(spec, pages, quantity=args.quantity)
    print(report.summary())
    if report.may_be_marked_verified:
        print(f"\nOK to set status: verified for {args.target}.")
        return 0
    return 1


def cmd_save_page(args: argparse.Namespace) -> int:
    from .authoring import save_page

    path = save_page(args.url, args.out, Policy.load(args.policy))
    print(f"Saved {args.url} -> {path}")
    return 0


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
    sweep.add_argument("--allow-unverified-selectors", action="store_true")
    sweep.add_argument("--selectors", default=str(DEFAULT_SELECTORS))
    sweep.set_defaults(func=cmd_sweep)

    status = sub.add_parser("selector-status", help="which Tier A specs are authored")
    status.add_argument("--selectors", default=str(DEFAULT_SELECTORS))
    status.set_defaults(func=cmd_selector_status)

    verify = sub.add_parser("verify-selectors", help="check a spec against saved pages")
    verify.add_argument("--target", required=True)
    verify.add_argument("--pages", required=True, help="directory of saved step pages")
    verify.add_argument("--selectors", default=str(DEFAULT_SELECTORS))
    verify.add_argument("--quantity", type=int, default=1)
    verify.set_defaults(func=cmd_verify_selectors)

    save = sub.add_parser("save-page", help="save one rendered page for authoring")
    save.add_argument("--url", required=True)
    save.add_argument("--out", required=True)
    save.set_defaults(func=cmd_save_page)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
