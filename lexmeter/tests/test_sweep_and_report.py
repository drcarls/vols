"""Phase 1 orchestration and reporting, exercised end to end on fixtures."""

from datetime import datetime, timezone

from conftest import CONFIG, FIXTURES, ROOT

from lexmeter_fees.capture import FlowRunner
from lexmeter_fees.drivers.fixture_driver import BlockingDriver, FixtureDriver
from lexmeter_fees.flags import Flag
from lexmeter_fees.model import StepKind
from lexmeter_fees.politeness import Pacer, Policy
from lexmeter_fees.report import (
    build_company_report,
    build_league_table,
    build_screen,
    load_patterns,
)
from lexmeter_fees.rules import load_rules
from lexmeter_fees.store import LocalArtifactStore, SqliteObservationStore
from lexmeter_fees.sweep import build_flow, run_differential_probe, run_sweep
from lexmeter_fees.targets import load_targets

TARGETS = ROOT / "config" / "targets" / "ticketing.yaml"
NOW = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
RULES = load_rules(CONFIG / "jurisdictions.yaml")
PATTERNS = load_patterns(CONFIG / "fact_patterns.yaml")

DRIP_STEPS = (StepKind.LISTING, StepKind.DETAIL, StepKind.CHECKOUT, StepKind.REVIEW)
DRIP_ACTIONS = {
    StepKind.LISTING: "01_listing.html",
    StepKind.DETAIL: "02_detail.html",
    StepKind.CHECKOUT: "03_checkout.html",
    StepKind.REVIEW: "04_review.html",
}
ALLIN_STEPS = (StepKind.LISTING, StepKind.DETAIL, StepKind.REVIEW)
ALLIN_ACTIONS = {
    StepKind.LISTING: "01_listing.html",
    StepKind.DETAIL: "02_detail.html",
    StepKind.REVIEW: "03_review.html",
}


def make_runner(tmp_path):
    policy = Policy.load(CONFIG / "collection_policy.yaml")
    return FlowRunner(
        policy=policy,
        artifacts=LocalArtifactStore(tmp_path / "artifacts"),
        pacer=Pacer(policy, sleep=lambda _: None),
        clock=lambda: NOW,
    )


def drip_flow(target, deployment, vantage):
    return build_flow(target, deployment, vantage, steps=DRIP_STEPS, actions=DRIP_ACTIONS)


def test_sweep_runs_tier_a_before_tier_b(tmp_path, monkeypatch):
    import lexmeter_fees.sweep as sweep_mod

    monkeypatch.setattr(sweep_mod, "build_flow", drip_flow)
    seen = []

    def factory(target, deployment, vantage):
        seen.append(target.tier)
        return FixtureDriver(FIXTURES / "drip_ticketing")

    tl = load_targets(TARGETS)
    store = SqliteObservationStore(tmp_path / "obs.db")
    run_sweep(tl, make_runner(tmp_path), factory, store, clock=lambda: NOW)
    assert seen == sorted(seen)  # every Tier A flow before any Tier B flow


def test_sweep_stores_observations_and_anchors_the_day(tmp_path, monkeypatch):
    import lexmeter_fees.sweep as sweep_mod

    monkeypatch.setattr(sweep_mod, "build_flow", drip_flow)
    tl = load_targets(TARGETS)
    store = SqliteObservationStore(tmp_path / "obs.db")
    result = run_sweep(
        tl,
        make_runner(tmp_path),
        lambda *_: FixtureDriver(FIXTURES / "drip_ticketing"),
        store,
        only_tiers={"B"},
        clock=lambda: NOW,
    )
    assert result.captured == len(result.observations)
    assert result.anchor is not None
    assert result.anchor.leaf_count == len(result.digests)
    assert store.anchor_for(NOW.date())["root"] == result.anchor.root


