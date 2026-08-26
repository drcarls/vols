"""Provider assembly.

One place decides which data sources are live for a run, and produces the
warnings that say so. The pipeline records this on the run, so a prediction's
evidentiary basis is recoverable months later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import DATA_DIR, get_settings
from app.providers.base import BuyerProvider, KeywordProvider
from app.providers.buyer import (CompanyFileBuyerProvider,
                                 ExampleFixtureBuyerProvider, NullBuyerProvider)
from app.providers.keyword import build_keyword_provider
from app.providers.llm import LlmProvider, build_llm_provider

EXAMPLE_COMPANY_FILE = DATA_DIR / "examples" / "companies_EXAMPLE_SYNTHETIC.csv"


@dataclass
class ProviderSet:
    keyword: KeywordProvider
    buyer: BuyerProvider
    llm: LlmProvider
    warnings: list[str] = field(default_factory=list)

    def describe(self) -> dict[str, Any]:
        return {"keyword": self.keyword.describe(),
                "buyer": self.buyer.describe(),
                "llm": self.llm.describe(),
                "warnings": self.warnings}


def build_providers(*, keyword_csv: Path | None = None,
                    company_csv: Path | None = None) -> ProviderSet:
    s = get_settings()
    warnings: list[str] = []

    keyword = build_keyword_provider(s.keyword_provider,
                                     keyword_csv or s.keyword_csv_path)
    if not keyword.available:
        warnings.append(
            "KEYWORD DATA MISSING: no search volume, CPC or advertiser "
            "competition source is configured. Commercial-intent multipliers "
            "are forced to neutral and valuation confidence is reduced. "
            "Configure KEYWORD_PROVIDER=csv with a Google Ads / Semrush / "
            "Ahrefs / DataForSEO export.")

    company_path = company_csv or s.buyer_company_csv_path
    if company_path and Path(company_path).exists():
        buyer: BuyerProvider = CompanyFileBuyerProvider(Path(company_path))
    elif s.allow_fixture_data and EXAMPLE_COMPANY_FILE.exists():
        buyer = ExampleFixtureBuyerProvider(EXAMPLE_COMPANY_FILE)
        warnings.append(
            "USING SYNTHETIC FIXTURE COMPANIES: ALLOW_FIXTURE_DATA is enabled "
            "and no real company file is configured. Every buyer candidate is "
            "tagged FIXTURE and is NOT evidence of a real company. Turn this "
            "off before making any capital decision.")
    else:
        buyer = NullBuyerProvider()
        warnings.append(
            "BUYER DATA MISSING: no company file is configured, so buyer depth "
            "- the primary signal this system exists to test - is UNKNOWN for "
            "every domain. Set BUYER_COMPANY_CSV_PATH to a company dataset.")

    llm = build_llm_provider()
    if not llm.available:
        warnings.append(
            "NO LLM CONFIGURED: semantic classification falls back to the "
            "deterministic taxonomy. Domains whose words are not in the "
            "taxonomy will have category MISSING.")

    return ProviderSet(keyword=keyword, buyer=buyer, llm=llm, warnings=warnings)
