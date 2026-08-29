from __future__ import annotations

from datetime import date

from pari_mutuel_trader.account.model import Account
from pari_mutuel_trader.portfolio.lots import WASH_SALE_DAYS
from pari_mutuel_trader.valuation.book import Candidate, build_redeploy_plan, opportunity_set, review_book
from pari_mutuel_trader.valuation.intrinsic import SPRING_LOADED
from pari_mutuel_trader.valuation.overlay import zone_ceilings
from pari_mutuel_trader.valuation.sell_rules import EXIT, TRIM, TRIM_TO_HOUSE_MONEY
from pari_mutuel_trader.valuation.tax import TAXABLE


def account_opportunity_set(account: Account) -> list[Candidate]:
    """Every spring-loaded name the account can reach, from any sleeve."""
    found: dict[str, Candidate] = {}
    for sleeve in account.sleeves:
        book = sleeve.book()
        if book is None:
            continue
        for candidate in opportunity_set(book):
            found.setdefault(candidate.symbol, candidate)
    return list(found.values())


def look_through_breaches(account: Account, decisions_by_sleeve: dict[str, list]) -> list[dict]:
    """Symbols whose account-level weight exceeds what any sleeve would allow alone.

    Each sleeve can respect its own ceiling and the account still end up over its
    limit in a name both sleeves like. Only a look-through sees it.
    """
    zones = {}
    for sleeve_name, decisions in decisions_by_sleeve.items():
        for d in decisions:
            zones.setdefault(d.symbol, {})[sleeve_name] = d.zone

    breaches = []
    for symbol, contributions in account.look_through().items():
        total = float(sum(contributions.values()))
        symbol_zones = zones.get(symbol, {})
        # The tightest ceiling any sleeve puts on the name is the account's ceiling.
        ceilings = [
            zone_ceilings(s.policy)[symbol_zones[s.name]]
            for s in account.sleeves
            if s.name in symbol_zones and s.policy.sizing == "absolute"
        ]
        limit = min(ceilings) if ceilings else account.look_through_ceiling
        if total > limit + 1e-9:
            breaches.append({
                "symbol": symbol,
                "account_weight": total,
                "limit": float(limit),
                "excess": float(total - limit),
                "sleeves": {k: float(v) for k, v in contributions.items()},
                "zones": symbol_zones,
            })
    return sorted(breaches, key=lambda b: b["excess"], reverse=True)


def wash_sale_conflicts(account: Account, decisions_by_sleeve: dict[str, list]) -> list[dict]:
    """Losses in one sleeve that another sleeve washes by buying the same ticker.

    The rule follows the taxpayer, not the strategy, so a sleeve that never
    repurchases can still lose its deduction. Two details only the account sees:

    - Only a taxable sleeve can realize a loss at all. A sale inside a retirement
      wrapper is not a taxable event, so it can never be the seller here.
    - A loss washed by a purchase inside a retirement wrapper is worse than an
      ordinary wash sale. The usual remedy - rolling the disallowed loss into the
      replacement lot's basis - is not available there, so the deduction is gone
      permanently rather than deferred (IRS Rev. Rul. 2008-5). Worth confirming
      with your own advisor before relying on it.
    """
    wrappers = account.wrappers()

    selling_at_loss: dict[str, list[str]] = {}
    for sleeve_name, decisions in decisions_by_sleeve.items():
        if wrappers.get(sleeve_name, TAXABLE) != TAXABLE:
            continue  # nothing realized inside a retirement wrapper
        for d in decisions:
            realized_loss = d.proceeds is not None and d.proceeds.gain < 0
            if d.action in (TRIM, TRIM_TO_HOUSE_MONEY, EXIT) and d.shares_to_sell > 0 and realized_loss:
                selling_at_loss.setdefault(d.symbol, []).append(sleeve_name)

    holders: dict[str, list[str]] = {}
    for sleeve in account.sleeves:
        for symbol in sleeve.holdings():
            holders.setdefault(symbol, []).append(sleeve.name)
        for trade in sleeve.recent_trades():
            for symbol in trade.get("added", []):
                holders.setdefault(symbol, []).append(sleeve.name)

    conflicts = []
    for symbol, sellers in selling_at_loss.items():
        elsewhere = sorted(set(holders.get(symbol, [])) - set(sellers))
        if not elsewhere:
            continue
        in_retirement = [name for name in elsewhere if wrappers.get(name, TAXABLE) != TAXABLE]
        conflicts.append({
            "symbol": symbol,
            "sold_at_loss_by": sorted(sellers),
            "held_or_bought_by": elsewhere,
            "window_days": WASH_SALE_DAYS,
            "severity": "permanent" if in_retirement else "deferred",
            "retirement_sleeves": in_retirement,
        })
    return sorted(conflicts, key=lambda c: c["severity"] != "permanent")


def review_account(account: Account, as_of: date | None = None) -> dict:
    """Review each sleeve against the whole account's opportunity set, then the
    three things no sleeve can check on its own."""
    as_of = as_of or account.as_of
    shared = account_opportunity_set(account)

    decisions_by_sleeve: dict[str, list] = {}
    payload_sleeves = []
    for sleeve in account.sleeves:
        book = sleeve.book()
        if book is None:
            payload_sleeves.append({
                "name": sleeve.name,
                "kind": sleeve.kind,
                "allocation": sleeve.allocation,
                "tax_status": sleeve.tax.status,
                "holdings": len(sleeve.holdings()),
                "decisions": [],
                "note": "systematic sleeve: weights only, no valuation assumptions to review",
            })
            continue
        external = [c for c in shared if c.symbol not in {p.symbol for p in book.positions}]
        decisions = review_book(book, as_of=as_of, extra_candidates=external)
        decisions_by_sleeve[sleeve.name] = decisions
        payload_sleeves.append({
            "name": sleeve.name,
            "kind": sleeve.kind,
            "allocation": sleeve.allocation,
            "tax_status": sleeve.tax.status,
            "holdings": len(book.positions),
            "decisions": [d.to_dict() for d in decisions],
            "redeploy_plan": build_redeploy_plan(book, decisions),
        })

    return {
        "as_of": str(as_of or date.today()),
        "allocation_total": account.allocation_total(),
        "sleeves": payload_sleeves,
        "opportunity_set": sorted(
            [{"symbol": c.symbol, "implied_return": c.implied_return, "zone": SPRING_LOADED} for c in shared],
            key=lambda c: c["implied_return"],
            reverse=True,
        ),
        "look_through": {
            symbol: {"account_weight": float(sum(v.values())), "sleeves": {k: float(w) for k, w in v.items()}}
            for symbol, v in sorted(account.look_through().items())
        },
        "wrappers": account.wrappers(),
        "look_through_breaches": look_through_breaches(account, decisions_by_sleeve),
        "wash_sale_conflicts": wash_sale_conflicts(account, decisions_by_sleeve),
    }


def run_account_review(path: str, as_of: date | None = None) -> dict:
    from pari_mutuel_trader.account.model import load_account

    return review_account(load_account(path), as_of=as_of)
