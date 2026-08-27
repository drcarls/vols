"""Column mapping for third-party domain listing exports.

Every marketplace exports a different CSV shape. GoDaddy's inventory files,
Dynadot's auction lists, a Sedo report and an ExpiredDomains export all describe
the same facts under different headers, and hand-editing headers before every
import is both tedious and a good way to introduce a silent mistake.

So this maps a source file's columns onto the canonical schema by matching
against alias sets.

**Design decision worth defending: this proposes, it does not silently apply.**
A wrong column mapping is the most dangerous kind of error in this system - map
`renewal_price` onto `asking_price` and every downstream number is wrong while
looking entirely plausible. So ``propose_mapping`` returns what it would do,
including what it is unsure about and what it ignored, and the importer prints
that for inspection. Guessing is fine; guessing invisibly is not.

The alias sets are deliberately generic rather than vendor-specific schemas.
Claiming to know a given marketplace's exact current headers would be asserting
something unverified about a file that changes without notice; matching on
aliases degrades gracefully when a vendor renames a column, and reports the
miss rather than mapping it wrong.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

# Canonical field -> header spellings that mean it. Lowercased, non-alphanumeric
# stripped, so "Buy Now Price" and "buy_now_price" both match "buynowprice".
CANONICAL_ALIASES: dict[str, set[str]] = {
    "domain": {
        "domain", "domainname", "name", "fqdn", "url", "domains", "sld",
    },
    "asking_price": {
        "askingprice", "price", "buynow", "buynowprice", "bin", "binprice",
        "buyitnow", "buyitnowprice", "listprice", "listingprice", "saleprice",
        "priceusd", "askprice", "asking", "fixedprice",
    },
    "current_bid": {
        "currentbid", "bid", "highbid", "highestbid", "currentprice",
        "leadingbid", "bidprice", "currentbidusd", "auctionprice",
    },
    "bid_count": {
        "bidcount", "bids", "numbids", "numberofbids", "totalbids", "bidders",
    },
    "auction_end_date": {
        "auctionenddate", "endtime", "enddate", "auctionend", "expires",
        "timeleft", "closingdate", "closetime", "endsat", "auctionendtime",
    },
    "expiration_date": {
        "expirationdate", "expirydate", "expiry", "expiresat", "renewaldate",
        "domainexpiration", "expdate",
    },
    "listing_type": {
        "listingtype", "type", "auctiontype", "saletype", "listing", "category",
        "producttype",
    },
    "source": {
        "source", "venue", "marketplace", "platform", "registrarmarket", "site",
    },
    "registrar": {
        "registrar", "registrarname", "sponsoringregistrar", "currentregistrar",
    },
    "traffic": {
        "traffic", "monthlytraffic", "visitors", "monthlyvisitors", "pageviews",
        "estimatedtraffic", "uniques",
    },
}

# Headers that look like a price or a date but mean something we must NOT map.
# Mapping `renewal_price` onto `asking_price` would corrupt every ROI in the
# system while looking completely normal, so these are refused by name.
DANGEROUS_LOOKALIKES: dict[str, str] = {
    "renewalprice": "the cost to renew, not to acquire",
    "renewalcost": "the cost to renew, not to acquire",
    "renewfee": "the cost to renew, not to acquire",
    "transferprice": "the cost to transfer, not the asking price",
    "restoreprice": "the redemption fee, not the asking price",
    "estimatedvalue": "an appraisal, not a price anyone is asking",
    "appraisal": "an appraisal, not a price anyone is asking",
    "estibot": "a third-party appraisal, not a price",
    "valuation": "an appraisal, not a price anyone is asking",
    "godaddyvalue": "a third-party appraisal, not a price",
    "minimumbid": "a reserve, not the current bid",
    "reserveprice": "a reserve, not the current bid",
}

REQUIRED = {"domain"}

# Headers that mark a file as a record of COMPLETED sales rather than live
# inventory. Importing a NameBio-style sales export as listings would read
# historical clearing prices as today's asking prices - the model would then
# "discover" that every domain is priced exactly at its market value, and the
# whole ranking would be noise. Worth an explicit check.
SALES_HISTORY_SIGNALS = {
    "saledate", "datesold", "solddate", "soldon", "salestime", "closedate",
    "transactiondate", "sold", "soldprice", "salesprice", "winningbid",
}


def normalise_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(header).strip().lower())


@dataclass
class MappingProposal:
    """What the mapper would do, and what it is unsure about."""

    mapping: dict[str, str] = field(default_factory=dict)      # source -> canonical
    unmapped: list[str] = field(default_factory=list)
    ambiguous: dict[str, list[str]] = field(default_factory=dict)  # canonical -> sources
    refused: dict[str, str] = field(default_factory=dict)      # source -> reason
    missing_required: list[str] = field(default_factory=list)
    looks_like_sales_history: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def usable(self) -> bool:
        """Safe to import without a human resolving something first.

        Ambiguity counts as unusable. An ambiguous price column is dropped
        rather than guessed, and an import that silently proceeds without a
        price looks successful while producing listings no ROI can be computed
        for - so the ambiguity has to stop the import, not just warn.
        """
        return (not self.missing_required
                and not self.looks_like_sales_history
                and not self.ambiguous)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__) | {"usable": self.usable}

    def describe(self) -> str:
        lines = ["proposed column mapping:"]
        for source, canonical in sorted(self.mapping.items(),
                                        key=lambda kv: kv[1]):
            lines.append(f"  {source:<28s} -> {canonical}")
        for source, reason in sorted(self.refused.items()):
            lines.append(f"  {source:<28s} -> REFUSED ({reason})")
        for source in sorted(self.unmapped):
            lines.append(f"  {source:<28s} -> ignored (kept on the raw row)")
        for warning in self.warnings:
            lines.append(f"  ! {warning}")
        if self.missing_required:
            lines.append(f"  ! MISSING REQUIRED: "
                         f"{', '.join(self.missing_required)}")
        return "\n".join(lines)


def propose_mapping(columns: list[str]) -> MappingProposal:
    """Work out which source columns correspond to canonical fields.

    Never resolves an ambiguity on its own: if two columns both look like the
    asking price, both are reported and neither is mapped. A human picking the
    right one takes a moment; a wrong guess corrupts a whole cohort.
    """
    proposal = MappingProposal()
    candidates: dict[str, list[str]] = {}

    for column in columns:
        key = normalise_header(column)
        if not key:
            continue
        if key in DANGEROUS_LOOKALIKES:
            proposal.refused[column] = DANGEROUS_LOOKALIKES[key]
            continue
        matched = [canonical for canonical, aliases in CANONICAL_ALIASES.items()
                   if key in aliases]
        if not matched:
            proposal.unmapped.append(column)
            continue
        if len(matched) > 1:
            # One header matching several canonical fields means the alias sets
            # overlap - a bug here, not in the file.
            proposal.warnings.append(
                f"column {column!r} matches several canonical fields "
                f"({', '.join(matched)}); alias sets overlap and need fixing")
        candidates.setdefault(matched[0], []).append(column)

    for canonical, sources in candidates.items():
        if len(sources) == 1:
            proposal.mapping[sources[0]] = canonical
        else:
            proposal.ambiguous[canonical] = sorted(sources)
            proposal.warnings.append(
                f"{len(sources)} columns could be {canonical!r} "
                f"({', '.join(sorted(sources))}); none mapped - choose one "
                f"explicitly with --map {sources[0]}={canonical}")

    mapped_canonicals = set(proposal.mapping.values())
    proposal.missing_required = sorted(REQUIRED - mapped_canonicals)

    keys = {normalise_header(c) for c in columns}
    sales_hits = sorted(keys & SALES_HISTORY_SIGNALS)
    if sales_hits:
        proposal.looks_like_sales_history = True
        proposal.warnings.append(
            f"THIS LOOKS LIKE A COMPLETED-SALES EXPORT, not live inventory "
            f"(found: {', '.join(sales_hits)}). Prices in it are what domains "
            f"SOLD for, not what anyone is asking today. Load it as comparable "
            f"sales with scripts/load_comparables.py instead; importing it as "
            f"listings would make every domain look fairly priced and turn the "
            f"whole ranking into noise.")

    if "asking_price" not in mapped_canonicals and "current_bid" not in mapped_canonicals:
        proposal.warnings.append(
            "no price column was identified. Listings will import with price "
            "MISSING, and no ROI, maximum bid or paper position is computable "
            "for them.")
    if "source" not in mapped_canonicals:
        proposal.warnings.append(
            "no venue/source column; pass --source-label to record where this "
            "inventory came from.")
    return proposal


def apply_mapping(frame: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Rename source columns onto canonical names, keeping everything else.

    Unmapped columns are retained under their original names so they survive
    onto the listing's ``raw_row``. Nothing from the source file is discarded.
    """
    renamed = frame.rename(columns=dict(mapping))
    # A canonical name colliding with an untouched source column would silently
    # produce duplicate columns; keep the mapped one.
    return renamed.loc[:, ~renamed.columns.duplicated(keep="first")]


def parse_overrides(pairs: list[str]) -> dict[str, str]:
    """Parse ``--map source=canonical`` arguments."""
    overrides: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"--map expects source=canonical, got {pair!r}")
        source, canonical = pair.split("=", 1)
        canonical = canonical.strip()
        if canonical not in CANONICAL_ALIASES:
            raise ValueError(
                f"unknown canonical field {canonical!r}; valid fields: "
                f"{', '.join(sorted(CANONICAL_ALIASES))}")
        overrides[source.strip()] = canonical
    return overrides
