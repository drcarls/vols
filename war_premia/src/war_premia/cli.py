"""Reproduce the paper's tables and run the July-1914 extension.

    war-premia reproduce                # Tables 3-7 on the mirrored NW short rates
    war-premia july1914                 # feasibility + the one observable bond change
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from neal_weidenmier.load import load_short_rates, to_series_map

from .july1914 import (
    bond_feasibility,
    bond_quote_audit,
    short_rate_feasibility,
)
from .run import format_table, run_crisis
from .warweeks import CRISES

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SHORT = os.path.join(_ROOT, "neal_weidenmier", "data", "stinterestrates.xls")
BONDS = os.path.join(_ROOT, "neal_weidenmier", "data", "longtermbonds.xls")


def _cmd_reproduce(args: argparse.Namespace) -> int:
    smap = to_series_map(load_short_rates(args.short or SHORT))
    for c in CRISES:
        print(format_table(c, run_crisis(smap, c)))
        print()
    return 0


def _cmd_july1914(args: argparse.Namespace) -> int:
    for feas in (short_rate_feasibility(args.short or SHORT), bond_feasibility(args.bonds or BONDS)):
        print(f"[{feas.asset}] estimable={feas.estimable}: {feas.reason}")
    print("\nRaw bond-quote audit across the closure (prices, points of par):")
    print(f"  {'sovereign':<24}{'Jun2':>7}{'Jun3':>7}{'Aug5':>7}{'Sep1':>7}  flags")
    for a in bond_quote_audit(args.bonds or BONDS):
        flags = []
        if a.exdiv_flag:
            flags.append("Jun3=EX-DIV")
        if not a.genuine:
            flags.append("post-closure NOT genuine (" + a.reason.split("—")[0].strip() + ")")
        def f(x):
            return f"{x:.2f}" if x is not None else "—"
        print(f"  {a.sovereign:<24}{f(a.clean_pre):>7}{f(a.exdiv_pre):>7}"
              f"{f(a.post_stale):>7}{f(a.post_sept):>7}  {'; '.join(flags)}")
    print("\nVerdict: the Jun2/Jun3-vs-Aug5/Sep1 cross-section is UNINTERPRETABLE — the "
          "June-3 baseline is ex-dividend and the post-closure quotes are nominal "
          "(belligerent bonds 'rise' during the war). The earlier ~2% reading is withdrawn.")
    print("\nBut the pre-closure decline IS observable — the weekly (text) vintage, "
          "15 Jun -> 31 Jul 1914 (clean = to last unflagged quote):")
    from .july1914 import war_week_bond_decline
    for w in war_week_bond_decline(args.bonds or BONDS):
        if not w.quotes:
            continue
        q = " ".join(f"{d.strftime('%m-%d')}={p:.1f}{'*' if fl else ''}" for d, p, fl in w.quotes)
        tail = f"  ->{w.pct_clean:+.1f}%" if w.pct_clean is not None else ""
        if w.final_flagged and w.final_price is not None:
            tail += f" [31Jul {w.final_price:.1f} footnoted]"
        print(f"  {w.sovereign:<22}{q}{tail}")
    print("  (* = flagged: ex-dividend or footnote; clean decline stops at the last unflagged quote)")
    print("The whole European sovereign complex fell ~2.5-6% in the final trading weeks — a\n"
          "broad war repricing, visible until the market shut. The IDENTIFIED premium is what's\n"
          "unestimable (regime truncated by closure), not the reaction, which is right here.")
    print("\nCAVEAT — read the LEVEL, not the ORDERING. That Consols (the safest sovereign\n"
          "credit on earth) fell as hard as the belligerents is a strong FLIGHT-TO-LIQUIDITY\n"
          "confound: in a cash scramble you sell what has a bid, and Consols were the most\n"
          "marketable asset there was, so they went first. So the cross-sectional ordering is\n"
          "dominated by marketability and can't be read as a clean war-risk ranking — don't\n"
          "infer 'Britain was the bigger war risk' from it. The aggregate fall is the war\n"
          "signal; whatever war-risk content the ordering holds is entangled with liquidity.")
    return 0


def _cmd_russia(args: argparse.Namespace) -> int:
    """Full-sample bank-rate premia for the belligerent capitals, incl. Russia."""
    from .warweeks import get_crisis
    smap = to_series_map(load_short_rates(args.short or SHORT))
    res = {r.city: r for r in run_crisis(smap, get_crisis("full"))}
    print("Full-sample war-risk premium on the BANK (official discount) rate:")
    print(f"{'capital':<16}{'beta':>8}{'t':>7}")
    for city, label in [("petersburg_bank", "St Petersburg"), ("berlin_bank", "Berlin"),
                        ("paris_bank", "Paris"), ("vienna_bank", "Vienna"),
                        ("london_bank", "London")]:
        r = res.get(city)
        if r:
            print(f"{label:<16}{r.single.beta:>8.2f}{r.single.t_stat:>7.2f}")
    print("\nRussia (St Petersburg) is available here for the first time — the paper "
          "lacked it. Its premium is ~0 because the State Bank rate was administered "
          "and sticky, unlike the Reichsbank's; only a market rate would carry the "
          "signal, and NW's St Petersburg open-market series ends in 1900.")
    return 0


def _cmd_kokovtsov(args: argparse.Namespace) -> int:
    """Did Russian short rates move around Kokovtsov's dismissal (Feb 1914)?"""
    from .kokovtsov import format_result, kokovtsov_test

    print(format_result(kokovtsov_test(args.short or SHORT, args.bonds or BONDS)))
    return 0


