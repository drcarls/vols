from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from pari_mutuel_trader.paper.state import load_state
from pari_mutuel_trader.portfolio.lots import HIFO
from pari_mutuel_trader.valuation.book import Book, load_book
from pari_mutuel_trader.valuation.sell_rules import SellPolicy
from pari_mutuel_trader.valuation.tax import TaxProfile

SYSTEMATIC = "systematic"
DISCRETIONARY = "discretionary"


@dataclass
class Sleeve:
    """One strategy allocation inside the account.

    A discretionary sleeve carries a book with valuation assumptions per name. A
    systematic sleeve carries only the weights its picker last produced - there are
    no fundamentals behind them, so the valuation checks simply do not apply to it.
    """

    name: str
    kind: str
    allocation: float
    positions_path: str | None = None
    state_path: str | None = None
    policy: SellPolicy = field(default_factory=SellPolicy)

    def book(self) -> Book | None:
        if self.kind != DISCRETIONARY or not self.positions_path:
            return None
        loaded = load_book(self.positions_path)
        loaded.policy = self.policy
        return loaded

    def holdings(self) -> dict[str, float]:
        """Sleeve-relative weights, whatever the sleeve's kind."""
        if self.kind == DISCRETIONARY:
            loaded = self.book()
            return {p.symbol: float(p.weight or 0.0) for p in loaded.positions} if loaded else {}
        if not self.state_path or not Path(self.state_path).exists():
            return {}
        state = load_state(self.state_path)
        history = state.get("holdings_history", {})
        latest = sorted(history)[-1] if history else None
        return {k: float(v) for k, v in history.get(latest, {}).items()} if latest else {}

    def recent_trades(self) -> list[dict]:
        if self.kind == DISCRETIONARY or not self.state_path or not Path(self.state_path).exists():
            return []
        return load_state(self.state_path).get("rebalance_trades", [])


@dataclass
class Account:
    """Sleeves plus the things that only exist above them.

    Tax is assessed on the account, not on a sleeve: losses in one offset gains in
    another, a wash sale is triggered by any repurchase anywhere, and a position
    limit means nothing unless it is measured through every sleeve at once.
    """

    sleeves: list[Sleeve] = field(default_factory=list)
    tax: TaxProfile = field(default_factory=TaxProfile)
    lot_method: str = HIFO
    wash_sales: bool = True
    look_through_ceiling: float = 0.10
    as_of: date | None = None

    def allocation_total(self) -> float:
        return float(sum(s.allocation for s in self.sleeves))

    def look_through(self) -> dict[str, dict[str, float]]:
        """Account-level weight per symbol, and the sleeves contributing it."""
        exposure: dict[str, dict[str, float]] = {}
        for sleeve in self.sleeves:
            for symbol, weight in sleeve.holdings().items():
                exposure.setdefault(symbol, {})[sleeve.name] = weight * sleeve.allocation
        return exposure


def _as_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def load_account(path: str) -> Account:
    import yaml

    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    cfg = raw.get("account") or {}
    tax_cfg = cfg.get("tax") or {}
    tax = TaxProfile(**{k: float(v) for k, v in tax_cfg.items() if k in TaxProfile.__dataclass_fields__})
    default_policy = cfg.get("policy") or {}

    sleeves = []
    for entry in cfg.get("sleeves") or []:
        policy_cfg = {**default_policy, **(entry.get("policy") or {})}
        sleeves.append(
            Sleeve(
                name=str(entry["name"]),
                kind=str(entry.get("kind", DISCRETIONARY)),
                allocation=float(entry.get("allocation", 0.0)),
                positions_path=entry.get("positions"),
                state_path=entry.get("state"),
                policy=SellPolicy.from_config(policy_cfg),
            )
        )

    return Account(
        sleeves=sleeves,
        tax=tax,
        lot_method=str(cfg.get("lot_method", HIFO)),
        wash_sales=bool(cfg.get("wash_sales", True)),
        look_through_ceiling=float(cfg.get("look_through_ceiling", 0.10)),
        as_of=_as_date(cfg.get("as_of")),
    )
