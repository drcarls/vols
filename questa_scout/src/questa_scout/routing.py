from __future__ import annotations

"""Route a qualified prospect to the right Questa product.

Questa ships three buyer-shaped products:

  * Questa Blackbox   -- self-hosted / on-prem, for enterprises with strict
    data-residency needs (hospitals, banks, insurers at scale).
  * Questa Developer  -- API-based redaction, for SaaS platforms that embed
    AI into their own product and need to protect *their customers'* data.
  * Questa Cloud      -- managed service, for startups and small teams.

This is a routing heuristic, not a quote -- it picks the lead product to
open the conversation with.
"""

from .models import Company, DataScopeVerdict

# NAICS prefixes for software / SaaS / hosting -> Developer (API) fit.
SAAS_PREFIXES = ("5112", "5182", "5415")

LARGE_EMPLOYEES = 250
LARGE_REVENUE_USD = 100_000_000
SMALL_EMPLOYEES = 50


def route_product(company: Company, scope: DataScopeVerdict) -> str:
    code = (company.naics_code or "").replace(".", "").replace(" ", "")
    is_saas = code.startswith(SAAS_PREFIXES)

    if is_saas:
        return "Questa Developer (API)"

    big = (
        (company.employees is not None and company.employees >= LARGE_EMPLOYEES)
        or (company.revenue_usd is not None and company.revenue_usd >= LARGE_REVENUE_USD)
    )
    small = company.employees is not None and company.employees < SMALL_EMPLOYEES

    # High-sensitivity + sizable -> on-prem Blackbox; small -> Cloud.
    if big or scope.sensitivity >= 3:
        if small:
            return "Questa Cloud"
        return "Questa Blackbox (self-hosted)"
    if small:
        return "Questa Cloud"
    return "Questa Blackbox (self-hosted)"
