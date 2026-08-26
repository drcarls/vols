"""Schema creation.

``create_all`` is adequate for the MVP. When PostgreSQL replaces SQLite, swap
this for Alembic migrations; the models are already written to be portable.
"""

from __future__ import annotations

from sqlalchemy import inspect

from app.config import DATA_DIR
from app.db.base import Base, engine
import app.models  # noqa: F401  (registers tables)


class SchemaDriftError(RuntimeError):
    """An existing database predates a model change.

    ``create_all`` creates missing tables but never alters existing ones, so a
    database created before a column was added keeps working until something
    selects that column - and then fails with a raw driver error a long way
    from the cause. Detecting it up front turns that into one clear sentence.

    This is the point at which Alembic earns its place; until then, the honest
    answer for a schema change is 'recreate the database'.
    """


def schema_drift() -> list[str]:
    """Columns the models expect that the live database does not have."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    problems: list[str] = []
    for name, table in Base.metadata.tables.items():
        if name not in existing_tables:
            continue          # create_all will make it
        actual = {c["name"] for c in inspector.get_columns(name)}
        missing = {c.name for c in table.columns} - actual
        if missing:
            problems.append(f"{name}: missing column(s) "
                            f"{', '.join(sorted(missing))}")
    return problems


def init_db(*, check_drift: bool = True) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    if not check_drift:
        return
    problems = schema_drift()
    if problems:
        raise SchemaDriftError(
            "This database was created by an older version of the models and "
            "is missing columns that the code now selects:\n  "
            + "\n  ".join(problems)
            + "\n\nThe MVP has no migrations. Recreate the database with "
              "`make reset` (destructive), or add the columns by hand if it "
              "holds paper positions you need to keep.")


def reset_db() -> None:
    """Drop and recreate. Destructive; used by tests and scripts/reset.py."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
