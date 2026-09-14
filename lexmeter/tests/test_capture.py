"""End-to-end capture against local fixtures. No network, no live sites."""

from datetime import datetime, timezone

import pytest
from conftest import CONFIG, FIXTURES

from lexmeter_fees.capture import FlowRunner, FlowSpec
from lexmeter_fees.drivers.fixture_driver import BlockingDriver, FixtureDriver
from lexmeter_fees.flags import Flag, compute_metrics, evaluate
from lexmeter_fees.model import Anchor, StepKind
from lexmeter_fees.politeness import Policy
from lexmeter_fees.store import LocalArtifactStore

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def policy():
    return Policy.load(CONFIG / "collection_policy.yaml")


@pytest.fixture
def runner(policy, tmp_path):
    # sleep is stubbed: the pacing contract is tested separately, and real delays
    # would make the suite unusable.
    from lexmeter_fees.politeness import Pacer

    return FlowRunner(
        policy=policy,
        artifacts=LocalArtifactStore(tmp_path / "artifacts"),
        pacer=Pacer(policy, sleep=lambda _: None),
        clock=lambda: NOW,
    )


def drip_spec():
    return FlowSpec(
        flow_id="drip-ticketing",
        company="FixtureTickets",
        industry="live_event_ticketing",
        start_url="https://fixture.test/event",
        steps=[
            (StepKind.LISTING, "01_listing.html"),
            (StepKind.DETAIL, "02_detail.html"),
            (StepKind.CHECKOUT, "03_checkout.html"),
            (StepKind.REVIEW, "04_review.html"),
        ],
        anchor=Anchor(descriptor="venue=fixture;event=test"),
        vantage_state="NY",
    )


def all_in_spec():
    return FlowSpec(
        flow_id="allin-ticketing",
        company="CompliantTickets",
        industry="live_event_ticketing",
        start_url="https://fixture.test/event",
        steps=[
            (StepKind.LISTING, "01_listing.html"),
            (StepKind.DETAIL, "02_detail.html"),
            (StepKind.REVIEW, "03_review.html"),
        ],
        anchor=Anchor(descriptor="venue=fixture;event=test"),
        vantage_state="CA",
    )


def test_flow_must_end_at_review():
    # The no-purchase rule is structural: a flow that does not end at review is
    # rejected at construction, not trusted to stop in time.
    with pytest.raises(ValueError, match="REVIEW"):
        FlowSpec(
            flow_id="bad",
            company="X",
            industry="live_event_ticketing",
            start_url="https://fixture.test/",
            steps=[(StepKind.CHECKOUT, "a.html")],
            anchor=Anchor(descriptor="x"),
        )


def test_drip_fixture_captures_the_step_index_of_first_appearance(runner):
    obs = runner.run(drip_spec(), FixtureDriver(FIXTURES / "drip_ticketing"))
    assert obs.completed
    assert len(obs.steps) == 4

    metrics = compute_metrics(obs)
    assert metrics.headline_cents == 8900
    assert metrics.total_cents == 12051
    # $18.40 service + $4.90 order processing; the $8.21 tax is excluded.
    assert metrics.mandatory_fee_cents == 2330
    assert metrics.latest_mandatory_fee_first_step == 3
    assert metrics.all_in_shown_before_final_step is False

    flags = evaluate(obs)
    assert Flag.MANDATORY_FEE_AT_FINAL_STEP in flags
    assert Flag.HEADLINE_EXCLUDES_ALL_MANDATORY_FEES in flags


def test_all_in_fixture_raises_no_flags(runner):
    obs = runner.run(all_in_spec(), FixtureDriver(FIXTURES / "allin_ticketing"))
    assert compute_metrics(obs).all_in_shown_before_final_step is True
    assert evaluate(obs) == set()


def test_fee_first_seen_index_survives_being_restated(runner):
    obs = runner.run(all_in_spec(), FixtureDriver(FIXTURES / "allin_ticketing"))
    service = [
        line
        for line in obs.steps[-1].fee_lines
        if line.raw_label == "Service Fee"
    ]
    assert len(service) == 1
    # Present on all three pages, but it first appeared at step 0 and stays there.
    assert service[0].first_seen_step_index == 0


def test_artifacts_are_stored_for_every_step(runner, tmp_path):
    obs = runner.run(drip_spec(), FixtureDriver(FIXTURES / "drip_ticketing"))
    for step in obs.steps:
        kinds = {a.kind for a in step.artifacts}
        assert {"screenshot", "dom"} <= kinds
        for artifact in step.artifacts:
            assert len(artifact.digest) == 64


def test_block_is_recorded_and_aborts_rather_than_retrying(runner):
    obs = runner.run(drip_spec(), BlockingDriver(status=429, after_steps=2))
    assert obs.blocked_reason == "HTTP 429"
    assert obs.completed is False
    # The partial capture is kept: a block is a fact about the site, and the two
    # steps observed before it are still evidence.
    assert len(obs.steps) == 2


def test_body_marker_block_is_detected(runner):
    obs = runner.run(drip_spec(), BlockingDriver(status=200, body="Please verify you are human"))
    assert obs.blocked_reason.startswith("body marker")


def test_driver_is_closed_even_when_blocked(runner):
    driver = BlockingDriver(status=403)
    runner.run(drip_spec(), driver)
    # Context close is what flushes HAR and video; skipping it on an aborted run
    # would lose that run's evidence.
    assert driver.closed is True


def test_flow_exceeding_the_step_cap_is_refused(runner):
    spec = drip_spec()
    spec.steps = [(StepKind.CHECKOUT, "03_checkout.html")] * 20 + [(StepKind.REVIEW, "04_review.html")]
    with pytest.raises(ValueError, match="policy caps"):
        runner.run(spec, FixtureDriver(FIXTURES / "drip_ticketing"))


def test_provenance_is_written_at_capture_time(runner):
    obs = runner.run(drip_spec(), FixtureDriver(FIXTURES / "drip_ticketing"),
                     egress_provider="pending-vendor", policy_digest="abc")
    prov = runner.last_provenance
    assert prov is not None
    assert prov.egress_state == "NY"
    assert prov.egress_provider == "pending-vendor"
    # Not yet certifiable: no human custodian named. Better to carry the gap
    # visibly than to discover it when a declaration is due.
    assert prov.custodian is None
    assert obs.flow_id == "drip-ticketing"
