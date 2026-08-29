"""Tax status belongs to the wrapper the shares sit in, not the strategy trading them."""

from datetime import date

import pytest
import yaml

from pari_mutuel_trader.account import Account, Sleeve, load_account, review_account
from pari_mutuel_trader.account.model import DISCRETIONARY, SYSTEMATIC
from pari_mutuel_trader.backtest.engine import run_backtest
from pari_mutuel_trader.data.features import build_features
from pari_mutuel_trader.data.loaders import generate_sample_features, generate_sample_fundamentals
from pari_mutuel_trader.valuation import (
    Position,
    QualityProfile,
    SellPolicy,
    TaxProfile,
    ValuationInputs,
    intrinsic_value,
    required_replacement_return,
    review_position,
    sale_proceeds,
)
from pari_mutuel_trader.valuation.features import attach_valuation
from pari_mutuel_trader.valuation.tax import TAX_DEFERRED, TAX_FREE, TAXABLE, build_tax_profile

AS_OF = date(2026, 8, 28)
CONFIG = "configs/dislocated_quality.yaml"


# --- the profile ------------------------------------------------------------

def test_a_retirement_wrapper_zeroes_every_rate():
    for status in (TAX_DEFERRED, TAX_FREE):
        profile = TaxProfile(state=0.09, status=status)
        assert profile.exempt
        assert profile.rate(long_term=True) == 0.0
        assert profile.rate(long_term=False) == 0.0
    taxable = TaxProfile(state=0.09)
    assert not taxable.exempt and taxable.rate(long_term=False) > 0


def test_an_unknown_wrapper_is_rejected():
    with pytest.raises(ValueError, match="Unknown tax status"):
        TaxProfile(status="brokerage")


def test_status_survives_config_loading_as_a_string():
    profile = build_tax_profile({"status": TAX_DEFERRED, "state": "0.05"})
    assert profile.status == TAX_DEFERRED and profile.state == 0.05
    assert build_tax_profile({}).status == TAXABLE


def test_a_sale_inside_the_wrapper_realizes_nothing():
    sale = sale_proceeds(100, 200.0, 100.0, long_term=False, profile=TaxProfile(status=TAX_DEFERRED))
    assert sale.tax == 0.0
    assert sale.net == sale.gross
    assert sale.net_price == sale.price
    assert sale.drag == 0.0


def test_the_replacement_hurdle_collapses_to_the_return_on_offer():
    """The after-tax comparison is the whole sell discipline, and it has nothing to bite on."""
    taxed = sale_proceeds(100, 200.0, 100.0, False, TaxProfile(state=0.05))
    sheltered = sale_proceeds(100, 200.0, 100.0, False, TaxProfile(state=0.05, status=TAX_DEFERRED))
    assert required_replacement_return(0.08, sheltered, 5) == pytest.approx(0.08)
    assert required_replacement_return(0.08, taxed, 5) > 0.08


# --- the position review ----------------------------------------------------

def _position(price, weight=0.18, basis=None):
    inputs = ValuationInputs(6.0, 0.15, QualityProfile(0.88, 0.30, 0.85))
    return Position("TEST", 1000, basis if basis is not None else price / 2, price, inputs,
                    acquired=date(2026, 7, 1), weight=weight)


def test_a_switch_that_tax_blocked_goes_through_inside_the_wrapper():
    policy = SellPolicy()
    inputs = ValuationInputs(6.0, 0.15, QualityProfile(0.88, 0.30, 0.85))
    price = intrinsic_value(inputs, 0.09)
    held = Position("TEST", 1000, price / 4, price, inputs, acquired=date(2026, 7, 1), weight=0.18)

    taxed = review_position(held, policy, TaxProfile(state=0.05), best_alternative_return=0.12, as_of=AS_OF)
    sheltered = review_position(held, policy, TaxProfile(state=0.05, status=TAX_DEFERRED),
                                best_alternative_return=0.12, as_of=AS_OF)

    assert taxed.required_replacement_return > 0.12 >= sheltered.required_replacement_return
    assert sheltered.target_weight < taxed.target_weight


def test_the_holding_period_note_is_replaced_by_the_wrapper_note():
    inputs = ValuationInputs(6.0, 0.15, QualityProfile(0.88, 0.30, 0.85))
    price = intrinsic_value(inputs, 0.08) * 1.5   # expensive, so it trims
    held = _position(price)

    taxed = review_position(held, SellPolicy(), TaxProfile(), as_of=AS_OF)
    sheltered = review_position(held, SellPolicy(), TaxProfile(status=TAX_DEFERRED), as_of=AS_OF)

    assert any("short-term gain accepted" in n for n in taxed.notes)
    assert not any("short-term" in n for n in sheltered.notes)
    assert any("tax_deferred wrapper" in n for n in sheltered.notes)
    assert sheltered.after_tax_price == sheltered.price


# --- the sleeve -------------------------------------------------------------

def _sample(days=400, n_symbols=30):
    feat = build_features(generate_sample_features(days=days, n_symbols=n_symbols))
    return attach_valuation(feat, generate_sample_fundamentals(feat))


