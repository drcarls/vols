from __future__ import annotations

import argparse
import sys

from .config import brightdata_token, fixtures_dir
from .collectors.serp import BrightDataSerpBackend, FixtureBackend
from .collectors.serp.base import SerpBackend
from .models import Company
from .pipeline import analyze, load_candidates, run, write_csv, write_findings_csv
from .scoring import brief


def _select_backend(args) -> SerpBackend:
    """Choose the SERP search backend.

    Live Bright Data SERP if a token is present and --offline wasn't set;
    otherwise the offline fixture backend (no token, no network).
    """
    token = brightdata_token()
    if token and not args.offline:
        print("SERP backend: Bright Data SERP API (live)", file=sys.stderr)
        return BrightDataSerpBackend(token, zone=args.serp_zone)
    reason = "offline flag" if args.offline else "no BRIGHTDATA_API_TOKEN"
    print(f"SERP backend: fixtures ({reason})", file=sys.stderr)
    return FixtureBackend(fixtures_dir() / "serp")


def cmd_scan(args):
    """Analyze a single company from command-line flags."""
    company = Company(
        name=args.name,
        domain=args.domain,
        naics_code=args.naics,
        employees=args.employees,
        revenue_usd=args.revenue_usd,
        state=args.state,
    )
    backend = _select_backend(args)
    report = analyze(company, backend, check_web=not args.no_web)
    print(brief(report))


def cmd_discover(args):
    """Analyze and rank a CSV of candidate companies."""
    companies = load_candidates(args.input)
    print(f"Loaded {len(companies)} candidate companies", file=sys.stderr)
    backend = _select_backend(args)
    reports = run(companies, backend, check_web=not args.no_web)

    if args.out:
        write_csv(reports, args.out)
        print(f"Ranked results written to {args.out}", file=sys.stderr)
    if args.findings_out:
        write_findings_csv(reports, args.findings_out)
        print(f"Per-finding rows written to {args.findings_out}", file=sys.stderr)

    top = reports[: args.top] if args.top else reports
    print(f"\nTop {len(top)} prospects\n" + "=" * 44)
    for r in top:
        print(brief(r))
        print()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="questa", description="Questa AI pre-sales prospecting")
    p.add_argument("--offline", action="store_true", help="force fixture backend (no network)")
    p.add_argument("--serp-zone", default="serp", help="Bright Data SERP zone name")
    p.add_argument("--no-web", action="store_true", help="skip the homepage AI/chatbot check")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("scan", help="analyze one company")
    s.add_argument("--name", required=True)
    s.add_argument("--domain")
    s.add_argument("--naics")
    s.add_argument("--employees", type=int)
    s.add_argument("--revenue-usd", dest="revenue_usd", type=float)
    s.add_argument("--state")
    s.set_defaults(func=cmd_scan)

    d = sub.add_parser("discover", help="rank a CSV of candidate companies")
    d.add_argument("--input", required=True, help="candidates CSV (see fixtures/candidates.sample.csv)")
    d.add_argument("--out", help="write ranked prospect rows to this CSV")
    d.add_argument("--findings-out", dest="findings_out", help="write per-finding rows to this CSV")
    d.add_argument("--top", type=int, default=0, help="print only the top N (0 = all)")
    d.set_defaults(func=cmd_discover)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
