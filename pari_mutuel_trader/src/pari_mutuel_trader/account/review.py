from __future__ import annotations

from datetime import date

from pari_mutuel_trader.account.model import Account
from pari_mutuel_trader.portfolio.lots import WASH_SALE_DAYS
from pari_mutuel_trader.valuation.book import Candidate, build_redeploy_plan, opportunity_set, review_book
from pari_mutuel_trader.valuation.intrinsic import SPRING_LOADED
from pari_mutuel_trader.valuation.overlay import zone_ceilings
from pari_mutuel_trader.valuation.sell_rules import EXIT, TRIM, TRIM_TO_HOUSE_MONEY


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
    """Sales at a loss in one sleeve that another sleeve is holding or buying back.

    The wash-sale rule follows the taxpayer, not the strategy. A sleeve that never
    repurchases a name can still have its loss disallowed by a different sleeve
    buying the same ticker inside the window.
    """
    selling_at_loss: dict[str, list[str]] = {}
    for sleeve_name, decisions in decisions_by_sleeve.items():
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
        if elsewhere:
            conflicts.append({
                "symbol": symbol,
                "sold_at_loss_by": sorted(sellers),
                "held_or_bought_by": elsewhere,
                "window_days": WASH_SALE_DAYS,
            })
    return conflicts


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
                "holdings": len(sleeve.holdings()),
                "decisions": [],
                "note": "systematic sleeve: weights only, no valuation assumptions to review",
            })
            continue
        book.tax = account.tax
        external = [c for c in shared if c.symbol not in {p.symbol for p in book.positions}]
        decisions = review_book(book, as_of=as_of, extra_candidates=external)
        decisions_by_sleeve[sleeve.name] = decisions
        payload_sleeves.append({
            "name": sleeve.name,
            "kind": sleeve.kind,
            "allocation": sleeve.allocation,
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
        "look_through_breaches": look_through_breaches(account, decisions_by_sleeve),
        "wash_sale_conflicts": wash_sale_conflicts(account, decisions_by_sleeve),
    }


def run_account_review(path: str, as_of: date | None = None) -> dict:
    from pari_mutuel_trader.account.model import load_account

    return review_account(load_account(path), as_of=as_of)
