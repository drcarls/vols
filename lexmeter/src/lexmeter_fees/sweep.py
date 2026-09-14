"""Weekly sweep orchestration.

Two capture modes, and the split is the cost argument from plan section 4.2:

* The **weekly sweep** runs every flow from the control vantage only. Fees in
  ticketing and lodging track the event or property, not the buyer, so running
  eight vantages weekly multiplies cost and block rate for almost no variance.
* The **differential probe** runs a sampled subset across every vantage, tuned to
  detect jurisdictional display switching -- a company rendering all-in to a
  claim-state visitor and drip elsewhere has shown it can comply and chose not to.

Targets are swept in tier and yield order so that if the run is cut short, what
was captured is the part worth having.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Callable, Iterable

from .capture import Driver, FlowRunner, FlowSpec
from .evidence import DailyAnchor, TimestampAuthority, build_daily_anchor
from .flags import Flag, evaluate, evaluate_across_vantages
from .model import Anchor, FlowObservation, StepKind
from .store import SqliteObservationStore
from .targets import Target, TargetList

#: The scripted funnel. Terminates at REVIEW; FlowSpec refuses anything else.
DEFAULT_FLOW = (
    StepKind.SEARCH,
    StepKind.LISTING,
    StepKind.DETAIL,
    StepKind.SELECT,
    StepKind.CHECKOUT,
    StepKind.REVIEW,
)

DriverFactory = Callable[[Target, str, str], Driver]
"""(target, deployment, vantage_state) -> a driver for one flow."""


@dataclass
class SweepResult:
    started_at: datetime
    observations: list[FlowObservation] = field(default_factory=list)
    digests: list[str] = field(default_factory=list)
    blocked: list[tuple[str, str]] = field(default_factory=list)
    anchor: DailyAnchor | None = None
    #: Negative controls that flagged. Any entry here means the collector is
    #: wrong, not the target, and the sweep's findings should not be published.
    control_failures: list[str] = field(default_factory=list)

    @property
    def captured(self) -> int:
        return sum(1 for o in self.observations if o.completed)

    @property
    def trustworthy(self) -> bool:
        return not self.control_failures


def flow_id_for(target: Target, deployment: str, vantage: str) -> str:
    return f"{target.id}:{deployment}:{vantage}"


def build_flow(
    target: Target,
    deployment: str,
    vantage: str,
    *,
    offset_days: int = 30,
    steps: Iterable[StepKind] = DEFAULT_FLOW,
    actions: dict[StepKind, str] | None = None,
) -> FlowSpec:
    actions = actions or {}
    return FlowSpec(
        flow_id=flow_id_for(target, deployment, vantage),
        company=target.company,
        industry="live_event_ticketing",
        start_url=f"https://{target.domain}/",
        steps=[(kind, actions.get(kind)) for kind in steps],
        anchor=Anchor(
            descriptor=f"platform={target.id};deployment={deployment}",
            date_mode="rolling_offset",
            offset_days=offset_days,
        ),
        vantage_state=vantage,
    )


def run_sweep(
    target_list: TargetList,
    runner: FlowRunner,
    driver_factory: DriverFactory,
    store: SqliteObservationStore,
    *,
    vantage: str | None = None,
    tsa: TimestampAuthority | None = None,
    only_tiers: set[str] | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> SweepResult:
    """One weekly sweep from the control vantage."""
    control = vantage or target_list.defaults.get("vantage_control", "NY")
    result = SweepResult(started_at=clock())

    for target in target_list.sweep_order():
        if only_tiers and target.tier not in only_tiers:
            continue
        for deployment in target.deployments or ("default",):
            spec = build_flow(target, deployment, control)
            obs = runner.run(spec, driver_factory(target, deployment, control))
            result.observations.append(obs)
            result.digests.append(store.append(obs))

            if obs.blocked_reason:
                # Logged, not evaded, and not retried inside this sweep.
                result.blocked.append((spec.flow_id, obs.blocked_reason))
                continue

            flags = evaluate(obs)
            if flags and target.is_negative_control:
                result.control_failures.append(
                    f"{target.id}: {sorted(f.name for f in flags)}"
                )

    if result.digests:
        result.anchor = build_daily_anchor(
            result.started_at.date(), result.digests, tsa
        )
        store.record_anchor(result.anchor)
    return result


@dataclass
class ProbeResult:
    flow_key: str
    company: str
    vantages: tuple[str, ...]
    flags: frozenset[Flag]

    @property
    def switching(self) -> bool:
        return Flag.JURISDICTIONAL_DISPLAY_SWITCHING in self.flags


def run_differential_probe(
    target: Target,
    deployment: str,
    runner: FlowRunner,
    driver_factory: DriverFactory,
    store: SqliteObservationStore,
    vantages: list[str],
) -> ProbeResult:
    """Same flow from every vantage, to detect display switching.

    Cross-vantage evaluation needs one flow_id, but flow ids embed the vantage so
    each capture stays individually addressable. The observations are relabelled
    onto a shared id purely for the comparison.
    """
    observations: list[FlowObservation] = []
    for vantage in vantages:
        spec = build_flow(target, deployment, vantage)
        obs = runner.run(spec, driver_factory(target, deployment, vantage))
        store.append(obs)
        observations.append(obs)

    shared = f"{target.id}:{deployment}"
    comparable = [
        FlowObservation(**{**o.__dict__, "flow_id": shared}) for o in observations
    ]
    return ProbeResult(
        flow_key=shared,
        company=target.company,
        vantages=tuple(vantages),
        flags=frozenset(evaluate_across_vantages(comparable)),
    )


def sweep_dates(result: SweepResult) -> date:
    return result.started_at.date()
