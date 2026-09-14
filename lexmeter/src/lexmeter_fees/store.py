"""Storage behind an adapter boundary.

The existing Lexmeter pipeline is not in this repository, so the collector talks
to protocols and ships local implementations. Pointing it at the real store is
then a config change rather than a rewrite, and the reference-price schema stays
separate from fee observations either way.

Append-only is enforced at the database, not by convention. Triggers that raise
on UPDATE and DELETE are what let a custodian testify that records could not be
revised after capture; a code comment saying "do not update" cannot be testified
to at all.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterator, Protocol

from .evidence import canonical_json, content_path, record_digest, sha256_hex
from .model import FlowObservation


class ArtifactStore(Protocol):
    """Content-addressed blob storage for screenshots, DOM, HAR and video."""

    def put(self, data: bytes, extension: str = "") -> str:
        """Store bytes, return the sha256 hex digest."""

    def get(self, digest: str, extension: str = "") -> bytes: ...

    def exists(self, digest: str, extension: str = "") -> bool: ...


class LocalArtifactStore:
    """Filesystem implementation.

    In production this is object storage with versioning and object lock in
    compliance mode; the interface is the same, which is the point of the seam.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, digest: str, extension: str) -> Path:
        return self.root / content_path(digest, extension)

    def put(self, data: bytes, extension: str = "") -> str:
        digest = sha256_hex(data)
        path = self._path(digest, extension)
        # Identical bytes are the same artifact; rewriting would only risk
        # disturbing a file a hash already vouches for.
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return digest

    def get(self, digest: str, extension: str = "") -> bytes:
        return self._path(digest, extension).read_bytes()

    def exists(self, digest: str, extension: str = "") -> bool:
        return self._path(digest, extension).exists()


class AppendOnlyViolation(RuntimeError):
    """Raised when something tries to revise a stored observation."""


_SCHEMA = """
CREATE TABLE IF NOT EXISTS observation (
    digest           TEXT PRIMARY KEY,
    flow_id          TEXT NOT NULL,
    company          TEXT NOT NULL,
    industry         TEXT NOT NULL,
    vantage_state    TEXT NOT NULL,
    device           TEXT NOT NULL,
    observed_on      TEXT NOT NULL,
    started_at       TEXT NOT NULL,
    blocked_reason   TEXT,
    payload          TEXT NOT NULL,
    recorded_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_observation_flow ON observation(flow_id, observed_on);
CREATE INDEX IF NOT EXISTS idx_observation_company ON observation(company, observed_on);

-- Append-only, enforced by the engine. In Postgres the equivalent is revoking
-- UPDATE and DELETE from the collector role rather than granting and trusting.
CREATE TRIGGER IF NOT EXISTS observation_no_update
BEFORE UPDATE ON observation
BEGIN
    SELECT RAISE(ABORT, 'observation is append-only: UPDATE refused');
END;

CREATE TRIGGER IF NOT EXISTS observation_no_delete
BEFORE DELETE ON observation
BEGIN
    SELECT RAISE(ABORT, 'observation is append-only: DELETE refused');
END;

CREATE TABLE IF NOT EXISTS daily_anchor (
    anchor_date  TEXT PRIMARY KEY,
    leaf_count   INTEGER NOT NULL,
    root         TEXT NOT NULL,
    token        BLOB,
    recorded_at  TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS anchor_no_update
BEFORE UPDATE ON daily_anchor
BEGIN
    SELECT RAISE(ABORT, 'daily_anchor is append-only: UPDATE refused');
END;
"""


class ObservationStore(Protocol):
    def append(self, obs: FlowObservation) -> str: ...
    def digests_for(self, day: date) -> list[str]: ...
    def iter_flow(self, flow_id: str) -> Iterator[FlowObservation]: ...


class SqliteObservationStore:
    """Local append-only store for observations and daily anchors."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def append(self, obs: FlowObservation) -> str:
        payload = canonical_json(asdict(obs))
        digest = record_digest(asdict(obs))
        try:
            self._conn.execute(
                "INSERT INTO observation (digest, flow_id, company, industry,"
                " vantage_state, device, observed_on, started_at, blocked_reason,"
                " payload, recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    digest,
                    obs.flow_id,
                    obs.company,
                    obs.industry,
                    obs.vantage_state,
                    obs.device,
                    obs.started_at.date().isoformat(),
                    obs.started_at.isoformat(),
                    obs.blocked_reason,
                    payload.decode("utf-8"),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            # Same bytes, same digest: the capture is already recorded. Not an
            # error, and re-inserting would be the revision we are preventing.
            self._conn.rollback()
        return digest

    def digests_for(self, day: date) -> list[str]:
        rows = self._conn.execute(
            "SELECT digest FROM observation WHERE observed_on = ? ORDER BY digest",
            (day.isoformat(),),
        ).fetchall()
        return [r["digest"] for r in rows]

    def raw_payloads_for_flow(self, flow_id: str) -> list[str]:
        rows = self._conn.execute(
            "SELECT payload FROM observation WHERE flow_id = ? ORDER BY started_at",
            (flow_id,),
        ).fetchall()
        return [r["payload"] for r in rows]

    def record_anchor(self, anchor) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO daily_anchor (anchor_date, leaf_count, root,"
            " token, recorded_at) VALUES (?,?,?,?,?)",
            (
                anchor.anchor_date.isoformat(),
                anchor.leaf_count,
                anchor.root,
                anchor.token,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def anchor_for(self, day: date) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM daily_anchor WHERE anchor_date = ?", (day.isoformat(),)
        ).fetchone()
