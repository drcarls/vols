"""Scripted flow capture.

The browser driver is imported lazily so the analysis half of the package --
flags, rules, metrics, reports -- runs anywhere without Playwright installed, and
so the test suite can exercise the full contract against local fixtures with no
network and no live sites.

Rules that hold for every flow, without exception:

* The flow stops at the final review step. A purchase is never completed.
* A block signal aborts the run. The partial observation is stored *with* its
  block reason, because a block is a fact about the site, not a missing reading.
* Every step writes its artifacts before the next navigation, so a crash leaves
  captured evidence rather than an empty record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Protocol, Sequence
from urllib.parse import urlparse

from .evidence import ProvenanceRecord, record_digest
from .extract import RawFeeRow, carry_forward, parse_money_cents, to_fee_lines
from .model import Anchor, Artifact, FlowObservation, Step, StepKind
from .politeness import Blocked, HostGate, Pacer, Policy, check_response
from .store import ArtifactStore


@dataclass(frozen=True)
class PageReading:
    """What a driver reports back for one step.

    This is the whole driver contract. Playwright satisfies it against a live
    site; the fixture driver satisfies it against local HTML. Nothing downstream
    knows or cares which.
    """

    url: str
    status: int
    body_text: str
    headline_text: str | None
    total_text: str | None
    fee_rows: Sequence[RawFeeRow]
    screenshot: bytes | None = None
    dom: bytes | None = None
    scroll_y: int | None = None


class Driver(Protocol):
    """Navigates one step of a flow and reports what the page displayed."""

    def read(self, step_kind: StepKind, action: str | None) -> PageReading: ...
    def close(self) -> None: ...


@dataclass
class FlowSpec:
    """A scripted flow: what to run, where, and against which anchor."""

    flow_id: str
    company: str
    industry: str
    start_url: str
    #: (step kind, action) pairs. ``action`` is the driver-specific instruction
    #: for reaching that step -- a selector to click, a fixture filename.
    steps: list[tuple[StepKind, str | None]]
    anchor: Anchor
    device: str = "desktop"
    vantage_state: str = "NY"
    delivery_address_state: str | None = None
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError("a flow needs at least one step")
        if self.steps[-1][0] is not StepKind.REVIEW:
            raise ValueError(
                "a flow must end at StepKind.REVIEW -- the collector stops at the "
                "final review step and never completes a purchase"
            )


class FlowRunner:
    """Drives one flow, enforcing policy and writing evidence as it goes."""

    def __init__(
        self,
        policy: Policy,
        artifacts: ArtifactStore,
        gate: HostGate | None = None,
        pacer: Pacer | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        collector_version: str = "0.1.0",
    ) -> None:
        self.policy = policy
        self.artifacts = artifacts
        self.gate = gate or HostGate(policy)
        self.pacer = pacer or Pacer(policy)
        self.clock = clock
        self.collector_version = collector_version
        self.last_provenance: ProvenanceRecord | None = None

    def run(
        self,
        spec: FlowSpec,
        driver: Driver,
        *,
        egress_provider: str | None = None,
        policy_digest: str = "",
        browser_version: str = "",
    ) -> FlowObservation:
        # The no-purchase rule is enforced structurally by FlowSpec, which
        # refuses to build a flow that does not terminate at the review step.
        if len(spec.steps) > self.policy.max_steps:
            raise ValueError(
                f"flow declares {len(spec.steps)} steps, policy caps at "
                f"{self.policy.max_steps}"
            )

        host = urlparse(spec.start_url).netloc
        started_at = self.clock()
        steps: list[Step] = []
        seen_fees: tuple = ()
        blocked: str | None = None

        if not self.gate.acquire(host):
            return self._observation(spec, started_at, (), "gate_timeout", egress_provider)

        try:
            for index, (kind, action) in enumerate(spec.steps):
                if index > 0:
                    self.pacer.wait()
                try:
                    reading = driver.read(kind, action)
                    check_response(reading.status, reading.body_text, self.policy)
                except Blocked as exc:
                    # Record and abort. Never retried inside the sweep: a retry
                    # past an explicit block is exactly the conduct the declared
                    # posture disclaims.
                    blocked = str(exc)
                    break

                lines = to_fee_lines(list(reading.fee_rows), index)
                seen_fees = carry_forward(seen_fees, lines)
                # A step carries every fee known by that point, each stamped with
                # where it *first* appeared, so the step index survives into the
                # metrics unchanged.
                steps.append(
                    Step(
                        index=index,
                        kind=kind,
                        url=reading.url,
                        observed_at=self.clock(),
                        headline_price_cents=parse_money_cents(reading.headline_text),
                        displayed_total_cents=parse_money_cents(reading.total_text),
                        fee_lines=seen_fees,
                        artifacts=self._store_artifacts(reading),
                    )
                )
        finally:
            self.gate.release(host)
            driver.close()

        obs = self._observation(spec, started_at, tuple(steps), blocked, egress_provider)
        self.last_provenance = ProvenanceRecord(
            observation_digest=record_digest(obs),
            captured_at=started_at,
            collector_version=self.collector_version,
            browser_version=browser_version,
            egress_provider=egress_provider,
            egress_state=spec.vantage_state,
            policy_digest=policy_digest,
        )
        return obs

    def _store_artifacts(self, reading: PageReading) -> tuple[Artifact, ...]:
        out: list[Artifact] = []
        if reading.screenshot:
            digest = self.artifacts.put(reading.screenshot, ".png")
            out.append(
                Artifact(
                    kind="screenshot",
                    digest=digest,
                    content_type="image/png",
                    byte_length=len(reading.screenshot),
                    scroll_y=reading.scroll_y,
                )
            )
        if reading.dom:
            digest = self.artifacts.put(reading.dom, ".html")
            out.append(
                Artifact(
                    kind="dom",
                    digest=digest,
                    content_type="text/html",
                    byte_length=len(reading.dom),
                )
            )
        return tuple(out)

    def _observation(
        self,
        spec: FlowSpec,
        started_at: datetime,
        steps: tuple,
        blocked: str | None,
        egress_provider: str | None,
    ) -> FlowObservation:
        return FlowObservation(
            flow_id=spec.flow_id,
            company=spec.company,
            industry=spec.industry,
            vantage_state=spec.vantage_state,
            device=spec.device,
            anchor=spec.anchor,
            started_at=started_at,
            steps=steps,
            blocked_reason=blocked,
            delivery_address_state=spec.delivery_address_state,
            egress_provider=egress_provider,
            collector_version=self.collector_version,
            extra=dict(spec.extra),
        )


def playwright_driver(*args, **kwargs):
    """Construct the live browser driver.

    Imported lazily and behind a function so the package stays usable -- and
    testable -- without Playwright present. Chromium is pre-installed in the
    collection image; never call ``playwright install``.
    """
    from .drivers.playwright_driver import PlaywrightDriver  # noqa: PLC0415

    return PlaywrightDriver(*args, **kwargs)
