import pytest

from pari_mutuel_trader.valuation import (
    EXPENSIVE,
    FAIR,
    RICH,
    SPRING_LOADED,
    QualityProfile,
    ValuationInputs,
    classify_zone,
    implied_return,
    intrinsic_value,
    iv8,
    iv15,
    valuation_report,
)


def make_inputs(**kwargs) -> ValuationInputs:
    quality = QualityProfile(
        moat=kwargs.pop("moat", 0.8),
        roic=kwargs.pop("roic", 0.25),
        roic_stability=kwargs.pop("roic_stability", 0.8),
    )
    return ValuationInputs(owner_earnings_ps=kwargs.pop("owner_earnings_ps", 5.0), quality=quality, **kwargs)


def test_iv15_is_below_iv8():
    inputs = make_inputs()
    assert iv15(inputs) < iv8(inputs)


def test_value_falls_as_required_return_rises():
    inputs = make_inputs()
    values = [intrinsic_value(inputs, r) for r in (0.08, 0.10, 0.12, 0.15, 0.20)]
    assert values == sorted(values, reverse=True)


def test_required_return_must_exceed_terminal_growth():
    inputs = make_inputs(terminal_growth=0.03)
    with pytest.raises(ValueError):
        intrinsic_value(inputs, 0.03)


def test_durability_lengthens_the_compounding_window():
    wide = QualityProfile(moat=0.95, roic=0.30, roic_stability=0.9)
    narrow = QualityProfile(moat=0.15, roic=0.09, roic_stability=0.2)
    assert wide.competitive_advantage_period() > narrow.competitive_advantage_period()
    assert wide.terminal_roic() > narrow.terminal_roic()
    assert iv15(make_inputs(moat=0.95, roic=0.30, roic_stability=0.9)) > iv15(
        make_inputs(moat=0.15, roic=0.09, roic_stability=0.2)
    )


def test_growth_is_funded_out_of_earnings():
    """Growth at a low ROIC consumes the cash it would otherwise return."""
    cheap_growth = make_inputs(growth=0.12, roic=0.30, moat=0.5, roic_stability=0.5)
    dear_growth = make_inputs(growth=0.12, roic=0.13, moat=0.5, roic_stability=0.5)
    assert iv15(cheap_growth) > iv15(dear_growth)


def test_implied_return_recovers_the_hurdle_rate():
    inputs = make_inputs()
    for target in (0.09, 0.12, 0.15, 0.22):
        price = intrinsic_value(inputs, target)
        assert implied_return(price, inputs) == pytest.approx(target, abs=1e-3)


def test_zone_boundaries():
    assert classify_zone(50, 50, 120) == SPRING_LOADED
    assert classify_zone(80, 50, 120) == FAIR
    assert classify_zone(130, 50, 120, rich_band=0.15) == RICH
    assert classify_zone(150, 50, 120, rich_band=0.15) == EXPENSIVE


def test_report_levels_bracket_the_zones():
    inputs = make_inputs()
    report = valuation_report(iv15(inputs) * 1.5, inputs)
    assert report["add_level"] < report["iv15"] < report["trim_level"]
    assert report["zone"] == FAIR
