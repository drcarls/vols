import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from milk_pricing.sources.harris_teeter import parse_search, store_name, visible_text

PAGE = ("<div>Pickup at Village at Chestnut Street | 136 Merrimon Ave Weekly Specials"
        "<p>$2.99 Discounted From Harris Teeter 2% Reduced Fat Milk 1 gal SNAP EBT "
        "Sign In to Add $1.79 Harris Teeter Fat Free Skim Milk 1/2 gal SNAP EBT "
        "Sign In to Add</p></div>")


def test_store_name_is_captured():
    """Store follows the proxy exit and cannot be pinned, so every row is only
    interpretable alongside the store the page names."""
    assert store_name(PAGE) == "Village at Chestnut Street | 136 Merrimon Ave"


def test_parses_name_size_price():
    rows = parse_search(PAGE)
    assert len(rows) == 2
    assert rows[0] == {"name": "Harris Teeter 2% Reduced Fat Milk", "size": "1 gal",
                       "price": 2.99, "brand": "", "in_stock": True,
                       "id": "Harris Teeter 2% Reduced Fat Milk|1 gal"}
    assert rows[1]["price"] == 1.79
    assert rows[1]["size"] == "1/2 gal"


def test_was_price_is_not_picked_up():
    """A struck-through 'Discounted From $X' trails the real price; taking the
    larger number would silently inflate every discounted item."""
    page = ("<p>$2.99 Discounted From $4.19 Harris Teeter Vitamin D Whole Milk "
            "1 gal SNAP EBT Sign In to Add</p>")
    rows = parse_search(page)
    assert len(rows) == 1
    assert rows[0]["price"] == 2.99
    assert "4.19" not in rows[0]["name"]


def test_rate_limit_body_yields_nothing():
    assert parse_search("A global adaptive rate limit has been applied.") == []


def test_store_context_reads_zip_and_number():
    """SC ZIPs are 29xxx; the Pickup-at line alone never says which state."""
    from milk_pricing.sources.harris_teeter import store_context
    page = PAGE + '"postalCode":"29401""storeNumber":"00337"'
    c = store_context(page)
    assert c["zip"] == "29401"
    assert c["store_number"] == "00337"
    assert c["state_guess"] == "SC"


def test_state_guess_distinguishes_carolinas():
    from milk_pricing.sources.harris_teeter import store_context
    assert store_context('"postalCode":"28801"')["state_guess"] == "NC"
    assert store_context('"postalCode":"30076"')["state_guess"] == "GA"
    assert store_context('"postalCode":"99999"')["state_guess"] is None
