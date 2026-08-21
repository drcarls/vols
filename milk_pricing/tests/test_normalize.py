import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from milk_pricing.normalize import (
    parse_size_fl_oz, classify_category, classify_fat, normalize_row,
)


@pytest.mark.parametrize("text,expected_oz,expected_pack", [
    ("1 gal", 128.0, 1),
    ("gallon", 128.0, 1),
    ("half gallon", 64.0, 1),
    ("1/2 gal", 64.0, 1),
    ("64 fl oz", 64.0, 1),
    ("quart", 32.0, 1),
    ("1 pt", 16.0, 1),
    ("12 x 8 fl oz", 96.0, 12),
    ("40 x 16.9 fl oz", 676.0, 40),
    ("2 gal", 256.0, 1),
    ("", None, 1),
    ("assorted", None, 1),
])
def test_parse_size(text, expected_oz, expected_pack):
    oz, pack = parse_size_fl_oz(text)
    if expected_oz is None:
        assert oz is None
    else:
        assert oz == pytest.approx(expected_oz, rel=1e-3)
    assert pack == expected_pack


@pytest.mark.parametrize("name,cat", [
    ("Great Value Whole Milk", "dairy_white"),
    ("Great Value 2% Reduced Fat Milk", "dairy_white"),
    ("Silk Almond Milk Original", "plant"),
    ("Oatly Oat Milk", "plant"),
    ("Nesquik Chocolate Milk", "dairy_flavored"),
    ("Great Value Heavy Whipping Cream", "excluded"),
    ("Coffee mate Creamer", "excluded"),
    ("Land O Lakes Half & Half", "excluded"),
    ("Eagle Brand Sweetened Condensed Milk", "excluded"),
    ("Great Value Buttermilk", "excluded"),
])
def test_classify_category(name, cat):
    assert classify_category(name)[0] == cat


@pytest.mark.parametrize("name,fat", [
    ("Great Value Whole Milk", "whole"),
    ("Vitamin D Milk", "whole"),
    ("2% Reduced Fat Milk", "2%"),
    ("1% Lowfat Milk", "1%"),
    ("Fat Free Skim Milk", "skim"),
    ("Nonfat Milk", "skim"),
    ("Milk", None),
])
def test_classify_fat(name, fat):
    assert classify_fat(name) == fat


def test_price_per_gallon_half_gallon_doubles():
    o = normalize_row(
        {"name": "Great Value Whole Milk", "brand": "Great Value",
         "size": "64 fl oz", "price": 2.24, "id": "x"}, "walmart", "29201")
    assert o.price_per_gal == pytest.approx(4.48)
    assert o.fat == "whole"
    assert o.is_private_label is True
    assert o.market == "Columbia"


def test_national_brand_not_flagged_private_label():
    o = normalize_row(
        {"name": "Fairlife 2% Ultra-Filtered Milk", "brand": "fairlife",
         "size": "52 fl oz", "price": 4.98}, "walmart", "29407")
    assert o.is_private_label is False
    assert o.is_ultrafiltered is True
    assert o.fat == "2%"
    assert o.market == "Charleston"


def test_organic_and_lactose_flags():
    o = normalize_row(
        {"name": "Horizon Organic Whole Milk", "brand": "Horizon",
         "size": "1 gal", "price": 9.48}, "publix", "29601")
    assert o.is_organic is True
    lf = normalize_row(
        {"name": "Lactaid Whole Lactose Free Milk", "brand": "Lactaid",
         "size": "96 fl oz", "price": 6.29}, "publix", "29601")
    assert lf.is_lactose_free is True


def test_unparseable_size_yields_no_ppg():
    o = normalize_row({"name": "Milk", "size": "each", "price": 3.0},
                      "aldi", "29201")
    assert o.price_per_gal is None
