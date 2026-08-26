"""Schema creation.

``create_all`` is adequate for the MVP. When PostgreSQL replaces SQLite, swap
this for Alembic migrations; the models are already written to be portable.
"""

from __future__ import annotations

from app.config import DATA_DIR
from app.db.base import Base, engine
import app.models  # noqa: F401  (registers tables)


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def reset_db() -> None:
    """Drop and recreate. Destructive; used by tests and scripts/reset.py."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
