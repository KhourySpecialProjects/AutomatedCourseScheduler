"""Test sqlite db"""

import os

# Must be set before any app imports — database.py reads this at module load time.
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Column, Integer, Table, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# Stub tables so SQLAlchemy can resolve Section's FK references without
# the real models being present. These only exist in the test process.
_stub_tables = [
    ("Schedule", "ScheduleID"),
    ("CampusTimeBlock", "CTBID"),
    ("Course", "CourseID"),
    ("Faculty", "NUID"),
]
for _table_name, _pk_name in _stub_tables:
    if _table_name not in Base.metadata.tables:
        Table(_table_name, Base.metadata, Column(_pk_name, Integer, primary_key=True))

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

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
