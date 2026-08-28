from __future__ import annotations

from dataclasses import dataclass, field

from pari_mutuel_trader.valuation.quality import QualityProfile

SPRING_LOADED = "spring_loaded"
FAIR = "fair"
RICH = "rich"
EXPENSIVE = "expensive"

ZONES = (SPRING_LOADED, FAIR, RICH, EXPENSIVE)


@dataclass
class ValuationInputs:
    """Per-share owner earnings and the growth/quality assumptions behind them."""

    owner_earnings_ps: float
    growth: float = 0.08
    quality: QualityProfile = field(default_factory=QualityProfile)
    fade_years: int | None = None
    terminal_growth: float | None = None

    def years(self) -> int:
        return int(self.fade_years) if self.fade_years else self.quality.competitive_advantage_period()

    def g_terminal(self) -> float:
        return float(self.terminal_growth) if self.terminal_growth is not None else self.quality.terminal_growth()


def _payout(growth: float, roic: float) -> float:
    """Share of earnings left over after funding growth at the given ROIC.

    Growth is not free: sustaining g requires reinvesting g/ROIC of earnings, so a
    high and enduring ROIC is what converts growth into owner cash.
    """
    if roic <= 1e-6:
        return 0.0
    return float(min(max(1.0 - growth / roic, 0.0), 1.0))


def intrinsic_value(inputs: ValuationInputs, required_return: float) -> float:
    """Per-share value at which the investment is priced to return `required_return`.

    IV15 (required_return=0.15) is the valuation guide for putting capital to work;
    IV8 is the point beyond which the business is no longer earning its keep for a
    holder. Both are the same model read at two hurdle rates.
    """
    q = inputs.quality
    n = max(inputs.years(), 1)
    g_term = inputs.g_terminal()
    if required_return <= g_term:
        raise ValueError("required_return must exceed terminal growth")

    roic_0 = max(q.roic, 1e-6)
    roic_term = max(q.terminal_roic(), 1e-6)

    earnings = float(inputs.owner_earnings_ps)
    pv = 0.0
    for t in range(1, n + 1):
        step = t / n
        g_t = inputs.growth + (g_term - inputs.growth) * step
        roic_t = roic_0 + (roic_term - roic_0) * step
        earnings *= 1.0 + g_t
        pv += earnings * _payout(g_t, roic_t) / (1.0 + required_return) ** t

    terminal_earnings = earnings * (1.0 + g_term)
    terminal_value = terminal_earnings * _payout(g_term, roic_term) / (required_return - g_term)
    pv += terminal_value / (1.0 + required_return) ** n
    return float(pv)


def iv15(inputs: ValuationInputs) -> float:
    return intrinsic_value(inputs, 0.15)


def iv8(inputs: ValuationInputs) -> float:
    return intrinsic_value(inputs, 0.08)


def price_for_return(inputs: ValuationInputs, required_return: float) -> float:
    """Alias for intrinsic_value, read as 'the price that buys this return'."""
    return intrinsic_value(inputs, required_return)


def implied_return(price: float, inputs: ValuationInputs, tol: float = 1e-6, max_iter: int = 200) -> float:
    """Annualized return the current price is priced to deliver."""
    if price <= 0:
        return float("nan")
    lo = inputs.g_terminal() + 0.005
    hi = 1.0
    if intrinsic_value(inputs, lo) <= price:
        return float(lo)
    if intrinsic_value(inputs, hi) >= price:
        return float(hi)
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        value = intrinsic_value(inputs, mid)
        if abs(value - price) < tol:
            return float(mid)
        if value > price:
            lo = mid
        else:
            hi = mid
    return float(0.5 * (lo + hi))


def classify_zone(price: float, value_15: float, value_8: float, rich_band: float = 0.15) -> str:
    """Where the price sits against the IV15 / IV8 pair.

    - spring_loaded: at or below IV15, priced for a 15%+ return
    - fair:          between IV15 and IV8, still earning its keep
    - rich:          past IV8 but within the band where a hold is defensible
    - expensive:     far enough past IV8 that size is no longer justified
    """
    if price <= value_15:
        return SPRING_LOADED
    if price <= value_8:
        return FAIR
    if price <= value_8 * (1.0 + rich_band):
        return RICH
    return EXPENSIVE


def valuation_report(
    price: float,
    inputs: ValuationInputs,
    required_return: float = 0.15,
    hold_return: float = 0.08,
    add_margin: float = 0.02,
    rich_band: float = 0.15,
) -> dict:
    """IV15/IV8 snapshot plus the price levels that would change the decision."""
    value_hi = intrinsic_value(inputs, required_return)
    value_lo = intrinsic_value(inputs, hold_return)
    add_level = intrinsic_value(inputs, required_return + add_margin)
    return {
        "price": float(price),
        "iv15": value_hi,
        "iv8": value_lo,
        "implied_return": implied_return(price, inputs),
        "discount_to_iv15": float(value_hi / price - 1.0) if price else float("nan"),
        "premium_to_iv8": float(price / value_lo - 1.0) if value_lo else float("nan"),
        "zone": classify_zone(price, value_hi, value_lo, rich_band),
        "add_level": add_level,
        "trim_level": value_lo,
        "durability": inputs.quality.durability(),
        "fade_years": inputs.years(),
        "terminal_growth": inputs.g_terminal(),
    }
