from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from pari_mutuel_trader.valuation.intrinsic import (
    EXPENSIVE,
    FAIR,
    RICH,
    SPRING_LOADED,
    ValuationInputs,
    valuation_report,
)
from pari_mutuel_trader.valuation.tax import (
    SaleProceeds,
    TaxProfile,
    days_to_long_term,
    is_long_term,
    required_replacement_return,
    sale_proceeds,
    switch_is_justified,
)

ADD = "add"
HOLD = "hold"
TRIM = "trim"
TRIM_TO_HOUSE_MONEY = "trim_to_house_money"
EXIT = "exit"


@dataclass
class SellPolicy:
    """Sizing bands and hurdles that turn a valuation read into a trade."""

    required_return: float = 0.15
    hold_return: float = 0.08
    add_margin: float = 0.02
    rich_band: float = 0.15
    conviction_weight: float = 0.08
    core_weight: float = 0.06
    house_money_weight: float = 0.03
    exit_durability: float = 0.45
    redeploy_horizon_years: float = 5.0
    switch_hurdle: float = 0.02
    long_term_wait_days: int = 45

    @classmethod
    def from_config(cls, cfg: dict | None) -> "SellPolicy":
        cfg = cfg or {}
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in cfg.items() if k in known})


@dataclass
class Position:
    symbol: str
    shares: float
    cost_basis_ps: float
    price: float
    inputs: ValuationInputs
    acquired: date | None = None
    weight: float | None = None
    thesis_intact: bool = True

    @property
    def market_value(self) -> float:
        return float(self.shares * self.price)

    @property
    def cost(self) -> float:
        return float(self.shares * self.cost_basis_ps)


@dataclass
class SellDecision:
    symbol: str
    action: str
    zone: str
    price: float
    iv15: float
    iv8: float
    implied_return: float
    durability: float
    current_weight: float
    target_weight: float
    shares_to_sell: float
    proceeds: SaleProceeds | None
    after_tax_price: float
    effective_tax_rate: float
    required_replacement_return: float
    best_alternative_return: float | None
    capital_recovered: float
    house_money: bool
    add_level: float
    trim_level: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        out = {
            "symbol": self.symbol,
            "action": self.action,
            "zone": self.zone,
            "price": self.price,
            "iv15": self.iv15,
            "iv8": self.iv8,
            "implied_return": self.implied_return,
            "durability": self.durability,
            "current_weight": self.current_weight,
            "target_weight": self.target_weight,
            "shares_to_sell": self.shares_to_sell,
            "gross_proceeds": self.proceeds.gross if self.proceeds else 0.0,
            "tax": self.proceeds.tax if self.proceeds else 0.0,
            "after_tax_proceeds": self.proceeds.net if self.proceeds else 0.0,
            "after_tax_price": self.after_tax_price,
            "effective_tax_rate": self.effective_tax_rate,
            "required_replacement_return": self.required_replacement_return,
            "best_alternative_return": self.best_alternative_return,
            "capital_recovered": self.capital_recovered,
            "house_money": self.house_money,
            "add_level": self.add_level,
            "trim_level": self.trim_level,
            "notes": list(self.notes),
        }
        return out


def _target_weight_for_zone(
    zone: str, current: float, policy: SellPolicy, price: float, add_level: float
) -> float:
    """Weight ceiling implied by the zone.

    Being at IV15 is enough to hold a full position but not to build one: capital is
    committed at the add level, which demands the required return plus a margin.
    """
    if zone == SPRING_LOADED:
        return max(current, policy.conviction_weight) if price <= add_level else current
    if zone == FAIR:
        return min(current, policy.core_weight)
    if zone == RICH:
        return min(current, 0.5 * (policy.core_weight + policy.house_money_weight))
    return min(current, policy.house_money_weight)


def _action_for(current: float, target: float, policy: SellPolicy) -> str:
    if current <= 1e-9:
        return ADD if target > 1e-9 else HOLD
    if target <= 1e-9:
        return EXIT
    if target > current + 1e-9:
        return ADD
    if target < current - 1e-9:
        return TRIM_TO_HOUSE_MONEY if target <= policy.house_money_weight + 1e-9 else TRIM
    return HOLD


