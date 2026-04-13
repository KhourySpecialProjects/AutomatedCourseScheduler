"""
WebSocket broadcast integration tests.

Each test connects a WebSocket listener to a schedule, triggers an HTTP
mutation, then asserts that the correct event type (and key payload fields)
arrive over the socket.

Pattern:
  1. Seed DB data.
  2. Open a WS connection (auth mocked via patch).
  3. Fire an HTTP request via `client`.
  4. ws.receive_json() — assert type + key payload fields.

Ordering note for PATCH /sections:
  PATCH first acquires the lock (broadcasts lock_acquired) then updates
  (broadcasts section_updated).  Tests that only care about section_updated
  pre-acquire the lock so the refresh is silent, leaving section_updated as
  the only message in the buffer.
"""

from contextlib import contextmanager
from datetime import time
from unittest.mock import MagicMock, patch

import pytest

from app.models import Comment, Course, Schedule, Section, TimeBlock
from app.models.campus import Campus
from app.models.semester import Semester
from app.models.user import User
from app.services.connection_manager import manager

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_manager():
    manager.connections.clear()
    yield
    manager.connections.clear()


def _seed(db):
    """Return (schedule, section, user) with all required FK rows in place."""
    campus = Campus(name="Boston")
    db.add(campus)
    db.flush()
    semester = Semester(season="Fall", year=2025)
    db.add(semester)
    db.flush()
    schedule = Schedule(name="Test", semester_id=semester.semester_id, campus=campus.campus_id)
    course = Course(subject="CS", code=2500, name="CS 2500", description="Fundamentals", credits=4)
    db.add_all([schedule, course])
    db.flush()
    tb = TimeBlock(
        meeting_days="MW",
        start_time=time(10, 0),
        end_time=time(11, 0),
        campus=campus.campus_id,
    )
    db.add(tb)
    db.flush()
    section = Section(
        schedule_id=schedule.schedule_id,
        time_block_id=tb.time_block_id,
        course_id=course.course_id,
        section_number=1,
        capacity=30,
    )
    user = User(
        nuid=9001,
        first_name="Admin",
        last_name="User",
        email="admin@test.com",
        role="ADMIN",
    )
    db.add_all([section, user])
    db.commit()
    return schedule, section, user


@contextmanager
def _ws(client, schedule_id, user):
    """Open an authenticated WebSocket connection to a schedule."""
    mock_user = MagicMock()
    mock_user.user_id = user.user_id
    with (
        patch("app.routers.websocket.get_sub", return_value="auth0|test"),
        patch("app.routers.websocket.get_or_link_user", return_value=mock_user),
    ):
        with client.websocket_connect(f"/ws/{schedule_id}?token=test") as ws:
            yield ws


# ---------------------------------------------------------------------------
# Section broadcasts
# ---------------------------------------------------------------------------


def test_create_section_broadcasts_section_created(client, db_session):
    schedule, section, user = _seed(db_session)

    with _ws(client, schedule.schedule_id, user) as ws:
        client.post(
            "/sections",
            json={
                "schedule_id": schedule.schedule_id,
                "time_block_id": section.time_block_id,
                "course_id": section.course_id,
                "capacity": 20,
                "section_number": 2,
            },
        )
        msg = ws.receive_json()

    assert msg["type"] == "section_created"
    assert msg["payload"]["schedule_id"] == schedule.schedule_id


def test_delete_section_broadcasts_section_deleted(client, db_session):
    schedule, section, user = _seed(db_session)

    with _ws(client, schedule.schedule_id, user) as ws:
        client.delete(f"/sections/{section.section_id}")
        msg = ws.receive_json()

    assert msg["type"] == "section_deleted"
    assert msg["payload"]["section_id"] == section.section_id


