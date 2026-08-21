import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from dataclasses import asdict
from milk_pricing import ladder
from milk_pricing.normalize import normalize_row


def o(name, size, price, retailer="walmart"):
    return asdict(normalize_row(
        {"name": name, "size": size, "price": price, "id": name}, retailer, "29201"))


def test_pack_size_penalty_is_per_gallon_not_per_unit():
    rows = [
        o("Great Value Whole Milk, Gallon", "128 fl oz", 3.46),
        o("Great Value Whole Milk, Half Gallon", "64 fl oz", 2.03),
    ]
    p = ladder.pack_size_penalty(rows)
    assert p["gallon"]["median_ppg"] == 3.46
    assert p["half gallon"]["median_ppg"] == 4.06
    assert p["half_gallon_premium_usd"] == 0.60


def test_segment_precedence_organic_beats_private_label():
    """An organic store-brand jug is an organic decision first; counting it in
    the private-label baseline would inflate the baseline and hide the premium."""
    seg = ladder.segment([o("Great Value Organic Whole Milk", "64 fl oz", 3.98)])
    assert list(seg) == ["organic"]


def test_tier_premium_against_baseline():
    rows = [
        o("Great Value Whole Milk, Gallon", "128 fl oz", 4.00),
        o("Horizon Organic Whole Milk", "64 fl oz", 4.00),
    ]
    t = ladder.tier_premiums(rows)
    assert t["baseline_private_label_ppg"] == 4.00
    assert t["organic"]["premium_pct"] == 100.0


def test_fat_spread_gallon_only():
    rows = [
        o("Great Value Whole Milk, Gallon", "128 fl oz", 3.52),
        o("Great Value Whole Milk, Half Gallon", "64 fl oz", 2.03),
        o("Great Value Fat-Free Milk, Gallon", "128 fl oz", 3.38),
    ]
    s = ladder.fat_tier_spread(rows)
    assert s == {"skim": 3.38, "whole": 3.52}   # half gallon excluded
