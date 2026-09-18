import pytest
from conftest import ROOT

from lexmeter_fees.model import StepKind
from lexmeter_fees.selectors import (
    FieldSelector,
    SelectorSpec,
    SpecStatus,
    StepSelectors,
    Verdict,
    assert_verified_before_sweep,
    load_specs,
    reconcile,
)

SELECTORS = ROOT / "config" / "selectors" / "ticketing.yaml"
FLOW = [StepKind.LISTING, StepKind.DETAIL, StepKind.CHECKOUT, StepKind.REVIEW]


# --- reconciliation: the check that verifies a spec without knowing the site ---

def test_correct_readings_reconcile():
    # The drip fixture: 8900 headline, 1840 + 490 + 821 in lines, 12051 total.
    assert reconcile(8900, [1840, 490, 821], 12051).verdict is Verdict.OK


def test_a_missed_fee_line_is_detected_and_named():
    # This is the finding-destroying error: a fee the spec does not capture reads
    # as an absent fee, which reads as compliance.
    result = reconcile(8900, [1840, 490], 12051)
    assert result.verdict is Verdict.UNDER_COUNTED
    assert result.discrepancy_cents == 821
    assert "does not capture" in result.detail
    assert result.spec_is_suspect


def test_double_counting_is_detected():
    result = reconcile(8900, [1840, 1840, 490, 821], 12051)
    assert result.verdict is Verdict.OVER_COUNTED
    assert "double-counted" in result.detail


def test_all_in_display_reconciles_as_inclusive():
    # Eventbrite, 2026-09-18: headline $215.26 "incl. $15.26 Fee", total $215.26.
    # The fees are already inside the headline, so adding them again would report
    # a correct spec as double-counting.
    from lexmeter_fees.selectors import FeeTreatment

    result = reconcile(21526, [1526], 21526)
    assert result.verdict is Verdict.OK
    assert result.fee_treatment is FeeTreatment.INCLUSIVE


def test_arithmetic_cannot_distinguish_all_in_from_a_grabbed_total():
    """An honest limit, recorded rather than papered over.

    A headline selector that mistakenly matched the total produces exactly the
    arithmetic of a genuine all-in display: headline == total, with fee lines
    shown. No sum can separate them, so reconciliation reports both as INCLUSIVE.

    The real mis-grab is caught by cross-step consistency instead -- a spec that
    grabs the total will read a different headline at steps where no total is
    displayed. See `Verification.headline_inconsistency`.
    """
    from lexmeter_fees.selectors import FeeTreatment

    genuine_all_in = reconcile(21526, [1526], 21526)
    grabbed_total = reconcile(12051, [1840, 490, 821], 12051)
    assert genuine_all_in.fee_treatment is grabbed_total.fee_treatment is FeeTreatment.INCLUSIVE


def test_quantity_multiplies_the_headline():
    # Per-ticket headline against a two-ticket total. Without quantity a correct
    # spec would be reported as broken.
    assert reconcile(8900, [1000], 18800, quantity=2).verdict is Verdict.OK
    assert reconcile(8900, [1000], 18800, quantity=1).verdict is Verdict.UNDER_COUNTED


def test_rounding_tolerance_absorbs_cents_not_fees():
    assert reconcile(3333, [0], 3334, quantity=1).verdict is Verdict.OK      # 1c
    assert reconcile(3333, [0], 3433, quantity=1).verdict is Verdict.UNDER_COUNTED  # $1


def test_missing_total_is_not_checkable_rather_than_failing():
    # Early steps legitimately show no total. That is not a spec error.
    result = reconcile(8900, [], None)
    assert result.verdict is Verdict.NOT_CHECKABLE
    assert result.ok and not result.spec_is_suspect


def test_missing_headline_is_not_checkable():
    assert reconcile(None, [1840], 12051).verdict is Verdict.NOT_CHECKABLE


def test_zero_quantity_is_rejected():
    with pytest.raises(ValueError):
        reconcile(8900, [], 8900, quantity=0)


# --- structural checks -----------------------------------------------------

