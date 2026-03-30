"""Tests for Auth0 authentication middleware."""

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from tests.conftest import TestingSessionLocal, engine


@pytest.fixture()
def unauthed_client():
    """Client with no auth override — real auth dependency is active."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    # Intentionally do NOT override get_current_user
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Routes that require auth should reject unauthenticated requests
# ---------------------------------------------------------------------------

# Routes with a GET endpoint protected by auth.
# /sections only exposes POST/PATCH/DELETE so it is excluded.
PROTECTED_GET_ROUTES = ["/courses", "/faculty", "/schedules"]


@pytest.mark.parametrize("path", PROTECTED_GET_ROUTES)
def test_protected_route_no_token(unauthed_client, path):
    response = unauthed_client.get(path)
    assert response.status_code == 400, (
        f"GET {path} should require auth, got {response.status_code}"
    )


@pytest.mark.parametrize("path", PROTECTED_GET_ROUTES)
def test_protected_route_malformed_token(unauthed_client, path):
    headers = {"Authorization": "Bearer not-a-token-1"}
    response = unauthed_client.get(path, headers=headers)
    assert response.status_code == 401, (
        f"GET {path} with bad token should be rejected, got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# Root endpoint is not protected
# ---------------------------------------------------------------------------


def test_root_no_auth_required(unauthed_client):
    response = unauthed_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Automated Course Scheduler API"}


# ---------------------------------------------------------------------------
# With a valid (mocked) user the protected routes are reachable
# ---------------------------------------------------------------------------


def test_authenticated_client_can_reach_protected_route(client):
    """The shared `client` fixture overrides auth — requests should succeed."""
    response = client.get("/courses")
    assert response.status_code == 200


def test_get_current_user_returns_claims(client):
    """get_current_user is overridden to return a fixed dict in tests."""
    # Verify the override is in place by hitting an endpoint that would
    # fail with a real JWT verifier and confirming we get a non-auth error.
    response = client.get("/courses")
    assert response.status_code != 401
    assert response.status_code != 403
