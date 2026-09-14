from datetime import date

from conftest import CONFIG

from lexmeter_fees.flags import Flag
from lexmeter_fees.rules import load_rules, resolve, unverified_rule_ids

RULES = load_rules(CONFIG / "jurisdictions.yaml")
DRIP = {Flag.MANDATORY_FEE_AT_FINAL_STEP, Flag.HEADLINE_EXCLUDES_ALL_MANDATORY_FEES}


def ids(findings):
    return {f.rule_id for f in findings}


def test_ca_ticketing_engages_both_federal_and_state():
    found = resolve(DRIP, industry="live_event_ticketing", vantage_state="CA",
                    observed_on=date(2026, 9, 1), rules=RULES)
    assert ids(found) == {"US-FED", "US-CA"}


def test_federal_rule_is_sector_limited():
    # The rule reaches live-event tickets and short-term lodging only. Asserting
    # it over car rental would be the fastest way to lose a reader's trust.
    found = resolve(DRIP, industry="car_rental", vantage_state="MN",
                    observed_on=date(2026, 9, 1), rules=RULES)
    assert ids(found) == {"US-MN"}


def test_federal_rule_covers_lodging():
    found = resolve(DRIP, industry="short_term_lodging", vantage_state="NY",
                    observed_on=date(2026, 9, 1), rules=RULES)
    assert ids(found) == {"US-FED"}


def test_nothing_engages_before_the_effective_date():
    # SB 478 from 2024-07-01, the federal rule from 2025-05-12. An observation in
    # January 2024 engages neither.
    found = resolve(DRIP, industry="live_event_ticketing", vantage_state="CA",
                    observed_on=date(2024, 1, 1), rules=RULES)
    assert found == []


def test_date_boundary_is_inclusive_of_the_effective_day():
    found = resolve(DRIP, industry="live_event_ticketing", vantage_state="CA",
                    observed_on=date(2024, 7, 1), rules=RULES)
    assert ids(found) == {"US-CA"}
    day_before = resolve(DRIP, industry="live_event_ticketing", vantage_state="CA",
                         observed_on=date(2024, 6, 30), rules=RULES)
    assert day_before == []


def test_colorado_not_in_force_in_2025():
    assert resolve(DRIP, industry="attractions", vantage_state="CO",
                   observed_on=date(2025, 12, 31), rules=RULES) == []
    assert ids(resolve(DRIP, industry="attractions", vantage_state="CO",
                       observed_on=date(2026, 1, 1), rules=RULES)) == {"US-CO"}


def test_private_right_of_action_is_surfaced_per_rule():
    found = resolve(DRIP, industry="live_event_ticketing", vantage_state="CA",
                    observed_on=date(2026, 9, 1), rules=RULES)
    by_id = {f.rule_id: f for f in found}
    assert by_id["US-CA"].private_right_of_action is True
    assert by_id["US-FED"].private_right_of_action is False
    assert "No private right of action" in by_id["US-FED"].note


def test_nj_is_marked_as_enforcement_posture_not_a_new_cause_of_action():
    found = resolve(DRIP, industry="food_delivery", vantage_state="NJ",
                    observed_on=date(2026, 9, 1), rules=RULES)
    nj = {f.rule_id: f for f in found}["US-NJ"]
    assert "Enforcement posture" in nj.note


def test_nj_posture_not_in_force_before_the_statement():
    assert resolve(DRIP, industry="food_delivery", vantage_state="NJ",
                   observed_on=date(2026, 6, 1), rules=RULES) == []


def test_unverified_rules_are_listed_and_never_assertable():
    unverified = unverified_rule_ids(RULES)
    assert "US-CT" in unverified and "US-OR" in unverified
    found = resolve(DRIP, industry="short_term_lodging", vantage_state="CT",
                    observed_on=date(2026, 9, 1), rules=RULES)
    # No effective date recorded, so it cannot be in force and cannot be asserted.
    assert all(not f.assertable for f in found if f.rule_id == "US-CT")


def test_every_confirmed_rule_carries_an_effective_date():
    # A rule marked confirmed but missing its date would silently never fire.
    for rule in RULES:
        if rule.verification == "confirmed":
            assert rule.effective is not None, rule.id


def test_no_flags_means_no_findings():
    assert resolve(set(), industry="live_event_ticketing", vantage_state="CA",
                   observed_on=date(2026, 9, 1), rules=RULES) == []
