from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from pari_mutuel_trader.valuation.tax import TaxProfile, is_long_term

HIFO = "hifo"
FIFO = "fifo"
WASH_SALE_DAYS = 30


@dataclass
class Lot:
    """A parcel of a position, held in portfolio-weight terms.

    The sleeve works in weights rather than shares, so a lot of weight `w` bought
    when the symbol traded at `price` is worth `w` of today's NAV and carries a
    cost basis of `w * price / current_price`.
    """

    weight: float
    price: float
    acquired: date


@dataclass
class RealizedSale:
    symbol: str
    weight: float
    entry_price: float
    exit_price: float
    acquired: date
    sold: date
    long_term: bool
    gain: float
    tax: float


@dataclass
class LossSale:
    symbol: str
    sold: date
    loss: float
    credit: float


@dataclass
class LotLedger:
    """Open lots per symbol, and the tax realized when they are closed.

    Lots are relieved highest-cost-first by default, which is what a holder who
    cares about the after-tax price would do: it realizes the smallest gain, and
    leaves the oldest cheap stock alone to season into long-term treatment.

    A rotating sleeve sells losers constantly and buys some of them back within
    weeks. Left uncorrected that books a tax credit the holder never receives, so
    a repurchase inside the wash-sale window disallows the loss and rolls it into
    the basis of the replacement lot.
    """

    method: str = HIFO
    wash_sales: bool = True
    lots: dict[str, list[Lot]] = field(default_factory=dict)
    loss_sales: list[LossSale] = field(default_factory=list)
    disallowed_loss: float = 0.0

    def weight_of(self, symbol: str) -> float:
        return float(sum(lot.weight for lot in self.lots.get(symbol, [])))

    def symbols(self) -> list[str]:
        return [s for s, lots in self.lots.items() if lots]

    def buy(self, symbol: str, weight: float, price: float, on: date) -> float:
        """Open a lot. Returns tax to claw back for any loss this repurchase washes."""
        if weight <= 0 or price <= 0:
            return 0.0
        basis = float(price)
        clawback = 0.0
        if self.wash_sales:
            washed = [
                s for s in self.loss_sales
                if s.symbol == symbol and 0 <= (on - s.sold).days <= WASH_SALE_DAYS
            ]
            if washed:
                loss = sum(s.loss for s in washed)          # negative
                clawback = -sum(s.credit for s in washed)   # credit taken back
                self.disallowed_loss += abs(loss)
                # The disallowed loss rides into the replacement lot's basis.
                basis = price * (1.0 + abs(loss) / weight)
                self.loss_sales = [s for s in self.loss_sales if s not in washed]
        self.lots.setdefault(symbol, []).append(Lot(float(weight), basis, on))
        return float(clawback)

    def _order(self, lots: list[Lot]) -> list[Lot]:
        if self.method == FIFO:
            return sorted(lots, key=lambda lot: lot.acquired)
        return sorted(lots, key=lambda lot: lot.price, reverse=True)

    def sell(
        self,
        symbol: str,
        weight: float,
        price: float,
        on: date,
        profile: TaxProfile,
    ) -> list[RealizedSale]:
        """Relieve `weight` of the position and return what each closed lot realized."""
        remaining = float(weight)
        sales: list[RealizedSale] = []
        open_lots = self.lots.get(symbol, [])
        for lot in self._order(open_lots):
            if remaining <= 1e-12:
                break
            taken = min(lot.weight, remaining)
            lot.weight -= taken
            remaining -= taken
            long_term = is_long_term(lot.acquired, on)
            # Gain accrued inside a position now worth `taken` of NAV.
            gain = taken * (1.0 - lot.price / price) if price > 0 else 0.0
            tax = gain * profile.rate(long_term)
            if self.wash_sales and gain < 0:
                self.loss_sales.append(LossSale(symbol, on, float(gain), float(tax)))
            sales.append(
                RealizedSale(
                    symbol=symbol,
                    weight=taken,
                    entry_price=lot.price,
                    exit_price=float(price),
                    acquired=lot.acquired,
                    sold=on,
                    long_term=long_term,
                    gain=float(gain),
                    tax=float(tax),
                )
            )
        self.lots[symbol] = [lot for lot in open_lots if lot.weight > 1e-12]
        return sales

    def unrealized_gain(self, symbol: str, price: float) -> float:
        """Accrued gain in the position, as a fraction of NAV."""
        if price <= 0:
            return 0.0
        return float(sum(lot.weight * (1.0 - lot.price / price) for lot in self.lots.get(symbol, [])))

    def newest_acquisition(self, symbol: str) -> date | None:
        lots = self.lots.get(symbol, [])
        return max((lot.acquired for lot in lots), default=None)
