"""Pydantic request/response models for the API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    batch_id: int | None
    rows_received: int
    rows_accepted: int
    rows_rejected: int
    rows_duplicate: int
    new_domains: int
    rejections: list[dict[str, Any]]
    warnings: list[str]
    unknown_columns: list[str]
    missing_optional_columns: list[str]


class RunRequest(BaseModel):
    domain_ids: list[int] | None = Field(
        default=None, description="Limit the run to these domain ids. Omit to score all.")


class RunResponse(BaseModel):
    run_id: int
    domains_scored: int
    duration_seconds: float
    providers: dict[str, Any]
    data_gaps: dict[str, int]
    warnings: list[str]


class RankedRow(BaseModel):
    rank: int | None
    domain: str
    asking_price: float | None
    retail_value_low: float | None
    retail_value_mid: float | None
    retail_value_high: float | None
    prob_sale_24m: float
    buyer_count: int
    recommended_max_bid: float | None
    expected_profit_24m: float | None
    expected_roi_24m: float | None
    opportunity_score: float
    confidence: float
    recommendation: str
    category: str | None
    data_gaps: list[str]


class RankedResponse(BaseModel):
    run_id: int
    total: int
    offset: int
    limit: int
    rows: list[RankedRow]
    warnings: list[str]


class PortfolioRequest(BaseModel):
    budget: float = Field(gt=0, description="Total capital available, in USD.")
    scenario: Literal["conservative", "balanced", "aggressive"] = "balanced"
    run_id: int | None = None


class PaperPositionRequest(BaseModel):
    domain: str
    status: Literal["PAPER_BUY", "PAPER_WATCH", "PAPER_PASS"] = "PAPER_BUY"
    run_id: int | None = None
    notes: str | None = None


class ObservationRequest(BaseModel):
    position_id: int
    event_type: Literal["AUCTION_RESULT", "SOLD", "LISTING_CHANGE",
                        "PRICE_CHANGE", "DELISTED", "RENEWED"]
    sold: bool | None = None
    observed_price: float | None = None
    listing_price: float | None = None
    venue: str | None = None
    bid_count: int | None = None
    source: str = "manual"
    evidence_url: str | None = Field(
        default=None,
        description="Where this was observed. Strongly recommended: an outcome "
                    "without a source cannot be audited later.")
    note: str | None = None
