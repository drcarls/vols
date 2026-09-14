"""robots.txt audit.

Discovery follows robots.txt without exception, so this runs before any target is
scheduled -- and separately, the audit is itself a finding: knowing which operators
disallow checkout paths is what makes the declared posture (plan D4) an informed
decision rather than an assumption.

Fetching is behind a protocol so the parsing, which is where the bugs live, is
testable without network access.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

from .evidence import sha256_hex

#: Paths a checkout flow has to traverse. If these sit under a wildcard Disallow,
#: strict robots compliance and scripted checkout capture are in direct conflict.
CHECKOUT_PATHS = ("/checkout", "/cart", "/order", "/purchase", "/basket", "/payment")


class Fetcher(Protocol):
    def get(self, url: str) -> tuple[int, str]:
        """Return (status, body). Raise on transport failure."""


@dataclass(frozen=True)
class RobotsAudit:
    domain: str
    reachable: bool
    status: int | None = None
    robots_sha256: str | None = None
    #: Disallow rules under ``User-agent: *`` only. Named-agent groups do not bind
    #: a session that identifies honestly and is not any of them.
    wildcard_disallow: tuple[str, ...] = ()
    disallows_everything: bool = False
    checkout_paths_disallowed: tuple[str, ...] = ()
    error: str | None = None

    @property
    def conflicts_with_checkout_capture(self) -> bool:
        return self.disallows_everything or bool(self.checkout_paths_disallowed)


def parse_wildcard_disallow(body: str) -> tuple[str, ...]:
    """Disallow rules belonging to the ``User-agent: *`` group.

    robots.txt groups consecutive User-agent lines against the rules that follow,
    so several agents can share one block. Tracking that properly matters: reading
    a Googlebot-only rule as universal would overstate the conflict and push the
    posture decision the wrong way.
    """
    rules: list[str] = []
    in_star = False
    starting_group = False

    for raw in body.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue

        agent = re.match(r"(?i)^user-agent:\s*(.*)$", line)
        if agent is not None:
            name = agent.group(1).strip()
            if starting_group:
                in_star = in_star or name == "*"
            else:
                in_star = name == "*"
                starting_group = True
            continue

        starting_group = False
        disallow = re.match(r"(?i)^disallow:\s*(.*)$", line)
        if disallow is not None and in_star:
            value = disallow.group(1).strip()
            if value:  # an empty Disallow allows everything and constrains nothing
                rules.append(value)

    return tuple(rules)


def _rule_covers(rule: str, path: str) -> bool:
    """Does a Disallow rule cover ``path``? Prefix match, with ``*`` truncated."""
    prefix = rule.split("*", 1)[0].rstrip("/")
    if not prefix:
        return True  # "/*" or bare "*" covers everything
    return path.startswith(prefix)


def audit_body(domain: str, status: int, body: str) -> RobotsAudit:
    rules = parse_wildcard_disallow(body)
    # A bare "/" blocks the whole site for the wildcard group.
    blocks_all = any(rule.rstrip("*") in ("/", "") or rule.strip() == "/" for rule in rules)
    blocked = tuple(
        path for path in CHECKOUT_PATHS if any(_rule_covers(rule, path) for rule in rules)
    )
    return RobotsAudit(
        domain=domain,
        reachable=True,
        status=status,
        robots_sha256=sha256_hex(body.encode("utf-8")),
        wildcard_disallow=rules,
        disallows_everything=blocks_all,
        checkout_paths_disallowed=blocked,
    )


def audit_domain(domain: str, fetcher: Fetcher) -> RobotsAudit:
    url = f"https://{domain}/robots.txt"
    try:
        status, body = fetcher.get(url)
    except Exception as exc:  # transport failure is a result, not a crash
        return RobotsAudit(domain=domain, reachable=False, error=str(exc)[:300])

    if status == 404:
        # No robots.txt is not a restriction. Recorded explicitly so the absence is
        # distinguishable from an unread file.
        return RobotsAudit(domain=domain, reachable=True, status=404, robots_sha256=None)
    if status >= 400:
        return RobotsAudit(
            domain=domain, reachable=False, status=status, error=f"HTTP {status}"
        )
    return audit_body(domain, status, body)


def audit_all(domains: list[str], fetcher: Fetcher) -> list[RobotsAudit]:
    return [audit_domain(d, fetcher) for d in domains]


def host_of(url: str) -> str:
    return urlparse(url).netloc
