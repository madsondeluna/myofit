"""Engine and session wiring. The database path is overridable through
MYOFIT_DB so tests and the Render deploy can point somewhere writable.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "myofit.db"
DATABASE_URL = os.getenv("MYOFIT_DB", f"sqlite:///{DEFAULT_DB_PATH}")

# check_same_thread=False is required because FastAPI serves requests from a
# thread pool while SQLite defaults to single-thread ownership.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


# SQLite ignores foreign keys unless the pragma is set per connection. Without
# it the ondelete="CASCADE" on workout_exercise would silently do nothing and
# deleting a workout would leave orphan rows behind.
@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db() -> None:
    # Import for the side effect of registering the tables on SQLModel.metadata.
    from . import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
