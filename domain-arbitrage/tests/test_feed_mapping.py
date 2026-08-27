"""Third-party feed column mapping.

A wrong column mapping is the most dangerous error available in this system:
map a renewal price or an appraisal onto ``asking_price`` and every downstream
number is wrong while looking entirely plausible. These tests pin the refusals.
"""

import pandas as pd
import pytest
from sqlalchemy import select

from app.models.core import Listing
from app.services.feed_mapping import (CANONICAL_ALIASES, apply_mapping,
                                       normalise_header, parse_overrides,
                                       propose_mapping)
from app.services.ingest import ingest_dataframe


@pytest.mark.parametrize("header,expected", [
    ("Buy Now Price", "buynowprice"), ("domain_name", "domainname"),
    ("  Current Bid  ", "currentbid"), ("BID-COUNT", "bidcount"),
])
def test_header_normalisation(header, expected):
    assert normalise_header(header) == expected


def test_alias_sets_do_not_overlap():
    """An overlapping alias would make a column's mapping order-dependent."""
    seen: dict[str, str] = {}
    for canonical, aliases in CANONICAL_ALIASES.items():
        for alias in aliases:
            assert alias not in seen, \
                f"{alias!r} claimed by both {seen.get(alias)} and {canonical}"
            seen[alias] = canonical


def test_maps_a_typical_auction_export():
    proposal = propose_mapping(
        ["Domain", "Current Bid", "Bids", "Auction End Time", "Traffic"])
    assert proposal.usable
    assert proposal.mapping["Domain"] == "domain"
    assert proposal.mapping["Current Bid"] == "current_bid"
    assert proposal.mapping["Bids"] == "bid_count"
    assert proposal.mapping["Auction End Time"] == "auction_end_date"


def test_maps_a_typical_marketplace_export():
    proposal = propose_mapping(
        ["domain_name", "Buy Now Price", "Listing Type", "Venue", "Registrar"])
    assert proposal.usable
    assert proposal.mapping["Buy Now Price"] == "asking_price"
    assert proposal.mapping["Venue"] == "source"


@pytest.mark.parametrize("header,fragment", [
    ("Renewal Price", "renew"),
    ("renewal_cost", "renew"),
    ("Estimated Value", "appraisal"),
    ("GoDaddy Value", "appraisal"),
    ("appraisal", "appraisal"),
    ("Minimum Bid", "reserve"),
    ("Reserve Price", "reserve"),
    ("Transfer Price", "transfer"),
])
def test_dangerous_lookalikes_are_refused_not_mapped(header, fragment):
    """These are the columns that would corrupt every number silently."""
    proposal = propose_mapping(["domain", header])
    assert header in proposal.refused
    assert fragment in proposal.refused[header]
    assert header not in proposal.mapping
    assert "asking_price" not in proposal.mapping.values()
    assert "current_bid" not in proposal.mapping.values()


def test_ambiguity_is_reported_and_neither_column_is_mapped():
    proposal = propose_mapping(["domain", "price", "asking_price"])
    assert "asking_price" in proposal.ambiguous
    assert set(proposal.ambiguous["asking_price"]) == {"price", "asking_price"}
    assert "asking_price" not in proposal.mapping.values()
    assert any("choose one explicitly" in w for w in proposal.warnings)
    assert proposal.usable is False, \
        "an unresolved ambiguity must block an automatic import, not just warn"


def test_missing_domain_column_makes_the_file_unusable():
    proposal = propose_mapping(["sale_price", "venue"])
    assert proposal.usable is False
    assert proposal.missing_required == ["domain"]


def test_missing_price_column_is_warned():
    proposal = propose_mapping(["domain", "registrar"])
    assert proposal.usable
    assert any("no price column" in w for w in proposal.warnings)


