"""Evidence chain: content addressing, canonical serialisation, Merkle anchoring.

A SHA-256 that we compute and store in our own database proves integrity only
relative to our own custody, which is worth little against a party arguing the
record was assembled after the fact. Two things fix that, and both are cheap:

1. A daily Merkle root over every new leaf hash, published to an external
   timestamp authority. One anchored root proves that no capture was added,
   removed or altered after that date.
2. A named human custodian who can certify the process under FRE 902(13)/(14).
   That is a people-and-paperwork requirement, not a code one, but the records
   have to carry the provenance a declarant would attest to -- which is why
   ``ProvenanceRecord`` exists and is written at capture time. Retrofitting it
   means re-collecting.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Protocol

#: Domain separation. Hashing leaves and interior nodes with different prefixes
#: prevents an interior node from being presented as a leaf (second-preimage).
_LEAF_PREFIX = b"\x00"
_NODE_PREFIX = b"\x01"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    raise TypeError(f"not serialisable for hashing: {type(obj)!r}")


def canonical_json(obj: Any) -> bytes:
    """Serialise deterministically so the same record always hashes the same.

    Sorted keys and fixed separators; without both, a dict reordering changes the
    digest and the chain breaks for no substantive reason.
    """
    return json.dumps(
        obj,
        default=_json_default,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def record_digest(obj: Any) -> str:
    return sha256_hex(canonical_json(obj))


def content_path(digest: str, extension: str = "") -> str:
    """Fan out by digest prefix so no directory grows unbounded."""
    if len(digest) < 4:
        raise ValueError("digest too short for a content path")
    return f"{digest[:2]}/{digest[2:4]}/{digest}{extension}"


def merkle_root(leaf_digests: list[str]) -> str:
    """Binary Merkle root over hex leaf digests.

    Leaves are sorted first so the root depends on the set of captures, not on
    the order they happened to be read out of storage. An odd node is promoted by
    pairing with itself, the conventional handling.
    """
    if not leaf_digests:
        raise ValueError("cannot anchor an empty set of leaves")

    level = [
        hashlib.sha256(_LEAF_PREFIX + bytes.fromhex(d)).digest()
        for d in sorted(leaf_digests)
    ]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            nxt.append(hashlib.sha256(_NODE_PREFIX + left + right).digest())
        level = nxt
    return level[0].hex()


@dataclass(frozen=True)
class ProvenanceRecord:
    """What a declarant would need to certify about a single capture.

    Written at capture time, never reconstructed. Anything a witness cannot
    testify to from these fields is not provable about the capture.
    """

    observation_digest: str
    captured_at: datetime  # UTC
    collector_version: str
    browser_version: str
    egress_provider: str | None
    egress_state: str
    policy_digest: str  # digest of collection_policy.yaml in force at capture
    custodian: str | None = None  # PENDING until a human is named
    notes: str | None = None

    def digest(self) -> str:
        return record_digest(self)


class TimestampAuthority(Protocol):
    """RFC 3161 timestamping seam.

    Kept behind a protocol because the choice of TSA is a legal decision and
    should not be soldered into the collector.
    """

    def stamp(self, digest_hex: str) -> bytes:
        """Return a timestamp token binding ``digest_hex`` to a trusted clock."""


class NullTimestampAuthority:
    """Default. Records that no external anchor exists yet.

    Deliberately not a silent no-op: an unanchored chain that looks anchored is
    worse than one that plainly is not, because it fails at the point of use.
    """

    anchored = False

    def stamp(self, digest_hex: str) -> bytes:
        raise NotImplementedError(
            "No RFC 3161 timestamp authority configured. Hashes prove integrity "
            "only within Lexmeter's own custody until one is set "
            "(collection_policy.yaml: evidence.timestamp_authority)."
        )


@dataclass(frozen=True)
class DailyAnchor:
    """One day's Merkle root, plus the TSA token if there is one."""

    anchor_date: date
    leaf_count: int
    root: str
    token: bytes | None = None

    @property
    def externally_anchored(self) -> bool:
        return self.token is not None


def build_daily_anchor(
    anchor_date: date,
    leaf_digests: list[str],
    tsa: TimestampAuthority | None = None,
) -> DailyAnchor:
    root = merkle_root(leaf_digests)
    token: bytes | None = None
    if tsa is not None:
        try:
            token = tsa.stamp(root)
        except NotImplementedError:
            token = None
    return DailyAnchor(
        anchor_date=anchor_date,
        leaf_count=len(leaf_digests),
        root=root,
        token=token,
    )