def review_position(
    position: Position,
    policy: SellPolicy | None = None,
    tax_profile: TaxProfile | None = None,
    best_alternative_return: float | None = None,
    as_of: date | None = None,
) -> SellDecision:
    """Decide what to do with one position, after tax.

    The valuation zone sets a ceiling on size. Opportunity cost can trim further:
    a position can be perfectly fine on its own terms and still lose its capital to
    a more spring-loaded idea, provided the alternative clears the hurdle implied
    by the after-tax price rather than the screen price.
    """
    policy = policy or SellPolicy()
    tax_profile = tax_profile or TaxProfile()
    as_of = as_of or date.today()

    report = valuation_report(
        position.price,
        position.inputs,
        required_return=policy.required_return,
        hold_return=policy.hold_return,
        add_margin=policy.add_margin,
        rich_band=policy.rich_band,
    )
    zone = report["zone"]
    durability = report["durability"]
    current = float(position.weight if position.weight is not None else 0.0)
    notes: list[str] = []

    long_term = is_long_term(position.acquired, as_of)
    to_long_term = days_to_long_term(position.acquired, as_of)

    if not position.thesis_intact:
        target = 0.0
        notes.append("thesis broken: valuation is not the binding consideration")
    else:
        target = _target_weight_for_zone(zone, current, policy, position.price, report["add_level"])
        if zone == EXPENSIVE and durability < policy.exit_durability:
            target = 0.0
            notes.append(
                f"expensive and durability {durability:.2f} below {policy.exit_durability:.2f}: "
                "no reason to keep a stub"
            )
        elif zone == EXPENSIVE:
            notes.append(
                "past IV8 by more than the rich band, but the franchise still earns a "
                "house-money stake"
            )
        elif zone == SPRING_LOADED and position.price > report["add_level"]:
            notes.append(
                f"below IV15 and priced for {report['implied_return']:.1%}; adds resume at "
                f"{report['add_level']:.2f}"
            )
        elif zone == SPRING_LOADED:
            notes.append(
                f"at or below the add level: priced for {report['implied_return']:.1%}"
            )

    # The after-tax price is a property of the lot, not of how much is sold, so the
    # hurdle is computed per share and stays meaningful even when nothing is trimmed.
    unit = sale_proceeds(1.0, position.price, position.cost_basis_ps, long_term, tax_profile)
    hurdle = required_replacement_return(report["implied_return"], unit, policy.redeploy_horizon_years)

    # Capital is not taken from a name still priced for the required return: a
    # spring-loaded position is already the kind of thing the proceeds would buy.
    if (
        position.thesis_intact
        and best_alternative_return is not None
        and zone != SPRING_LOADED
        and target > policy.house_money_weight
        and switch_is_justified(
            report["implied_return"],
            best_alternative_return,
            unit,
            policy.redeploy_horizon_years,
            policy.switch_hurdle,
        )
    ):
        target = min(target, policy.house_money_weight)
        notes.append(
            f"alternative at {best_alternative_return:.1%} clears the {hurdle:.1%} after-tax "
            f"hurdle against holding at {report['implied_return']:.1%}"
        )

    shares_to_sell = 0.0
    if current > 0 and target < current:
        shares_to_sell = position.shares * (1.0 - target / current)
    proceeds = sale_proceeds(
        shares_to_sell, position.price, position.cost_basis_ps, long_term, tax_profile
    )

    action = _action_for(current, target, policy)

    if action in (TRIM, TRIM_TO_HOUSE_MONEY, EXIT) and not long_term:
        if zone == EXPENSIVE or not position.thesis_intact:
            notes.append(
                f"short-term gain accepted: {to_long_term} days to long-term treatment is not a "
                "reason to sit in a position this rich"
            )
        elif to_long_term <= policy.long_term_wait_days:
            notes.append(
                f"{to_long_term} days from long-term treatment; waiting is defensible here since "
                "the position is not yet uncomfortable"
            )

    cost = position.cost
    capital_recovered = float(proceeds.net / cost) if cost else 0.0
    house_money = bool(cost and proceeds.net >= cost)
    if house_money and action != HOLD:
        notes.append(
            "original capital recovered after tax: the position is closed at a profit"
            if action == EXIT
            else "original capital recovered after tax: the remaining stake is house money"
        )

    return SellDecision(
        symbol=position.symbol,
        action=action,
        zone=zone,
        price=report["price"],
        iv15=report["iv15"],
        iv8=report["iv8"],
        implied_return=report["implied_return"],
        durability=durability,
        current_weight=current,
        target_weight=float(target),
        shares_to_sell=float(shares_to_sell),
        proceeds=proceeds,
        after_tax_price=unit.net_price,
        effective_tax_rate=proceeds.tax_rate,
        required_replacement_return=hurdle,
        best_alternative_return=best_alternative_return,
        capital_recovered=capital_recovered,
        house_money=house_money,
        add_level=report["add_level"],
        trim_level=report["trim_level"],
        notes=notes,
    )
