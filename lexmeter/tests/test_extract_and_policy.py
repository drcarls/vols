import pytest
from conftest import CONFIG

from lexmeter_fees.extract import (
    RawFeeRow,
    carry_forward,
    label_reads_optional,
    parse_money_cents,
    to_fee_line,
    to_fee_lines,
)
from lexmeter_fees.model import FeeCategory, Mandatory
from lexmeter_fees.politeness import (
    Blocked,
    HostGate,
    Pacer,
    Policy,
    PolicyViolation,
    assert_permitted,
    check_egress,
    check_response,
    user_agent,
)
from lexmeter_fees.taxonomy import classify, unclassified_rate


@pytest.fixture
def policy():
    return Policy.load(CONFIG / "collection_policy.yaml")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("$12.50", 1250),
        ("$1,234.56", 123456),
        ("USD 12.50", 1250),
        ("12", 1200),
        ("$1.5", 150),        # one decimal place is tenths, not hundredths
        ("-$5.00", -500),
        ("$0.00", 0),
        ("Free", 0),
        ("waived", 0),
        ("", None),
        ("tbd", None),
        (None, None),
    ],
)
def test_money_parsing(text, expected):
    assert parse_money_cents(text) == expected


def test_missing_amount_is_not_a_zero_fee():
    # Collapsing "unreadable" into "$0" would quietly understate every gap.
    assert parse_money_cents("tbd") is None
    assert parse_money_cents("Free") == 0


def test_unreadable_row_is_dropped_rather_than_zeroed():
    assert to_fee_line(RawFeeRow(label="Service Fee", amount_text="--"), 0) is None


def test_removability_drives_mandatory_classification():
    unknown = to_fee_line(RawFeeRow("Service Fee", "$5.00", removable=None), 0)
    optional = to_fee_line(RawFeeRow("Tip", "$5.00", removable=True), 0)
    mandatory = to_fee_line(RawFeeRow("Service Fee", "$5.00", removable=False), 0)
    # Absent evidence of a removal control, the fee stays UNKNOWN rather than
    # being guessed into a violation.
    assert unknown.mandatory is Mandatory.UNKNOWN
    assert optional.mandatory is Mandatory.OPTIONAL
    assert mandatory.mandatory is Mandatory.MANDATORY
    assert unknown.counts_toward_mandatory_total is False
    assert mandatory.counts_toward_mandatory_total is True


def test_tax_never_counts_toward_the_mandatory_total():
    tax = to_fee_line(RawFeeRow("Sales Tax", "$8.21", removable=False), 0)
    assert tax.category is FeeCategory.TAX
    assert tax.counts_toward_mandatory_total is False


def test_optional_wording_is_detected():
    assert label_reads_optional("Optional service charge")
    assert label_reads_optional("Service charge", "You may remove this at checkout")
    assert not label_reads_optional("Service charge")


def test_carry_forward_keeps_the_first_appearance():
    first = to_fee_lines([RawFeeRow("Service Fee", "$5.00", removable=False)], 1)
    restated = to_fee_lines([RawFeeRow("Service Fee", "$5.00", removable=False)], 3)
    merged = carry_forward(first, restated)
    assert len(merged) == 1
    assert merged[0].first_seen_step_index == 1


def test_taxonomy_covers_the_named_junk_fee_vocabulary():
    expected = {
        "Service Fee": FeeCategory.SERVICE,
        "Convenience Fee": FeeCategory.CONVENIENCE,
        "Processing Fee": FeeCategory.PROCESSING,
        "Resort Fee": FeeCategory.RESORT,
        "Destination Fee": FeeCategory.DESTINATION,
        "Reservation Fee": FeeCategory.RESERVATION,
        "Customer Facility Charge": FeeCategory.FACILITY,
        "Concession Recovery Fee": FeeCategory.CONCESSION_RECOVERY,
    }
    for label, category in expected.items():
        assert classify(label) is category, label


def test_unclassified_rate_tracks_taxonomy_drift():
    assert unclassified_rate(["Service Fee", "Wombat Levy"]) == 0.5
    assert unclassified_rate([]) == 0.0


