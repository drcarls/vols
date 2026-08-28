from datetime import date, timedelta

import pytest

from pari_mutuel_trader.portfolio.lots import FIFO, HIFO, LotLedger
from pari_mutuel_trader.valuation.tax import TaxProfile

TAX = TaxProfile(federal_long_term=0.20, federal_short_term=0.37, state=0.0, niit=0.038)
DAY = date(2026, 6, 1)


def test_hifo_relieves_the_highest_cost_lot_first():
    led = LotLedger(method=HIFO)
    led.buy("A", 0.02, 100.0, DAY)
    led.buy("A", 0.02, 150.0, DAY + timedelta(days=30))
    sales = led.sell("A", 0.02, 200.0, DAY + timedelta(days=60), TAX)
    assert [s.entry_price for s in sales] == [150.0]
    assert led.weight_of("A") == pytest.approx(0.02)


def test_fifo_relieves_the_oldest_lot_first():
    led = LotLedger(method=FIFO)
    led.buy("A", 0.02, 150.0, DAY)
    led.buy("A", 0.02, 100.0, DAY + timedelta(days=30))
    sales = led.sell("A", 0.02, 200.0, DAY + timedelta(days=60), TAX)
    assert [s.acquired for s in sales] == [DAY]


def test_hifo_realizes_less_gain_than_fifo():
    def realize(method):
        led = LotLedger(method=method)
        led.buy("A", 0.02, 100.0, DAY)
        led.buy("A", 0.02, 150.0, DAY + timedelta(days=30))
        return sum(s.gain for s in led.sell("A", 0.02, 200.0, DAY + timedelta(days=60), TAX))

    assert realize(HIFO) < realize(FIFO)


def test_gain_is_a_share_of_nav_and_a_loss_shelters():
    led = LotLedger(wash_sales=False)
    led.buy("A", 0.04, 100.0, DAY)
    win = led.sell("A", 0.04, 200.0, DAY + timedelta(days=10), TAX)[0]
    assert win.gain == pytest.approx(0.04 * 0.5)
    assert win.tax > 0

    led.buy("B", 0.04, 200.0, DAY)
    loss = led.sell("B", 0.04, 100.0, DAY + timedelta(days=10), TAX)[0]
    assert loss.gain == pytest.approx(-0.04)
    assert loss.tax < 0


def test_a_sale_spanning_lots_splits_the_weight():
    led = LotLedger(method=FIFO)
    led.buy("A", 0.02, 100.0, DAY)
    led.buy("A", 0.02, 120.0, DAY + timedelta(days=5))
    sales = led.sell("A", 0.03, 200.0, DAY + timedelta(days=10), TAX)
    assert sum(s.weight for s in sales) == pytest.approx(0.03)
    assert led.weight_of("A") == pytest.approx(0.01)


def test_holding_period_decides_the_rate():
    led = LotLedger(wash_sales=False)
    led.buy("A", 0.02, 100.0, DAY)
    short = led.sell("A", 0.02, 200.0, DAY + timedelta(days=100), TAX)[0]
    led.buy("B", 0.02, 100.0, DAY)
    long = led.sell("B", 0.02, 200.0, DAY + timedelta(days=400), TAX)[0]
    assert not short.long_term and long.long_term
    assert short.tax > long.tax


def test_a_repurchase_inside_the_window_washes_the_loss():
    led = LotLedger()
    led.buy("A", 0.04, 200.0, DAY)
    sale = led.sell("A", 0.04, 100.0, DAY + timedelta(days=10), TAX)[0]
    assert sale.tax < 0  # the credit is booked at the sale

    clawback = led.buy("A", 0.04, 100.0, DAY + timedelta(days=20))
    assert clawback == pytest.approx(-sale.tax)  # and taken straight back
    assert led.disallowed_loss == pytest.approx(abs(sale.gain))
    # The disallowed loss rides into the replacement lot's basis.
    assert led.lots["A"][0].price > 100.0


def test_a_repurchase_outside_the_window_keeps_the_loss():
    led = LotLedger()
    led.buy("A", 0.04, 200.0, DAY)
    led.sell("A", 0.04, 100.0, DAY + timedelta(days=10), TAX)
    clawback = led.buy("A", 0.04, 100.0, DAY + timedelta(days=45))
    assert clawback == 0.0
    assert led.disallowed_loss == 0.0
    assert led.lots["A"][0].price == 100.0


def test_a_winning_sale_is_never_washed():
    led = LotLedger()
    led.buy("A", 0.04, 100.0, DAY)
    led.sell("A", 0.04, 200.0, DAY + timedelta(days=10), TAX)
    assert led.buy("A", 0.04, 200.0, DAY + timedelta(days=12)) == 0.0


def test_wash_sales_can_be_switched_off():
    led = LotLedger(wash_sales=False)
    led.buy("A", 0.04, 200.0, DAY)
    led.sell("A", 0.04, 100.0, DAY + timedelta(days=10), TAX)
    assert led.buy("A", 0.04, 100.0, DAY + timedelta(days=12)) == 0.0
    assert led.disallowed_loss == 0.0