def test_update_section_broadcasts_section_updated(client, db_session):
    from app.core.auth import get_db_user
    from app.main import app

    schedule, section, user = _seed(db_session)
    app.dependency_overrides[get_db_user] = lambda: user

    # Pre-acquire lock so the PATCH refresh is silent (no lock_acquired message).
    client.post(f"/sections/{section.section_id}/lock")

    with _ws(client, schedule.schedule_id, user) as ws:
        client.patch(f"/sections/{section.section_id}", json={"capacity": 99})
        msg = ws.receive_json()

    assert msg["type"] == "section_updated"
    assert msg["payload"]["section_id"] == section.section_id
    assert msg["payload"]["data"]["capacity"] == 99


# ---------------------------------------------------------------------------
# Lock broadcasts
# ---------------------------------------------------------------------------


def test_acquire_lock_broadcasts_lock_acquired(client, db_session):
    from app.core.auth import get_db_user
    from app.main import app

    schedule, section, user = _seed(db_session)
    app.dependency_overrides[get_db_user] = lambda: user

    with _ws(client, schedule.schedule_id, user) as ws:
        client.post(f"/sections/{section.section_id}/lock")
        msg = ws.receive_json()

    assert msg["type"] == "lock_acquired"
    assert msg["payload"]["section_id"] == section.section_id
    assert msg["payload"]["locked_by"] == user.user_id


def test_acquire_lock_refresh_does_not_broadcast(client, db_session):
    """Re-acquiring a lock you already hold must not send a second lock_acquired."""
    from app.core.auth import get_db_user
    from app.main import app

    schedule, section, user = _seed(db_session)
    app.dependency_overrides[get_db_user] = lambda: user

    # First acquire — will broadcast lock_acquired.
    client.post(f"/sections/{section.section_id}/lock")

    with _ws(client, schedule.schedule_id, user) as ws:
        # Refresh — same user, no broadcast expected.
        client.post(f"/sections/{section.section_id}/lock")

        # No message should arrive; send a refresh to get a known response.
        ws.send_json({"action": "refresh"})
        msg = ws.receive_json()

    # The only message in the buffer is the explicit schedule refresh, not a lock event.
    assert msg["type"] == "schedule"


def test_release_lock_broadcasts_lock_released(client, db_session):
    from app.core.auth import get_db_user
    from app.main import app

    schedule, section, user = _seed(db_session)
    app.dependency_overrides[get_db_user] = lambda: user

    # Acquire first (broadcasts lock_acquired — consumed before opening WS listener).
    client.post(f"/sections/{section.section_id}/lock")

    with _ws(client, schedule.schedule_id, user) as ws:
        client.post(f"/sections/{section.section_id}/unlock")
        msg = ws.receive_json()

    assert msg["type"] == "lock_released"
    assert msg["payload"]["section_id"] == section.section_id


# ---------------------------------------------------------------------------
# Comment broadcasts
# ---------------------------------------------------------------------------


def test_post_comment_broadcasts_comment_added(client, db_session):
    schedule, section, user = _seed(db_session)

    with _ws(client, schedule.schedule_id, user) as ws:
        client.post(
            "/comments",
            json={
                "section_id": section.section_id,
                "user_id": user.user_id,
                "content": "Hello",
            },
        )
        msg = ws.receive_json()

    assert msg["type"] == "comment_added"
    assert msg["payload"]["section_id"] == section.section_id
    assert msg["payload"]["content"] == "Hello"


def test_post_reply_broadcasts_comment_added(client, db_session):
    schedule, section, user = _seed(db_session)

    parent = Comment(
        user_id=user.user_id,
        section_id=section.section_id,
        content="Parent",
    )
    db_session.add(parent)
    db_session.commit()

    with _ws(client, schedule.schedule_id, user) as ws:
        client.post(
            f"/comments/{parent.comment_id}",
            json={
                "section_id": section.section_id,
                "user_id": user.user_id,
                "content": "Reply",
            },
        )
        msg = ws.receive_json()

    assert msg["type"] == "comment_added"
    assert msg["payload"]["parent_id"] == parent.comment_id


