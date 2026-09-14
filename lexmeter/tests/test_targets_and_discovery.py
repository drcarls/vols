import pytest
from conftest import ROOT

from lexmeter_fees.discovery import (
    CHECKOUT_PATHS,
    RobotsAudit,
    audit_body,
    audit_domain,
    parse_wildcard_disallow,
)
from lexmeter_fees.targets import assert_uncaptured, load_targets

TARGETS = ROOT / "config" / "targets" / "ticketing.yaml"


# --- target list -----------------------------------------------------------

def test_target_list_loads():
    tl = load_targets(TARGETS)
    assert tl.industry == "live_event_ticketing"
    assert tl.phase == 1
    assert len(tl.targets) >= 20


def test_nothing_in_the_list_claims_an_observed_fee_display():
    # The list is a hypothesis about where to look. Guards against it drifting
    # into asserted fact before a single capture exists.
    assert_uncaptured(load_targets(TARGETS))


def test_sweep_order_puts_tier_a_high_yield_first():
    order = load_targets(TARGETS).sweep_order()
    assert order[0].tier == "A"
    assert order[0].expected_yield == "high"
    tiers = [t.tier for t in order]
    assert tiers == sorted(tiers)  # all of A before any of B


def test_negative_control_is_declared():
    # TickPick is built on all-in pricing. If the collector flags it, the
    # collector is wrong, and the sweep says so rather than publishing.
    controls = load_targets(TARGETS).negative_controls()
    assert [t.id for t in controls] == ["tickpick"]


def test_live_nation_subsidiaries_carry_their_ownership():
    tl = load_targets(TARGETS)
    for tid in ("ticketweb", "frontgate"):
        assert tl.by_id(tid).owned_by == "Live Nation Entertainment"


def test_known_defendants_are_marked():
    tl = load_targets(TARGETS)
    assert tl.by_id("ticketmaster").litigation_status == "active_defendant"
    assert tl.by_id("stubhub").litigation_status == "settled_ftc"


def test_assert_uncaptured_raises_when_a_display_is_claimed():
    tl = load_targets(TARGETS)
    tampered = tl.__class__(
        industry=tl.industry,
        phase=tl.phase,
        defaults=tl.defaults,
        targets=tuple(
            t.__class__(**{**t.__dict__, "fee_display": "all_in"}) if t.id == "etix" else t
            for t in tl.targets
        ),
        excluded=tl.excluded,
    )
    with pytest.raises(AssertionError, match="etix"):
        assert_uncaptured(tampered)


# --- robots.txt parsing ----------------------------------------------------

def test_wildcard_group_only():
    body = """
    User-agent: Googlebot
    Disallow: /secret

    User-agent: *
    Disallow: /checkout
    """
    assert parse_wildcard_disallow(body) == ("/checkout",)


def test_named_agent_rules_do_not_bind_us():
    # Reading a Googlebot-only rule as universal would overstate the conflict and
    # push the robots.txt posture decision the wrong way.
    body = "User-agent: Googlebot\nDisallow: /checkout\n"
    assert parse_wildcard_disallow(body) == ()


def test_shared_group_with_multiple_agents_includes_star():
    body = "User-agent: Bingbot\nUser-agent: *\nDisallow: /cart\n"
    assert parse_wildcard_disallow(body) == ("/cart",)


def test_empty_disallow_allows_everything():
    body = "User-agent: *\nDisallow:\n"
    assert parse_wildcard_disallow(body) == ()


def test_comments_are_stripped():
    body = "User-agent: *  # everyone\nDisallow: /cart  # no carts\n"
    assert parse_wildcard_disallow(body) == ("/cart",)


def test_checkout_conflict_is_detected():
    audit = audit_body("x.test", 200, "User-agent: *\nDisallow: /checkout\nDisallow: /cart\n")
    assert audit.conflicts_with_checkout_capture
    assert set(audit.checkout_paths_disallowed) == {"/checkout", "/cart"}


def test_wildcard_path_rule_covers_prefix():
    audit = audit_body("x.test", 200, "User-agent: *\nDisallow: /check*\n")
    assert "/checkout" in audit.checkout_paths_disallowed


def test_full_site_disallow():
    audit = audit_body("x.test", 200, "User-agent: *\nDisallow: /\n")
    assert audit.disallows_everything
    assert set(audit.checkout_paths_disallowed) == set(CHECKOUT_PATHS)


def test_no_conflict_when_only_unrelated_paths_blocked():
    audit = audit_body("x.test", 200, "User-agent: *\nDisallow: /admin\nDisallow: /api\n")
    assert not audit.conflicts_with_checkout_capture


def test_robots_body_is_hashed_for_the_record():
    a = audit_body("x.test", 200, "User-agent: *\nDisallow: /cart\n")
    b = audit_body("x.test", 200, "User-agent: *\nDisallow: /checkout\n")
    assert a.robots_sha256 != b.robots_sha256


# --- fetch handling --------------------------------------------------------

class StubFetcher:
    def __init__(self, status=200, body="", raises=None):
        self.status, self.body, self.raises = status, body, raises

    def get(self, url):
        if self.raises:
            raise self.raises
        return self.status, self.body


def test_missing_robots_is_not_a_restriction():
    audit = audit_domain("x.test", StubFetcher(status=404))
    assert audit.reachable and audit.status == 404
    assert not audit.conflicts_with_checkout_capture
    assert audit.robots_sha256 is None  # absence is distinguishable from unread


def test_transport_failure_is_recorded_not_raised():
    # The proxy denial that blocked this audit in the build environment lands here.
    audit = audit_domain("x.test", StubFetcher(raises=RuntimeError("CONNECT 403")))
    assert isinstance(audit, RobotsAudit)
    assert audit.reachable is False
    assert "CONNECT 403" in audit.error


def test_server_error_is_unreachable_not_permissive():
    audit = audit_domain("x.test", StubFetcher(status=503))
    assert audit.reachable is False
