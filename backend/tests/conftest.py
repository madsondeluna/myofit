"""Shared fixtures. Every test runs against a fresh in-memory database so no
test can observe another's writes.
"""

from __future__ import annotations

import os
import tempfile

# Set before importing the app: backend.app.db builds its engine at import time
# from MYOFIT_DB, and without this the application lifespan would create and
# seed a real myofit.db in the repository root during the test run.
_TEST_DB = os.path.join(tempfile.mkdtemp(prefix="myofit-test-"), "lifespan.db")
os.environ.setdefault("MYOFIT_DB", f"sqlite:///{_TEST_DB}")
# Point the Garmin token directory somewhere disposable so no test can read or
# write the developer's real session.
os.environ.setdefault("GARMINTOKENS", os.path.join(os.path.dirname(_TEST_DB), "garth"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from backend.app.db import get_session  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.seed import seed_exercises  # noqa: E402


@pytest.fixture(name="engine")
def engine_fixture():
    # StaticPool keeps every connection pointed at the same in-memory database;
    # the default pool would hand out a fresh, empty one per connection.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="seeded_session")
def seeded_session_fixture(session):
    seed_exercises(session)
    return session


@pytest.fixture(name="client")
def client_fixture(engine):
    with Session(engine) as session:
        seed_exercises(session)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    # The app lifespan seeds the real database; TestClient is entered without
    # it here because the fixture already provisioned the schema and catalog.
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
