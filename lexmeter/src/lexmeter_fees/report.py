"""The three outputs: per-company findings, league table, pattern-match screen.

The screen is the product. Its value is not that it lists violations -- a company
already being sued is worth nothing to a plaintiff firm -- but that it lists
*unlitigated* companies exhibiting a fact pattern a court has already been asked
to rule on. So the litigation filter is load-bearing, not cosmetic, and the
exclusion is visible in the output rather than silently applied.

Nothing here asserts a legal conclusion on its own. Every finding carries the rule
it engages, whether that rule has a private right of action, and whether the rule
itself is verified. Unverified rules produce candidates that stay internal.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import yaml

from .flags import Flag, Metrics, compute_metrics, evaluate
from .model import FlowObservation
from .rules import Finding, Rule, resolve

_DEFAULT_PATTERNS = (
    Path(__file__).resolve().parents[2] / "config" / "fact_patterns.yaml"
)

#: Litigation states that disqualify a company from the screen. A defendant already
#: facing the claim is not a lead.
LITIGATED = frozenset({"active_defendant", "settled_ftc", "settled", "filed"})


@dataclass(frozen=True)
class CompanyReport:
    company: str
    industry: str
    vantage_state: str
    observed_on: date
    metrics: Metrics
    flags: frozenset[Flag]
    findings: tuple[Finding, ...]
    blocked: bool
    blocked_reason: str | None = None
    evidence_digests: tuple[str, ...] = ()

    @property
    def assertable_findings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.assertable)

    @property
    def actionable_for_plaintiff(self) -> bool:
        """A finding is sellable to a plaintiff firm only with a private right of action."""
        return any(
            f.private_right_of_action is True for f in self.assertable_findings
        )


def build_company_report(
    obs: FlowObservation,
    *,
    rules: list[Rule] | None = None,
) -> CompanyReport:
    if obs.blocked_reason:
        # A blocked run yields no findings but is still reported: silence about a
        # target that refused us would read as a clean result.
        return CompanyReport(
            company=obs.company,
            industry=obs.industry,
            vantage_state=obs.vantage_state,
            observed_on=obs.started_at.date(),
            metrics=compute_metrics(obs),
            flags=frozenset(),
            findings=(),
            blocked=True,
            blocked_reason=obs.blocked_reason,
        )

    flags = evaluate(obs)
    findings = resolve(
        flags,
        industry=obs.industry,
        vantage_state=obs.vantage_state,
        observed_on=obs.started_at.date(),
        rules=rules,
    )
    digests = tuple(
        artifact.digest for step in obs.steps for artifact in step.artifacts
    )
    return CompanyReport(
        company=obs.company,
        industry=obs.industry,
        vantage_state=obs.vantage_state,
        observed_on=obs.started_at.date(),
        metrics=compute_metrics(obs),
        flags=frozenset(flags),
        findings=tuple(findings),
        blocked=False,
        evidence_digests=digests,
    )


@dataclass(frozen=True)
class LeagueRow:
    company: str
    observations: int
    flagged: int
    blocked: int
    states_flagged: tuple[str, ...]
    worst_gap_pct: float | None
    latest_mandatory_step: int | None

    @property
    def density(self) -> float:
        """Share of *completed* observations that flagged.

        Blocked runs are excluded from the denominator. Counting them as clean
        would reward the operators with the most aggressive bot management.
        """
        usable = self.observations - self.blocked
        return round(self.flagged / usable, 4) if usable else 0.0


def build_league_table(reports: Iterable[CompanyReport]) -> list[LeagueRow]:
    grouped: dict[str, list[CompanyReport]] = defaultdict(list)
    for report in reports:
        grouped[report.company].append(report)

    rows: list[LeagueRow] = []
    for company, items in grouped.items():
        flagged = [r for r in items if r.flags and not r.blocked]
        gaps = [
            r.metrics.gap_pct for r in items if r.metrics.gap_pct is not None
        ]
        steps = [
            r.metrics.latest_mandatory_fee_first_step
            for r in items
            if r.metrics.latest_mandatory_fee_first_step is not None
        ]
        rows.append(
            LeagueRow(
                company=company,
                observations=len(items),
                flagged=len(flagged),
                blocked=sum(1 for r in items if r.blocked),
                states_flagged=tuple(sorted({r.vantage_state for r in flagged})),
                worst_gap_pct=max(gaps) if gaps else None,
                latest_mandatory_step=max(steps) if steps else None,
            )
        )
    # Density first, then absolute gap: a company that drips on every capture
    # outranks one that did it once by a larger margin.
    rows.sort(key=lambda r: (-r.density, -(r.worst_gap_pct or 0.0), r.company))
    return rows


@dataclass(frozen=True)
class PatternMatch:
    pattern_id: str
    pattern_label: str
    company: str
    states: tuple[str, ...]
    anchor_cases: tuple[str, ...]
    litigated: bool
    #: False where the pattern itself is not yet verified against a filed case.
    pattern_verified: bool = True
    evidence_digests: tuple[str, ...] = ()


@dataclass
class Screen:
    matches: list[PatternMatch] = field(default_factory=list)
    excluded_as_litigated: list[str] = field(default_factory=list)

    @property
    def leads(self) -> list[PatternMatch]:
        """Unlitigated companies showing a filed-case fact pattern. The product."""
        return [m for m in self.matches if not m.litigated and m.pattern_verified]


def load_patterns(path: Path | str | None = None) -> list[dict[str, Any]]:
    doc = yaml.safe_load(Path(path or _DEFAULT_PATTERNS).read_text())
    return doc.get("patterns", [])


def _pattern_matches(pattern: dict[str, Any], report: CompanyReport) -> bool:
    match = pattern.get("match", {})
    flag_names = {f.value for f in report.flags}
    categories = set(report.metrics.fee_categories)

    for clause in match.get("all", []):
        if "flag" in clause and clause["flag"].lower() not in {
            f.name.lower() for f in report.flags
        } and clause["flag"] not in flag_names:
            return False
        if "fee_category_in" in clause and not (categories & set(clause["fee_category_in"])):
            return False

    any_clauses = match.get("any", [])
    if any_clauses:
        satisfied = False
        for clause in any_clauses:
            if "flag" in clause and clause["flag"] in {f.name for f in report.flags}:
                satisfied = True
            if "metric" in clause and clause["metric"] == "gap_pct":
                gap = report.metrics.gap_pct
                if gap is not None and gap >= float(clause.get("gte", 0)):
                    satisfied = True
        if not satisfied:
            return False

    return bool(match.get("all") or any_clauses)


def build_screen(
    reports: Iterable[CompanyReport],
    litigation_status: dict[str, str] | None = None,
    patterns: list[dict[str, Any]] | None = None,
) -> Screen:
    catalogue = patterns if patterns is not None else load_patterns()
    status = litigation_status or {}
    screen = Screen()

    grouped: dict[str, list[CompanyReport]] = defaultdict(list)
    for report in reports:
        if not report.blocked:
            grouped[report.company].append(report)

    for pattern in catalogue:
        for company, items in grouped.items():
            hits = [r for r in items if _pattern_matches(pattern, r)]
            if not hits:
                continue
            litigated = status.get(company) in LITIGATED
            if litigated:
                screen.excluded_as_litigated.append(f"{pattern['id']}:{company}")
            screen.matches.append(
                PatternMatch(
                    pattern_id=pattern["id"],
                    pattern_label=pattern.get("label", pattern["id"]),
                    company=company,
                    states=tuple(sorted({r.vantage_state for r in hits})),
                    anchor_cases=tuple(
                        c.get("caption", c.get("id", ""))
                        for c in pattern.get("anchor_cases", [])
                    ),
                    litigated=litigated,
                    pattern_verified=pattern.get("verification", "confirmed") == "confirmed"
                    and not pattern.get("novel", False),
                    evidence_digests=tuple(
                        d for r in hits for d in r.evidence_digests
                    ),
                )
            )
    return screen
