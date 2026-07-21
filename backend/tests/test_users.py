"""Tests for GET /api/users, focused on the has_signed_up field."""

from app.models.user import User


def _make_user(db, nuid, email, *, auth0_sub=None, role="ADMIN", active=True):
    u = User(
        nuid=nuid,
        first_name="First",
        last_name=f"User{nuid}",
        email=email,
        role=role,
        auth0_sub=auth0_sub,
        active=active,
    )
    db.add(u)
    db.flush()
    return u


def test_list_users_reports_has_signed_up(client, db_session):
    """Users with an auth0_sub are signed up; pending invites are not."""
    _make_user(db_session, 3001, "linked@example.com", auth0_sub="auth0|abc")
    _make_user(db_session, 3002, "pending@example.com", auth0_sub=None)
    db_session.commit()

    response = client.get("/api/users")
    assert response.status_code == 200
    by_email = {u["email"]: u for u in response.json()}

    assert by_email["linked@example.com"]["has_signed_up"] is True
    assert by_email["pending@example.com"]["has_signed_up"] is False


def test_list_users_includes_expected_fields(client, db_session):
    """Response exposes the admin-view fields including has_signed_up."""
    _make_user(db_session, 3003, "admin@example.com", auth0_sub="auth0|xyz")
    db_session.commit()

    response = client.get("/api/users")
    assert response.status_code == 200
    user = next(u for u in response.json() if u["email"] == "admin@example.com")
    for field in ("user_id", "nuid", "first_name", "last_name", "email", "role", "active", "has_signed_up"):
        assert field in user
