"""Enforcement of the declared collection posture.

The recorded position is that robots.txt is a crawler convention and does not
govern a single user-paced scripted session. That position is defensible only
while the observable behaviour matches it -- one session per host, human pacing,
honest identification, no access-control bypass, and a hard stop on any block.

So it is enforced here rather than documented and hoped for. Everything in this
module exists to make the method statement true of the traffic a defendant would
see in their own logs.
"""

from __future__ import annotations

import random
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_POLICY = Path(__file__).resolve().parents[2] / "config" / "collection_policy.yaml"


class PolicyViolation(RuntimeError):
    """A prohibited action was attempted. Never caught and continued past."""


class Blocked(RuntimeError):
    """The site signalled a block. The flow aborts and is recorded as blocked."""


@dataclass(frozen=True)
class Policy:
    prohibitions: frozenset[str]
    min_delay: float
    max_delay: float
    jitter: bool
    max_steps: int
    max_concurrent_per_host: int
    block_statuses: frozenset[int]
    block_markers: tuple[re.Pattern[str], ...]
    user_agent_suffix: str
    forbidden_provider_classes: frozenset[str]
    default_tier: str | None
    allowed_tiers: frozenset[str]
    fallback_tiers: frozenset[str]
    forbidden_tiers: frozenset[str]
    forbidden_products: frozenset[str]
    raw: dict[str, Any]

    @classmethod
    def load(cls, path: Path | str | None = None) -> "Policy":
        doc = yaml.safe_load(Path(path or _DEFAULT_POLICY).read_text())
        pacing = doc.get("pacing", {})
        blocks = doc.get("block_signals", {})
        egress = doc.get("egress", {})
        return cls(
            prohibitions=frozenset(doc.get("prohibitions", [])),
            min_delay=float(pacing.get("min_seconds_between_actions", 2.5)),
            max_delay=float(pacing.get("max_seconds_between_actions", 7.0)),
            jitter=bool(pacing.get("jitter", True)),
            max_steps=int(pacing.get("max_steps_per_flow", 12)),
            max_concurrent_per_host=int(pacing.get("max_concurrent_sessions_per_host", 1)),
            block_statuses=frozenset(blocks.get("http_status", [])),
            block_markers=tuple(
                re.compile(re.escape(m), re.IGNORECASE)
                for m in blocks.get("body_markers", [])
            ),
            user_agent_suffix=doc.get("identification", {}).get("user_agent_suffix", ""),
            forbidden_provider_classes=frozenset(
                egress.get("forbidden_provider_classes", [])
            ),
            default_tier=egress.get("default_product_tier"),
            allowed_tiers=frozenset(egress.get("allowed_product_tiers", [])),
            fallback_tiers=frozenset(egress.get("fallback_product_tiers", [])),
            forbidden_tiers=frozenset(egress.get("forbidden_product_tiers", [])),
            forbidden_products=frozenset(egress.get("forbidden_products", [])),
            raw=doc,
        )


class HostGate:
    """One in-flight session per host, enforced with a lock per host.

    Concurrency is the difference between a scripted session and a crawler, and
    it is the first thing visible in a defendant's access logs.
    """

    def __init__(self, policy: Policy) -> None:
        self._policy = policy
        self._locks: dict[str, threading.Semaphore] = {}
        self._guard = threading.Lock()

    def _semaphore(self, host: str) -> threading.Semaphore:
        with self._guard:
            if host not in self._locks:
                self._locks[host] = threading.Semaphore(
                    self._policy.max_concurrent_per_host
                )
            return self._locks[host]

    def acquire(self, host: str, timeout: float = 600.0) -> bool:
        return self._semaphore(host).acquire(timeout=timeout)

    def release(self, host: str) -> None:
        self._semaphore(host).release()


