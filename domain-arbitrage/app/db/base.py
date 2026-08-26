"""Database engine, session factory and declarative base.

SQLite is the default. Nothing in the model layer uses SQLite-specific types or
behaviour, so switching ``DATABASE_URL`` to PostgreSQL is a configuration
change: JSON columns use SQLAlchemy's portable ``JSON`` type, timestamps are
timezone-aware, and no ``AUTOINCREMENT`` or ``PRAGMA`` semantics are relied on.
"""

from __future__ import annotations

import datetime as _dt
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import DateTime, TypeDecorator, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class UtcDateTime(TypeDecorator):
    """Timezone-aware datetime that round-trips correctly on SQLite.

    SQLite drops tzinfo. This coerces on the way in and reattaches UTC on the
    way out so application code never sees a naive datetime.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=_dt.timezone.utc)
        return value.astimezone(_dt.timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=_dt.timezone.utc)
        return value.astimezone(_dt.timezone.utc)


class Base(DeclarativeBase):
    pass


_settings = get_settings()
_connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    _settings.database_url,
    echo=_settings.sql_echo,
    future=True,
    connect_args=_connect_args,
)

if _settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):  # pragma: no cover - driver glue
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False,
                            class_=Session, future=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional scope. Commits on success, rolls back on exception."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