def _cmd_basis(args: argparse.Namespace) -> int:
    """Re-estimate the premia against neutral bases, and placebo-test the neutrals."""
    from .warweeks import get_crisis

    smap = to_series_map(load_short_rates(args.short or SHORT))
    full = get_crisis("full")
    bases = [("London-trade(orig)", "london_trade3mo"), ("Switzerland", "geneva_market"),
             ("Sweden", "stockholm_market"), ("Amsterdam(near)", "amsterdam_openmkt"),
             ("US-call", "new_york_call")]
    cities = [("berlin_openmkt", "Berlin"), ("paris_openmkt", "Paris"),
              ("vienna_openmkt", "Vienna"), ("petersburg_bank", "StPburg")]
    print("Rigobon-Sack premium (single-IV beta), full sample, by BASIS asset:")
    print(f"  {'basis':<18}" + "".join(f"{lab:>9}" for _, lab in cities))
    for bname, bkey in bases:
        res = {r.city: r for r in run_crisis(smap, full, basis_key=bkey)}
        print(f"  {bname:<18}" + "".join(
            f"{(f'{res[c].single.beta:.2f}' if c in res else '—'):>9}" for c, _ in cities))
    print("\nPLACEBO — premium OF each neutral, basis=London (a true neutral should be ~0):")
    res = {r.city: r for r in run_crisis(smap, full, basis_key="london_trade3mo")}
    for slug, lab in [("amsterdam_openmkt", "Amsterdam"), ("geneva_market", "Switzerland"),
                      ("stockholm_market", "Sweden"), ("new_york_call", "US-call")]:
        if slug in res:
            print(f"  {lab:<12} beta={res[slug].single.beta:+.2f}  t={res[slug].single.t_stat:+.2f}")
    print("\nBerlin (~0.35) is robust across the London and Swiss bases and clearly exceeds the\n"
          "neutral floor. But the neutrals themselves carry premia of 0.09-0.12 -- the SAME size\n"
          "as Paris (0.11) and Vienna (0.13) -- so the premium partly measures money-market\n"
          "integration with the basis under war-week stress, not pure war risk. Only premia\n"
          "clearly ABOVE the ~0.10 neutral floor (Berlin) are safely read as war risk.")
    print("\nAnd LONDON itself -- the paper's 'basis' -- carries a large premium vs neutral bases:")
    lon = [("london_bank", "London BoE rate"), ("london_trade3mo", "London 3mo trade bill"),
           ("london_bank_bills_90_days_bid", "London 90d bank bills")]
    print(f"  {'London rate':<24}" + "".join(f"{b:>12}" for b, _ in
          [("Amsterdam", 0), ("Switzerland", 0), ("Sweden", 0)]))
    for lslug, llab in lon:
        row = []
        for bkey in ("amsterdam_openmkt", "geneva_market", "stockholm_market"):
            res = {r.city: r for r in run_crisis(smap, full, basis_key=bkey)}
            row.append(f"{res[lslug].single.beta:+.2f}" if lslug in res else "—")
        print(f"  {llab:<24}" + "".join(f"{x:>12}" for x in row))
    print("London's premium vs Switzerland/Sweden (0.22-0.42) MATCHES Berlin's -- so London is\n"
          "not a war-neutral basis, it is one of the two MOST war-sensitive money markets (the\n"
          "global bill/acceptance/gold centre, frozen hardest in July 1914). Using it as the\n"
          "basis differences every other city against a war-moving reference -- the core reason\n"
          "the premia are compressed and their ranking distorted. A neutral basis is required.")
    return 0


