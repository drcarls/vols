"""South Carolina market universe and retailer definitions.

The ZIP set is chosen to span SC's distinct trade areas rather than to be
exhaustive: milk is zone-priced, and zones track metro trade areas far more
closely than they track county or ZIP boundaries.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Market:
    """An SC trade area we sample. `zips` are representative, not exhaustive."""

    name: str
    region: str
    zips: tuple[str, ...]
    note: str = ""


# Eleven trade areas covering the Upstate, Midlands, Lowcountry, Pee Dee and
# the two out-of-state metro spillovers (Charlotte via Rock Hill, Augusta via
# Aiken) where SC stores are priced against another state's competitive set.
SC_MARKETS: tuple[Market, ...] = (
    Market("Columbia", "Midlands", ("29201", "29203", "29229"),
           "State capital; densest overlap of mass, conventional and discount."),
    Market("Charleston", "Lowcountry", ("29401", "29407", "29414", "29464"),
           "Highest-income SC metro; Publix and Harris Teeter over-index."),
    Market("Greenville", "Upstate", ("29601", "29607", "29615"),
           "Fastest-growing SC metro; Lidl and Aldi both present."),
    Market("Spartanburg", "Upstate", ("29301", "29306")),
    Market("Myrtle Beach", "Grand Strand", ("29577", "29572"),
           "Tourist demand; seasonal price and assortment swings."),
    Market("Rock Hill", "Charlotte metro", ("29730",),
           "Priced into the Charlotte NC competitive zone, not the SC one."),
    Market("Florence", "Pee Dee", ("29501",),
           "Thinner competitive set; a Walmart price-leadership market."),
    Market("Anderson", "Upstate", ("29621",)),
    Market("Sumter", "Midlands", ("29150",)),
    Market("Hilton Head", "Lowcountry", ("29926", "29902"),
           "Resort pricing; highest expected index in the state."),
    Market("Aiken", "CSRA", ("29801",),
           "Priced into the Augusta GA zone."),
)


@dataclass(frozen=True)
class Retailer:
    """An Instacart retailer slug plus the metadata the analysis needs."""

    slug: str            # Instacart URL slug, e.g. "walmart"
    name: str
    channel: str         # mass | conventional | hard_discount | club | drug
    private_labels: tuple[str, ...] = field(default=())
    markup: str = "unknown"   # "none" if Instacart shows shelf price verbatim


# Channel drives how a price is interpreted: a club unit price is not
# comparable to a drug-channel single without normalising both to $/gal AND
# acknowledging they serve different shopper missions.
RETAILERS: tuple[Retailer, ...] = (
    Retailer("walmart", "Walmart", "mass", ("Great Value",), markup="none"),
    Retailer("publix", "Publix", "conventional", ("Publix", "GreenWise")),
    Retailer("food-lion", "Food Lion", "conventional", ("Food Lion", "Nature's Promise")),
    Retailer("harris-teeter", "Harris Teeter", "conventional", ("Harris Teeter", "HT Traders")),
    Retailer("ingles", "Ingles", "conventional", ("Laura Lynn",)),
    Retailer("lowes-foods", "Lowes Foods", "conventional", ("Lowes Foods",)),
    Retailer("aldi", "Aldi", "hard_discount", ("Friendly Farms", "Simply Nature")),
    Retailer("lidl", "Lidl", "hard_discount", ("Lidl",)),
    Retailer("sams-club", "Sam's Club", "club", ("Member's Mark",)),
    Retailer("costco", "Costco", "club", ("Kirkland Signature",)),
    Retailer("walgreens", "Walgreens", "drug", ("Nice!",)),
    Retailer("cvs-pharmacy", "CVS", "drug", ("Gold Emblem",)),
)

# KNOWN GAP — the dollar channel and rural independents are absent above.
#
# In small SC markets these ARE the grocery competitive set: Williston (29853),
# the highest Walmart milk price in the SC sample, has both a Dollar General and
# a Family Dollar. Because they were missing from RETAILERS, an early analysis
# read "not in our retailer list" as "no competition in the market" and drew a
# conclusion that had to be withdrawn.
#
# Collection status, tested:
#   Dollar General  — product sitemap readable (32k products) and its Bright
#                     Data dataset returns prices, but with no store or ZIP
#                     context, and the catalog defaults to non-Southeast
#                     regional dairy brands. National band, not an SC price.
#   Family Dollar   — fully client-rendered, no dataset exists. Not collectable.
#   Dollar Tree     — client-rendered, dataset has no discovery mode, sitemap
#                     host unreachable. Not collectable.
#   Piggly Wiggly   — unreachable.
# DG's measured gallon band ($3.20-$4.00) straddles Walmart's Williston price
# of $3.72, so the dollar channel cannot be assumed to price above Walmart.
UNMEASURED_CHANNELS: tuple[Retailer, ...] = (
    Retailer("dollar-general", "Dollar General", "dollar", ("Clover Valley",)),
    Retailer("family-dollar", "Family Dollar", "dollar", ("Family Gourmet",)),
    Retailer("dollar-tree", "Dollar Tree", "dollar", ()),
    Retailer("piggly-wiggly", "Piggly Wiggly", "rural_independent", ()),
    Retailer("iga", "IGA", "rural_independent", ()),
)

BY_SLUG = {r.slug: r for r in RETAILERS}
ALL_ZIPS = tuple(z for m in SC_MARKETS for z in m.zips)
MARKET_OF_ZIP = {z: m.name for m in SC_MARKETS for z in m.zips}


def private_label_brands() -> set[str]:
    return {pl.lower() for r in RETAILERS for pl in r.private_labels}
