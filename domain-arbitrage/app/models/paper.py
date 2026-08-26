"""Paper portfolio: predictions recorded now, outcomes recorded later.

This is the part of the system that decides whether any of the rest of it
works. The scoring model is uncalibrated by construction, so its only route to
credibility is: write down a falsifiable prediction, timestamp it, freeze the
config version, and come back later with the observed outcome.

Nothing in here may be back-filled from a model. ``PaperObservation`` rows are
OBSERVED facts entered by a human or an outcome feed.
"""

from __future__ import annotations

import datetime as _dt

from sqlalchemy import (JSON, Boolean, Float, ForeignKey, Integer, String,
                        Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UtcDateTime
from app.provenance import utcnow


class PaperPosition(Base):
    """A frozen prediction about one domain at one moment in time."""

    __tablename__ = "paper_positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"),
                                           index=True)
    domain_name: Mapped[str] = mapped_column(String(255), index=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("pipeline_runs.id"), default=None)

    status: Mapped[str] = mapped_column(String(24), default="PAPER_BUY", index=True)
    # PAPER_BUY | PAPER_WATCH | PAPER_PASS | CLOSED

    date_seen: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)
    asking_price: Mapped[float | None] = mapped_column(Float, default=None)

    # --- the frozen prediction ---
    predicted_wholesale_value: Mapped[float | None] = mapped_column(Float, default=None)
    predicted_retail_value: Mapped[float | None] = mapped_column(Float, default=None)
    predicted_retail_low: Mapped[float | None] = mapped_column(Float, default=None)
    predicted_retail_high: Mapped[float | None] = mapped_column(Float, default=None)
    predicted_sale_probability_12m: Mapped[float | None] = mapped_column(Float, default=None)
    predicted_sale_probability_24m: Mapped[float | None] = mapped_column(Float, default=None)
    predicted_sale_probability_36m: Mapped[float | None] = mapped_column(Float, default=None)
    opportunity_score: Mapped[float | None] = mapped_column(Float, default=None)
    recommended_max_bid: Mapped[float | None] = mapped_column(Float, default=None)
    expected_profit_24m: Mapped[float | None] = mapped_column(Float, default=None)
    expected_roi_24m: Mapped[float | None] = mapped_column(Float, default=None)
    recommendation: Mapped[str | None] = mapped_column(String(16), default=None)

    # Signal snapshot: exactly the values the signal-power analysis will test.
    signal_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)

    # Which sampling batch and stratum this position came from. Recorded so the
    # analysis can check whether the cohort actually spans the score and
    # buyer-depth ranges - a sample drawn only from the model's own top picks
    # can measure precision but never recall, and cannot falsify anything.
    sample_cohort: Mapped[str | None] = mapped_column(String(64), default=None,
                                                      index=True)
    sample_stratum: Mapped[str | None] = mapped_column(String(64), default=None,
                                                       index=True)
    config_stamp: Mapped[str] = mapped_column(String(64), default="")
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    # --- resolved outcome (filled in later, from observations) ---
    outcome: Mapped[str | None] = mapped_column(String(32), default=None, index=True)
    # SOLD | UNSOLD | LOST_AUCTION | EXPIRED_UNSOLD | CENSORED | UNKNOWN
    #
    # CENSORED means the observation window closed while the domain was still
    # unsold and still inside its modelled horizon. That is NOT the same as
    # UNSOLD, and treating it as such would bias the measured sale rate
    # downward. Censored positions are excluded from the testable set.
    outcome_price: Mapped[float | None] = mapped_column(Float, default=None)
    outcome_date: Mapped[_dt.datetime | None] = mapped_column(UtcDateTime, default=None)
    outcome_resolved_at: Mapped[_dt.datetime | None] = mapped_column(UtcDateTime, default=None)

    observations: Mapped[list["PaperObservation"]] = relationship(
        back_populates="position", cascade="all, delete-orphan",
        order_by="PaperObservation.observed_at")


class PaperObservation(Base):
    """An OBSERVED event about a paper position after it was opened."""

    __tablename__ = "paper_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("paper_positions.id",
                                                        ondelete="CASCADE"), index=True)
    observed_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)
    event_type: Mapped[str] = mapped_column(String(32), default="LISTING_CHANGE")
    # AUCTION_RESULT | SOLD | LISTING_CHANGE | PRICE_CHANGE | DELISTED | RENEWED

    sold: Mapped[bool | None] = mapped_column(Boolean, default=None)
    observed_price: Mapped[float | None] = mapped_column(Float, default=None)
    listing_price: Mapped[float | None] = mapped_column(Float, default=None)
    venue: Mapped[str | None] = mapped_column(String(128), default=None)
    bid_count: Mapped[int | None] = mapped_column(Integer, default=None)

    provenance: Mapped[str] = mapped_column(String(16), default="OBSERVED")
    source: Mapped[str] = mapped_column(String(128), default="manual")
    evidence_url: Mapped[str | None] = mapped_column(Text, default=None)
    note: Mapped[str | None] = mapped_column(Text, default=None)

    position: Mapped[PaperPosition] = relationship(back_populates="observations")