def _cmd_grid(args: argparse.Namespace) -> int:
    """Per-crisis, per-country premia re-estimated against each neutral basis."""
    from .warweeks import CRISES

    smap = to_series_map(load_short_rates(args.short or SHORT))
    bases = [("London", "london_trade3mo"), ("Amsterdam", "amsterdam_openmkt"),
             ("Swiss", "geneva_market"), ("Swedish", "stockholm_market")]
    countries = [("berlin_openmkt", "Germany"), ("paris_openmkt", "France"),
                 ("vienna_openmkt", "Austria"), ("petersburg_bank", "Russia*"),
                 ("brussels_openmkt", "Belgium")]
    cr = {c.key: c for c in CRISES}
    for ck in ("morocco1", "bosnia", "morocco2", "balkans", "full"):
        c = cr[ck]
        n = "small-n, weakly identified" if ck in ("morocco2", "bosnia", "balkans", "morocco1") else "n=485"
        print(f"=== {c.label} ({ck}; {n}) ===")
        print(f"  {'country':<10}" + "".join(f"{b:>10}" for b, _ in bases))
        rbb = {b: {r.city: r for r in run_crisis(smap, c, basis_key=k)} for b, k in bases}
        for slug, name in countries:
            print(f"  {name:<10}" + "".join(
                f"{(f'{rbb[b][slug].single.beta:+.2f}' if slug in rbb[b] else '—'):>10}" for b, _ in bases))
        print()
    print("Read: only the FULL sub-sample is well-identified. Per-crisis estimates swing wildly")
    print("across bases and blow up at small n (Agadir n=22: Belgium +5.75) -- not interpretable.")
    print("Robust across neutral bases (full sample): Germany ~0.30 (3/4 bases; Amsterdam the")
    print("outlier), Belgium ~0.17 (all 4). France ~0.10 sits at the neutral floor; Austria is")
    print("unstable; Russia ~0 is the administered bank rate (a data gap, not a finding).")
    print("* Russia = administered bank rate (sticky); no open-market rate exists.")
    return 0


def _cmd_matrix(args: argparse.Namespace) -> int:
    """Every city's premium in every crisis vs the London basis (belligerent + neutral)."""
    from .warweeks import CRISES

    smap = to_series_map(load_short_rates(args.short or SHORT))
    cr = {c.key: c for c in CRISES}
    order = ["morocco1", "bosnia", "morocco2", "balkans", "full"]
    cities = [("berlin_openmkt", "Berlin"), ("vienna_openmkt", "Vienna"),
              ("paris_openmkt", "Paris"), ("brussels_openmkt", "Brussels"),
              ("petersburg_bank", "StPburg*"), ("amsterdam_openmkt", "Amsterdam~"),
              ("geneva_market", "Geneva~"), ("stockholm_market", "Stockholm~"),
              ("copenhagen_market", "Copenhagen~"), ("christiana_market", "Christiana~"),
              ("new_york_call", "NewYork~")]
    res = {k: {r.city: r for r in run_crisis(smap, cr[k], basis_key="london_trade3mo")} for k in order}
    print("Premium (single-IV beta) vs LONDON basis, city x crisis  (~ = neutral):")
    print(f"  {'city':<12}" + "".join(f"{cr[k].label.split()[0][:9]:>10}" for k in order))
    for slug, name in cities:
        print(f"  {name:<12}" + "".join(
            f"{(f'{res[k][slug].single.beta:+.2f}' if slug in res[k] else '—'):>10}" for k in order))
    print("\nOnly the FULL column is well-identified (Agadir n=22 blows everyone up; Bosnia is")
    print("near-zero for all). Neutrals (~) carry pooled premia (Amsterdam 0.09, Geneva 0.09,")
    print("Stockholm 0.12, Copenhagen 0.14) as large as Paris/Vienna -- and in the Balkans,")
    print("neutral Stockholm (+0.34) beats belligerent Berlin (+0.26). So the 'neutral floor'")
    print("is a pooled artifact driven by specific periods, and a neutral can outscore a")
    print("belligerent -- the premium is not cleanly war risk. Only Berlin's full-sample ~0.35")
    print("stands clearly and consistently above the neutral cluster.")
    print("* administered bank rate (sticky).  ~ Christiania = Oslo (Norway) -- name until 1925.")
    return 0


