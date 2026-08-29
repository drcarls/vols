"""The account level: what no individual sleeve can see on its own."""

from datetime import date

import pytest

from pari_mutuel_trader.account import (
    Account,
    Sleeve,
    account_opportunity_set,
    load_account,
    look_through_breaches,
    review_account,
    wash_sale_conflicts,
)
from pari_mutuel_trader.account.model import DISCRETIONARY, SYSTEMATIC
from pari_mutuel_trader.valuation.sell_rules import SellPolicy

ACCOUNT = "configs/account.example.yaml"
BOOK = "configs/positions.example.yaml"
SATELLITE = "configs/positions.satellite.example.yaml"
AS_OF = date(2026, 8, 28)


def test_account_loads_sleeves_tax_and_per_sleeve_policy():
    acct = load_account(ACCOUNT)
    names = [s.name for s in acct.sleeves]
    assert names == ["quant_sw50", "conviction_book", "dislocated_quality", "satellite_book"]
    assert acct.allocation_total() == pytest.approx(1.0)

    quant = next(s for s in acct.sleeves if s.name == "quant_sw50")
    book = next(s for s in acct.sleeves if s.name == "conviction_book")
    assert quant.kind == SYSTEMATIC and book.kind == DISCRETIONARY
    # Units differ by sleeve; the hurdle rates are inherited from the account.
    assert quant.policy.sizing == "relative"
    assert book.policy.sizing == "absolute"
    assert book.policy.required_return == 0.15
    # Tax is configured once, on the account.
    assert acct.tax.state == 0.05


def test_a_systematic_sleeve_contributes_weights_but_no_valuation_review():
    acct = load_account(ACCOUNT)
    payload = review_account(acct, as_of=AS_OF)
    quant = next(s for s in payload["sleeves"] if s["name"] == "quant_sw50")
    assert quant["decisions"] == []
    assert "no valuation assumptions" in quant["note"]
    assert quant["holdings"] > 0  # it still counts toward look-through


def test_look_through_scales_sleeve_weights_by_allocation():
    acct = load_account(ACCOUNT)
    exposure = acct.look_through()
    book = next(s for s in acct.sleeves if s.name == "conviction_book")
    veev = next(p for p in book.book().positions if p.symbol == "VEEV")
    assert exposure["VEEV"]["conviction_book"] == pytest.approx(veev.weight * book.allocation)


def test_a_name_two_sleeves_each_size_correctly_can_still_breach_the_account():
    """Neither sleeve is wrong on its own; only the sum is."""
    acct = load_account(ACCOUNT)
    payload = review_account(acct, as_of=AS_OF)
    breaches = {b["symbol"]: b for b in payload["look_through_breaches"]}

    pypl = breaches["PYPL"]
    assert set(pypl["sleeves"]) == {"conviction_book", "satellite_book"}
    assert all(z == "spring_loaded" for z in pypl["zones"].values())
    assert pypl["account_weight"] > pypl["limit"]
    assert pypl["account_weight"] == pytest.approx(sum(pypl["sleeves"].values()))


def test_breaches_are_ranked_by_how_far_over_they_are():
    payload = review_account(load_account(ACCOUNT), as_of=AS_OF)
    excess = [b["excess"] for b in payload["look_through_breaches"]]
    assert excess == sorted(excess, reverse=True)


def test_a_wash_sale_is_triggered_by_a_different_sleeve():
    payload = review_account(load_account(ACCOUNT), as_of=AS_OF)
    conflicts = {c["symbol"]: c for c in payload["wash_sale_conflicts"]}
    assert conflicts["FROG"]["sold_at_loss_by"] == ["satellite_book"]
    assert conflicts["FROG"]["held_or_bought_by"] == ["conviction_book"]


def test_a_sale_at_a_gain_is_not_a_wash_sale():
    """The conviction book also exits FROG, but at a profit."""
    acct = load_account(ACCOUNT)
    payload = review_account(acct, as_of=AS_OF)
    book = next(s for s in payload["sleeves"] if s["name"] == "conviction_book")
    frog = next(d for d in book["decisions"] if d["symbol"] == "FROG")
    assert frog["action"] == "exit"
    assert frog["gross_proceeds"] > 0
    assert "conviction_book" not in payload["wash_sale_conflicts"][0]["sold_at_loss_by"]


def test_no_conflict_when_only_one_sleeve_touches_the_name():
    acct = Account(sleeves=[Sleeve("solo", DISCRETIONARY, 1.0, positions_path=SATELLITE)])
    payload = review_account(acct, as_of=AS_OF)
    assert payload["wash_sale_conflicts"] == []


def test_the_opportunity_set_spans_sleeves():
    acct = load_account(ACCOUNT)
    shared = {c.symbol for c in account_opportunity_set(acct)}
    solo = {c.symbol for c in account_opportunity_set(
        Account(sleeves=[Sleeve("solo", DISCRETIONARY, 1.0, positions_path=SATELLITE)])
    )}
    assert solo < shared
    assert {"SNPS", "IOT"} <= shared  # reachable only through the other sleeve


def test_a_sleeve_is_measured_against_the_whole_account():
    """A trim benchmarked against one book's watchlist understates the alternative."""
    alone = review_account(
        Account(sleeves=[Sleeve("solo", DISCRETIONARY, 1.0, positions_path=SATELLITE)]), as_of=AS_OF
    )
    together = review_account(load_account(ACCOUNT), as_of=AS_OF)

    solo_pypl = next(d for d in alone["sleeves"][0]["decisions"] if d["symbol"] == "PYPL")
    joint_pypl = next(
        d for s in together["sleeves"] if s["name"] == "satellite_book"
        for d in s["decisions"] if d["symbol"] == "PYPL"
    )
    assert solo_pypl["best_alternative_return"] is None
    assert joint_pypl["best_alternative_return"] > 0.15


def test_the_account_tax_profile_overrides_whatever_a_book_declares():
    acct = load_account(ACCOUNT)
    payload = review_account(acct, as_of=AS_OF)
    book = next(s for s in payload["sleeves"] if s["name"] == "conviction_book")
    expected = acct.tax.rate(long_term=True)
    rates = {d["effective_tax_rate"] for d in book["decisions"]}
    assert expected in rates


def test_an_empty_account_reviews_cleanly():
    payload = review_account(Account(), as_of=AS_OF)
    assert payload["sleeves"] == []
    assert payload["look_through_breaches"] == []
    assert payload["wash_sale_conflicts"] == []
    assert payload["allocation_total"] == 0.0


def test_the_payload_is_serializable():
    import json

    json.loads(json.dumps(review_account(load_account(ACCOUNT), as_of=AS_OF)))


def test_relative_sizing_sleeves_defer_to_the_account_ceiling():
    """A sleeve with no absolute ceiling cannot set the account's limit."""
    acct = Account(
        sleeves=[
            Sleeve("a", DISCRETIONARY, 0.5, positions_path=BOOK, policy=SellPolicy(sizing="relative")),
        ],
        look_through_ceiling=0.02,
    )
    breaches = look_through_breaches(acct, {"a": []})
    assert all(b["limit"] == 0.02 for b in breaches)
    assert breaches


def test_wash_sale_scan_needs_a_realized_loss_not_just_a_sale():
    acct = load_account(ACCOUNT)
    payload = review_account(acct, as_of=AS_OF)
    sold = {c["symbol"] for c in wash_sale_conflicts(acct, {})}
    assert sold == set()  # no decisions in, no conflicts out
    assert payload["wash_sale_conflicts"]
