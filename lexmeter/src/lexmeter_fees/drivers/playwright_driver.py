"""Live browser driver.

Imported only via ``capture.playwright_driver`` so the package works without
Playwright installed. Chromium is pre-installed in the collection image at
``PLAYWRIGHT_BROWSERS_PATH``; never run ``playwright install``.

Four things here are policy, not preference, and should not be "optimised" away:

* The real user agent is kept and honest identification appended. Disguising
  automation is prohibited and courts read it as bad faith.
* Screenshots are viewport-sized with the scroll position recorded. Full-page
  capture on a dynamic checkout silently mis-renders lazy-loaded and sticky
  elements, which is precisely the content in dispute.
* A HAR with response bodies is recorded per flow. A DOM snapshot at the review
  step cannot prove what was rendered at step one; the network record can.
* A required selector that matches nothing raises. A rotted selector must surface
  as a capture error, because its silent form -- no match, no fee, apparent
  compliance -- makes the blindest target look like the cleanest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from ..capture import PageReading
from ..extract import RawFeeRow, parse_money_cents
from ..model import StepKind
from ..politeness import Policy, user_agent
from ..selectors import (
    FieldSelector,
    Reconciliation,
    SelectorError,
    SelectorSpec,
    StepSelectors,
    reconcile,
)


class PlaywrightDriver:
    """Drives one live flow. One instance per flow, never shared."""

    def __init__(
        self,
        page: Any,
        spec: SelectorSpec,
        policy: Policy,
        actions: dict[str, Any] | None = None,
        *,
        quantity: int = 1,
        reconcile_tolerance_cents: int = 2,
    ) -> None:
        self.page = page
        self.spec = spec
        self.policy = policy
        self.actions = actions or {}
        self.quantity = quantity
        self.tolerance = reconcile_tolerance_cents
        #: Reconciliation outcome per step, surfaced to the sweep so a suspect
        #: spec is visible in the run rather than discovered in the report.
        self.reconciliations: list[tuple[StepKind, Reconciliation]] = []

    # -- selector reading ---------------------------------------------------

    @staticmethod
    def launch_context(browser: Any, policy: Policy, har_path: Path | str, **kwargs):
        """Context configured for evidence capture and honest identification."""
        base_ua = kwargs.pop("base_user_agent", None)
        return browser.new_context(
            user_agent=user_agent(base_ua, policy) if base_ua else None,
            record_har_path=str(har_path),
            record_har_content="embed",  # response bodies, per plan 4.4
            record_video_dir=kwargs.pop("video_dir", None),
            **kwargs,
        )

    def _read(self, scope: Any, selector: FieldSelector | None, what: str) -> str | None:
        if selector is None:
            return None
        locator = scope.locator(selector.css)
        if locator.count() == 0:
            if selector.required:
                raise SelectorError(
                    f"{self.spec.target_id}: required selector for {what!r} "
                    f"({selector.css!r}) matched nothing. Treating this as a capture "
                    "error rather than an absent fee -- re-author the spec."
                )
            return None
        first = locator.first
        if selector.attribute:
            return first.get_attribute(selector.attribute)
        return first.inner_text()

    def _fee_rows(self, step: StepSelectors) -> Sequence[RawFeeRow]:
        if step.fee_row is None:
            return []
        container = self.page.locator(step.fee_row.css)
        count = container.count()
        if count == 0:
            if step.fee_row.required:
                raise SelectorError(
                    f"{self.spec.target_id}: fee_row selector "
                    f"({step.fee_row.css!r}) matched nothing"
                )
            return []

        rows: list[RawFeeRow] = []
        for i in range(count):
            row = container.nth(i)
            label = self._read(row, step.fee_label, "fee_label") or row.inner_text()
            amount = self._read(row, step.fee_amount, "fee_amount") or ""
            purpose = self._read(row, step.fee_purpose, "fee_purpose")
            # Removability is only known if a control that removes the charge is
            # visible. Absent one it stays None -> Mandatory.UNKNOWN, never a guess.
            removable: bool | None = None
            if step.fee_remove_control is not None:
                removable = row.locator(step.fee_remove_control.css).count() > 0
            rows.append(
                RawFeeRow(
                    label=label,
                    amount_text=amount,
                    removable=removable,
                    purpose_text=purpose,
                    nearby_text=row.inner_text(),
                )
            )
        return rows

    # -- step ---------------------------------------------------------------

    def read(self, step_kind: StepKind, action: str | None) -> PageReading:
        status = 200
        if action:
            handler = self.actions.get(action)
            if handler is not None:
                response = handler(self.page)
            else:
                # A bare action string is a selector to click.
                response = self.page.click(action)
            if response is not None and hasattr(response, "status"):
                status = response.status
            self.page.wait_for_load_state("networkidle")

        step = self.spec.for_step(step_kind)
        headline_text = self._read(self.page, step.headline, "headline")
        total_text = self._read(self.page, step.total, "total")
        fee_rows = self._fee_rows(step)

        quantity = self.quantity
        if step.quantity is not None:
            read_qty = self._read(self.page, step.quantity, "quantity")
            parsed = parse_money_cents(read_qty)
            if parsed is not None and parsed >= 100:
                quantity = parsed // 100  # the field is a count, parsed as money

        # Does the page's own arithmetic agree with what we read off it? This
        # needs no knowledge of the site, so it catches a spec authored by someone
        # who has never seen its DOM.
        self.reconciliations.append(
            (
                step_kind,
                reconcile(
                    parse_money_cents(headline_text),
                    [
                        c
                        for c in (parse_money_cents(r.amount_text) for r in fee_rows)
                        if c is not None
                    ],
                    parse_money_cents(total_text),
                    quantity=quantity,
                    tolerance_cents=self.tolerance,
                ),
            )
        )

        scroll_y = self.page.evaluate("() => Math.round(window.scrollY)")
        content = self.page.content()
        return PageReading(
            url=self.page.url,
            status=status,
            body_text=content,
            headline_text=headline_text,
            total_text=total_text,
            fee_rows=fee_rows,
            screenshot=self.page.screenshot(full_page=False),
            dom=content.encode("utf-8"),
            scroll_y=scroll_y,
        )

    @property
    def suspect_steps(self) -> list[tuple[StepKind, Reconciliation]]:
        return [(k, r) for k, r in self.reconciliations if r.spec_is_suspect]

    def close(self) -> None:
        # Context close is what flushes the HAR and video, so it must happen even
        # on an aborted run or the evidence for that run is lost.
        try:
            self.page.context.close()
        except Exception:  # pragma: no cover - teardown must not mask the result
            pass
