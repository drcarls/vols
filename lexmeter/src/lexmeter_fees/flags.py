"""Derived metrics and violation flags.

Two families, and the distinction matters operationally:

* Single-observation flags run on one flow from one vantage.
* Cross-observation flags need the same flow from several vantages, which is why
  the multi-vantage differential probe exists (plan 4.2). They are the more
  valuable half -- display switching shows a company can comply and elected not
  to -- and the cheaper half to run, because they need a sample, not a sweep.

Nothing here asserts a legal conclusion. A flag says what was observed; whether
that is a violation depends on jurisdiction and date, which is rules.py's job.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from .model import FlowObservation, Mandatory, PriceBasis, Step, StepKind

#: Seller types SB 1524's conditional exemption can attach to. The flag is
#: meaningless outside them -- a ticketing flow cannot fail a restaurant
#: exemption -- and firing it there would put nonsense in front of a lawyer.
FOOD_SELLER_INDUSTRIES = frozenset(
    {"restaurants", "food_delivery", "grocery", "food_concession", "bars"}
)


class Flag(enum.Enum):
    #: The core claim in nearly every filed case.
    MANDATORY_FEE_AT_FINAL_STEP = "mandatory_fee_first_shown_at_final_step"
    HEADLINE_EXCLUDES_ALL_MANDATORY_FEES = "headline_excludes_all_mandatory_fees"
    OPTIONAL_LABEL_BUT_UNAVOIDABLE = "fee_named_optional_but_unavoidable"
    FEE_VARIES_BY_VANTAGE = "fee_amount_varies_by_vantage_state"
    #: SB 1524's exemption is conditional; failing a limb drops the seller back
    #: under SB 478 and its private right of action.
    RESTAURANT_EXEMPTION_CONDITION_FAILED = "restaurant_exemption_condition_failed"
    JURISDICTIONAL_DISPLAY_SWITCHING = "jurisdictional_display_switching"


@dataclass(frozen=True)
class Metrics:
    """Per-observation derived measures."""

    headline_cents: int | None
    #: What kind of number the headline was. A gap computed against a floor is an
    #: artefact of the comparison, so the gap is withheld unless this is EXACT.
    headline_basis: PriceBasis
    #: Units the total covers. The gap is total minus headline x quantity.
    quantity: int
    total_cents: int | None
    mandatory_fee_cents: int
    gap_abs_cents: int | None
    gap_pct: float | None
    #: Latest step index at which any mandatory fee first appeared. This, not the
    #: gap, is what the "not shown until the last step" pleading turns on.
    latest_mandatory_fee_first_step: int | None
    all_in_shown_before_final_step: bool
    fee_categories: tuple[str, ...]


def _first_headline(obs: FlowObservation) -> tuple[int | None, PriceBasis, int | None]:
    """Headline as first displayed, preferring the first price of the actual item.

    Resale marketplaces open with a floor across all listings ("From $307+"). That
    is not the price of anything a buyer can select, and comparing it to a checkout
    total invents a gap: on a real TickPick flow it produced 556% against a site
    that charges no fees at all. So an exact price is taken where the flow provides
    one, and a floor is only reported when nothing better exists -- carrying its
    basis so the gap can be withheld rather than published.
    """
    fallback: tuple[int | None, PriceBasis, int | None] = (None, PriceBasis.UNKNOWN, None)
    for step in obs.steps:
        if step.headline_price_cents is None:
            continue
        if step.headline_basis is PriceBasis.EXACT:
            return step.headline_price_cents, PriceBasis.EXACT, step.index
        if fallback[0] is None:
            fallback = (step.headline_price_cents, step.headline_basis, step.index)
    return fallback


def _final_total(obs: FlowObservation) -> tuple[int | None, int]:
    """Last displayed total, with the quantity in effect where it was displayed."""
    for step in reversed(obs.steps):
        if step.displayed_total_cents is not None:
            return step.displayed_total_cents, max(1, step.quantity)
    return None, 1


def _mandatory_lines(obs: FlowObservation):
    seen: dict[tuple[str, int], object] = {}
    for step in obs.steps:
        for line in step.fee_lines:
            if not line.counts_toward_mandatory_total:
                continue
            # A fee restated on later steps is one fee, keyed on where it first
            # appeared, or the gap would double-count it.
            seen.setdefault((line.raw_label, line.first_seen_step_index), line)
    return list(seen.values())


def compute_metrics(obs: FlowObservation) -> Metrics:
    headline, basis, _ = _first_headline(obs)
    total, quantity = _final_total(obs)
    lines = _mandatory_lines(obs)
    mandatory_cents = sum(line.amount_cents for line in lines)

    gap_abs: int | None = None
    gap_pct: float | None = None
    # Two conditions, both learned from a real capture that got them wrong:
    # the headline must be this item's price, and it must be scaled to the units
    # the total covers. $1,008 each against a $2,016 two-ticket total is a zero
    # gap, not a 100% one.
    if headline is not None and total is not None and basis is PriceBasis.EXACT:
        expected_headline = headline * quantity
        gap_abs = total - expected_headline
        if expected_headline > 0:
            gap_pct = round(100.0 * gap_abs / expected_headline, 4)

    latest = max((line.first_seen_step_index for line in lines), default=None)

    return Metrics(
        headline_cents=headline,
        headline_basis=basis,
        quantity=quantity,
        total_cents=total,
        mandatory_fee_cents=mandatory_cents,
        gap_abs_cents=gap_abs,
        gap_pct=gap_pct,
        latest_mandatory_fee_first_step=latest,
        all_in_shown_before_final_step=_all_in_before_final(obs, mandatory_cents),
        fee_categories=tuple(sorted({line.category.value for line in lines})),
    )


def _all_in_before_final(obs: FlowObservation, mandatory_cents: int) -> bool:
    """Did any step before the last show a total that already carried the fees?

    This is the compliance question the FTC rule actually asks, and it is why a
    large gap alone is not a finding: a site can show a big fee total honestly,
    up front, and be fine.
    """
    if len(obs.steps) < 2 or mandatory_cents <= 0:
        return False
    for step in obs.steps[:-1]:
        if step.displayed_total_cents is None or step.headline_price_cents is None:
            continue
        if step.headline_basis is not PriceBasis.EXACT:
            continue
        unit_total = step.headline_price_cents * max(1, step.quantity)
        if step.displayed_total_cents >= unit_total + mandatory_cents:
            return True
    return False


def _is_final(step: Step, obs: FlowObservation) -> bool:
    return step.index == obs.steps[-1].index


def evaluate(obs: FlowObservation) -> set[Flag]:
    """Single-observation flags."""
    flags: set[Flag] = set()
    if not obs.steps:
        return flags

    metrics = compute_metrics(obs)
    final_index = obs.steps[-1].index

    # A mandatory fee whose first appearance is the final step. Requires a real
    # funnel: a one-step flow cannot drip, and treating it as such would inflate
    # every league table with flows that were simply short.
    if len(obs.steps) > 1 and metrics.latest_mandatory_fee_first_step == final_index:
        flags.add(Flag.MANDATORY_FEE_AT_FINAL_STEP)

    if metrics.mandatory_fee_cents > 0 and not metrics.all_in_shown_before_final_step:
        flags.add(Flag.HEADLINE_EXCLUDES_ALL_MANDATORY_FEES)

    is_food_seller = obs.industry in FOOD_SELLER_INDUSTRIES

    for step in obs.steps:
        for line in step.fee_lines:
            if line.label_says_optional and line.mandatory is Mandatory.MANDATORY:
                flags.add(Flag.OPTIONAL_LABEL_BUT_UNAVOIDABLE)
            # SB 1524 exempts the fee only if displayed AND its purpose explained,
            # and only for food sellers. Whether that exemption matters at all is
            # a jurisdiction question, left to rules.py.
            if (
                is_food_seller
                and line.mandatory is Mandatory.MANDATORY
                and not (line.purpose_text or "").strip()
                and step.kind in (StepKind.LISTING, StepKind.DETAIL, StepKind.SELECT)
            ):
                flags.add(Flag.RESTAURANT_EXEMPTION_CONDITION_FAILED)

    return flags


def evaluate_across_vantages(observations: list[FlowObservation]) -> set[Flag]:
    """Cross-observation flags over the same flow from different vantage points.

    Callers must pass observations of one flow only; mixing flows would compare
    unrelated prices and produce a meaningless variance signal.
    """
    flags: set[Flag] = set()
    usable = [o for o in observations if o.completed]
    if len({o.flow_id for o in usable}) > 1:
        raise ValueError("evaluate_across_vantages expects a single flow_id")
    if len(usable) < 2:
        return flags

    by_state = {o.vantage_state: compute_metrics(o) for o in usable}

    # Fee amount varying by vantage. Expected to be rare in ticketing and lodging,
    # where fees track the event or property rather than the buyer -- see plan 4.2.
    fee_totals = {m.mandatory_fee_cents for m in by_state.values()}
    if len(fee_totals) > 1:
        flags.add(Flag.FEE_VARIES_BY_VANTAGE)

    # Display switching: all-in rendered to some vantages and not others. The
    # company has shown it can comply, which goes to knowledge.
    all_in = {state: m.all_in_shown_before_final_step for state, m in by_state.items()}
    if any(all_in.values()) and not all(all_in.values()):
        flags.add(Flag.JURISDICTIONAL_DISPLAY_SWITCHING)

    return flags
