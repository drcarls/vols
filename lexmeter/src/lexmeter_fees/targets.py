"""Loading the target list.

The target unit is the platform, not the venue: the long tail of American
ticketing runs on a dozen or so platforms, and the fee display belongs to the
platform. One pattern therefore replicates across every venue on it, which is the
same shape as the Tyler Technologies claim -- one vendor, many deployments.

Expected yield is a hypothesis about where to spend the first fortnight, and
nothing in the list is a finding. ``fee_display`` stays ``unknown`` until a sweep
fills it, and :func:`assert_uncaptured` exists so that invariant is checked rather
than trusted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_DEFAULT = Path(__file__).resolve().parents[2] / "config" / "targets" / "ticketing.yaml"

#: Tier A is the platform long tail, Tier B the majors. Sweeps run A before B:
#: the two-week date is protected by getting yield-bearing targets captured first,
#: and Tier B carries the bot-management risk.
TIER_ORDER = {"A": 0, "B": 1, "C": 2}

_YIELD_ORDER = {"high": 0, "medium": 1, "low": 2, "none": 3}


@dataclass(frozen=True)
class Target:
    id: str
    company: str
    tier: str
    domain: str
    role: str
    expected_yield: str
    deployments: tuple[str, ...] = ()
    owned_by: str | None = None
    litigation_status: str | None = None
    rationale: str = ""
    fee_display: str = "unknown"
    robots: str = "unaudited"
    expected_block_risk: str = "unknown"
    serves_via_venue_domains: bool = False
    setup_cost: str = "normal"
    role_in_design: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def captured(self) -> bool:
        return self.fee_display != "unknown"

    @property
    def is_negative_control(self) -> bool:
        """A target the collector must NOT flag. If it does, the collector is wrong."""
        return self.role_in_design == "negative_control"


@dataclass(frozen=True)
class TargetList:
    industry: str
    phase: int
    defaults: dict[str, Any]
    targets: tuple[Target, ...]
    excluded: tuple[dict[str, Any], ...]

    def by_id(self, target_id: str) -> Target:
        for target in self.targets:
            if target.id == target_id:
                return target
        raise KeyError(target_id)

    def sweep_order(self) -> list[Target]:
        """Tier first, then expected yield. Highest-yield work happens earliest."""
        return sorted(
            self.targets,
            key=lambda t: (
                TIER_ORDER.get(t.tier, 99),
                _YIELD_ORDER.get(t.expected_yield, 99),
                t.id,
            ),
        )

    def negative_controls(self) -> list[Target]:
        return [t for t in self.targets if t.is_negative_control]


def load_targets(path: Path | str | None = None) -> TargetList:
    doc = yaml.safe_load(Path(path or _DEFAULT).read_text())
    meta = doc.get("meta", {})
    targets = tuple(
        Target(
            id=entry["id"],
            company=entry["company"],
            tier=entry["tier"],
            domain=entry["domain"],
            role=entry.get("role", "primary"),
            expected_yield=entry.get("expected_yield", "unknown"),
            deployments=tuple(entry.get("deployments", ())),
            owned_by=entry.get("owned_by"),
            litigation_status=entry.get("litigation_status"),
            rationale=entry.get("rationale", ""),
            fee_display=entry.get("fee_display", "unknown"),
            robots=entry.get("robots", "unaudited"),
            expected_block_risk=entry.get("expected_block_risk", "unknown"),
            serves_via_venue_domains=bool(entry.get("serves_via_venue_domains", False)),
            setup_cost=entry.get("setup_cost", "normal"),
            role_in_design=entry.get("role_in_design"),
            raw=entry,
        )
        for entry in doc.get("targets", [])
    )
    return TargetList(
        industry=meta.get("industry", ""),
        phase=int(meta.get("phase", 0)),
        defaults=doc.get("defaults", {}),
        targets=targets,
        excluded=tuple(doc.get("excluded", [])),
    )


def assert_uncaptured(target_list: TargetList) -> None:
    """Fail loudly if the list claims a fee display nothing has actually observed.

    Cheap guard against the list drifting from hypothesis into asserted fact
    between now and the first sweep.
    """
    claimed = [t.id for t in target_list.targets if t.captured]
    if claimed:
        raise AssertionError(
            "targets claim a fee_display without a capture backing it: "
            + ", ".join(claimed)
        )
