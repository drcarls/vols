from datetime import datetime, timezone

from lexmeter_fees.flags import Flag, compute_metrics, evaluate, evaluate_across_vantages
from lexmeter_fees.model import (
    Anchor,
    FeeCategory,
    FeeLine,
    FlowObservation,
    Mandatory,
    Step,
    StepKind,
)

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
ANCHOR = Anchor(descriptor="venue=test")


def fee(label, cents, step, category=FeeCategory.SERVICE, mandatory=Mandatory.MANDATORY, **kw):
    return FeeLine(
        raw_label=label,
        amount_cents=cents,
        category=category,
        mandatory=mandatory,
        first_seen_step_index=step,
        **kw,
    )


def obs(steps, *, state="NY", flow_id="f1", industry="live_event_ticketing"):
    return FlowObservation(
        flow_id=flow_id,
        company="TestCo",
        industry=industry,
        vantage_state=state,
        device="desktop",
        anchor=ANCHOR,
        started_at=NOW,
        steps=tuple(steps),
    )


def step(i, kind, headline=None, total=None, fees=()):
    return Step(
        index=i,
        kind=kind,
        url=f"https://example.test/{i}",
        observed_at=NOW,
        headline_price_cents=headline,
        displayed_total_cents=total,
        fee_lines=tuple(fees),
    )


def drip_observation(state="NY"):
    """Headline holds at $89 until a $18.40 fee lands on the final step."""
    service = fee("Service Fee", 1840, 3)
    return obs(
        [
            step(0, StepKind.LISTING, headline=8900),
            step(1, StepKind.DETAIL, headline=8900, total=8900),
            step(2, StepKind.CHECKOUT, headline=8900, total=8900),
            step(3, StepKind.REVIEW, headline=8900, total=10740, fees=[service]),
        ],
        state=state,
    )


def all_in_observation(state="CA"):
    """Same charges, disclosed in the initial display."""
    service = fee("Service Fee", 1840, 0)
    return obs(
        [
            step(0, StepKind.LISTING, headline=8900, total=10740, fees=[service]),
            step(1, StepKind.DETAIL, headline=8900, total=10740, fees=[service]),
            step(2, StepKind.REVIEW, headline=8900, total=10740, fees=[service]),
        ],
        state=state,
    )


def test_drip_flow_raises_the_core_flag():
    flags = evaluate(drip_observation())
    assert Flag.MANDATORY_FEE_AT_FINAL_STEP in flags
    assert Flag.HEADLINE_EXCLUDES_ALL_MANDATORY_FEES in flags


def test_all_in_flow_raises_nothing():
    # A large fee disclosed up front is not a violation, and a collector that
    # flags it would drown every league table in noise.
    assert evaluate(all_in_observation()) == set()


def test_gap_metrics():
    metrics = compute_metrics(drip_observation())
    assert metrics.headline_cents == 8900
    assert metrics.total_cents == 10740
    assert metrics.gap_abs_cents == 1840
    assert metrics.gap_pct == 20.6742
    assert metrics.latest_mandatory_fee_first_step == 3


def test_taxes_do_not_count_toward_the_mandatory_gap():
    # SB 478 and its analogues exclude government taxes; counting them would
    # manufacture violations out of lawful line items.
    tax = fee("Sales Tax", 821, 2, category=FeeCategory.TAX)
    observation = obs(
        [
            step(0, StepKind.LISTING, headline=8900),
            step(1, StepKind.CHECKOUT, headline=8900, total=8900),
            step(2, StepKind.REVIEW, headline=8900, total=9721, fees=[tax]),
        ]
    )
    assert compute_metrics(observation).mandatory_fee_cents == 0
    assert evaluate(observation) == set()


def test_single_step_flow_cannot_drip():
    # No funnel, no drip. Without this guard every short flow inflates the table.
    observation = obs([step(0, StepKind.REVIEW, headline=8900, total=10740,
                            fees=[fee("Service Fee", 1840, 0)])])
    assert Flag.MANDATORY_FEE_AT_FINAL_STEP not in evaluate(observation)


