"""Refuse to collect until collection can be certified.

Captures made without an egress attestation, an external timestamp anchor and a
named custodian are not worthless -- they are sound within Lexmeter's own custody
-- but they are not self-authenticating, and a weekly series founded on them
starts with a first data point that cannot be put in front of a court.

So the sweep refuses by default and the operator has to say ``--uncertified`` out
loud. The point is not to be obstructive; it is that this gap is invisible at
capture time and extremely visible when a declaration is due.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Preflight:
    egress_provider: str | None
    attestation_on_file: bool
    timestamp_authority: str | None
    custodian: str | None

    @property
    def blockers(self) -> list[str]:
        out = []
        if not self.egress_provider:
            out.append(
                "egress.provider is not set -- captures would carry no vantage "
                "provenance (METHOD_STATEMENT section 7.1)"
            )
        elif not self.attestation_on_file:
            out.append(
                "egress provider named but attestation_on_file is false -- consent "
                "provenance cannot be evidenced (section 7.1)"
            )
        if not self.timestamp_authority:
            out.append(
                "evidence.timestamp_authority is not set -- the hash chain would be "
                "unanchored outside our own custody (section 7.2)"
            )
        if not self.custodian:
            out.append(
                "evidence.custodian is not set -- no qualified person to certify "
                "under FRE 902(13)/(14) (section 7.3)"
            )
        return out

    @property
    def certifiable(self) -> bool:
        return not self.blockers


def load_preflight(policy_path: Path | str) -> Preflight:
    doc = yaml.safe_load(Path(policy_path).read_text())
    egress = doc.get("egress", {}) or {}
    evidence = doc.get("evidence", {}) or {}
    return Preflight(
        egress_provider=egress.get("provider"),
        attestation_on_file=bool(egress.get("attestation_on_file", False)),
        timestamp_authority=evidence.get("timestamp_authority"),
        custodian=evidence.get("custodian"),
    )