def test_completed_sales_export_is_detected_and_refused():
    """Importing sold prices as asking prices would make every domain look
    fairly priced and turn the ranking into noise."""
    proposal = propose_mapping(["domain", "sale_price", "sale_date", "venue"])
    assert proposal.looks_like_sales_history is True
    assert proposal.usable is False
    assert any("COMPLETED-SALES EXPORT" in w for w in proposal.warnings)
    assert any("load_comparables" in w for w in proposal.warnings)


def test_live_inventory_is_not_mistaken_for_sales_history():
    proposal = propose_mapping(
        ["domain", "asking_price", "auction_end_date", "source"])
    assert proposal.looks_like_sales_history is False
    assert proposal.usable is True


def test_apply_mapping_keeps_unmapped_columns():
    frame = pd.DataFrame({"Domain": ["a.com"], "Current Bid": [10],
                          "Renewal Price": [21.99]})
    mapped = apply_mapping(frame, {"Domain": "domain", "Current Bid": "current_bid"})
    assert list(mapped.columns) == ["domain", "current_bid", "Renewal Price"]


def test_apply_mapping_does_not_duplicate_a_canonical_column():
    frame = pd.DataFrame({"Domain": ["a.com"], "domain": ["b.com"]})
    mapped = apply_mapping(frame, {"Domain": "domain"})
    assert list(mapped.columns).count("domain") == 1


def test_parse_overrides():
    assert parse_overrides(["Price=asking_price"]) == {"Price": "asking_price"}
    with pytest.raises(ValueError, match="source=canonical"):
        parse_overrides(["nonsense"])
    with pytest.raises(ValueError, match="unknown canonical field"):
        parse_overrides(["Price=not_a_field"])


# --------------------------------------------------------------------------
# integration with ingest
# --------------------------------------------------------------------------

VENDOR_FRAME = pd.DataFrame({
    "Domain": ["fleetanalytics.com", "berlinroofing.com"],
    "Current Bid": ["1250", "425"],
    "Bids": ["14", "3"],
    "Auction End Time": ["2026-09-12", "2026-09-10"],
    "Renewal Price": ["21.99", "21.99"],
    "Estimated Value": ["14000", "9000"],
})


def test_auto_map_imports_a_vendor_shaped_file(db):
    report = ingest_dataframe(db, VENDOR_FRAME.copy(), filename="vendor.csv",
                              source_label="testvendor", auto_map=True)
    assert report.rows_accepted == 2
    assert report.column_mapping["Current Bid"] == "current_bid"

    listings = db.execute(select(Listing)).scalars().all()
    assert {l.current_bid for l in listings} == {1250.0, 425.0}
    for listing in listings:
        assert listing.asking_price is None, \
            "a refused appraisal or renewal price must never become a price"
        assert listing.bid_count in {14, 3}


def test_refused_columns_survive_on_the_raw_row(db):
    ingest_dataframe(db, VENDOR_FRAME.copy(), filename="vendor.csv",
                     source_label="testvendor", auto_map=True)
    listing = db.execute(select(Listing)).scalars().first()
    kept = {k.lower().replace(" ", "_") for k in listing.raw_row}
    assert "renewal_price" in kept
    assert "estimated_value" in kept


def test_auto_map_refuses_an_ambiguous_file_rather_than_guessing(db):
    frame = pd.DataFrame({"domain": ["a.com"], "price": ["10"],
                          "asking_price": ["20"]})
    with pytest.raises(ValueError, match="cannot import this file"):
        ingest_dataframe(db, frame, filename="ambiguous.csv", auto_map=True)


def test_explicit_override_resolves_the_ambiguity(db):
    frame = pd.DataFrame({"domain": ["a.com"], "price": ["10"],
                          "asking_price": ["20"]})
    report = ingest_dataframe(db, frame, filename="ambiguous.csv",
                              column_mapping={"asking_price": "asking_price"})
    assert report.rows_accepted == 1
    listing = db.execute(select(Listing)).scalars().one()
    assert listing.asking_price == 20.0
