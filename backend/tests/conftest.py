"""Test configuration, in-memory SQLite database, and test fixtures."""

import os
import sys
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.db.base import Base
from app.main import app
from app.models.moderator import Moderator
from app.services.auth_service import create_moderator
from app.schemas.moderator import ModeratorCreate

# In-memory SQLite engine for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test tables in SQLite."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Provide a transactional database session rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient wired with test database session override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_moderator(db: Session) -> Moderator:
    """Fixture creating an active test moderator."""
    moderator_in = ModeratorCreate(
        email="moderator@whistledrop.org",
        username="mod_lead",
        password="SecureTestPassword123!",
    )
    return create_moderator(db=db, moderator_in=moderator_in)


@pytest.fixture
def inactive_moderator(db: Session) -> Moderator:
    """Fixture creating a deactivated test moderator."""
    moderator_in = ModeratorCreate(
        email="inactive@whistledrop.org",
        username="inactive_mod",
        password="DeactivatedPassword123!",
    )
    mod = create_moderator(db=db, moderator_in=moderator_in)
    mod.is_active = False
    db.commit()
    db.refresh(mod)
    return mod


@pytest.fixture
def moderator_token(test_moderator: Moderator) -> str:
    """JWT bearer token for test moderator."""
    return create_access_token(subject=str(test_moderator.id))


@pytest.fixture
def auth_headers(moderator_token: str) -> dict:
    """Authorization header dict for moderator requests."""
    return {"Authorization": f"Bearer {moderator_token}"}
