"""Selector specs, and the machinery that keeps them honest.

Selectors are the weak joint in the whole collector. They are site-specific, they
rot without warning, and their failure mode is silent: a selector that stops
matching returns nothing, nothing parses to no fee, and no fee reads as a
compliant page. A collector that quietly reports its blindest targets as its
cleanest is worse than one that does not run.

Two defences, and they are the reason this module exists rather than a dict of
CSS strings living in the driver:

1. **Required selectors fail loudly.** A required field that matches nothing
   raises :class:`SelectorError` and the capture is recorded as an error, never as
   a zero.

2. **The numbers must reconcile.** ``headline x quantity + every displayed fee``
   has to equal the total the page itself shows. That check needs no knowledge of
   the site, so it verifies a spec written by someone who has never seen its DOM,
   and it diagnoses the failure directionally: a positive discrepancy means a fee
   line was missed, a negative one means something was double-counted or the
   headline selector grabbed the wrong element.

Reconciliation deliberately counts *every* displayed line including tax and
shipping, because the page's total includes them. That is the opposite of the
legal test in flags.py, which excludes them because the statutes do. Same numbers,
different questions.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .model import StepKind


class SelectorError(RuntimeError):
    """A required selector matched nothing. The capture is an error, not a zero."""


@dataclass(frozen=True)
class FieldSelector:
    css: str
    #: A required field that matches nothing aborts the capture. Optional fields
    #: (a purpose blurb, a remove control) legitimately may not exist.
    required: bool = True
    #: Read an attribute rather than the element's text, where the displayed value
    #: lives in one (``content``, ``data-price``, ``aria-label``).
    attribute: str | None = None

    @classmethod
    def parse(cls, value: Any) -> "FieldSelector | None":
        if value is None:
            return None
        if isinstance(value, str):
            return cls(css=value)
        return cls(
            css=value["css"],
            required=bool(value.get("required", True)),
            attribute=value.get("attribute"),
        )


@dataclass(frozen=True)
class StepSelectors:
    """Selectors for one step kind.

    Per step, not per site: a listing page and a checkout page are different
    documents, and a single spec per site is the most common way these go wrong.
    """

    headline: FieldSelector | None = None
    total: FieldSelector | None = None
    quantity: FieldSelector | None = None
    fee_row: FieldSelector | None = None
    fee_label: FieldSelector | None = None
    fee_amount: FieldSelector | None = None
    fee_purpose: FieldSelector | None = None
    fee_remove_control: FieldSelector | None = None

    @classmethod
    def parse(cls, doc: dict[str, Any] | None) -> "StepSelectors":
        doc = doc or {}
        return cls(**{f: FieldSelector.parse(doc.get(f)) for f in cls.__annotations__})

    @property
    def authored(self) -> bool:
        return any(getattr(self, f) is not None for f in self.__annotations__)

    def missing_required_for_fees(self) -> list[str]:
        """Fee extraction needs a row plus an amount; a label alone reads nothing."""
        if self.fee_row is None:
            return []
        missing = []
        if self.fee_amount is None:
            missing.append("fee_amount")
        if self.fee_label is None:
            missing.append("fee_label")
        return missing


class SpecStatus(enum.Enum):
    UNAUTHORED = "unauthored"
    #: Selectors written but never run against a saved page.
    AUTHORED = "authored"
    #: Extracts, and the arithmetic reconciles on a saved page.
    VERIFIED = "verified"


@dataclass(frozen=True)
class SelectorSpec:
    target_id: str
    domain: str
    by_step: dict[StepKind, StepSelectors] = field(default_factory=dict)
    #: Applied where a step has no entry of its own.
    fallback: StepSelectors = field(default_factory=StepSelectors)
    status: SpecStatus = SpecStatus.UNAUTHORED
    authored_against_url: str | None = None
    authored_on: str | None = None
    notes: str | None = None

    def for_step(self, kind: StepKind) -> StepSelectors:
        return self.by_step.get(kind, self.fallback)

    @property
    def authored(self) -> bool:
        return self.fallback.authored or any(s.authored for s in self.by_step.values())

    def structural_problems(self, flow: list[StepKind]) -> list[str]:
        """Checks that need no browser: is this spec even coherent?

        Catches the errors that are cheapest to make and most expensive to find
        during a live sweep.
        """
        problems: list[str] = []
        if not self.authored:
            return [f"{self.target_id}: no selectors authored"]

        for kind in flow:
            step = self.for_step(kind)
            if not step.authored:
                problems.append(f"{self.target_id}/{kind.value}: no selectors")
                continue
            if step.headline is None and step.total is None:
                problems.append(
                    f"{self.target_id}/{kind.value}: neither headline nor total; "
                    "the step can contribute no price reading"
                )
            for missing in step.missing_required_for_fees():
                problems.append(
                    f"{self.target_id}/{kind.value}: fee_row set but {missing} missing"
                )

        final = flow[-1] if flow else None
        if final is not None and self.for_step(final).total is None:
            problems.append(
                f"{self.target_id}/{final.value}: final step has no total selector, "
                "so the headline-to-total gap cannot be computed"
            )
        return problems


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

class FeeTreatment(enum.Enum):
    """How the displayed fee lines relate to the displayed headline.

    Not a workaround for two possible arithmetics -- it *is* the compliance
    question. A headline that already contains the mandatory fees is an all-in
    display; one the fees are added to is not. Resolving which closes the books
    therefore answers the thing the collector exists to measure.
    """

    #: total = headline x quantity + fees. Fees sit on top.
    EXCLUSIVE = "exclusive"
    #: total = headline x quantity. Fees are already inside the headline.
    INCLUSIVE = "inclusive"
    #: Both close, because the fees sum to nothing. Nothing to distinguish.
    INDETERMINATE = "indeterminate"
    UNRESOLVED = "unresolved"


class Verdict(enum.Enum):
    OK = "ok"
    #: Total exceeds what we accounted for: a fee line was missed.
    UNDER_COUNTED = "under_counted"
    #: Total is below what we accounted for: double-count, or a wrong headline.
    OVER_COUNTED = "over_counted"
    #: The page showed no total, so nothing can be checked here.
    NOT_CHECKABLE = "not_checkable"


@dataclass(frozen=True)
class Reconciliation:
    verdict: Verdict
    expected_cents: int | None
    total_cents: int | None
    discrepancy_cents: int | None
    detail: str = ""
    #: Which arithmetic closed, and so whether the headline was all-in.
    fee_treatment: FeeTreatment = FeeTreatment.UNRESOLVED

    @property
    def ok(self) -> bool:
        return self.verdict in (Verdict.OK, Verdict.NOT_CHECKABLE)

    @property
    def spec_is_suspect(self) -> bool:
        return self.verdict in (Verdict.UNDER_COUNTED, Verdict.OVER_COUNTED)


def reconcile(
    headline_cents: int | None,
    fee_amounts_cents: list[int],
    total_cents: int | None,
    *,
    quantity: int = 1,
    tolerance_cents: int = 2,
) -> Reconciliation:
    """Check that the readings add up to the total the page displayed.

    ``quantity`` matters and is a common source of false alarms: many sites show a
    per-ticket or per-night headline against a multi-unit total, and a spec that
    reads both correctly still fails to reconcile unless the multiplier is applied.

    ``tolerance_cents`` absorbs per-unit rounding, not real gaps.
    """
    if total_cents is None:
        return Reconciliation(
            Verdict.NOT_CHECKABLE, None, None, None,
            "page displayed no total at this step",
        )
    if headline_cents is None:
        return Reconciliation(
            Verdict.NOT_CHECKABLE, None, total_cents, None,
            "no headline reading to reconcile against",
        )
    if quantity < 1:
        raise ValueError("quantity must be at least 1")

    base = headline_cents * quantity
    fees = sum(fee_amounts_cents)

    # Two readings are possible and only one is right for a given page. Testing
    # both is not hedging: the one that closes says whether the headline already
    # contained the mandatory fees, which is the compliance question itself.
    exclusive = base + fees
    inclusive = base
    exclusive_gap = total_cents - exclusive
    inclusive_gap = total_cents - inclusive

    exclusive_ok = abs(exclusive_gap) <= tolerance_cents
    inclusive_ok = abs(inclusive_gap) <= tolerance_cents

    if exclusive_ok and inclusive_ok:
        # Only happens when the fees sum to nothing, so there is nothing to tell
        # apart and no reason to prefer either reading.
        return Reconciliation(
            Verdict.OK, exclusive, total_cents, exclusive_gap,
            fee_treatment=FeeTreatment.INDETERMINATE,
        )
    if exclusive_ok:
        return Reconciliation(
            Verdict.OK, exclusive, total_cents, exclusive_gap,
            fee_treatment=FeeTreatment.EXCLUSIVE,
        )
    if inclusive_ok:
        return Reconciliation(
            Verdict.OK, inclusive, total_cents, inclusive_gap,
            detail="headline already includes the displayed fees (all-in display)",
            fee_treatment=FeeTreatment.INCLUSIVE,
        )

    expected = exclusive
    discrepancy = exclusive_gap

    if discrepancy > 0:
        detail = (
            f"total exceeds headline x{quantity} plus {len(fee_amounts_cents)} fee "
            f"line(s) by {discrepancy} cents -- a fee is displayed that the spec "
            "does not capture, which is the failure mode that reads as compliance"
        )
        return Reconciliation(
            Verdict.UNDER_COUNTED, expected, total_cents, discrepancy, detail
        )

    detail = (
        f"accounted amount exceeds the displayed total by {-discrepancy} cents, and "
        "an all-in reading does not close either -- a fee is double-counted, or the "
        "headline selector is matching a total rather than a headline"
    )
    return Reconciliation(
        Verdict.OVER_COUNTED, expected, total_cents, discrepancy, detail
    )


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

_DEFAULT = Path(__file__).resolve().parents[2] / "config" / "selectors" / "ticketing.yaml"


def _parse_spec(target_id: str, doc: dict[str, Any]) -> SelectorSpec:
    steps = {}
    for name, sub in (doc.get("steps") or {}).items():
        steps[StepKind(name)] = StepSelectors.parse(sub)
    return SelectorSpec(
        target_id=target_id,
        domain=doc.get("domain", ""),
        by_step=steps,
        fallback=StepSelectors.parse(doc.get("fallback")),
        status=SpecStatus(doc.get("status", "unauthored")),
        authored_against_url=doc.get("authored_against_url"),
        authored_on=doc.get("authored_on"),
        notes=doc.get("notes"),
    )


def load_specs(path: Path | str | None = None) -> dict[str, SelectorSpec]:
    doc = yaml.safe_load(Path(path or _DEFAULT).read_text()) or {}
    return {
        target_id: _parse_spec(target_id, sub or {})
        for target_id, sub in (doc.get("specs") or {}).items()
    }


def assert_verified_before_sweep(specs: dict[str, SelectorSpec], target_ids: list[str]) -> list[str]:
    """Target ids whose spec is not verified. A sweep over these produces noise."""
    return [
        tid
        for tid in target_ids
        if tid not in specs or specs[tid].status is not SpecStatus.VERIFIED
    ]