def test_negative_control_failure_marks_the_sweep_untrustworthy(tmp_path, monkeypatch):
    # Every target served the dripping fixture, including TickPick. The sweep must
    # notice that its own negative control flagged and refuse to vouch for itself.
    import lexmeter_fees.sweep as sweep_mod

    monkeypatch.setattr(sweep_mod, "build_flow", drip_flow)
    tl = load_targets(TARGETS)
    store = SqliteObservationStore(tmp_path / "obs.db")
    result = run_sweep(
        tl,
        make_runner(tmp_path),
        lambda *_: FixtureDriver(FIXTURES / "drip_ticketing"),
        store,
        only_tiers={"B"},
        clock=lambda: NOW,
    )
    assert result.control_failures
    assert result.trustworthy is False


def test_clean_sweep_is_trustworthy(tmp_path, monkeypatch):
    import lexmeter_fees.sweep as sweep_mod

    monkeypatch.setattr(
        sweep_mod,
        "build_flow",
        lambda t, d, v, **kw: build_flow(t, d, v, steps=ALLIN_STEPS, actions=ALLIN_ACTIONS),
    )
    tl = load_targets(TARGETS)
    store = SqliteObservationStore(tmp_path / "obs.db")
    result = run_sweep(
        tl,
        make_runner(tmp_path),
        lambda *_: FixtureDriver(FIXTURES / "allin_ticketing"),
        store,
        only_tiers={"B"},
        clock=lambda: NOW,
    )
    assert result.trustworthy is True
    assert not result.control_failures


def test_blocked_targets_are_logged_not_dropped(tmp_path, monkeypatch):
    import lexmeter_fees.sweep as sweep_mod

    monkeypatch.setattr(sweep_mod, "build_flow", drip_flow)
    tl = load_targets(TARGETS)
    store = SqliteObservationStore(tmp_path / "obs.db")
    result = run_sweep(
        tl,
        make_runner(tmp_path),
        lambda *_: BlockingDriver(status=403),
        store,
        only_tiers={"B"},
        clock=lambda: NOW,
    )
    assert result.blocked
    assert result.captured == 0
    # Still stored: a block is evidence about the site.
    assert len(result.digests) == len(result.observations)


def test_differential_probe_detects_display_switching(tmp_path, monkeypatch):
    import lexmeter_fees.sweep as sweep_mod

    def per_vantage(target, deployment, vantage):
        # All-in to California, drip to New York.
        folder = "allin_ticketing" if vantage == "CA" else "drip_ticketing"
        return FixtureDriver(FIXTURES / folder)

    def flow(t, d, v, **kw):
        steps, actions = (ALLIN_STEPS, ALLIN_ACTIONS) if v == "CA" else (DRIP_STEPS, DRIP_ACTIONS)
        return build_flow(t, d, v, steps=steps, actions=actions)

    monkeypatch.setattr(sweep_mod, "build_flow", flow)
    tl = load_targets(TARGETS)
    store = SqliteObservationStore(tmp_path / "obs.db")
    probe = run_differential_probe(
        tl.by_id("axs"), "arena_concert", make_runner(tmp_path), per_vantage, store, ["CA", "NY"]
    )
    assert probe.switching is True


# --- reporting -------------------------------------------------------------

def capture(tmp_path, target_id="etix", vantage="CA", drip=True):
    tl = load_targets(TARGETS)
    target = tl.by_id(target_id)
    steps, actions, folder = (
        (DRIP_STEPS, DRIP_ACTIONS, "drip_ticketing")
        if drip
        else (ALLIN_STEPS, ALLIN_ACTIONS, "allin_ticketing")
    )
    spec = build_flow(target, "default", vantage, steps=steps, actions=actions)
    return make_runner(tmp_path).run(spec, FixtureDriver(FIXTURES / folder))


def test_company_report_carries_rule_and_remedy(tmp_path):
    report = build_company_report(capture(tmp_path, vantage="CA"), rules=RULES)
    assert Flag.MANDATORY_FEE_AT_FINAL_STEP in report.flags
    rule_ids = {f.rule_id for f in report.findings}
    assert rule_ids == {"US-FED", "US-CA"}
    # Only the CLRA route is sellable to a plaintiff firm.
    assert report.actionable_for_plaintiff is True