def _cmd_neutrals(args: argparse.Namespace) -> int:
    """Belligerents vs each neutral basis, and how robust the neutral premia are."""
    from .warweeks import get_crisis

    smap = to_series_map(load_short_rates(args.short or SHORT))
    full = get_crisis("full")
    neut = [("amsterdam_openmkt", "Amsterdam"), ("geneva_market", "Geneva"),
            ("stockholm_market", "Stockholm"), ("copenhagen_market", "Copenhagen"),
            ("christiana_market", "Christiania"), ("new_york_call", "NewYork")]
    bell = [("berlin_openmkt", "Berlin"), ("vienna_openmkt", "Vienna"),
            ("paris_openmkt", "Paris"), ("brussels_openmkt", "Brussels")]
    byb = {slug: {r.city: r for r in run_crisis(smap, full, basis_key=slug)} for slug, _ in neut}

    def b(basis, x):
        r = byb[basis].get(x)
        return f"{r.single.beta:+.2f}" if r else "  -"

    print("BELLIGERENTS' premium vs each NEUTRAL basis (full sample, beta):")
    print("  country   " + "".join(f"{n:>11}" for _, n in neut))
    for xs, xn in bell:
        print(f"  {xn:<10}" + "".join(f"{b(bs, xs):>11}" for bs, _ in neut))
    print("\nNEUTRAL (x) vs NEUTRAL (basis) -- do the neutrals differ from each other?")
    print("  x / basis  " + "".join(f"{n[:9]:>10}" for _, n in neut))
    for xs, xn in neut:
        print(f"  {xn:<11}" + "".join(
            (f"{'self':>10}" if bs == xs else f"{b(bs, xs):>10}") for bs, _ in neut))
    print("\nChristiania = Oslo (Norway's capital was named Christiania until 1925).")
    print("Reading: Berlin clears ~0.26-0.34 against 3 of 5 credible neutrals (Geneva, Copenhagen,")
    print("Stockholm), suppressed only against Amsterdam (the most Germany-integrated neutral) and")
    print("noisy NY. The Scandinavian trio co-moves hugely (Stockholm/Copenhagen/Christiania betas")
    print("0.33-0.61) -- the Scandinavian Monetary Union (gold krone, 1873-1914) -- so they are ONE")
    print("neutral bloc, not three independent checks. Amsterdam/Geneva are more independent. So")
    print("the neutral premia are a common/bloc factor, not independent country-specific war risk.")
    return 0