class Pacer:
    """Human-paced delays between actions.

    Jittered rather than fixed: a constant interval is the signature of a bot and
    is inconsistent with the posture being claimed.
    """

    def __init__(self, policy: Policy, sleep=time.sleep, rng: random.Random | None = None) -> None:
        self._policy = policy
        self._sleep = sleep
        self._rng = rng or random.Random()

    def next_delay(self) -> float:
        if not self._policy.jitter:
            return self._policy.min_delay
        return self._rng.uniform(self._policy.min_delay, self._policy.max_delay)

    def wait(self) -> float:
        delay = self.next_delay()
        self._sleep(delay)
        return delay


def assert_permitted(action: str, policy: Policy) -> None:
    """Refuse a prohibited action outright.

    CAPTCHA solving, login, and access-control bypass are not merely impolite:
    they are what moves scraping across the line Van Buren and hiQ left standing,
    and they forfeit the robots.txt position at the same time.
    """
    if action in policy.prohibitions:
        raise PolicyViolation(
            f"{action!r} is prohibited by collection policy and would forfeit the "
            "declared robots.txt position (see METHOD_STATEMENT.md)."
        )


def check_response(status: int, body: str, policy: Policy) -> None:
    """Raise ``Blocked`` on a block signal so the caller records and aborts.

    A block is evidence, not a gap: the run is stored with its reason, and it is
    never retried inside the same sweep.
    """
    if status in policy.block_statuses:
        raise Blocked(f"HTTP {status}")
    for marker in policy.block_markers:
        if marker.search(body):
            raise Blocked(f"body marker: {marker.pattern}")


def check_egress(provider_class: str | None, policy: Policy) -> None:
    """Reject egress whose consent provenance cannot be put in front of a court."""
    if provider_class in policy.forbidden_provider_classes:
        raise PolicyViolation(
            f"egress provider class {provider_class!r} is excluded: undocumented "
            "consent provenance makes the collection method the story."
        )


def check_egress_product(product: str | None, policy: Policy) -> None:
    """Refuse the vendor's unblocking products.

    Web Unlocker, Scraping Browser and the CAPTCHA solvers are ordinary SKUs from
    the same vendor as the proxies, and they are exactly what one reaches for when
    a target blocks the collector. That is the moment the temptation is highest and
    the cost is largest: they automate CAPTCHA solving and anti-bot circumvention,
    which forfeits the declared robots.txt position and hands a defendant an
    argument against the whole dataset rather than one capture.

    A blocked target is logged as blocked.
    """
    if product is None:
        return
    name = product.strip().lower()
    if name in policy.forbidden_products:
        raise PolicyViolation(
            f"egress product {product!r} is prohibited: it automates CAPTCHA "
            "solving and anti-bot circumvention, which forfeits the declared "
            "robots.txt position (METHOD_STATEMENT section 3) and moves the conduct "
            "toward the CFAA access-control line. A blocked target is logged as "
            "blocked, not unblocked."
        )


def check_egress_tier(tier: str | None, policy: Policy, *, justification: str | None = None) -> str:
    """Validate the proxy tier a capture will run on, returning it normalised.

    The ISP tier is the default because its provenance is a commercial contract
    with an ISP. The residential tier is a permitted fallback where ISP coverage
    for a claim state does not exist, but only with a recorded reason -- so that a
    capture on the tier a defendant will probe can always be explained, and so
    that findings from ISP-sourced captures stand on their own.
    """
    if tier is None:
        raise PolicyViolation("egress tier must be recorded on every capture")
    name = tier.strip().lower()
    if name in policy.forbidden_tiers:
        raise PolicyViolation(f"egress tier {tier!r} is prohibited by collection policy")
    if name in policy.allowed_tiers:
        return name
    if name in policy.fallback_tiers:
        if not (justification or "").strip():
            raise PolicyViolation(
                f"egress tier {tier!r} is a fallback and requires a recorded "
                "justification (typically: no ISP coverage for this claim state)"
            )
        return name
    raise PolicyViolation(f"egress tier {tier!r} is not permitted by collection policy")


def user_agent(base: str, policy: Policy) -> str:
    """Append honest identification to the browser's real UA.

    The real UA is never replaced. Disguising automation is both prohibited and
    treated by courts as evidence of bad faith.
    """
    suffix = policy.user_agent_suffix.strip()
    return f"{base} {suffix}".strip() if suffix else base