def test_fixture_spec_is_structurally_sound():
    spec = load_specs(SELECTORS)["_fixture_drip"]
    assert spec.structural_problems(FLOW) == []
    assert spec.status is SpecStatus.VERIFIED


def test_unauthored_spec_is_reported_as_such():
    assert load_specs(SELECTORS)["etix"].structural_problems(FLOW) == [
        "etix: no selectors authored"
    ]


def test_all_tier_a_specs_are_unauthored():
    # Guards the honesty of the config: nothing here was written against a real
    # DOM, and a guessed selector is worse than none.
    specs = load_specs(SELECTORS)
    real = {k: v for k, v in specs.items() if not k.startswith("_")}
    assert len(real) == 14
    assert all(v.status is SpecStatus.UNAUTHORED for v in real.values())
    assert len(assert_verified_before_sweep(specs, list(real))) == 14


def test_fee_row_without_an_amount_selector_is_a_problem():
    spec = SelectorSpec(
        target_id="t",
        domain="t.test",
        fallback=StepSelectors(
            headline=FieldSelector("h"),
            total=FieldSelector("tot"),
            fee_row=FieldSelector("row"),
        ),
    )
    problems = spec.structural_problems([StepKind.REVIEW])
    assert any("fee_amount missing" in p for p in problems)
    assert any("fee_label missing" in p for p in problems)


def test_step_with_no_price_reading_is_a_problem():
    spec = SelectorSpec(
        target_id="t",
        domain="t.test",
        fallback=StepSelectors(fee_row=FieldSelector("row", required=False)),
    )
    problems = spec.structural_problems([StepKind.LISTING])
    assert any("neither headline nor total" in p for p in problems)


def test_final_step_without_a_total_is_a_problem():
    # Without a final total there is no headline-to-total gap, which is the
    # headline number in every report.
    spec = SelectorSpec(
        target_id="t",
        domain="t.test",
        fallback=StepSelectors(headline=FieldSelector("h")),
    )
    problems = spec.structural_problems([StepKind.LISTING, StepKind.REVIEW])
    assert any("final step has no total selector" in p for p in problems)


def test_per_step_selectors_override_the_fallback():
    spec = load_specs(SELECTORS)["_fixture_drip"]
    # The fallback marks total optional; the review step requires it.
    assert spec.for_step(StepKind.LISTING).total.required is False
    assert spec.for_step(StepKind.REVIEW).total.required is True


def test_attribute_selectors_parse():
    spec = load_specs(SELECTORS)["_fixture_drip"]
    amount = spec.for_step(StepKind.REVIEW).fee_amount
    assert amount.attribute == "data-amount"


# --- verification gating ---------------------------------------------------

def test_verification_requires_an_arithmetic_check_that_actually_closed():
    from lexmeter_fees.authoring import StepVerification, Verification
    from lexmeter_fees.selectors import Reconciliation

    not_checkable = Verification(
        target_id="t",
        steps=[
            StepVerification(
                StepKind.REVIEW,
                Reconciliation(Verdict.NOT_CHECKABLE, None, None, None),
            )
        ],
    )
    # No step produced a closing check, so nothing has been proven. Marking this
    # verified is how an unverified spec reaches a live sweep.
    assert not_checkable.ok is True
    assert not_checkable.may_be_marked_verified is False
    assert "NOT VERIFIABLE" in not_checkable.summary()

    closed = Verification(
        target_id="t",
        steps=[
            StepVerification(
                StepKind.REVIEW, Reconciliation(Verdict.OK, 12051, 12051, 0)
            )
        ],
    )
    assert closed.may_be_marked_verified is True


def test_structural_problems_block_verification():
    from lexmeter_fees.authoring import StepVerification, Verification
    from lexmeter_fees.selectors import Reconciliation

    report = Verification(
        target_id="t",
        structural_problems=["t/review: no selectors"],
        steps=[
            StepVerification(StepKind.REVIEW, Reconciliation(Verdict.OK, 1, 1, 0))
        ],
    )
    assert report.ok is False
    assert report.may_be_marked_verified is False
