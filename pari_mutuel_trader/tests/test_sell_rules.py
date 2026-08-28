from datetime import date

from pari_mutuel_trader.valuation import (
    ADD,
    EXIT,
    EXPENSIVE,
    FAIR,
    HOLD,
    SPRING_LOADED,
    Position,
    QualityProfile,
    SellPolicy,
    TaxProfile,
    TRIM_TO_HOUSE_MONEY,
    ValuationInputs,
    intrinsic_value,
    iv15,
    review_position,
)

AS_OF = date(2026, 8, 28)
POLICY = SellPolicy()
TAX = TaxProfile(state=0.05)


def franchise(moat=0.88, roic=0.30, roic_stability=0.85, growth=0.15, owner_earnings_ps=6.0):
    return ValuationInputs(
        owner_earnings_ps=owner_earnings_ps,
        growth=growth,
        quality=QualityProfile(moat=moat, roic=roic, roic_stability=roic_stability),
    )


def position_at(price, inputs, weight=0.12, cost_basis_ps=None, acquired=date(2023, 1, 10), **kwargs):
    return Position(
        symbol="TEST",
        shares=1000,
        cost_basis_ps=cost_basis_ps if cost_basis_ps is not None else price / 2,
        price=price,
        inputs=inputs,
        acquired=acquired,
        weight=weight,
        **kwargs,
    )


def test_below_the_add_level_builds_the_position():
    inputs = franchise()
    price = intrinsic_value(inputs, POLICY.required_return + POLICY.add_margin) * 0.95
    decision = review_position(position_at(price, inputs, weight=0.02), POLICY, TAX, as_of=AS_OF)
    assert decision.zone == SPRING_LOADED
    assert decision.action == ADD
    assert decision.target_weight == POLICY.conviction_weight


def test_between_the_add_level_and_iv15_it_only_holds():
    """Being cheap is enough to keep a position, not to add to one."""
    inputs = franchise()
    price = 0.5 * (intrinsic_value(inputs, POLICY.required_return + POLICY.add_margin) + iv15(inputs))
    decision = review_position(position_at(price, inputs, weight=0.02), POLICY, TAX, as_of=AS_OF)
    assert decision.zone == SPRING_LOADED
    assert decision.action == HOLD
    assert decision.add_level < price


def test_expensive_and_durable_keeps_a_house_money_stake():
    inputs = franchise()
    price = intrinsic_value(inputs, POLICY.hold_return) * 1.5
    decision = review_position(position_at(price, inputs), POLICY, TAX, as_of=AS_OF)
    assert decision.zone == EXPENSIVE
    assert decision.action == TRIM_TO_HOUSE_MONEY
    assert decision.target_weight == POLICY.house_money_weight


def test_expensive_and_fragile_is_sold_outright():
    inputs = franchise(moat=0.2, roic=0.10, roic_stability=0.2)
    price = intrinsic_value(inputs, POLICY.hold_return) * 1.5
    decision = review_position(position_at(price, inputs), POLICY, TAX, as_of=AS_OF)
    assert decision.action == EXIT
    assert decision.target_weight == 0.0


def test_broken_thesis_overrides_a_cheap_price():
    inputs = franchise()
    price = iv15(inputs) * 0.5
    decision = review_position(position_at(price, inputs, thesis_intact=False), POLICY, TAX, as_of=AS_OF)
    assert decision.action == EXIT


def test_a_better_opportunity_cuts_a_fairly_valued_winner_to_house_money():
    """Nothing is wrong with the position; the capital is simply worth more elsewhere."""
    inputs = franchise()
    price = intrinsic_value(inputs, 0.09)
    held = position_at(price, inputs, weight=0.18, cost_basis_ps=price / 2)

    alone = review_position(held, POLICY, TAX, as_of=AS_OF)
    assert alone.zone == FAIR
    assert alone.target_weight == POLICY.core_weight

    switched = review_position(held, POLICY, TAX, best_alternative_return=0.20, as_of=AS_OF)
    assert switched.action == TRIM_TO_HOUSE_MONEY
    assert switched.target_weight == POLICY.house_money_weight
    assert switched.shares_to_sell > alone.shares_to_sell


def test_a_marginal_alternative_does_not_justify_the_tax():
    inputs = franchise()
    price = intrinsic_value(inputs, 0.09)
    held = position_at(price, inputs, weight=0.18, cost_basis_ps=price / 4)
    decision = review_position(held, POLICY, TAX, best_alternative_return=0.10, as_of=AS_OF)
    assert decision.target_weight == POLICY.core_weight
    assert decision.required_replacement_return > 0.10


def test_a_position_inside_its_zone_ceiling_is_left_alone():
    inputs = franchise()
    price = intrinsic_value(inputs, 0.09)
    held = position_at(price, inputs, weight=0.04, cost_basis_ps=price / 2)
    decision = review_position(held, POLICY, TAX, as_of=AS_OF)
    assert decision.zone == FAIR
    assert decision.action == HOLD
    assert decision.shares_to_sell == 0.0


def test_a_spring_loaded_name_keeps_its_capital():
    inputs = franchise()
    held = position_at(iv15(inputs) * 0.9, inputs, weight=0.18)
    decision = review_position(held, POLICY, TAX, best_alternative_return=0.30, as_of=AS_OF)
    assert decision.zone == SPRING_LOADED
    assert decision.shares_to_sell == 0.0


def test_a_short_term_gain_does_not_buy_time_in_an_expensive_name():
    inputs = franchise()
    price = intrinsic_value(inputs, POLICY.hold_return) * 1.5
    held = position_at(price, inputs, acquired=date(2026, 7, 1))
    decision = review_position(held, POLICY, TAX, as_of=AS_OF)
    assert decision.action == TRIM_TO_HOUSE_MONEY
    assert not decision.proceeds.long_term
    assert any("short-term gain accepted" in n for n in decision.notes)


def test_trim_sizes_the_sale_to_the_target_weight():
    inputs = franchise()
    price = intrinsic_value(inputs, POLICY.hold_return) * 1.5
    held = position_at(price, inputs, weight=0.12)
    decision = review_position(held, POLICY, TAX, as_of=AS_OF)
    expected = held.shares * (1 - POLICY.house_money_weight / 0.12)
    assert decision.shares_to_sell == expected
    assert decision.proceeds.gross == expected * price


def test_house_money_is_flagged_once_the_cost_is_back():
    inputs = franchise()
    price = intrinsic_value(inputs, POLICY.hold_return) * 1.5
    held = position_at(price, inputs, cost_basis_ps=price / 8)
    decision = review_position(held, POLICY, TAX, as_of=AS_OF)
    assert decision.house_money
    assert decision.capital_recovered > 1.0


def test_an_unheld_name_is_never_reported_as_a_sale():
    inputs = franchise(moat=0.2, roic=0.10, roic_stability=0.2)
    price = intrinsic_value(inputs, POLICY.hold_return) * 1.5
    decision = review_position(position_at(price, inputs, weight=0.0), POLICY, TAX, as_of=AS_OF)
    assert decision.action == HOLD
    assert decision.shares_to_sell == 0.0
