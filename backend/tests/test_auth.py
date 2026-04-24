"""Tests for Auth0 authentication middleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.services.user import get_or_link_user
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
    assert response.status_code == 400, f"GET {path} should require auth, got {response.status_code}"


@pytest.mark.parametrize("path", PROTECTED_GET_ROUTES)
def test_protected_route_malformed_token(unauthed_client, path):
    headers = {"Authorization": "Bearer not-a-token-1"}
    response = unauthed_client.get(path, headers=headers)
    assert response.status_code == 401, f"GET {path} with bad token should be rejected, got {response.status_code}"


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


# ---------------------------------------------------------------------------
# get_or_link_user: inactive users are blocked
# ---------------------------------------------------------------------------


def _mock_userinfo(email: str):
    """Build a patch for httpx.AsyncClient returning the given email from /userinfo."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={"email": email})

    client_mock = MagicMock()
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=None)
    client_mock.get = AsyncMock(return_value=resp)

    return patch("httpx.AsyncClient", return_value=client_mock)


async def test_get_or_link_user_blocks_inactive_user_on_first_login(db_session):
    """First login by an inactive user should raise LookupError."""
    db_session.add(
        User(
            nuid=12345,
            first_name="Inactive",
            last_name="User",
            email="inactive@example.com",
            role="VIEWER",
            auth0_sub=None,
            active=False,
        )
    )
    db_session.commit()

    with _mock_userinfo("inactive@example.com"):
        with pytest.raises(LookupError):
            await get_or_link_user(db_session, sub="auth0|new-sub", access_token="token")

    refreshed = db_session.query(User).filter(User.email == "inactive@example.com").first()
    assert refreshed.auth0_sub is None, "inactive user should not be linked"


async def test_get_or_link_user_blocks_inactive_user_on_subsequent_request(db_session):
    """A user whose auth0_sub is already linked but who is now inactive should be blocked."""
    db_session.add(
        User(
            nuid=67890,
            first_name="Deactivated",
            last_name="User",
            email="deactivated@example.com",
            role="VIEWER",
            auth0_sub="auth0|linked-sub",
            active=False,
        )
    )
    db_session.commit()

    with pytest.raises(LookupError):
        await get_or_link_user(db_session, sub="auth0|linked-sub", access_token="token")


async def test_get_or_link_user_allows_active_user_on_first_login(db_session):
    """First login by an active user should link the sub and return the user."""
    db_session.add(
        User(
            nuid=11111,
            first_name="Active",
            last_name="User",
            email="active@example.com",
            role="VIEWER",
            auth0_sub=None,
            active=True,
        )
    )
    db_session.commit()

    with _mock_userinfo("active@example.com"):
        user = await get_or_link_user(db_session, sub="auth0|fresh-sub", access_token="token")

    assert user.email == "active@example.com"
    assert user.auth0_sub == "auth0|fresh-sub"
