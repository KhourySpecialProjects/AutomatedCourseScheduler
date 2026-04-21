"""Tests for GET /api/invites/export."""

from unittest.mock import patch

from app.models.faculty import Faculty
from app.models.user import User

FAKE_URL = "https://test.auth0.com/authorize?login_hint="


def _make_faculty(db, nuid, first_name, last_name, email, active=True):
    f = Faculty(
        nuid=nuid,
        first_name=first_name,
        last_name=last_name,
        email=email,
        campus=1,
        active=active,
    )
    db.add(f)
    db.flush()
    return f


def _make_user(db, faculty, auth0_sub=None):
    u = User(
        nuid=faculty.nuid,
        first_name=faculty.first_name,
        last_name=faculty.last_name,
        email=faculty.email,
        role="VIEWER",
        auth0_sub=auth0_sub,
        active=True,
    )
    db.add(u)
    db.flush()
    return u


@patch(
    "app.services.user.auth0_service.build_signup_url",
    side_effect=lambda email: f"{FAKE_URL}{email}",
)
def test_export_empty(mock_url, client, db_session):
    """No faculty → empty list."""
    response = client.get("/api/invites/export")
    assert response.status_code == 200
    assert response.json() == []


@patch(
    "app.services.user.auth0_service.build_signup_url",
    side_effect=lambda email: f"{FAKE_URL}{email}",
)
def test_export_returns_uninvited_faculty(mock_url, client, db_session):
    """Uninvited active faculty appear in the response."""
    _make_faculty(db_session, 1001, "Jane", "Doe", "jane@example.com")
    db_session.commit()

    response = client.get("/api/invites/export")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["first_name"] == "Jane"
    assert data[0]["last_name"] == "Doe"
    assert data[0]["email"] == "jane@example.com"
    assert data[0]["invite_link"] == f"{FAKE_URL}jane@example.com"


@patch(
    "app.services.user.auth0_service.build_signup_url",
    side_effect=lambda email: f"{FAKE_URL}{email}",
)
def test_export_creates_user_records_for_uninvited(mock_url, client, db_session):
    """A User record is created for faculty that had none."""
    _make_faculty(db_session, 1002, "Bob", "Smith", "bob@example.com")
    db_session.commit()

    client.get("/api/invites/export")

    user = db_session.query(User).filter(User.nuid == 1002).first()
    assert user is not None
    assert user.auth0_sub is None
    assert user.role == "VIEWER"


@patch(
    "app.services.user.auth0_service.build_signup_url",
    side_effect=lambda email: f"{FAKE_URL}{email}",
)
def test_export_includes_pending_faculty(mock_url, client, db_session):
    """Faculty with a User record but no auth0_sub (invited, never logged in) are included."""
    f = _make_faculty(db_session, 1003, "Alice", "Green", "alice@example.com")
    _make_user(db_session, f, auth0_sub=None)
    db_session.commit()

    response = client.get("/api/invites/export")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "alice@example.com"


@patch(
    "app.services.user.auth0_service.build_signup_url",
    side_effect=lambda email: f"{FAKE_URL}{email}",
)
def test_export_excludes_linked_faculty(mock_url, client, db_session):
    """Faculty with a linked account (auth0_sub set) are excluded."""
    f = _make_faculty(db_session, 1004, "Carol", "White", "carol@example.com")
    _make_user(db_session, f, auth0_sub="auth0|abc123")
    db_session.commit()

    response = client.get("/api/invites/export")
    assert response.status_code == 200
    assert response.json() == []


@patch(
    "app.services.user.auth0_service.build_signup_url",
    side_effect=lambda email: f"{FAKE_URL}{email}",
)
def test_export_excludes_inactive_faculty(mock_url, client, db_session):
    """Inactive faculty are excluded even if uninvited."""
    _make_faculty(db_session, 1005, "Dan", "Brown", "dan@example.com", active=False)
    db_session.commit()

    response = client.get("/api/invites/export")
    assert response.status_code == 200
    assert response.json() == []


@patch(
    "app.services.user.auth0_service.build_signup_url",
    side_effect=lambda email: f"{FAKE_URL}{email}",
)
def test_export_idempotent_for_pending(mock_url, client, db_session):
    """Re-exporting does not create a duplicate User record for already-pending faculty."""
    f = _make_faculty(db_session, 1006, "Eve", "Black", "eve@example.com")
    _make_user(db_session, f, auth0_sub=None)
    db_session.commit()

    client.get("/api/invites/export")
    client.get("/api/invites/export")

    count = db_session.query(User).filter(User.nuid == 1006).count()
    assert count == 1


@patch(
    "app.services.user.auth0_service.build_signup_url",
    side_effect=lambda email: f"{FAKE_URL}{email}",
)
def test_export_mixed_faculty(mock_url, client, db_session):
    """Only uninvited and pending faculty appear; linked and inactive are excluded."""
    uninvited = _make_faculty(db_session, 2001, "Uninvited", "One", "uninvited@example.com")
    pending = _make_faculty(db_session, 2002, "Pending", "Two", "pending@example.com")
    linked = _make_faculty(db_session, 2003, "Linked", "Three", "linked@example.com")
    inactive = _make_faculty(db_session, 2004, "Inactive", "Four", "inactive@example.com", active=False)

    _make_user(db_session, pending, auth0_sub=None)
    _make_user(db_session, linked, auth0_sub="auth0|xyz")
    db_session.commit()

    response = client.get("/api/invites/export")
    assert response.status_code == 200
    emails = {row["email"] for row in response.json()}
    assert emails == {"uninvited@example.com", "pending@example.com"}

    _ = uninvited, inactive  # referenced to avoid lint warnings


# ---------------------------------------------------------------------------
# POST /api/invites/admin
# ---------------------------------------------------------------------------


@patch(
    "app.services.user.auth0_service.build_signup_url",
    side_effect=lambda email: f"{FAKE_URL}{email}",
)
def test_invite_admin_creates_pending_admin_and_returns_url(mock_url, client, db_session):
    response = client.post(
        "/api/invites/admin",
        json={
            "nuid": 88001,
            "first_name": "Pat",
            "last_name": "Admin",
            "email": "pat.admin@example.com",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["nuid"] == 88001
    assert data["user"]["role"] == "ADMIN"
    assert data["user"]["first_name"] == "Pat"
    assert data["signup_url"] == f"{FAKE_URL}pat.admin@example.com"


@patch(
    "app.services.user.auth0_service.build_signup_url",
    side_effect=lambda email: f"{FAKE_URL}{email}",
)
def test_invite_admin_rejects_duplicate_nuid(mock_url, client, db_session):
    _make_user(db_session, _make_faculty(db_session, 88002, "A", "B", "a@example.com"))
    db_session.commit()

    response = client.post(
        "/api/invites/admin",
        json={
            "nuid": 88002,
            "first_name": "Other",
            "last_name": "Name",
            "email": "other@example.com",
        },
    )
    assert response.status_code == 400
    assert "88002" in response.json()["detail"]


@patch(
    "app.services.user.auth0_service.build_signup_url",
    side_effect=lambda email: f"{FAKE_URL}{email}",
)
def test_invite_admin_rejects_duplicate_email(mock_url, client, db_session):
    _make_user(db_session, _make_faculty(db_session, 88003, "A", "B", "taken@example.com"))
    db_session.commit()

    response = client.post(
        "/api/invites/admin",
        json={
            "nuid": 999999,
            "first_name": "Other",
            "last_name": "Name",
            "email": "taken@example.com",
        },
    )
    assert response.status_code == 400
    assert "taken@example.com" in response.json()["detail"]
