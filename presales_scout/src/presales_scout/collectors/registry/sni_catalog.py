from __future__ import annotations

"""Sector -> concrete SNI codes, for querying a company registry.

`nis2.py` maps an SNI *prefix* to a NIS2 sector (one direction, for scoring a
company we already have). Harvesting needs the reverse at full granularity: to
ask a registry "give me every company in these industries with >= 50 staff" we
must hand it the actual 5-digit SNI codes.

Energy and transport — Cyber Defencely's initial focus — are enumerated in
full. Other NIS2 sectors are listed at 2-digit prefix granularity; fill them in
the same way when the focus widens. SNI 2007 ~ EU NACE Rev. 2.
"""

# sector -> list of 5-digit SNI 2007 codes
SECTOR_SNI: dict[str, list[str]] = {
    "Energy": [
        "35110",  # Produktion av elektricitet
        "35120",  # Överföring av elektricitet (transmission)
        "35130",  # Distribution av elektricitet
        "35140",  # Handel med elektricitet
        "35210",  # Framställning av gas
        "35220",  # Distribution av gasformiga bränslen via ledningsnät
        "35230",  # Handel med gas via ledningsnät
        "35300",  # Försörjning av värme och kyla (district heating/cooling)
    ],
    "Transport": [
        "49100",  # Järnvägstransport, passagerare
        "49200",  # Järnvägstransport, gods
        "49310",  # Kollektivtrafik (urban/suburban passenger land transport)
        "49390",  # Annan landtransport av passagerare
        "49410",  # Vägtransport, godstrafik (road freight)
        "49500",  # Transport i rörsystem (pipeline)
        "50100",  # Sjötransport av passagerare
        "50200",  # Sjötransport av gods
        "50300",  # Transport på inre vattenvägar, passagerare
        "50400",  # Transport på inre vattenvägar, gods
        "51100",  # Lufttransport, passagerare
        "51210",  # Lufttransport, gods
        "52100",  # Magasinering och varulagring
        "52210",  # Stödtjänster till landtransport
        "52220",  # Stödtjänster till sjötransport
        "52230",  # Stödtjänster till lufttransport
        "52240",  # Godshantering (cargo handling)
        "52290",  # Övriga stödtjänster till transport
    ],
    # Below: 2-digit prefixes; enumerate to 5-digit when the focus widens.
    "Drinking water": ["36"],
    "Waste water": ["37"],
    "Waste management": ["38"],
    "Postal and courier": ["53"],
    "Digital infrastructure": ["61", "63"],
    "ICT service management": ["62"],
    "Health": ["86"],
}

# friendly CLI aliases -> canonical sector name
ALIASES: dict[str, str] = {
    "energy": "Energy",
    "el": "Energy",
    "power": "Energy",
    "transport": "Transport",
    "transportation": "Transport",
    "water": "Drinking water",
    "waste": "Waste management",
    "postal": "Postal and courier",
    "digital": "Digital infrastructure",
    "ict": "ICT service management",
    "health": "Health",
}


def resolve_sector(name: str) -> str | None:
    """Map a CLI token or canonical name to a catalog sector."""
    n = name.strip()
    if n in SECTOR_SNI:
        return n
    return ALIASES.get(n.lower())


def codes_for_sectors(sectors: list[str]) -> list[str]:
    """Flatten the SNI codes for the given sectors (dedup, order-stable).

    Unknown sector tokens are skipped by the caller via resolve_sector; passing
    an already-canonical name works too.
    """
    out: list[str] = []
    seen: set[str] = set()
    for s in sectors:
        canon = resolve_sector(s) or s
        for code in SECTOR_SNI.get(canon, []):
            if code not in seen:
                seen.add(code)
                out.append(code)
    return out
