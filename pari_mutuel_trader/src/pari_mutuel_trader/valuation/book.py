from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from pari_mutuel_trader.valuation.intrinsic import (
    SPRING_LOADED,
    ValuationInputs,
    valuation_report,
)
from pari_mutuel_trader.valuation.quality import QualityProfile
from pari_mutuel_trader.valuation.sell_rules import (
    Position,
    SellDecision,
    SellPolicy,
    review_position,
)
from pari_mutuel_trader.valuation.tax import TaxProfile, build_tax_profile


def _as_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def _quality_from(row: dict) -> QualityProfile:
    return QualityProfile(
        moat=float(row.get("moat", 0.5)),
        roic=float(row.get("roic", 0.12)),
        roic_stability=float(row.get("roic_stability", 0.5)),
        wacc=float(row.get("wacc", 0.08)),
    )


def _inputs_from(row: dict) -> ValuationInputs:
    fade = row.get("fade_years")
    terminal = row.get("terminal_growth")
    return ValuationInputs(
        owner_earnings_ps=float(row["owner_earnings_ps"]),
        growth=float(row.get("growth", 0.08)),
        quality=_quality_from(row),
        fade_years=int(fade) if fade else None,
        terminal_growth=float(terminal) if terminal is not None else None,
    )


def _position_from(row: dict) -> Position:
    return Position(
        symbol=str(row["symbol"]),
        shares=float(row.get("shares", 0.0)),
        cost_basis_ps=float(row.get("cost_basis", row.get("cost_basis_ps", 0.0))),
        price=float(row["price"]),
        inputs=_inputs_from(row),
        acquired=_as_date(row.get("acquired")),
        weight=float(row["weight"]) if row.get("weight") is not None else None,
        thesis_intact=bool(row.get("thesis_intact", True)),
    )


@dataclass
class Candidate:
    """A name that could absorb redeployed capital."""

    symbol: str
    price: float
    inputs: ValuationInputs
    implied_return: float
    zone: str


@dataclass
class Book:
    positions: list[Position] = field(default_factory=list)
    watchlist: list[Candidate] = field(default_factory=list)
    cash: float = 0.0
    as_of: date | None = None
    tax: TaxProfile = field(default_factory=TaxProfile)
    policy: SellPolicy = field(default_factory=SellPolicy)

    @property
    def market_value(self) -> float:
        return float(sum(p.market_value for p in self.positions) + self.cash)

    def assign_weights(self) -> None:
        """Fill in weights from market value for any position that did not supply one."""
        total = self.market_value
        if total <= 0:
            return
        for p in self.positions:
            if p.weight is None:
                p.weight = p.market_value / total


def _candidate_from(row: dict, policy: SellPolicy) -> Candidate:
    inputs = _inputs_from(row)
    price = float(row["price"])
    report = valuation_report(
        price,
        inputs,
        required_return=policy.required_return,
        hold_return=policy.hold_return,
        add_margin=policy.add_margin,
        rich_band=policy.rich_band,
    )
    return Candidate(
        symbol=str(row["symbol"]),
        price=price,
        inputs=inputs,
        implied_return=report["implied_return"],
        zone=report["zone"],
    )


def load_book(path: str) -> Book:
    """Load positions, watchlist, tax rates and policy from YAML (or a positions CSV)."""
    p = Path(path)
    if p.suffix.lower() == ".csv":
        rows = pd.read_csv(p).to_dict("records")
        raw = {"positions": rows}
    else:
        import yaml

        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    policy = SellPolicy.from_config(raw.get("policy"))
    tax_cfg = raw.get("tax") or {}
    tax = build_tax_profile(tax_cfg)
    meta = raw.get("book") or {}

    book = Book(
        positions=[_position_from(r) for r in raw.get("positions") or []],
        watchlist=[_candidate_from(r, policy) for r in raw.get("watchlist") or []],
        cash=float(meta.get("cash", 0.0)),
        as_of=_as_date(meta.get("as_of")),
        tax=tax,
        policy=policy,
    )
    book.assign_weights()
    return book


