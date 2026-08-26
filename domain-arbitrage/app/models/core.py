"""Domain, listing and enrichment tables.

Design note: DATA / FEATURES / VALUATION / PROBABILITY / DECISION are kept in
separate tables on purpose. A domain has exactly one row per *stage per run*,
so any published number can be walked backwards through its own table chain to
the raw imported row it came from.
"""

from __future__ import annotations

import datetime as _dt

from sqlalchemy import (JSON, Boolean, Float, ForeignKey, Index, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UtcDateTime
from app.provenance import utcnow


class ImportBatch(Base):
    """One CSV upload."""

    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(512))
    source_label: Mapped[str | None] = mapped_column(String(128), default=None)
    rows_received: Mapped[int] = mapped_column(Integer, default=0)
    rows_accepted: Mapped[int] = mapped_column(Integer, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0)
    rows_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)
    warnings: Mapped[list] = mapped_column(JSON, default=list)

    listings: Mapped[list["Listing"]] = relationship(back_populates="batch")


class Domain(Base):
    """A normalised domain name. One row per unique name, ever."""

    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    sld: Mapped[str] = mapped_column(String(255), index=True)
    tld: Mapped[str] = mapped_column(String(64), index=True)
    is_idn: Mapped[bool] = mapped_column(Boolean, default=False)
    unicode_name: Mapped[str | None] = mapped_column(String(255), default=None)
    first_seen_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)
    last_seen_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)

    listings: Mapped[list["Listing"]] = relationship(back_populates="domain",
                                                     cascade="all, delete-orphan")
    features: Mapped[list["DomainFeatures"]] = relationship(back_populates="domain",
                                                           cascade="all, delete-orphan")
    enrichments: Mapped[list["Enrichment"]] = relationship(back_populates="domain",
                                                           cascade="all, delete-orphan")


class Listing(Base):
    """An observed offer for a domain. OBSERVED data - straight from the import.

    Kept separate from ``Domain`` because the same name can be listed many
    times, at different prices, in different venues. Price history matters for
    the paper portfolio.
    """

    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"),
                                           index=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"),
                                                 default=None, index=True)

    asking_price: Mapped[float | None] = mapped_column(Float, default=None)
    current_bid: Mapped[float | None] = mapped_column(Float, default=None)
    bid_count: Mapped[int | None] = mapped_column(Integer, default=None)
    source: Mapped[str] = mapped_column(String(128), default="unknown")
    listing_type: Mapped[str | None] = mapped_column(String(64), default=None)
    auction_end_date: Mapped[_dt.datetime | None] = mapped_column(UtcDateTime, default=None)
    expiration_date: Mapped[_dt.datetime | None] = mapped_column(UtcDateTime, default=None)
    registrar: Mapped[str | None] = mapped_column(String(255), default=None)
    traffic: Mapped[float | None] = mapped_column(Float, default=None)

    raw_row: Mapped[dict] = mapped_column(JSON, default=dict)
    observed_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    domain: Mapped[Domain] = relationship(back_populates="listings")
    batch: Mapped[ImportBatch | None] = relationship(back_populates="listings")

    @property
    def effective_price(self) -> float | None:
        """What it would cost to acquire right now.

        For auctions the live bid is the floor; asking_price may be a buy-now.
        Returns None when neither is known - callers must handle that rather
        than assuming zero.
        """
        candidates = [p for p in (self.asking_price, self.current_bid) if p is not None]
        if not candidates:
            return None
        if self.current_bid is not None and self.asking_price is not None:
            return max(self.current_bid, 0.0) if self.listing_type == "auction" else self.asking_price
        return candidates[0]


class DomainFeatures(Base):
    """Deterministic structural + linguistic features. All DERIVED.

    Stored one row per (domain, features_version) so a feature change does not
    silently rewrite history.
    """

    __tablename__ = "domain_features"
    __table_args__ = (UniqueConstraint("domain_id", "features_version",
                                       name="uq_features_domain_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"),
                                           index=True)
    features_version: Mapped[str] = mapped_column(String(32), default="f0.1.0")
    computed_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)

    # --- structural ---
    length: Mapped[int] = mapped_column(Integer, default=0)
    sld_length: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    words: Mapped[list] = mapped_column(JSON, default=list)
    has_hyphen: Mapped[bool] = mapped_column(Boolean, default=False)
    has_digit: Mapped[bool] = mapped_column(Boolean, default=False)
    digit_count: Mapped[int] = mapped_column(Integer, default=0)
    hyphen_count: Mapped[int] = mapped_column(Integer, default=0)
    syllable_count: Mapped[int] = mapped_column(Integer, default=0)
    vowel_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    max_consonant_run: Mapped[int] = mapped_column(Integer, default=0)
    dictionary_word_count: Mapped[int] = mapped_column(Integer, default=0)
    all_words_dictionary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_single_dictionary_word: Mapped[bool] = mapped_column(Boolean, default=False)
    is_plural: Mapped[bool] = mapped_column(Boolean, default=False)
    prefix: Mapped[str | None] = mapped_column(String(32), default=None)
    suffix: Mapped[str | None] = mapped_column(String(32), default=None)
    has_generic_modifier: Mapped[bool] = mapped_column(Boolean, default=False)
    acronym_likelihood: Mapped[float] = mapped_column(Float, default=0.0)
    segmentation_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    mean_word_zipf: Mapped[float] = mapped_column(Float, default=0.0)

    # --- linguistic scores, 0..100, all DERIVED from the above ---
    pronounceability: Mapped[float] = mapped_column(Float, default=0.0)
    memorability: Mapped[float] = mapped_column(Float, default=0.0)
    spelling_ambiguity: Mapped[float] = mapped_column(Float, default=0.0)
    semantic_coherence: Mapped[float] = mapped_column(Float, default=0.0)
    brandability: Mapped[float] = mapped_column(Float, default=0.0)
    business_name_plausibility: Mapped[float] = mapped_column(Float, default=0.0)

    components: Mapped[dict] = mapped_column(JSON, default=dict)

    domain: Mapped[Domain] = relationship(back_populates="features")


class Enrichment(Base):
    """Generic provenance-carrying field store.

    Any externally sourced or model-inferred scalar lands here rather than as a
    bare column, because the requirement is that *every* enriched field carries
    value + source + retrieved_at + confidence. A wide table cannot do that
    without quadrupling its column count.

    Numeric values go in ``value_num`` so they can be aggregated in SQL;
    structured values go in ``value_json``.
    """

    __tablename__ = "enrichments"
    __table_args__ = (
        UniqueConstraint("domain_id", "field", "source", name="uq_enrichment_field_source"),
        Index("ix_enrichment_field", "field"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"),
                                           index=True)
    field: Mapped[str] = mapped_column(String(128))
    value_num: Mapped[float | None] = mapped_column(Float, default=None)
    value_text: Mapped[str | None] = mapped_column(Text, default=None)
    value_json: Mapped[dict | None] = mapped_column(JSON, default=None)

    provenance: Mapped[str] = mapped_column(String(16), default="MISSING", index=True)
    source: Mapped[str] = mapped_column(String(128), default="unknown")
    retrieved_at: Mapped[_dt.datetime] = mapped_column(UtcDateTime, default=utcnow)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_url: Mapped[str | None] = mapped_column(Text, default=None)
    note: Mapped[str | None] = mapped_column(Text, default=None)

    domain: Mapped[Domain] = relationship(back_populates="enrichments")
