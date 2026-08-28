import pandas as pd

from pari_mutuel_trader.valuation import EXPENSIVE, RICH, SPRING_LOADED, SellPolicy
from pari_mutuel_trader.valuation.book import (
    build_redeploy_plan,
    decisions_frame,
    load_book,
    opportunity_set,
    review_book,
    run_review,
    summarize_review,
)
from pari_mutuel_trader.valuation.overlay import apply_valuation_caps, zone_caps, zones_from_frame

BOOK_PATH = "configs/positions.example.yaml"


def test_example_book_loads_with_weights_from_market_value():
    book = load_book(BOOK_PATH)
    assert {p.symbol for p in book.positions} == {"VEEV", "PYPL", "FROG", "CDNS"}
    assert book.market_value == sum(p.market_value for p in book.positions) + book.cash
    assert all(p.weight is not None for p in book.positions)
    assert sum(p.weight for p in book.positions) < 1.0  # cash is the remainder


def test_example_book_review_reproduces_the_intended_calls():
    book = load_book(BOOK_PATH)
    decisions = {d.symbol: d for d in review_book(book)}

    # Below IV8, so not expensive on its own terms - trimmed on opportunity cost.
    veev = decisions["VEEV"]
    assert veev.target_weight == book.policy.house_money_weight
    assert veev.best_alternative_return > veev.required_replacement_return

    # Cheap enough to keep, not cheap enough to add to.
    pypl = decisions["PYPL"]
    assert pypl.zone == SPRING_LOADED
    assert pypl.shares_to_sell == 0.0
    assert pypl.add_level < pypl.price

    # Rich with a thin moat: closed out.
    assert decisions["FROG"].zone == EXPENSIVE
    assert decisions["FROG"].target_weight == 0.0

    # Rich but durable: kept small.
    assert decisions["CDNS"].zone == RICH
    assert decisions["CDNS"].target_weight == book.policy.house_money_weight


def test_redeploy_plan_never_exceeds_what_was_harvested():
    book = load_book(BOOK_PATH)
    decisions = review_book(book)
    plan = build_redeploy_plan(book, decisions)
    allocated = sum(a["amount"] for a in plan["allocations"])
    assert allocated <= plan["harvested_after_tax"] + 1e-6
    assert allocated <= plan["deployable_capacity"] + 1e-6
    assert all(a["weight"] <= book.policy.conviction_weight + 1e-9 for a in plan["allocations"])
    assert {a["symbol"] for a in plan["allocations"]} <= {c.symbol for c in opportunity_set(book)}


def test_run_review_payload_is_serializable():
    payload = run_review(BOOK_PATH)
    assert set(payload) == {"summary", "decisions", "redeploy_plan"}
    assert payload["summary"]["positions"] == 4
    import json

    json.loads(json.dumps(payload))


def test_decisions_frame_flattens_notes():
    book = load_book(BOOK_PATH)
    frame = decisions_frame(review_book(book))
    assert isinstance(frame, pd.DataFrame)
    assert frame["notes"].map(lambda n: isinstance(n, str)).all()
    summary = summarize_review(book, review_book(book))
    assert sum(summary["actions"].values()) == len(book.positions)


def _frame(discounts, premiums):
    return pd.DataFrame(
        {"discount_to_iv15": discounts, "premium_to_iv8": premiums},
        index=["a", "b", "c", "d"],
    )


def test_zones_from_frame():
    zones = zones_from_frame(_frame([0.10, -0.20, -0.40, -0.60], [-0.5, -0.1, 0.05, 0.40]))
    assert list(zones) == [SPRING_LOADED, "fair", RICH, EXPENSIVE]


def test_valuation_caps_tighten_rich_names_and_renormalize():
    policy = SellPolicy()
    caps = zone_caps(_frame([0.10, -0.20, -0.40, -0.60], [-0.5, -0.1, 0.05, 0.40]), policy)
    weights = pd.Series(0.25, index=["a", "b", "c", "d"])
    capped = apply_valuation_caps(weights, caps, default_cap=0.05)
    assert float(capped.sum()) == 1.0
    assert capped["a"] > capped["b"] > capped["c"] > capped["d"]


def test_overlay_is_a_no_op_without_valuation_columns():
    weights = pd.Series([0.5, 0.5], index=["a", "b"])
    frame = pd.DataFrame({"close": [1.0, 2.0]}, index=["a", "b"])
    assert zone_caps(frame, SellPolicy()) is None
    assert apply_valuation_caps(weights, None, 0.05).equals(weights)
