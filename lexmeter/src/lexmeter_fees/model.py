"""The capture data contract.

Everything downstream -- evidence chain, flags, reports, the pattern-match
screen -- reads these types, so they are deliberately boring and explicit.

Money is integer cents throughout. Float dollars silently lose the cent that
distinguishes a $2.00 fee from a $1.995 fee, and the gap metric is the headline
number in every report.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class StepKind(enum.Enum):
    """Where in the funnel a step sits.

    ``REVIEW`` is the last step we ever reach: the flow stops at the final
    review page and never completes a purchase.
    """

    SEARCH = "search"
    LISTING = "listing"
    DETAIL = "detail"
    SELECT = "select"
    CART = "cart"
    CHECKOUT = "checkout"
    REVIEW = "review"


class Mandatory(enum.Enum):
    """Whether a fee can be avoided by a buyer who still completes the purchase.

    ``UNKNOWN`` is a real and common state -- it is recorded rather than guessed,
    because an unavoidable fee misclassified as optional is the difference
    between a claim and a nuisance.
    """

    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    UNKNOWN = "unknown"


class PriceBasis(enum.Enum):
    """What kind of number a displayed price actually is.

    Resale marketplaces lead with a floor across all listings ("From $307+"),
    which is not the price of any item a buyer can select. Treating it as the
    headline and comparing it to a checkout total manufactures an enormous gap out
    of nothing -- the observed failure was a 556% gap on a site that charges no
    fees at all. A floor is therefore recorded and kept out of the item-level gap.
    """

    #: The price of the specific item being bought.
    EXACT = "exact"
    #: A "from"/"starting at" floor across many items.
    FLOOR = "floor"
    #: A span ("$300-$900").
    RANGE = "range"
    UNKNOWN = "unknown"


class FeeCategory(enum.Enum):
    """Canonical fee taxonomy. ``OTHER`` is a work queue, not a resting place."""

    SERVICE = "service"
    CONVENIENCE = "convenience"
    PROCESSING = "processing"
    ORDER_PROCESSING = "order_processing"
    RESORT = "resort"
    DESTINATION = "destination"
    RESERVATION = "reservation"
    TRANSACTION = "transaction"
    FACILITY = "facility"
    CONCESSION_RECOVERY = "concession_recovery"
    CLEANING = "cleaning"
    DELIVERY = "delivery"
    SMALL_ORDER = "small_order"
    REGULATORY_RECOVERY = "regulatory_recovery"
    TAX = "tax"
    SHIPPING = "shipping"
    OTHER = "other"


#: Categories excluded from a "mandatory fee" finding by statute. SB 478 and its
#: state analogues exclude government taxes and fees and reasonable shipping from
#: the all-in price requirement, so counting them would manufacture violations.
STATUTORILY_EXCLUDED = frozenset({FeeCategory.TAX, FeeCategory.SHIPPING})


@dataclass(frozen=True)
class Artifact:
    """One captured file, addressed by the digest of its bytes."""

    kind: str  # screenshot | dom | har | video
    digest: str  # sha256 hex
    content_type: str
    byte_length: int
    scroll_y: int | None = None  # viewport screenshots record where they were taken


@dataclass(frozen=True)
class FeeLine:
    """A single fee as displayed, plus what we concluded about it."""

    raw_label: str
    amount_cents: int
    category: FeeCategory
    mandatory: Mandatory
    first_seen_step_index: int
    #: Text the site offered as the fee's purpose, if any. Drives the SB 1524
    #: conditional-exemption test, which turns on whether a purpose was explained.
    purpose_text: str | None = None
    #: True where the label reads as optional but the fee could not be removed
    #: without abandoning the purchase.
    label_says_optional: bool = False
    #: Who the page says keeps this fee, where it says at all. Usually nothing,
    #: which is the point: on a government-branded site operated under contract by
    #: a private vendor, a mandatory fee with no stated beneficiary reads as though
    #: it accrues to the agency. That inference is the gravamen of Chowning, and
    #: it is also what takes the fee outside the statutory government-fee
    #: exclusion -- a vendor's revenue is not a government fee.
    stated_beneficiary: str | None = None

    @property
    def beneficiary_disclosed(self) -> bool:
        return bool((self.stated_beneficiary or "").strip())

    @property
    def counts_toward_mandatory_total(self) -> bool:
        return (
            self.mandatory is Mandatory.MANDATORY
            and self.category not in STATUTORILY_EXCLUDED
        )


@dataclass(frozen=True)
class ReferencePriceClaim:
    """A "you save $X" or struck-through price shown next to the real one.

    A different claim family from drip pricing, and one the fee machinery cannot
    express: nothing is being added to the price, a counterfactual is being
    asserted about it. Captured because the counterfactual is the regulated part --
    a savings figure is only meaningful if the reference it implies is a price
    someone could actually have paid.

    Recording it is not an accusation. A disclosed, substantiated methodology is
    lawful; the point is that the claim is measurable and currently unmeasured.
    """

    raw_text: str
    savings_cents: int | None = None
    #: Price implied by the claim: what the buyer is being told they avoided.
    implied_reference_cents: int | None = None
    #: Text the page offered explaining what the reference is. Usually absent,
    #: which is the whole question.
    stated_basis: str | None = None

    @property
    def basis_disclosed(self) -> bool:
        return bool((self.stated_basis or "").strip())


@dataclass(frozen=True)
class Step:
    """One page state in the flow."""

    index: int
    kind: StepKind
    url: str
    observed_at: datetime  # UTC
    #: Price shown most prominently at this step, as a buyer would read it.
    headline_price_cents: int | None = None
    #: Whether that price is this item's price or a floor across many.
    headline_basis: PriceBasis = PriceBasis.EXACT
    #: Total the page itself displays, where it displays one.
    displayed_total_cents: int | None = None
    #: Units in the order at this step. A per-unit headline against a multi-unit
    #: total is the other half of the same false-positive: $1,008 each against a
    #: $2,016 total is a zero gap, not a 100% one.
    quantity: int = 1
    fee_lines: tuple[FeeLine, ...] = ()
    reference_claims: tuple[ReferencePriceClaim, ...] = ()
    artifacts: tuple[Artifact, ...] = ()
    notes: str | None = None


@dataclass(frozen=True)
class Anchor:
    """What was bought, defined so week-over-week deltas stay comparable.

    An anchor whose identity silently changed between sweeps produces a price
    delta that means nothing, so ``stable`` travels with every observation and
    the metrics layer refuses to diff across a substitution.
    """

    descriptor: str  # e.g. "venue=MSG;event=knicks-regular-season"
    #: Rolling offsets stay comparable across weeks; fixed dates capture peaks.
    date_mode: str = "rolling_offset"  # rolling_offset | fixed_date
    offset_days: int | None = 30
    fixed_date: str | None = None
    nights: int | None = None
    stable: bool = True
    substitution_note: str | None = None


@dataclass(frozen=True)
class FlowObservation:
    """One scripted run of one flow from one vantage point."""

    flow_id: str
    company: str
    industry: str
    vantage_state: str
    device: str  # desktop | mobile
    anchor: Anchor
    started_at: datetime  # UTC
    steps: tuple[Step, ...] = ()
    #: Set when the run stopped on a block signal. A blocked run is evidence of a
    #: block, not a missing observation, and is stored rather than discarded.
    blocked_reason: str | None = None
    #: Address entered, where the platform geolocates on address rather than IP.
    delivery_address_state: str | None = None
    #: True where the site carries a government agency's branding but is operated
    #: under contract by a private vendor. Set from the target list, not inferred
    #: from the page -- who holds the contract is a procurement fact.
    agency_branded_vendor_operated: bool = False
    egress_provider: str | None = None
    #: Which proxy tier produced this capture. Recorded per observation, not per
    #: run: findings from ISP-sourced captures must be able to stand independently
    #: if the residential-sourced ones are challenged.
    egress_tier: str | None = None
    #: Why a fallback tier was used, where one was.
    egress_tier_justification: str | None = None
    collector_version: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def completed(self) -> bool:
        return self.blocked_reason is None and bool(self.steps)

    @property
    def final_step(self) -> Step | None:
        return self.steps[-1] if self.steps else None
