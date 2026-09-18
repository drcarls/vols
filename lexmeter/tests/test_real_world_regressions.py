"""Regressions from real captures.

Every case here is numbers observed on a live site, not invented. They exist
because the collector got two of them wrong, and both errors were of the kind
that publishes a confident falsehood rather than failing visibly.
"""

from datetime import datetime, timezone

from lexmeter_fees.extract import classify_price_basis, parse_money_cents
from lexmeter_fees.flags import compute_metrics, evaluate
from lexmeter_fees.model import Anchor, FlowObservation, PriceBasis, Step, StepKind

NOW = datetime(2026, 9, 18, tzinfo=timezone.utc)


def step(i, kind, headline=None, total=None, quantity=1, fees=()):
    return Step(
        index=i,
        kind=kind,
        url=f"https://example.test/{i}",
        observed_at=NOW,
        headline_price_cents=parse_money_cents(headline),
        headline_basis=classify_price_basis(headline),
        displayed_total_cents=parse_money_cents(total),
        quantity=quantity,
        fee_lines=tuple(fees),
    )


def observation(company, steps):
    return FlowObservation(
        flow_id=f"{company}:flow",
        company=company,
        industry="live_event_ticketing",
        vantage_state="NY",
        device="desktop",
        anchor=Anchor(descriptor="regression"),
        started_at=NOW,
        steps=tuple(steps),
    )


# --- TickPick, 2026-09-18, Bears vs Vikings --------------------------------
# The negative control. Two listings walked to checkout. No fees charged.

def tickpick(unit_price, total, quantity=2):
    return observation(
        "TickPick",
        [
            step(0, StepKind.LISTING, "From $307+"),
            step(1, StepKind.DETAIL, unit_price),
            step(2, StepKind.REVIEW, unit_price, total, quantity=quantity),
        ],
    )


def test_tickpick_section_110_reads_zero_gap():
    m = compute_metrics(tickpick("$1,008 each", "$2,016.00"))
    assert m.gap_abs_cents == 0
    assert m.gap_pct == 0.0
    assert evaluate(tickpick("$1,008 each", "$2,016.00")) == set()


def test_tickpick_section_108_reads_zero_gap():
    m = compute_metrics(tickpick("$1,190 each", "$2,380.00"))
    assert m.gap_abs_cents == 0
    assert evaluate(tickpick("$1,190 each", "$2,380.00")) == set()


def test_floor_price_is_not_used_as_the_headline():
    # "From $307+" is a floor across every listing, not the price of anything a
    # buyer can select. Using it against a $2,016 total produced a 556% gap on a
    # site that charges no fees -- the negative control topping the league table
    # as the worst offender in the market.
    m = compute_metrics(tickpick("$1,008 each", "$2,016.00"))
    assert m.headline_basis is PriceBasis.EXACT
    assert m.headline_cents == 100800  # not 30700


def test_quantity_scales_the_headline():
    # $1,008 each against a two-ticket $2,016 total is a zero gap, not 100%.
    m = compute_metrics(tickpick("$1,008 each", "$2,016.00"))
    assert m.quantity == 2
    assert m.gap_abs_cents == 0


def test_gap_is_withheld_when_only_a_floor_price_exists():
    # Better to publish no gap than a fabricated one. A flow that never shows an
    # exact price cannot support an item-level comparison at all.
    floor_only = observation(
        "SomeMarketplace",
        [
            step(0, StepKind.LISTING, "From $307+"),
            step(1, StepKind.REVIEW, "From $307+", "$2,016.00", quantity=2),
        ],
    )
    m = compute_metrics(floor_only)
    assert m.headline_basis is PriceBasis.FLOOR
    assert m.gap_abs_cents is None
    assert m.gap_pct is None


# --- Etix / Zanies Chicago, 2026-09-18 -------------------------------------
# All-in venue. Headline holds at $37.95 through to the total.

def test_etix_zanies_all_in_flow_reads_zero_gap():
    obs = observation(
        "Etix",
        [
            step(0, StepKind.LISTING, "$37.95"),
            step(1, StepKind.DETAIL, "$37.95"),
            step(2, StepKind.CART, "$37.95", "$37.95", quantity=1),
            step(3, StepKind.REVIEW, "$37.95", "$37.95", quantity=1),
        ],
    )
    m = compute_metrics(obs)
    assert m.gap_abs_cents == 0
    assert evaluate(obs) == set()


def test_zero_value_fee_line_does_not_flag():
    # Etix checkout shows "Will Call Delivery Fee: $0.00" -- a real line item
    # worth nothing. It must be read, and must not produce a finding.
    from lexmeter_fees.extract import RawFeeRow, to_fee_lines

    lines = to_fee_lines([RawFeeRow("Will Call Delivery Fee", "$0.00", removable=False)], 3)
    assert lines[0].amount_cents == 0
    obs = observation(
        "Etix",
        [
            step(0, StepKind.LISTING, "$37.95"),
            step(1, StepKind.REVIEW, "$37.95", "$37.95", quantity=1, fees=lines),
        ],
    )
    assert compute_metrics(obs).gap_abs_cents == 0
    assert evaluate(obs) == set()


# --- the shape the collector must still catch ------------------------------

