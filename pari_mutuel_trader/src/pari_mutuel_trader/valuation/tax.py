from __future__ import annotations

from dataclasses import dataclass
from datetime import date

LONG_TERM_DAYS = 366


@dataclass
class TaxProfile:
    """Marginal rates applied to a realized gain."""

    federal_long_term: float = 0.20
    federal_short_term: float = 0.37
    state: float = 0.0
    niit: float = 0.038

    def rate(self, long_term: bool) -> float:
        federal = self.federal_long_term if long_term else self.federal_short_term
        return float(federal + self.state + self.niit)


def is_long_term(acquired: date | None, as_of: date | None = None) -> bool:
    if acquired is None:
        return True
    as_of = as_of or date.today()
    return (as_of - acquired).days >= LONG_TERM_DAYS


def days_to_long_term(acquired: date | None, as_of: date | None = None) -> int:
    if acquired is None:
        return 0
    as_of = as_of or date.today()
    return max(LONG_TERM_DAYS - (as_of - acquired).days, 0)


@dataclass
class SaleProceeds:
    shares: float
    price: float
    cost_basis_ps: float
    long_term: bool
    tax_rate: float
    gross: float
    gain: float
    tax: float
    net: float
    net_price: float

    @property
    def drag(self) -> float:
        """Fraction of gross proceeds surrendered to tax."""
        return float(1.0 - self.net / self.gross) if self.gross else 0.0


def sale_proceeds(
    shares: float,
    price: float,
    cost_basis_ps: float,
    long_term: bool,
    profile: TaxProfile,
) -> SaleProceeds:
    """Gross and after-tax proceeds from selling `shares`.

    A loss produces a negative tax, i.e. the shelter value of harvesting it.
    """
    gross = float(shares * price)
    gain = float(shares * (price - cost_basis_ps))
    rate = profile.rate(long_term)
    tax = float(gain * rate)
    net = gross - tax
    return SaleProceeds(
        shares=float(shares),
        price=float(price),
        cost_basis_ps=float(cost_basis_ps),
        long_term=bool(long_term),
        tax_rate=rate,
        gross=gross,
        gain=gain,
        tax=tax,
        net=net,
        net_price=float(net / shares) if shares else 0.0,
    )


def required_replacement_return(
    hold_return: float,
    proceeds: SaleProceeds,
    horizon_years: float = 5.0,
) -> float:
    """Return a replacement must earn to beat holding, starting from the after-tax price.

    Selling hands the taxman part of the position, so the new idea compounds a
    smaller base. This is the hurdle that number implies over `horizon_years`.
    """
    if proceeds.net <= 0 or proceeds.gross <= 0 or horizon_years <= 0:
        return float("inf")
    ratio = proceeds.gross / proceeds.net
    return float((1.0 + hold_return) * ratio ** (1.0 / horizon_years) - 1.0)


def switch_is_justified(
    hold_return: float,
    alternative_return: float,
    proceeds: SaleProceeds,
    horizon_years: float = 5.0,
    hurdle: float = 0.02,
) -> bool:
    """True when the alternative clears the after-tax hurdle with room to spare."""
    return bool(alternative_return >= required_replacement_return(hold_return, proceeds, horizon_years) + hurdle)