def _cmd_factor(args: argparse.Namespace) -> int:
    """Common European money-market factor + idiosyncratic loadings; the US outlier."""
    import datetime
    import statistics

    from .warweeks import get_crisis, war_mask

    smap = to_series_map(load_short_rates(args.short or SHORT))
    full = get_crisis("full")
    lo, hi = full.window
    week = datetime.timedelta(days=7)

    def dchg(slug):
        s = dict(smap[slug])
        return {d: s[d] - s[d - week] for d in s if lo <= d <= hi and (d - week) in s}

    eur = ["berlin_openmkt", "paris_openmkt", "vienna_openmkt", "brussels_openmkt",
           "amsterdam_openmkt", "geneva_market", "stockholm_market",
           "copenhagen_market", "christiana_market"]
    ch = {k: dchg(k) for k in eur + ["new_york_call"]}
    dates = sorted(set.intersection(*[set(ch[k]) for k in eur]))
    F = {d: statistics.mean(ch[k][d] for k in eur) for d in dates}
    mask = dict(zip(dates, war_mask(dates, full.war_events)))
    warv = statistics.pvariance([F[d] for d in dates if mask[d]])
    peacev = statistics.pvariance([F[d] for d in dates if not mask[d]])

    def loading(slug):
        common = sorted(set(ch[slug]) & set(F))
        x = [ch[slug][d] for d in common]
        f = [F[d] for d in common]
        fb, xb = statistics.mean(f), statistics.mean(x)
        beta = sum((a - xb) * (b - fb) for a, b in zip(x, f)) / sum((b - fb) ** 2 for b in f)
        ss = sum((a - xb) ** 2 for a in x)
        sr = sum((a - (xb + beta * (b - fb))) ** 2 for a, b in zip(x, f))
        return beta, (1 - sr / ss if ss else 0.0)

    print("Common European money-market factor F (mean of European weekly rate changes):")
    print(f"  var(F) war weeks {warv:.4f} vs peace weeks {peacev:.4f} ({warv/peacev:.1f}x) --")
    print("  NOT war-amplified: the common factor is financial integration (1907 panic,")
    print("  autumn seasonals dominate), not a war-stress factor. War risk is the smaller")
    print("  Rigobon component on top (war-premia basis/matrix).\n")
    print("  Loading on F (beta) and R2 (= share of the market that is COMMON):")
    for slug, name in [("berlin_openmkt", "Berlin"), ("vienna_openmkt", "Vienna"),
                       ("paris_openmkt", "Paris"), ("amsterdam_openmkt", "Amsterdam~"),
                       ("geneva_market", "Geneva~"), ("stockholm_market", "Stockholm~"),
                       ("copenhagen_market", "Copenhagen~"), ("christiana_market", "Christiania~"),
                       ("new_york_call", "NewYork~US")]:
        b, r2 = loading(slug)
        print(f"    {name:<14} beta={b:+.2f}  R2={r2:.2f}")
    print("\nEvery European market (belligerent + neutral) loads positively on F; the US alone")
    print("has R2~0 -- it is OUTSIDE the European system, and its war premium is negative (a")
    print("safe haven: gold flowed IN). So risk decomposes into a COMMON European factor")
    print("(integration) + IDIOSYNCRATIC country risk (Berlin's excess), with the US as the")
    print("non-European control. ~ = neutral; Christiania = Oslo.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="war-premia", description="Reproduce/extend Carls (2005).")
    p.add_argument("--short", help="path to stinterestrates.xls")
    p.add_argument("--bonds", help="path to longtermbonds.xls")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("reproduce", help="Tables 3-7").set_defaults(func=_cmd_reproduce)
    sub.add_parser("july1914", help="the extension").set_defaults(func=_cmd_july1914)
    sub.add_parser("russia", help="St Petersburg bank-rate premium").set_defaults(func=_cmd_russia)
    sub.add_parser("kokovtsov", help="the Kokovtsov dismissal event test (Feb 1914)").set_defaults(func=_cmd_kokovtsov)
    sub.add_parser("basis", help="premia under neutral bases + neutral placebo").set_defaults(func=_cmd_basis)
    sub.add_parser("grid", help="per-crisis per-country premia across neutral bases").set_defaults(func=_cmd_grid)
    sub.add_parser("matrix", help="every city's premium in every crisis vs London (incl. neutrals)").set_defaults(func=_cmd_matrix)
    sub.add_parser("neutrals", help="belligerents vs each neutral + neutral-vs-neutral robustness").set_defaults(func=_cmd_neutrals)
    sub.add_parser("factor", help="common European factor + idiosyncratic loadings; the US outlier").set_defaults(func=_cmd_factor)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