def test_the_sleeve_runs_the_tax_machinery_only_when_it_applies():
    cfg = yaml.safe_load(open(CONFIG))
    feat = _sample()

    sheltered = run_backtest(feat, dict(cfg, tax={**cfg["tax"], "status": TAX_DEFERRED})).metrics
    taxed = run_backtest(feat, dict(cfg, tax={**cfg["tax"], "status": TAXABLE})).metrics

    assert sheltered["tax_drag_annual"] == pytest.approx(0.0)
    assert sheltered["realized_tax"] == pytest.approx(0.0)
    assert sheltered["wash_sale_disallowed"] == 0.0
    assert sheltered["deferred_for_seasoning"] == 0
    assert taxed["tax_drag_annual"] != pytest.approx(0.0)


def test_trading_still_costs_inside_the_wrapper():
    """With tax gone this is the only friction left, so it must not be zero."""
    cfg = yaml.safe_load(open(CONFIG))
    feat = _sample()
    priced = run_backtest(feat, cfg).metrics
    free = run_backtest(feat, dict(cfg, portfolio={**cfg["portfolio"], "cost_bps": 0.0})).metrics

    assert priced["cost_drag_annual"] > 0
    assert priced["CAGR"] < priced["CAGR_gross"]
    assert free["cost_drag_annual"] == pytest.approx(0.0)
    assert free["CAGR"] == pytest.approx(free["CAGR_gross"])


def test_costs_rise_with_cadence_even_with_no_tax():
    cfg = yaml.safe_load(open(CONFIG))
    feat = _sample(days=800, n_symbols=40)
    fast = run_backtest(feat, dict(cfg, backtest={**cfg["backtest"], "rebalance_days": 5})).metrics
    slow = run_backtest(feat, dict(cfg, backtest={**cfg["backtest"], "rebalance_days": 252})).metrics
    assert fast["trading_cost_total"] > slow["trading_cost_total"]


# --- the account ------------------------------------------------------------

def test_a_sleeve_can_sit_in_its_own_wrapper():
    acct = load_account("configs/account.example.yaml")
    wrappers = acct.wrappers()
    assert wrappers["dislocated_quality"] == TAX_DEFERRED
    assert wrappers["conviction_book"] == TAXABLE
    # Rates are inherited even where they are inert.
    dq = next(s for s in acct.sleeves if s.name == "dislocated_quality")
    assert dq.tax.state == 0.05 and dq.exempt


def test_a_retirement_sleeve_can_never_be_the_seller_in_a_wash_sale():
    acct = Account(sleeves=[
        Sleeve("ira", DISCRETIONARY, 0.5, positions_path="configs/positions.satellite.example.yaml",
               tax=TaxProfile(status=TAX_DEFERRED)),
        Sleeve("brokerage", DISCRETIONARY, 0.5, positions_path="configs/positions.example.yaml"),
    ])
    payload = review_account(acct, as_of=AS_OF)
    for conflict in payload["wash_sale_conflicts"]:
        assert "ira" not in conflict["sold_at_loss_by"]


def test_a_loss_washed_into_a_retirement_wrapper_is_permanent():
    """The usual remedy - rolling the loss into the replacement basis - is unavailable."""
    deferred = Account(sleeves=[
        Sleeve("satellite", DISCRETIONARY, 0.5, positions_path="configs/positions.satellite.example.yaml"),
        Sleeve("book", DISCRETIONARY, 0.5, positions_path="configs/positions.example.yaml"),
    ])
    permanent = Account(sleeves=[
        Sleeve("satellite", DISCRETIONARY, 0.5, positions_path="configs/positions.satellite.example.yaml"),
        Sleeve("book", DISCRETIONARY, 0.5, positions_path="configs/positions.example.yaml",
               tax=TaxProfile(status=TAX_DEFERRED)),
    ])
    a = review_account(deferred, as_of=AS_OF)["wash_sale_conflicts"][0]
    b = review_account(permanent, as_of=AS_OF)["wash_sale_conflicts"][0]

    assert a["symbol"] == b["symbol"] == "FROG"
    assert a["severity"] == "deferred" and a["retirement_sleeves"] == []
    assert b["severity"] == "permanent" and b["retirement_sleeves"] == ["book"]


def test_permanent_conflicts_are_reported_first():
    acct = load_account("configs/account.example.yaml")
    payload = review_account(acct, as_of=AS_OF)
    severities = [c["severity"] for c in payload["wash_sale_conflicts"]]
    assert severities == sorted(severities, key=lambda s: s != "permanent")


def test_wrappers_are_reported_alongside_the_sleeves():
    payload = review_account(load_account("configs/account.example.yaml"), as_of=AS_OF)
    assert payload["wrappers"]["dislocated_quality"] == TAX_DEFERRED
    assert all("tax_status" in s for s in payload["sleeves"])
    assert next(s for s in payload["sleeves"] if s["kind"] == SYSTEMATIC)["tax_status"] in (TAXABLE, TAX_DEFERRED)