def test_restated_fee_is_counted_once():
    service = fee("Service Fee", 1840, 2)
    observation = obs(
        [
            step(0, StepKind.LISTING, headline=8900),
            step(1, StepKind.CHECKOUT, headline=8900),
            step(2, StepKind.REVIEW, headline=8900, total=10740, fees=[service]),
            # same fee restated on a later render of the same step content
        ]
    )
    assert compute_metrics(observation).mandatory_fee_cents == 1840


def test_optional_label_but_unavoidable():
    sneaky = fee("Optional service charge", 500, 1, label_says_optional=True,
                 mandatory=Mandatory.MANDATORY)
    observation = obs([
        step(0, StepKind.LISTING, headline=5000),
        step(1, StepKind.REVIEW, headline=5000, total=5500, fees=[sneaky]),
    ])
    assert Flag.OPTIONAL_LABEL_BUT_UNAVOIDABLE in evaluate(observation)


def test_restaurant_exemption_condition_fails_without_a_purpose():
    # SB 1524 exempts the fee only if its purpose is explained. No purpose text
    # on the menu display means the exemption does not attach.
    no_purpose = fee("Service Fee", 300, 0, purpose_text=None)
    observation = obs([
        step(0, StepKind.LISTING, headline=2000, fees=[no_purpose]),
        step(1, StepKind.REVIEW, headline=2000, total=2300, fees=[no_purpose]),
    ], industry="restaurants")
    assert Flag.RESTAURANT_EXEMPTION_CONDITION_FAILED in evaluate(observation)


def test_restaurant_exemption_holds_when_purpose_is_explained():
    explained = fee("Service Fee", 300, 0, purpose_text="Supports staff wages")
    observation = obs([
        step(0, StepKind.LISTING, headline=2000, total=2300, fees=[explained]),
        step(1, StepKind.REVIEW, headline=2000, total=2300, fees=[explained]),
    ], industry="restaurants")
    assert Flag.RESTAURANT_EXEMPTION_CONDITION_FAILED not in evaluate(observation)


def test_display_switching_across_vantages():
    # The company renders all-in to CA and drips to NY: it can comply, and does
    # so selectively. This is the knowledge fact, and it is the point of the probe.
    flags = evaluate_across_vantages([all_in_observation("CA"), drip_observation("NY")])
    assert Flag.JURISDICTIONAL_DISPLAY_SWITCHING in flags


def test_no_switching_when_every_vantage_drips():
    flags = evaluate_across_vantages([drip_observation("CA"), drip_observation("NY")])
    assert Flag.JURISDICTIONAL_DISPLAY_SWITCHING not in flags


def test_fee_amount_variance_across_vantages():
    a = obs([step(0, StepKind.LISTING, headline=5000),
             step(1, StepKind.REVIEW, headline=5000, total=5500,
                  fees=[fee("Service Fee", 500, 1)])], state="CA")
    b = obs([step(0, StepKind.LISTING, headline=5000),
             step(1, StepKind.REVIEW, headline=5000, total=5700,
                  fees=[fee("Service Fee", 700, 1)])], state="NY")
    assert Flag.FEE_VARIES_BY_VANTAGE in evaluate_across_vantages([a, b])


def test_cross_vantage_refuses_to_mix_flows():
    import pytest

    a = drip_observation("CA")
    b = obs([step(0, StepKind.REVIEW, headline=1)], state="NY", flow_id="other")
    with pytest.raises(ValueError):
        evaluate_across_vantages([a, b])


def test_restaurant_exemption_flag_does_not_fire_outside_food_industries():
    # Guards against the flag leaking into ticketing and lodging, where SB 1524
    # has nothing to say.
    no_purpose = fee("Service Fee", 300, 0, purpose_text=None)
    observation = obs([
        step(0, StepKind.LISTING, headline=2000, total=2300, fees=[no_purpose]),
        step(1, StepKind.REVIEW, headline=2000, total=2300, fees=[no_purpose]),
    ], industry="live_event_ticketing")
    assert Flag.RESTAURANT_EXEMPTION_CONDITION_FAILED not in evaluate(observation)
