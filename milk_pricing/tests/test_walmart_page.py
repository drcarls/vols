import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from milk_pricing.sources.walmart_page import read_shelf_price, Rejected

SKU = "10450114"


def page(item_id, price, cents=None, pad=True):
    body = f'"usItemId":"{item_id}"' + f'"priceString":"${price}"'
    if cents:
        body += f'"priceString":"{cents} ¢/fl oz"'
    body += '"storeId":"3081""city":"Sacramento""stateOrProvinceCode":"CA""postalCode":"95829"'
    return body + ("x" * 600 if pad else "")


def test_accepts_genuine_shelf_price():
    r = read_shelf_price(page(SKU, "3.52", "2.8"), SKU)
    assert r["price"] == 3.52
    assert r["state"] == "CA"
    assert r["price_per_gal"] == 3.52


def test_rejects_marketplace_substitution():
    """The $9.97 case: right title, right unit price, wrong listing."""
    with pytest.raises(Rejected, match="not 10450114"):
        read_shelf_price(page("498874357", "9.97", "7.8"), SKU)


def test_rejects_when_canonical_sku_is_merely_referenced():
    """The subtle variant: the marketplace seller's id is primary and the real
    SKU appears further down. Presence on the page is not identity."""
    html = ('"usItemId":"498874357""priceString":"$9.97""priceString":"7.8 ¢/fl oz"'
            f'"usItemId":"{SKU}"' + "x" * 600)
    with pytest.raises(Rejected, match="not 10450114"):
        read_shelf_price(html, SKU)


def test_rejects_price_contradicted_by_unit_price():
    with pytest.raises(Rejected, match="contradicts"):
        read_shelf_price(page(SKU, "6.26", "9.8"), SKU)


def test_rejects_blocked_response():
    with pytest.raises(Rejected, match="empty"):
        read_shelf_price("Premium permissions required", SKU)


def test_half_gallon_normalises_to_gallon():
    r = read_shelf_price(page(SKU, "2.03", "3.2"), SKU, size_fl_oz=64.0)
    assert r["price_per_gal"] == 4.06
