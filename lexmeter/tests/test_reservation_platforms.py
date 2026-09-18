"""Reservation platforms: the sector, the vendor flag, and the target list."""

from datetime import date, datetime, timezone

import pytest
import yaml
from conftest import CONFIG, ROOT

from lexmeter_fees.extract import RawFeeRow, to_fee_lines
from lexmeter_fees.flags import Flag, evaluate
from lexmeter_fees.model import Anchor, FlowObservation, Step, StepKind
from lexmeter_fees.rules import load_rules, resolve

TARGETS = ROOT / "config" / "targets" / "reservation_platforms.yaml"
RULES = load_rules(CONFIG / "jurisdictions.yaml")
NOW = datetime(2026, 9, 18, tzinfo=timezone.utc)


def booking(fees, *, vendor_operated=True, state="CA"):
    return FlowObservation(
        flow_id="tyler:CA", company="Tyler Technologies (US eDirect)",
        industry="reservation_platforms", vantage_state=state, device="desktop",
        anchor=Anchor(descriptor="park=example"), started_at=NOW,
        agency_branded_vendor_operated=vendor_operated,
        steps=(
            Step(0, StepKind.LISTING, "https://x.test/0", NOW, headline_price_cents=3500),
            Step(1, StepKind.REVIEW, "https://x.test/1", NOW,
                 headline_price_cents=3500, displayed_total_cents=3500 + sum(f.amount_cents for f in fees),
                 quantity=1, fee_lines=tuple(fees)),
        ),
    )


# --- the sector is not covered by the federal rule -------------------------

def test_federal_fee_rule_does_not_reach_this_sector():
    # 16 CFR pt. 464 is limited to live-event tickets and short-term lodging.
    # Asserting it here would be the fastest way to lose a reader's trust, and it
    # is also the structural reason this sector did not converge on all-in.
    found = resolve(
        {Flag.MANDATORY_FEE_AT_FINAL_STEP}, industry="reservation_platforms",
        vantage_state="CA", observed_on=date(2026, 9, 18), rules=RULES,
    )
    assert {f.rule_id for f in found} == {"US-CA"}


def test_control_state_yields_nothing_in_this_sector():
    # NY has no cross-sector all-in statute and the federal rule does not apply,
    # so a drip finding there engages no rule at all. That is what makes NY a
    # control rather than a target.
    assert resolve(
        {Flag.MANDATORY_FEE_AT_FINAL_STEP}, industry="reservation_platforms",
        vantage_state="NY", observed_on=date(2026, 9, 18), rules=RULES,
    ) == []


@pytest.mark.parametrize("state", ["MN", "VA", "MA"])
def test_priority_states_engage_a_rule_but_remedy_is_unconfirmed(state):
    """The priority deployments engage a statute -- but with no confirmed remedy.

    This is load-bearing rather than pedantic. MN, VA and MA are where the Tyler
    and Aspira screens point, and whether those statutes carry a private right of
    action decides whether a finding there is a plaintiff-firm lead or only
    regulator exposure. The config records it as unknown, and this test fails the
    moment someone fills it in without saying so.
    """
    found = resolve(
        {Flag.MANDATORY_FEE_AT_FINAL_STEP}, industry="reservation_platforms",
        vantage_state=state, observed_on=date(2026, 9, 18), rules=RULES,
    )
    assert [f.rule_id for f in found] == [f"US-{state}"]
    assert found[0].private_right_of_action is None, (
        f"US-{state} private right of action is now set -- confirm the source and "
        "update this test deliberately"
    )


# --- the Chowning gravamen: who does the page say keeps the fee? -----------

def test_undisclosed_beneficiary_flags_on_a_vendor_operated_agency_site():
    fees = to_fee_lines([RawFeeRow("Reservation Fee", "$7.99", removable=False)], 1)
    assert Flag.VENDOR_FEE_BENEFICIARY_UNDISCLOSED in evaluate(booking(fees))


def test_disclosed_beneficiary_does_not_flag():
    # A page that says who keeps the fee is not making the inference available.
    from lexmeter_fees.model import FeeLine

    line = to_fee_lines([RawFeeRow("Reservation Fee", "$7.99", removable=False)], 1)[0]
    disclosed = FeeLine(**{**line.__dict__,
                          "stated_beneficiary": "Retained by the reservation service provider"})
    assert Flag.VENDOR_FEE_BENEFICIARY_UNDISCLOSED not in evaluate(booking([disclosed]))


def test_flag_does_not_fire_on_a_site_that_is_not_agency_branded():
    # A private campground's own booking page invites no inference about an agency.
    fees = to_fee_lines([RawFeeRow("Reservation Fee", "$7.99", removable=False)], 1)
    assert Flag.VENDOR_FEE_BENEFICIARY_UNDISCLOSED not in evaluate(
        booking(fees, vendor_operated=False)
    )


def test_statutory_tax_does_not_trigger_the_beneficiary_flag():
    # Government-imposed charges are excluded from the mandatory total, so they
    # never reach the beneficiary test. Counting them would manufacture findings
    # out of lawful line items.
    fees = to_fee_lines([RawFeeRow("State Occupancy Tax", "$4.20", removable=False)], 1)
    assert Flag.VENDOR_FEE_BENEFICIARY_UNDISCLOSED not in evaluate(booking(fees))


# --- target list hygiene ---------------------------------------------------

def test_target_list_claims_no_captures():
    doc = yaml.safe_load(TARGETS.read_text())
    assert doc["meta"]["captured"] is False
    assert doc["meta"]["ftc_rule_applies"] is False


def test_every_deployment_carries_a_verification_state():
    doc = yaml.safe_load(TARGETS.read_text())
    for target in doc["targets"]:
        for dep in target.get("deployments", []):
            assert "verification" in dep, (target["id"], dep)


def test_only_california_is_marked_in_litigation():
    # The screen is the deployments that are not. If a second one is ever marked
    # in_litigation, the screen shrinks and someone should notice deliberately.
    doc = yaml.safe_load(TARGETS.read_text())
    in_lit = [
        (t["id"], d.get("state"))
        for t in doc["targets"]
        for d in t.get("deployments", [])
        if d.get("status") == "in_litigation"
    ]
    assert in_lit == [("tyler_usedirect", "CA")]


def test_falsification_condition_is_stated_in_advance():
    # Stated before capture so the answer cannot be chosen after the fact.
    doc = yaml.safe_load(TARGETS.read_text())
    assert doc["falsification"]
