from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import brightdata_token, fixtures_dir
from .collectors.ciso import BrightDataSerpBackend, FixtureBackend
from .collectors.ciso.base import CisoBackend
from .collectors import registry
from .models import Company
from .pipeline import analyze, load_candidates, run, write_companies, write_csv
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


def _select_registry_backend(args) -> registry.RegistryBackend:
    """Live Roaring if credentials are present and a CSV export wasn't given;
    a CSV export if --export is set; otherwise the bundled offline fixture."""
    if args.export:
        print(f"Registry backend: CSV export ({args.export})", file=sys.stderr)
        return registry.CsvExportBackend(args.export)
    if not args.offline:
        try:
            backend = registry.RoaringBackend()
            print("Registry backend: Roaring API (live)", file=sys.stderr)
            return backend
        except registry.RegistryAuthError:
            pass
    reason = "offline flag" if args.offline else "no ROARING credentials / --export"
    print(f"Registry backend: fixture sample ({reason})", file=sys.stderr)
    return registry.FixtureBackend()


def cmd_harvest(args):
    """Build the candidate universe from SNI sectors + size — no hand assembly."""
    sectors = [s.strip() for s in args.sectors.split(",") if s.strip()]
    unknown = [s for s in sectors if registry.resolve_sector(s) is None]
    if unknown:
        print(f"warning: unrecognised sector(s) {unknown}; "
              f"known: {', '.join(sorted(registry.SECTOR_SNI))}", file=sys.stderr)
    backend = _select_registry_backend(args)
    companies = registry.discover_universe(
        backend, sectors,
        min_employees=args.min_employees,
        include_likely=not args.strict_size,
        limit=args.limit or None,
    )
    print(f"Harvested {len(companies)} in-scope candidates "
          f"for {', '.join(sectors)}", file=sys.stderr)
    if args.out:
        write_companies(companies, args.out)
        print(f"Candidate universe written to {args.out} "
              f"(feed it to `presales discover --input {args.out}`)", file=sys.stderr)
    for c in companies[: args.show or len(companies)]:
        size = f"{c.employees} staff" if c.employees is not None else "size?"
        print(f"  {c.name}  ·  SNI {c.sni_code}  ·  {size}  ·  {c.domain or 'no domain'}")


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

    h = sub.add_parser("harvest", help="build the candidate universe from SNI sectors + size")
    h.add_argument("--sectors", required=True,
                   help="comma-separated, e.g. 'energy,transport' (aliases resolved)")
    h.add_argument("--min-employees", dest="min_employees", type=int, default=50,
                   help="size floor passed to the registry (default 50)")
    h.add_argument("--export", help="a downloaded registry CSV export (allabolag/Bolagsverket/Roaring)")
    h.add_argument("--out", help="write the candidate universe CSV (feeds `discover`)")
    h.add_argument("--limit", type=int, default=0, help="cap the number of candidates (0 = all)")
    h.add_argument("--show", type=int, default=0, help="print only the first N to stdout (0 = all)")
    h.add_argument("--strict-size", action="store_true",
                   help="drop companies whose size is unknown (keep only confirmed in-scope)")
    h.set_defaults(func=cmd_harvest)

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