def test_delete_comment_broadcasts_comment_deleted(client, db_session):
    schedule, section, user = _seed(db_session)

    comment = Comment(
        user_id=user.user_id,
        section_id=section.section_id,
        content="To delete",
    )
    db_session.add(comment)
    db_session.commit()

    with _ws(client, schedule.schedule_id, user) as ws:
        client.delete(f"/comments/{comment.comment_id}")
        msg = ws.receive_json()

    assert msg["type"] == "comment_deleted"
    assert msg["payload"]["comment_id"] == comment.comment_id
    assert msg["payload"]["section_id"] == section.section_id


def test_resolve_comment_broadcasts_comment_resolved(client, db_session):
    schedule, section, user = _seed(db_session)

    comment = Comment(
        user_id=user.user_id,
        section_id=section.section_id,
        content="To resolve",
    )
    db_session.add(comment)
    db_session.commit()

    with _ws(client, schedule.schedule_id, user) as ws:
        client.put(f"/comments/{comment.comment_id}")
        msg = ws.receive_json()

    assert msg["type"] == "comment_resolved"
    assert msg["payload"]["comment_id"] == comment.comment_id
    assert msg["payload"]["section_id"] == section.section_id


# ---------------------------------------------------------------------------
# Schedule broadcasts
# ---------------------------------------------------------------------------


def test_update_schedule_broadcasts_schedule_updated(client, db_session):
    schedule, _, user = _seed(db_session)

    with _ws(client, schedule.schedule_id, user) as ws:
        client.put(f"/schedules/{schedule.schedule_id}", json={"name": "Renamed"})
        msg = ws.receive_json()

    assert msg["type"] == "schedule_updated"
    assert msg["payload"]["schedule_id"] == schedule.schedule_id
    assert msg["payload"]["name"] == "Renamed"


def test_delete_schedule_broadcasts_schedule_deleted(client, db_session):
    schedule, _, user = _seed(db_session)

    with _ws(client, schedule.schedule_id, user) as ws:
        client.delete(f"/schedules/{schedule.schedule_id}")
        msg = ws.receive_json()

    assert msg["type"] == "schedule_deleted"
    assert msg["payload"]["schedule_id"] == schedule.schedule_id


def test_delete_schedule_removes_all_connections(client, db_session):
    schedule, _, user = _seed(db_session)

    with _ws(client, schedule.schedule_id, user) as ws:
        assert schedule.schedule_id in manager.connections
        client.delete(f"/schedules/{schedule.schedule_id}")
        ws.receive_json()  # consume schedule_deleted

    assert schedule.schedule_id not in manager.connections


def test_no_broadcast_to_other_schedule(client, db_session):
    """Events on schedule A must not reach a listener connected to schedule B."""
    campus = Campus(name="Boston")
    db_session.add(campus)
    db_session.flush()
    semester = Semester(season="Fall", year=2025)
    db_session.add(semester)
    db_session.flush()

    schedule_a = Schedule(name="A", semester_id=semester.semester_id, campus=campus.campus_id)
    schedule_b = Schedule(name="B", semester_id=semester.semester_id, campus=campus.campus_id)
    db_session.add_all([schedule_a, schedule_b])
    db_session.commit()

    user = MagicMock()
    user.user_id = 99

    with (
        patch("app.routers.websocket.get_sub", return_value="auth0|test"),
        patch("app.routers.websocket.get_or_link_user", return_value=user),
    ):
        with client.websocket_connect(f"/ws/{schedule_b.schedule_id}?token=test") as ws:
            # Mutate schedule A — schedule B listener should receive nothing.
            client.put(f"/schedules/{schedule_a.schedule_id}", json={"name": "Changed"})

            # Trigger a known message on schedule B so the listener has something to consume.
            client.put(f"/schedules/{schedule_b.schedule_id}", json={"name": "B Updated"})
            msg = ws.receive_json()

    # The first (and only) message the B listener receives is from its own schedule.
    assert msg["payload"]["schedule_id"] == schedule_b.schedule_id
