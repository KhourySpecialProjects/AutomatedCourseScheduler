"""Test sqlite db"""

import os

# Must be set before any app imports — auth.py and database.py
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("AUTH0_DOMAIN", "test.auth0.com")
os.environ.setdefault("AUTH0_AUDIENCE", "https://test.api")

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import get_current_user, get_db_user
from app.core.database import Base, get_db
from app.main import app

SQLITE_URL = "sqlite://"

# StaticPool ensures all connections share the same in-memory DB,
# so create_all() and the test session see the same tables and data.
engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    default_user = MagicMock()
    default_user.user_id = 1
    default_user.role = "ADMIN"

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test-user"}
    app.dependency_overrides[get_db_user] = lambda: default_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
