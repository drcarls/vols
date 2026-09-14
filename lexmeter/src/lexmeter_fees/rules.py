"""Resolve observed flags against jurisdiction rules.

The separation from flags.py is deliberate. A flag records what the site did; a
finding says which rule that engages, in which state, on which date. Keeping them
apart means a later correction to the legal map re-scores the existing captures
instead of invalidating them.

Two gates run before anything is asserted:

* **Date.** A rule that was not yet effective on the observation date cannot be
  engaged by it. This is the single easiest way to produce an embarrassing
  finding, so it is enforced here rather than trusted to the caller.
* **Verification.** A rule marked ``needs_confirmation`` produces a candidate,
  never an assertion. Candidates are useful internally and must not reach a
  lawyer-facing page.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .flags import Flag

_DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "jurisdictions.yaml"

#: Flags that, standing alone, engage an all-in pricing requirement.
_PRICING_FLAGS = frozenset(
    {
        Flag.MANDATORY_FEE_AT_FINAL_STEP,
        Flag.HEADLINE_EXCLUDES_ALL_MANDATORY_FEES,
        Flag.OPTIONAL_LABEL_BUT_UNAVOIDABLE,
    }
)


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    instrument: str
    effective: date | None
    verification: str
    industries: tuple[str, ...]
    kind: str | None
    private_right_of_action: bool | None
    raw: dict[str, Any]

    def applies_to_industry(self, industry: str) -> bool:
        return "all" in self.industries or industry in self.industries

    def in_force_on(self, when: date) -> bool:
        # An unknown effective date is never assumed to be in force.
        return self.effective is not None and when >= self.effective


@dataclass(frozen=True)
class Finding:
    rule_id: str
    rule_name: str
    instrument: str
    flags: tuple[Flag, ...]
    #: False where the rule is not yet verified. Candidates stay internal.
    assertable: bool
    private_right_of_action: bool | None
    note: str | None = None


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def load_rules(config_path: Path | str | None = None) -> list[Rule]:
    path = Path(config_path) if config_path else _DEFAULT_CONFIG
    doc = yaml.safe_load(path.read_text())
    rules: list[Rule] = []
    for entry in doc.get("jurisdictions", []):
        remedy = entry.get("remedy") or {}
        industries = entry.get("industries") or ["all"]
        rules.append(
            Rule(
                id=entry["id"],
                name=entry["name"],
                instrument=entry.get("instrument", ""),
                effective=_as_date(entry.get("effective")),
                verification=entry.get("verification", "needs_confirmation"),
                industries=tuple(industries),
                kind=entry.get("kind"),
                private_right_of_action=remedy.get("private_right_of_action"),
                raw=entry,
            )
        )
    return rules


def _rule_ids_for_state(state: str) -> tuple[str, ...]:
    """Federal always applies; state rules are matched on the two-letter code."""
    return ("US-FED", f"US-{state.upper()}")


def resolve(
    flags: set[Flag],
    *,
    industry: str,
    vantage_state: str,
    observed_on: date,
    rules: list[Rule] | None = None,
) -> list[Finding]:
    """Which rules the observed flags engage, for this state on this date."""
    if not flags & (_PRICING_FLAGS | {Flag.RESTAURANT_EXEMPTION_CONDITION_FAILED}):
        return []

    catalogue = rules if rules is not None else load_rules()
    wanted = _rule_ids_for_state(vantage_state)
    findings: list[Finding] = []

    for rule in catalogue:
        if rule.id not in wanted:
            continue
        if not rule.applies_to_industry(industry):
            continue
        if not rule.in_force_on(observed_on):
            continue

        engaged = tuple(sorted(flags & _PRICING_FLAGS, key=lambda f: f.name))
        if not engaged:
            continue

        note = None
        if rule.kind == "enforcement_posture":
            note = (
                "Enforcement posture under an existing statute, not a new cause "
                "of action. Read as regulator-exposure."
            )
        if rule.private_right_of_action is False:
            note = (note + " " if note else "") + (
                "No private right of action; cited in support of state-law claims."
            )

        findings.append(
            Finding(
                rule_id=rule.id,
                rule_name=rule.name,
                instrument=rule.instrument,
                flags=engaged,
                assertable=rule.verification == "confirmed",
                private_right_of_action=rule.private_right_of_action,
                note=note,
            )
        )

    return findings


def unverified_rule_ids(rules: list[Rule] | None = None) -> list[str]:
    """Rules that must not appear on a lawyer-facing page until confirmed."""
    catalogue = rules if rules is not None else load_rules()
    return [r.id for r in catalogue if r.verification != "confirmed"]
