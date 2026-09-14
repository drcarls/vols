"""Authoring and verifying selector specs against saved pages.

Selectors are written once against a saved copy of the page and verified there,
not discovered by trial and error against the live site. That matters for two
reasons: repeatedly re-running a flow to tune a selector is exactly the traffic
pattern the declared posture disclaims, and a saved page gives a stable target so
a failing check means the spec is wrong rather than the page having changed.

Verification runs two checks. The structural one asks whether the spec is
coherent, and needs nothing. The arithmetic one asks whether the readings add up
to the total the page displayed, and needs a real CSS engine -- so it renders the
saved HTML in the same browser the collector uses, with no network involved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .extract import parse_money_cents
from .model import StepKind
from .selectors import (
    Reconciliation,
    SelectorError,
    SelectorSpec,
    StepSelectors,
    Verdict,
    reconcile,
)


@dataclass
class StepVerification:
    step: StepKind
    reconciliation: Reconciliation
    headline_text: str | None = None
    total_text: str | None = None
    fee_labels: tuple[str, ...] = ()
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.reconciliation.ok


@dataclass
class Verification:
    target_id: str
    structural_problems: list[str] = field(default_factory=list)
    steps: list[StepVerification] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.structural_problems and all(s.ok for s in self.steps)

    @property
    def may_be_marked_verified(self) -> bool:
        """Verified requires at least one step where the arithmetic actually closed.

        A spec whose every step returns NOT_CHECKABLE has proven nothing: no total
        on any page means no check ran. Marking that verified is how an unverified
        spec reaches a live sweep.
        """
        return self.ok and any(
            s.reconciliation.verdict is Verdict.OK for s in self.steps
        )

    def summary(self) -> str:
        lines = [f"{self.target_id}:"]
        for problem in self.structural_problems:
            lines.append(f"  STRUCTURE  {problem}")
        for step in self.steps:
            if step.error:
                lines.append(f"  ERROR      {step.step.value}: {step.error}")
                continue
            rec = step.reconciliation
            tag = "OK" if rec.ok else "MISMATCH"
            lines.append(
                f"  {tag:10} {step.step.value}: {rec.verdict.value}"
                + (f" ({rec.detail})" if rec.detail and not rec.ok else "")
            )
        if not self.may_be_marked_verified and self.ok:
            lines.append(
                "  NOT VERIFIABLE: no step produced a closing arithmetic check, so "
                "nothing has been proven about this spec."
            )
        return "\n".join(lines)


def _read(scope, selector, what: str, target_id: str) -> str | None:
    if selector is None:
        return None
    locator = scope.locator(selector.css)
    if locator.count() == 0:
        if selector.required:
            raise SelectorError(
                f"{target_id}: required selector for {what!r} ({selector.css!r}) "
                "matched nothing"
            )
        return None
    first = locator.first
    if selector.attribute:
        return first.get_attribute(selector.attribute)
    return first.inner_text()


def _verify_step(page, spec: SelectorSpec, kind: StepKind, quantity: int) -> StepVerification:
    step: StepSelectors = spec.for_step(kind)
    try:
        headline = _read(page, step.headline, "headline", spec.target_id)
        total = _read(page, step.total, "total", spec.target_id)
        labels: list[str] = []
        amounts: list[int] = []
        if step.fee_row is not None:
            rows = page.locator(step.fee_row.css)
            for i in range(rows.count()):
                row = rows.nth(i)
                labels.append(
                    _read(row, step.fee_label, "fee_label", spec.target_id)
                    or row.inner_text()
                )
                cents = parse_money_cents(
                    _read(row, step.fee_amount, "fee_amount", spec.target_id) or ""
                )
                if cents is not None:
                    amounts.append(cents)
    except SelectorError as exc:
        return StepVerification(
            step=kind,
            reconciliation=Reconciliation(Verdict.NOT_CHECKABLE, None, None, None),
            error=str(exc),
        )

    return StepVerification(
        step=kind,
        reconciliation=reconcile(
            parse_money_cents(headline),
            amounts,
            parse_money_cents(total),
            quantity=quantity,
        ),
        headline_text=headline,
        total_text=total,
        fee_labels=tuple(labels),
    )


def verify_spec(
    spec: SelectorSpec,
    pages: dict[StepKind, str],
    *,
    quantity: int = 1,
) -> Verification:
    """Render each saved page and check the spec against it.

    ``pages`` maps step kind to that step's saved HTML.
    """
    result = Verification(
        target_id=spec.target_id,
        structural_problems=spec.structural_problems(list(pages)),
    )
    if not pages:
        return result

    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        try:
            for kind, html in pages.items():
                page.set_content(html)  # no network
                result.steps.append(_verify_step(page, spec, kind, quantity))
        finally:
            browser.close()
    return result


def load_saved_pages(directory: Path | str) -> dict[StepKind, str]:
    """Read a directory of saved step pages named ``<index>_<stepkind>.html``."""
    pages: dict[StepKind, str] = {}
    for path in sorted(Path(directory).glob("*.html")):
        stem = path.stem.split("_", 1)
        name = (stem[1] if len(stem) > 1 else stem[0]).lower()
        try:
            kind = StepKind(name)
        except ValueError:
            continue
        pages[kind] = path.read_text()
    return pages


def save_page(url: str, out: Path | str, policy, *, wait: str = "networkidle") -> Path:
    """Save one rendered page for offline spec authoring.

    One navigation, honest identification, no interaction. Authoring against the
    saved copy afterwards keeps the tuning loop off the live site.
    """
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    from .politeness import user_agent

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(
            user_agent=user_agent(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like "
                "Gecko) Chrome/120.0 Safari/537.36",
                policy,
            )
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until=wait)
            out.write_text(page.content())
        finally:
            browser.close()
    return out