def test_prohibited_actions_are_refused(policy):
    for action in ("captcha_solving", "login_or_account_creation",
                   "paywall_or_access_control_bypass", "completing_a_purchase"):
        with pytest.raises(PolicyViolation):
            assert_permitted(action, policy)


def test_permitted_action_passes(policy):
    assert_permitted("navigate", policy) is None


def test_block_statuses_and_markers(policy):
    for status in (401, 403, 429, 503):
        with pytest.raises(Blocked):
            check_response(status, "", policy)
    with pytest.raises(Blocked):
        check_response(200, "Please verify you are human", policy)
    check_response(200, "<html>normal page</html>", policy)  # no raise


def test_residential_egress_is_refused(policy):
    # Undocumented consent provenance makes the collection method the story.
    with pytest.raises(PolicyViolation, match="consent provenance"):
        check_egress("residential_consumer_pool", policy)
    check_egress("isp_or_datacenter_with_provenance_attestation", policy)


def test_user_agent_appends_rather_than_replaces(policy):
    ua = user_agent("Mozilla/5.0 (X11; Linux x86_64) Chrome/120", policy)
    assert ua.startswith("Mozilla/5.0")   # real UA preserved
    assert "Lexmeter" in ua               # identification appended


def test_host_gate_allows_one_session_per_host(policy):
    gate = HostGate(policy)
    assert gate.acquire("example.test", timeout=0.1)
    assert not gate.acquire("example.test", timeout=0.1)   # second is held off
    assert gate.acquire("other.test", timeout=0.1)         # different host is fine
    gate.release("example.test")
    assert gate.acquire("example.test", timeout=0.1)


def test_pacing_is_jittered_within_the_configured_band(policy):
    import random

    pacer = Pacer(policy, sleep=lambda _: None, rng=random.Random(7))
    delays = [pacer.next_delay() for _ in range(50)]
    assert all(policy.min_delay <= d <= policy.max_delay for d in delays)
    # A constant interval is a bot signature and contradicts the stated posture.
    assert len(set(delays)) > 1


# --- egress tier and product enforcement -----------------------------------

def test_default_tier_is_isp_not_alphabetical(policy):
    # 'datacenter' sorts before 'isp'. The default must come from the declared
    # value, or every capture silently runs on weaker provenance.
    assert policy.default_tier == "isp"


def test_isp_tier_is_allowed_without_justification(policy):
    from lexmeter_fees.politeness import check_egress_tier

    assert check_egress_tier("isp", policy) == "isp"
    assert check_egress_tier("ISP", policy) == "isp"


def test_residential_fallback_requires_a_recorded_reason(policy):
    from lexmeter_fees.politeness import check_egress_tier

    with pytest.raises(PolicyViolation, match="requires a recorded justification"):
        check_egress_tier("residential", policy)
    assert check_egress_tier(
        "residential", policy, justification="no ISP coverage for MN"
    ) == "residential"


def test_unknown_and_forbidden_tiers_are_refused(policy):
    from lexmeter_fees.politeness import check_egress_tier

    with pytest.raises(PolicyViolation):
        check_egress_tier("mobile", policy)      # explicitly forbidden
    with pytest.raises(PolicyViolation):
        check_egress_tier("whatever", policy)    # not in any list
    with pytest.raises(PolicyViolation, match="must be recorded"):
        check_egress_tier(None, policy)


@pytest.mark.parametrize("product", ["web_unlocker", "scraping_browser", "captcha_solver"])
def test_unblocking_products_are_refused(policy, product):
    # These are ordinary SKUs from the same vendor as the proxies, and they are
    # what one reaches for exactly when a target blocks the collector.
    from lexmeter_fees.politeness import check_egress_product

    with pytest.raises(PolicyViolation, match="CAPTCHA"):
        check_egress_product(product, policy)


def test_plain_proxy_use_is_permitted(policy):
    from lexmeter_fees.politeness import check_egress_product

    check_egress_product(None, policy)
    check_egress_product("residential_proxy", policy)
