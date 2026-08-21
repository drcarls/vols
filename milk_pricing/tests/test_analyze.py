import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from milk_pricing.analyze import (
    comparable_set, market_table, recommendations, walmart_zone_dispersion,
)
from milk_pricing.normalize import normalize_row


def obs(retailer, zip_code, name, size, price, **kw):
    d = {"name": name, "size": size, "price": price, "id": name}
    d.update(kw)
    from dataclasses import asdict
    return asdict(normalize_row(d, retailer, zip_code))


def test_comparable_set_filters_noise():
    rows = [
        obs("walmart", "29201", "Great Value Whole Milk", "1 gal", 3.24),
        obs("walmart", "29201", "Silk Almond Milk", "64 fl oz", 3.99),
        obs("walmart", "29201", "Horizon Organic Whole Milk", "1 gal", 9.48),
        obs("walmart", "29201", "Great Value Heavy Cream", "16 fl oz", 3.12),
        obs("walmart", "29201", "Great Value 2% Milk", "1 gal", 3.18),
    ]
    keep = comparable_set(rows, fat="whole")
    assert len(keep) == 1
    assert keep[0]["name"] == "Great Value Whole Milk"


def test_market_table_picks_cheapest_and_floor():
    rows = [
        obs("walmart", "29201", "Great Value Whole Milk", "1 gal", 3.44),
        obs("aldi", "29201", "Friendly Farms Whole Milk", "1 gal", 2.99),
        obs("publix", "29201", "Publix Whole Milk", "1 gal", 4.29),
    ]
    t = market_table(rows)["Columbia"]
    assert t["walmart"] == 3.44
    assert t["floor_slug"] == "aldi"
    assert t["gap_to_floor"] == 0.45
    assert t["cheapest_discount"] == 2.99
    assert t["cheapest_conventional"] == 4.29


def test_half_gallon_competitor_normalises_before_comparison():
    # Aldi half gallon at $1.60 is $3.20/gal — cheaper than Walmart's gallon.
    rows = [
        obs("walmart", "29201", "Great Value Whole Milk", "1 gal", 3.44),
        obs("aldi", "29201", "Friendly Farms Whole Milk", "64 fl oz", 1.60),
    ]
    t = market_table(rows)["Columbia"]
    assert t["floor_price"] == 3.20
    assert t["gap_to_floor"] == 0.24


def test_recommendation_exposed_and_margin_left():
    exposed = recommendations([
        obs("walmart", "29201", "Great Value Whole Milk", "1 gal", 3.99),
        obs("aldi", "29201", "Friendly Farms Whole Milk", "1 gal", 2.99),
    ])[0]
    assert exposed["action"] == "EXPOSED"
    assert exposed["suggested_price"] == 2.99

    left = recommendations([
        obs("walmart", "29501", "Great Value Whole Milk", "1 gal", 2.50),
        obs("food-lion", "29501", "Food Lion Whole Milk", "1 gal", 3.50),
    ])[0]
    assert left["action"] == "MARGIN_LEFT"


def test_recommendation_holds_inside_band():
    r = recommendations([
        obs("walmart", "29201", "Great Value Whole Milk", "1 gal", 3.05),
        obs("aldi", "29201", "Friendly Farms Whole Milk", "1 gal", 2.99),
    ])[0]
    assert r["action"] == "HOLD"


def test_dispersion_across_markets():
    rows = [
        obs("walmart", "29201", "Great Value Whole Milk", "1 gal", 3.24),
        obs("walmart", "29401", "Great Value Whole Milk", "1 gal", 3.68),
        obs("walmart", "29601", "Great Value Whole Milk", "1 gal", 3.44),
    ]
    d = walmart_zone_dispersion(rows)
    assert d["spread"] == 0.44
    assert d["n_markets"] == 3


def test_out_of_stock_excluded():
    rows = [
        obs("walmart", "29201", "Great Value Whole Milk", "1 gal", 2.50,
            in_stock=False),
        obs("walmart", "29201", "Great Value Whole Milk 2", "1 gal", 3.24),
    ]
    assert market_table(rows)["Columbia"]["walmart"] == 3.24


def test_club_and_drug_never_set_the_floor():
    """A Costco 2-gal pack is cheaper per gallon than any supercenter price,
    but it sits behind a membership fee and a 2-gallon commitment. It must be
    reported as context and must not drive a Walmart price recommendation."""
    rows = [
        obs("walmart", "29201", "Great Value Whole Milk", "1 gal", 3.24),
        obs("costco", "29201", "Kirkland Signature Whole Milk", "2 gal", 5.78),
        obs("cvs-pharmacy", "29201", "Gold Emblem Whole Milk", "64 fl oz", 2.79),
        obs("food-lion", "29201", "Food Lion Whole Milk", "1 gal", 3.29),
    ]
    t = market_table(rows)["Columbia"]
    assert t["cheapest_club"] == 2.89       # captured as context
    assert t["cheapest_drug"] == 5.58
    assert t["floor_slug"] == "food-lion"   # but the floor is shoppable
    assert t["floor_price"] == 3.29
    # -$0.05 vs the shoppable floor is inside the hold band. The point of the
    # test is that the $2.89 club price did not turn this into a false
    # "Walmart is 35c expensive" recommendation.
    assert recommendations(rows)[0]["action"] == "HOLD"


def test_index_excludes_club_distortion():
    rows = [
        obs("walmart", "29201", "Great Value Whole Milk", "1 gal", 3.24),
        obs("aldi", "29201", "Friendly Farms Whole Milk", "1 gal", 3.19),
        obs("costco", "29201", "Kirkland Signature Whole Milk", "2 gal", 4.00),
    ]
    t = market_table(rows)["Columbia"]
    assert t["index_vs_market"] == 101.6  # vs Aldi alone, not vs $2.00/gal club
