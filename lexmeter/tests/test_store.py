import sqlite3
from datetime import date, datetime, timezone

import pytest

from lexmeter_fees.evidence import build_daily_anchor
from lexmeter_fees.model import Anchor, FlowObservation, Step, StepKind
from lexmeter_fees.store import LocalArtifactStore, SqliteObservationStore

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)


def make_obs(flow_id="f1", company="TestCo"):
    return FlowObservation(
        flow_id=flow_id,
        company=company,
        industry="live_event_ticketing",
        vantage_state="NY",
        device="desktop",
        anchor=Anchor(descriptor="venue=test"),
        started_at=NOW,
        steps=(Step(index=0, kind=StepKind.REVIEW, url="https://x.test", observed_at=NOW),),
    )


def test_artifact_store_is_content_addressed(tmp_path):
    store = LocalArtifactStore(tmp_path)
    a = store.put(b"screenshot-bytes", ".png")
    b = store.put(b"screenshot-bytes", ".png")
    assert a == b  # identical bytes are one artifact
    assert store.get(a, ".png") == b"screenshot-bytes"
    assert store.exists(a, ".png")


def test_artifact_store_separates_different_bytes(tmp_path):
    store = LocalArtifactStore(tmp_path)
    assert store.put(b"one", ".png") != store.put(b"two", ".png")


def test_observation_append_and_digest(tmp_path):
    store = SqliteObservationStore(tmp_path / "obs.db")
    digest = store.append(make_obs())
    assert len(digest) == 64
    assert store.digests_for(date(2026, 9, 14)) == [digest]


def test_reappending_identical_capture_is_a_no_op(tmp_path):
    store = SqliteObservationStore(tmp_path / "obs.db")
    first = store.append(make_obs())
    second = store.append(make_obs())
    assert first == second
    assert len(store.digests_for(date(2026, 9, 14))) == 1


def test_update_is_refused_by_the_database(tmp_path):
    # Enforced by trigger, not convention: this is what a custodian can testify
    # to. A comment saying "do not update" is not evidence of anything.
    store = SqliteObservationStore(tmp_path / "obs.db")
    store.append(make_obs())
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store._conn.execute("UPDATE observation SET company = 'Rewritten'")


def test_delete_is_refused_by_the_database(tmp_path):
    store = SqliteObservationStore(tmp_path / "obs.db")
    store.append(make_obs())
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store._conn.execute("DELETE FROM observation")


def test_daily_anchor_round_trips(tmp_path):
    store = SqliteObservationStore(tmp_path / "obs.db")
    digest = store.append(make_obs())
    anchor = build_daily_anchor(date(2026, 9, 14), store.digests_for(date(2026, 9, 14)))
    store.record_anchor(anchor)
    row = store.anchor_for(date(2026, 9, 14))
    assert row["root"] == anchor.root
    assert row["leaf_count"] == 1
    assert row["token"] is None  # no TSA configured yet, and it says so
    assert digest


def test_anchor_changes_when_a_capture_is_added(tmp_path):
    store = SqliteObservationStore(tmp_path / "obs.db")
    store.append(make_obs("f1"))
    first = build_daily_anchor(date(2026, 9, 14), store.digests_for(date(2026, 9, 14))).root
    store.append(make_obs("f2"))
    second = build_daily_anchor(date(2026, 9, 14), store.digests_for(date(2026, 9, 14))).root
    assert first != second