def test_a_genuine_multi_quantity_drip_is_still_caught():
    # Guards against the quantity fix silently suppressing real findings: same
    # two-ticket shape, but with a fee that appears only at the final step.
    from lexmeter_fees.extract import RawFeeRow, to_fee_lines
    from lexmeter_fees.flags import Flag

    fee = to_fee_lines([RawFeeRow("Service Fee", "$40.00", removable=False)], 2)
    obs = observation(
        "DripCo",
        [
            step(0, StepKind.LISTING, "$100.00"),
            step(1, StepKind.DETAIL, "$100.00"),
            step(2, StepKind.REVIEW, "$100.00", "$240.00", quantity=2, fees=fee),
        ],
    )
    m = compute_metrics(obs)
    assert m.gap_abs_cents == 4000  # $240 total vs $100 x 2
    assert Flag.MANDATORY_FEE_AT_FINAL_STEP in evaluate(obs)


# --- block detection, from an observed interstitial -------------------------

def test_observed_tickpick_block_page_is_detected():
    """TickPick interstitial, 2026-09-18, served to a datacenter IP.

    This page returned a normal status with normal-looking prose, and the original
    marker list missed it entirely. An undetected block is the worse failure: the
    required selectors then fail, the run is filed as a spec error, and someone is
    sent to re-author a spec that was never wrong.
    """
    import pytest
    from conftest import CONFIG
    from lexmeter_fees.politeness import Blocked, Policy, check_response

    policy = Policy.load(CONFIG / "collection_policy.yaml")
    body = (
        "Something's not right. We couldn't verify your session, which helps us "
        "fight bots that make tickets harder to get. We've blocked access to this "
        "page for now."
    )
    with pytest.raises(Blocked):
        check_response(200, body, policy)


def test_ordinary_pages_still_pass_the_widened_markers():
    # Guards against the wider marker list swallowing real captures.
    from conftest import CONFIG
    from lexmeter_fees.politeness import Policy, check_response

    policy = Policy.load(CONFIG / "collection_policy.yaml")
    for body in (
        "<html><body>Service Fee $18.40 Total $120.51</body></html>",
        "This venue uses All-In Pricing. The total price listed includes ticket fees and taxes.",
        "The price you see is the price you pay",
    ):
        check_response(200, body, policy)  # no raise


# --- reference price claims, TickPick 2026-09-18 ---------------------------

def test_tickpick_savings_claims_imply_a_consistent_uplift():
    """Both observed savings figures sit at ~10.5% of the order total.

    212/2016 = 10.516%, 250/2380 = 10.504%. Agreement that tight across two
    unrelated listings points at a formula applied to the total, not a live
    comparison against competitor listings -- scatter would be expected if the
    figure came from actually observed prices.

    Two points is weak evidence and any two points fit something. The test locks
    the arithmetic so a third observation either corroborates or breaks it.
    """
    from lexmeter_fees.extract import to_reference_claim

    for savings_text, total, unit_price in (("$212 SAVINGS", 201600, 100800),
                                            ("$250 SAVINGS", 238000, 119000)):
        claim = to_reference_claim(savings_text, total)
        assert claim is not None
        assert total == unit_price * 2
        ratio = claim.savings_cents / total
        assert 0.104 < ratio < 0.106, (savings_text, ratio)
        assert claim.implied_reference_cents == total + claim.savings_cents


def test_undisclosed_savings_basis_flags():
    from lexmeter_fees.extract import to_reference_claim
    from lexmeter_fees.flags import Flag

    claim = to_reference_claim("$212 SAVINGS", 201600)
    obs = observation(
        "TickPick",
        [
            step(0, StepKind.DETAIL, "$1,008 each"),
            step(1, StepKind.REVIEW, "$1,008 each", "$2,016.00", quantity=2),
        ],
    )
    obs = FlowObservation(
        **{**obs.__dict__,
           "steps": obs.steps[:-1] + (
               Step(**{**obs.steps[-1].__dict__, "reference_claims": (claim,)}),)}
    )
    assert Flag.REFERENCE_PRICE_BASIS_UNDISCLOSED in evaluate(obs)


def test_disclosed_basis_does_not_flag():
    # A substantiated, disclosed methodology is lawful and must not be flagged.
    from lexmeter_fees.extract import to_reference_claim
    from lexmeter_fees.flags import Flag
    from lexmeter_fees.model import ReferencePriceClaim

    claim = to_reference_claim(
        "$212 SAVINGS", 201600,
        stated_basis="Compared to average fees charged by other major marketplaces",
    )
    assert isinstance(claim, ReferencePriceClaim)
    obs = observation("TickPick", [
        step(0, StepKind.DETAIL, "$1,008 each"),
        step(1, StepKind.REVIEW, "$1,008 each", "$2,016.00", quantity=2),
    ])
    obs = FlowObservation(**{**obs.__dict__, "steps": obs.steps[:-1] + (
        Step(**{**obs.steps[-1].__dict__, "reference_claims": (claim,)}),)})
    assert Flag.REFERENCE_PRICE_BASIS_UNDISCLOSED not in evaluate(obs)


def test_ordinary_text_is_not_read_as_a_savings_claim():
    from lexmeter_fees.extract import to_reference_claim

    assert to_reference_claim("Service Fee $18.40", 201600) is None
    assert to_reference_claim("Total (USD) $2,016.00", 201600) is None