def test_control_state_yields_federal_exposure_only(tmp_path):
    report = build_company_report(capture(tmp_path, vantage="NY"), rules=RULES)
    assert {f.rule_id for f in report.findings} == {"US-FED"}
    assert report.actionable_for_plaintiff is False


def test_evidence_digests_are_linked_from_the_report(tmp_path):
    report = build_company_report(capture(tmp_path), rules=RULES)
    assert len(report.evidence_digests) >= 8  # screenshot + DOM per step
    assert all(len(d) == 64 for d in report.evidence_digests)


def test_blocked_report_is_not_reported_as_clean(tmp_path):
    tl = load_targets(TARGETS)
    spec = build_flow(tl.by_id("ticketmaster"), "arena_concert", "NY",
                      steps=DRIP_STEPS, actions=DRIP_ACTIONS)
    obs = make_runner(tmp_path).run(spec, BlockingDriver(status=403))
    report = build_company_report(obs, rules=RULES)
    assert report.blocked is True
    assert report.flags == frozenset()
    assert report.findings == ()


def test_league_table_excludes_blocked_runs_from_the_denominator(tmp_path):
    # Otherwise the most aggressive bot management scores as the cleanest operator.
    drip = build_company_report(capture(tmp_path), rules=RULES)
    tl = load_targets(TARGETS)
    spec = build_flow(tl.by_id("etix"), "default", "NY", steps=DRIP_STEPS, actions=DRIP_ACTIONS)
    blocked = build_company_report(
        make_runner(tmp_path).run(spec, BlockingDriver(status=429)), rules=RULES
    )
    row = build_league_table([drip, blocked])[0]
    assert row.observations == 2
    assert row.blocked == 1
    assert row.density == 1.0  # 1 flagged of 1 usable, not 0.5 of 2


def test_league_table_ranks_by_density_then_gap(tmp_path):
    dirty = build_company_report(capture(tmp_path, "etix"), rules=RULES)
    clean = build_company_report(capture(tmp_path, "tickpick", drip=False), rules=RULES)
    rows = build_league_table([clean, dirty])
    assert rows[0].company == "Etix"
    assert rows[-1].density == 0.0


def test_screen_matches_the_last_step_service_charge_pattern(tmp_path):
    report = build_company_report(capture(tmp_path, "etix"), rules=RULES)
    screen = build_screen([report], litigation_status={}, patterns=PATTERNS)
    ids = {m.pattern_id for m in screen.matches}
    assert "last_step_service_charge" in ids
    match = next(m for m in screen.matches if m.pattern_id == "last_step_service_charge")
    assert "FTC and seven states v. Live Nation Entertainment / Ticketmaster" in match.anchor_cases


def test_screen_excludes_companies_already_litigated(tmp_path):
    # A defendant already facing the claim is not a lead. This filter is the
    # product, so it is tested rather than assumed.
    etix = build_company_report(capture(tmp_path, "etix"), rules=RULES)
    tm = build_company_report(capture(tmp_path, "ticketmaster"), rules=RULES)
    screen = build_screen(
        [etix, tm],
        litigation_status={"Ticketmaster (Live Nation Entertainment)": "active_defendant"},
        patterns=PATTERNS,
    )
    lead_companies = {m.company for m in screen.leads}
    assert "Etix" in lead_companies
    assert "Ticketmaster (Live Nation Entertainment)" not in lead_companies
    assert screen.excluded_as_litigated


def test_novel_pattern_is_not_counted_as_a_filed_case_lead(tmp_path):
    # jurisdictional_display_switching has no anchor case; it must not be sold as
    # resembling one.
    report = build_company_report(capture(tmp_path, "etix"), rules=RULES)
    screen = build_screen([report], patterns=PATTERNS)
    for match in screen.leads:
        assert match.anchor_cases, match.pattern_id


def test_clean_company_produces_no_screen_match(tmp_path):
    report = build_company_report(capture(tmp_path, "tickpick", drip=False), rules=RULES)
    assert build_screen([report], patterns=PATTERNS).matches == []
