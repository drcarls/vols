from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import brightdata_token, fixtures_dir
from .collectors.ciso import BrightDataSerpBackend, FixtureBackend
from .collectors.ciso.base import CisoBackend
from .models import Company
from .pipeline import analyze, load_candidates, run, write_csv
from .scoring import brief


def _select_backend(args) -> CisoBackend:
    """Choose the CISO search backend.

    Live Bright Data SERP if a token is present and --offline wasn't set;
    otherwise the offline fixture backend (no token, no network).
    """
    token = brightdata_token()
    if token and not args.offline:
        print("CISO backend: Bright Data SERP API (live)", file=sys.stderr)
        return BrightDataSerpBackend(token, zone=args.serp_zone)
    reason = "offline flag" if args.offline else "no BRIGHTDATA_API_TOKEN"
    print(f"CISO backend: fixtures ({reason})", file=sys.stderr)
    return FixtureBackend(fixtures_dir() / "serp")


def cmd_scan(args):
    """Analyze a single company from command-line flags."""
    company = Company(
        name=args.name,
        domain=args.domain,
        org_number=args.org_number,
        sni_code=args.sni,
        employees=args.employees,
        turnover_eur=args.turnover_eur,
    )
    backend = _select_backend(args)
    report = analyze(company, backend, check_email=not args.no_email)
    print(brief(report))


def cmd_discover(args):
    """Analyze and rank a CSV of candidate companies."""
    companies = load_candidates(args.input)
    print(f"Loaded {len(companies)} candidate companies", file=sys.stderr)
    backend = _select_backend(args)
    reports = run(companies, backend, check_email=not args.no_email)

    if args.out:
        write_csv(reports, args.out)
        print(f"Ranked results written to {args.out}", file=sys.stderr)

    top = reports[: args.top] if args.top else reports
    print(f"\nTop {len(top)} prospects\n" + "=" * 40)
    for r in top:
        print(brief(r))
        print()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="presales", description="Cyber Defencely pre-sales prospecting")
    p.add_argument("--offline", action="store_true", help="force fixture backend (no network)")
    p.add_argument("--serp-zone", default="serp", help="Bright Data SERP zone name")
    p.add_argument("--no-email", action="store_true", help="skip DNS email-security check")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("scan", help="analyze one company")
    s.add_argument("--name", required=True)
    s.add_argument("--domain")
    s.add_argument("--org-number", dest="org_number")
    s.add_argument("--sni")
    s.add_argument("--employees", type=int)
    s.add_argument("--turnover-eur", dest="turnover_eur", type=float)
    s.set_defaults(func=cmd_scan)

    d = sub.add_parser("discover", help="rank a CSV of candidate companies")
    d.add_argument("--input", required=True, help="candidates CSV (see fixtures/candidates.sample.csv)")
    d.add_argument("--out", help="write ranked results to this CSV")
    d.add_argument("--top", type=int, default=0, help="print only the top N (0 = all)")
    d.set_defaults(func=cmd_discover)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