def opportunity_set(book: Book, extra: list[Candidate] | None = None) -> list[Candidate]:
    """Spring-loaded names - held, watched, or offered by another sleeve.

    `extra` is how the rest of the portfolio gets a say: a trim is only honest if
    the alternative it is measured against is the best one the account can reach,
    not merely the best one this book happens to track.
    """
    out = list(book.watchlist) + list(extra or [])
    for p in book.positions:
        report = valuation_report(
            p.price,
            p.inputs,
            required_return=book.policy.required_return,
            hold_return=book.policy.hold_return,
            add_margin=book.policy.add_margin,
            rich_band=book.policy.rich_band,
        )
        out.append(
            Candidate(
                symbol=p.symbol,
                price=p.price,
                inputs=p.inputs,
                implied_return=report["implied_return"],
                zone=report["zone"],
            )
        )
    return [c for c in out if c.zone == SPRING_LOADED]


def review_book(
    book: Book, as_of: date | None = None, extra_candidates: list[Candidate] | None = None
) -> list[SellDecision]:
    """Review every position against IV15/IV8, tax, and the best available alternative."""
    as_of = as_of or book.as_of or date.today()
    candidates = opportunity_set(book, extra_candidates)
    decisions = []
    for position in book.positions:
        rivals = [c.implied_return for c in candidates if c.symbol != position.symbol]
        best = max(rivals) if rivals else None
        decisions.append(
            review_position(
                position,
                policy=book.policy,
                tax_profile=book.tax,
                best_alternative_return=best,
                as_of=as_of,
            )
        )
    return decisions


def build_redeploy_plan(book: Book, decisions: list[SellDecision]) -> dict:
    """Route harvested after-tax capital into the most spring-loaded names.

    Room is capped by the conviction weight so the proceeds of one trim cannot
    recreate an oversized position somewhere else.
    """
    harvested = float(sum(d.proceeds.net for d in decisions if d.proceeds and d.shares_to_sell > 0))
    total = book.market_value
    held = {d.symbol: d for d in decisions}
    candidates = sorted(opportunity_set(book), key=lambda c: c.implied_return, reverse=True)

    room = []
    for c in candidates:
        current = held[c.symbol].target_weight if c.symbol in held else 0.0
        available = max(book.policy.conviction_weight - current, 0.0) * total
        if available > 0:
            room.append((c, available))

    capacity = sum(a for _, a in room)
    allocations = []
    if harvested > 0 and capacity > 0:
        deployable = min(harvested, capacity)
        for c, available in room:
            amount = deployable * (available / capacity)
            allocations.append(
                {
                    "symbol": c.symbol,
                    "implied_return": c.implied_return,
                    "amount": float(amount),
                    "weight": float(amount / total) if total else 0.0,
                }
            )

    return {
        "harvested_after_tax": harvested,
        "tax_paid": float(sum(d.proceeds.tax for d in decisions if d.proceeds and d.shares_to_sell > 0)),
        "deployable_capacity": float(capacity),
        "undeployed": float(max(harvested - capacity, 0.0)),
        "allocations": allocations,
    }


def decisions_frame(decisions: list[SellDecision]) -> pd.DataFrame:
    if not decisions:
        return pd.DataFrame()
    frame = pd.DataFrame([d.to_dict() for d in decisions])
    frame["notes"] = frame["notes"].apply(lambda n: " | ".join(n))
    return frame


def summarize_review(book: Book, decisions: list[SellDecision]) -> dict:
    actions: dict[str, int] = {}
    for d in decisions:
        actions[d.action] = actions.get(d.action, 0) + 1
    return {
        "as_of": str(book.as_of or date.today()),
        "book_market_value": book.market_value,
        "positions": len(decisions),
        "actions": actions,
        "zones": {z: sum(1 for d in decisions if d.zone == z) for z in {d.zone for d in decisions}},
        "weighted_implied_return": float(
            sum(d.implied_return * d.current_weight for d in decisions)
            / sum(d.current_weight for d in decisions)
        )
        if sum(d.current_weight for d in decisions) > 0
        else 0.0,
    }


def run_review(
    path: str, as_of: date | None = None, extra_candidates: list[Candidate] | None = None
) -> dict:
    """Load a book, review it, and return a JSON-serializable payload."""
    book = load_book(path)
    decisions = review_book(book, as_of=as_of, extra_candidates=extra_candidates)
    return {
        "summary": summarize_review(book, decisions),
        "decisions": [d.to_dict() for d in decisions],
        "redeploy_plan": build_redeploy_plan(book, decisions),
    }
