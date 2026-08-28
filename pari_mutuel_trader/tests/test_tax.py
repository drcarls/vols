from datetime import date

import pytest

from pari_mutuel_trader.valuation import (
    TaxProfile,
    days_to_long_term,
    is_long_term,
    required_replacement_return,
    sale_proceeds,
    switch_is_justified,
)

PROFILE = TaxProfile(federal_long_term=0.20, federal_short_term=0.37, state=0.05, niit=0.038)


def test_short_term_gain_is_taxed_harder():
    long_sale = sale_proceeds(100, 200.0, 100.0, True, PROFILE)
    short_sale = sale_proceeds(100, 200.0, 100.0, False, PROFILE)
    assert short_sale.net < long_sale.net
    assert long_sale.net_price < 200.0


def test_tax_lands_between_twenty_and_fifty_percent_of_the_gain():
    sale = sale_proceeds(100, 200.0, 100.0, True, PROFILE)
    assert 0.20 <= sale.tax / sale.gain <= 0.50
    assert sale.net == pytest.approx(sale.gross - sale.tax)


def test_a_loss_shelters_rather_than_costs():
    sale = sale_proceeds(100, 50.0, 80.0, True, PROFILE)
    assert sale.tax < 0
    assert sale.net_price > sale.price


def test_hurdle_exceeds_the_holding_return_when_there_is_a_gain():
    sale = sale_proceeds(100, 200.0, 100.0, True, PROFILE)
    hurdle = required_replacement_return(0.08, sale, horizon_years=5)
    assert hurdle > 0.08


def test_longer_horizons_dilute_the_tax_drag():
    sale = sale_proceeds(100, 200.0, 100.0, True, PROFILE)
    assert required_replacement_return(0.08, sale, 10) < required_replacement_return(0.08, sale, 3)


def test_switch_requires_clearing_the_hurdle_with_margin():
    sale = sale_proceeds(100, 200.0, 100.0, True, PROFILE)
    hurdle = required_replacement_return(0.08, sale, 5)
    assert not switch_is_justified(0.08, hurdle + 0.01, sale, 5, hurdle=0.02)
    assert switch_is_justified(0.08, hurdle + 0.03, sale, 5, hurdle=0.02)


def test_long_term_holding_period():
    as_of = date(2026, 8, 28)
    assert not is_long_term(date(2026, 6, 1), as_of)
    assert is_long_term(date(2024, 1, 1), as_of)
    assert days_to_long_term(date(2026, 6, 1), as_of) == 366 - 88
    assert days_to_long_term(date(2024, 1, 1), as_of) == 0
