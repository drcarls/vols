"""Live browser driver.

Imported only via ``capture.playwright_driver`` so the package works without
Playwright installed. Chromium is pre-installed in the collection image at
``PLAYWRIGHT_BROWSERS_PATH``; never run ``playwright install``.

Three things here are policy, not preference, and should not be "optimised" away:

* The real user agent is kept and honest identification appended. Disguising
  automation is prohibited and courts read it as bad faith.
* Screenshots are viewport-sized with the scroll position recorded. Full-page
  capture on a dynamic checkout silently mis-renders lazy-loaded and sticky
  elements, which is precisely the content in dispute.
* A HAR with response bodies is recorded per flow. A DOM snapshot at the review
  step cannot prove what was rendered at step one; the network record can.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from ..capture import PageReading
from ..extract import RawFeeRow
from ..model import StepKind
from ..politeness import Policy, user_agent


@dataclass(frozen=True)
class SelectorSpec:
    """Per-site CSS selectors. One of these per company, held as config.

    Kept as data rather than code because selectors rot weekly and a rotted
    selector must fail loudly as a capture error, never silently as a zero fee.
    """

    headline: str
    total: str | None = None
    fee_row: str | None = None
    fee_label: str | None = None
    fee_amount: str | None = None
    fee_purpose: str | None = None
    fee_remove_control: str | None = None


class PlaywrightDriver:
    """Drives one live flow. One instance per flow, never shared."""

    def __init__(
        self,
        page: Any,
        selectors: SelectorSpec,
        policy: Policy,
        actions: dict[str, Any] | None = None,
    ) -> None:
        self.page = page
        self.selectors = selectors
        self.policy = policy
        self.actions = actions or {}

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

    def _text(self, selector: str | None) -> str | None:
        if not selector:
            return None
        locator = self.page.locator(selector)
        if locator.count() == 0:
            return None
        return locator.first.inner_text()

    def _fee_rows(self) -> Sequence[RawFeeRow]:
        spec = self.selectors
        if not spec.fee_row:
            return []
        rows: list[RawFeeRow] = []
        container = self.page.locator(spec.fee_row)
        for i in range(container.count()):
            row = container.nth(i)
            label = row.locator(spec.fee_label).first.inner_text() if spec.fee_label else row.inner_text()
            amount = row.locator(spec.fee_amount).first.inner_text() if spec.fee_amount else ""
            purpose = None
            if spec.fee_purpose and row.locator(spec.fee_purpose).count():
                purpose = row.locator(spec.fee_purpose).first.inner_text()
            # Removability is only known if we can see a control that removes it.
            # Absent one it stays None -> Mandatory.UNKNOWN, never a guess.
            removable: bool | None = None
            if spec.fee_remove_control:
                removable = row.locator(spec.fee_remove_control).count() > 0
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

        scroll_y = self.page.evaluate("() => Math.round(window.scrollY)")
        return PageReading(
            url=self.page.url,
            status=status,
            body_text=self.page.content(),
            headline_text=self._text(self.selectors.headline),
            total_text=self._text(self.selectors.total),
            fee_rows=self._fee_rows(),
            screenshot=self.page.screenshot(full_page=False),
            dom=self.page.content().encode("utf-8"),
            scroll_y=scroll_y,
        )

    def close(self) -> None:
        # Context close is what flushes the HAR and video, so it must happen even
        # on an aborted run or the evidence for that run is lost.
        try:
            self.page.context.close()
        except Exception:  # pragma: no cover - teardown must not mask the result
            pass
