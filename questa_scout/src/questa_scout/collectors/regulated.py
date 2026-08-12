from __future__ import annotations

"""Regulated-data scope qualification for the US market.

Questa is built for organizations that handle sensitive, regulated data and
want to use AI on it safely. This collector is the qualifier: from a
company's NAICS industry code it decides whether the org sits in a
regulated-data sector, what class of data it handles (PHI / financial /
legal-privileged / consumer PII), and which US regime applies (HIPAA, GLBA,
state privacy laws such as CCPA/CPRA).

This is a screening heuristic, not a legal determination -- final scope
always needs a human read of the entity's actual activities and data.
"""

from ..models import Company, DataScopeVerdict

# NAICS prefix -> (sector, data_class, regime). Longest prefix wins.
# data_class drives the sensitivity tier; regime is the compliance hook.
NAICS_SECTORS: list[tuple[str, str, str, str]] = [
    # Health care & social assistance -> PHI, HIPAA
    ("621", "Ambulatory health care", "PHI", "HIPAA"),
    ("622", "Hospitals", "PHI", "HIPAA"),
    ("623", "Nursing & residential care", "PHI", "HIPAA"),
    ("6215", "Medical & diagnostic labs", "PHI", "HIPAA"),
    ("62", "Health care", "PHI", "HIPAA"),
    ("3254", "Pharmaceutical manufacturing", "PHI", "HIPAA / FDA"),
    # Finance & insurance -> financial data, GLBA
    ("522", "Credit intermediation (banking)", "financial", "GLBA"),
    ("523", "Securities & investments", "financial", "GLBA / SEC"),
    ("524", "Insurance carriers", "financial", "GLBA / state insurance"),
    ("525", "Funds & trusts", "financial", "GLBA / SEC"),
    ("52", "Finance & insurance", "financial", "GLBA"),
    # Legal -> privileged / M&A confidential, state privacy + privilege
    ("5411", "Legal services", "legal_privileged", "state privacy + privilege"),
    # Data-heavy professional & business services -> consumer PII, state privacy
    ("5416", "Management & technical consulting", "consumer_pii", "state privacy"),
    ("5412", "Accounting & tax", "financial", "GLBA / state privacy"),
    ("5613", "Employment services / HR", "consumer_pii", "state privacy"),
    ("5614", "Business support services (BPO)", "consumer_pii", "state privacy + client DPAs"),
    ("561", "Administrative & support (BPO)", "consumer_pii", "state privacy + client DPAs"),
    # Software / SaaS / hosting -> processes customers' regulated data
    ("5112", "Software publishers (SaaS)", "consumer_pii", "state privacy (processor)"),
    ("5182", "Data processing & hosting", "consumer_pii", "state privacy (processor)"),
    ("5415", "Computer systems design", "consumer_pii", "state privacy (processor)"),
]

# Sensitivity tier per data class (higher = more sensitive = more valuable).
SENSITIVITY = {"PHI": 4, "legal_privileged": 3, "financial": 3, "consumer_pii": 2}

# Below this we still qualify but flag as smaller (routing, not exclusion).
SMALL_EMPLOYEES = 20


def match_sector(naics_code: str | None) -> tuple[str, str, str] | None:
    """Return (sector, data_class, regime) for a NAICS code, longest-prefix
    match, or None if it maps to no regulated-data sector."""
    if not naics_code:
        return None
    code = naics_code.strip().replace(".", "").replace(" ", "")
    best: tuple[str, str, str, str] | None = None
    for prefix, sector, data_class, regime in NAICS_SECTORS:
        if code.startswith(prefix):
            if best is None or len(prefix) > len(best[0]):
                best = (prefix, sector, data_class, regime)
    if best is None:
        return None
    return best[1], best[2], best[3]


def qualify(company: Company) -> DataScopeVerdict:
    match = match_sector(company.naics_code)
    reasons: list[str] = []

    if match is None:
        if company.naics_code:
            reasons.append(
                f"NAICS {company.naics_code} does not map to a regulated-data sector"
            )
            verdict = "out_of_scope"
        else:
            reasons.append("No NAICS code -- regulated-data scope unknown")
            verdict = "unknown"
        return DataScopeVerdict(
            verdict=verdict, sector=None, data_class=None, regime=None,
            sensitivity=0, reasons=reasons,
        )

    sector, data_class, regime = match
    sensitivity = SENSITIVITY.get(data_class, 1)
    reasons.append(
        f"Regulated-data sector: {sector} (NAICS {company.naics_code}) -> "
        f"{data_class} under {regime}"
    )

    # Everyone in a regulated-data sector qualifies; size only affects routing.
    if company.employees is not None and company.employees < SMALL_EMPLOYEES:
        reasons.append(f"Small org ({company.employees} employees) -- Questa Cloud fit")
        verdict = "likely_in_scope"
    else:
        verdict = "in_scope"

    return DataScopeVerdict(
        verdict=verdict, sector=sector, data_class=data_class, regime=regime,
        sensitivity=sensitivity, reasons=reasons,
    )
