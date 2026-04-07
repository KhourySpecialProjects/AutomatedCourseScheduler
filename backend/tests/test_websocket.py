"""Integration tests for the /ws/{schedule_id} WebSocket endpoint."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from starlette.websockets import WebSocketDisconnect

from app.models import Schedule
from app.models.campus import Campus
from app.models.section_lock import SectionLock
from app.models.semester import Semester
from app.services.connection_manager import manager


@pytest.fixture(autouse=True)
def reset_manager():
    """Ensure the global ConnectionManager is empty before and after each test."""
    manager.connections.clear()
    yield
    manager.connections.clear()


def _make_schedule(db) -> Schedule:
    campus = Campus(name="Boston")
    db.add(campus)
    db.flush()
    semester = Semester(season="Fall", year=2025)
    db.add(semester)
    db.flush()
    schedule = Schedule(name="Test", semester_id=semester.semester_id, campus=campus.campus_id)
    db.add(schedule)
    db.commit()
    return schedule


def _mock_user(user_id: int = 1):
    user = MagicMock()
    user.user_id = user_id
    return user


# ---------------------------------------------------------------------------
# Auth failures — close with code 4001
# ---------------------------------------------------------------------------


def test_invalid_token_closes_4001(client):
    with patch("app.routers.websocket.get_sub", side_effect=Exception("bad token")):
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/1?token=bad"):
                pass
        assert exc_info.value.code == 4001


def test_unknown_user_closes_4001(client, db_session):
    with (
        patch("app.routers.websocket.get_sub", return_value="auth0|unknown"),
        patch(
            "app.routers.websocket.get_or_link_user",
            side_effect=LookupError("not found"),
        ),
    ):
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/1?token=fake"):
                pass
        assert exc_info.value.code == 4001


def test_invalid_user_value_error_closes_4001(client, db_session):
    with (
        patch("app.routers.websocket.get_sub", return_value="auth0|x"),
        patch(
            "app.routers.websocket.get_or_link_user",
            side_effect=ValueError("bad value"),
        ),
    ):
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/1?token=fake"):
                pass
        assert exc_info.value.code == 4001


# ---------------------------------------------------------------------------
# Successful connection
# ---------------------------------------------------------------------------


def test_successful_connection_is_tracked(client, db_session):
    schedule = _make_schedule(db_session)
    user = _mock_user(user_id=7)

    with (
        patch("app.routers.websocket.get_sub", return_value="auth0|abc"),
        patch("app.routers.websocket.get_or_link_user", return_value=user),
        patch("app.services.section.get_rich_sections", return_value=[]),
    ):
        with client.websocket_connect(f"/ws/{schedule.schedule_id}?token=good") as ws:
            assert schedule.schedule_id in manager.connections
            ws.send_json({"action": "refresh"})
            ws.receive_json()  # consume the broadcast so the loop progresses


def test_disconnect_removes_connection_from_manager(client, db_session):
    schedule = _make_schedule(db_session)
    user = _mock_user(user_id=7)

    with (
        patch("app.routers.websocket.get_sub", return_value="auth0|abc"),
        patch("app.routers.websocket.get_or_link_user", return_value=user),
        patch("app.services.section.get_rich_sections", return_value=[]),
    ):
        with client.websocket_connect(f"/ws/{schedule.schedule_id}?token=good") as ws:
            ws.send_json({"action": "refresh"})
            ws.receive_json()

    assert schedule.schedule_id not in manager.connections


# ---------------------------------------------------------------------------
# Message handling / broadcast
# ---------------------------------------------------------------------------


def test_receive_message_returns_schedule_type(client, db_session):
    schedule = _make_schedule(db_session)
    user = _mock_user()

    with (
        patch("app.routers.websocket.get_sub", return_value="auth0|abc"),
        patch("app.routers.websocket.get_or_link_user", return_value=user),
        patch("app.services.section.get_rich_sections", return_value=[]),
    ):
        with client.websocket_connect(f"/ws/{schedule.schedule_id}?token=good") as ws:
            ws.send_json({"action": "anything"})
            payload = ws.receive_json()
            assert payload["type"] == "schedule"
            assert "payload" in payload
            assert isinstance(payload["payload"], list)


def test_receive_message_payload_is_empty_when_no_sections(client, db_session):
    schedule = _make_schedule(db_session)
    user = _mock_user()

    with (
        patch("app.routers.websocket.get_sub", return_value="auth0|abc"),
        patch("app.routers.websocket.get_or_link_user", return_value=user),
        patch("app.services.section.get_rich_sections", return_value=[]),
    ):
        with client.websocket_connect(f"/ws/{schedule.schedule_id}?token=good") as ws:
            ws.send_json({})
            payload = ws.receive_json()
            assert payload["payload"] == []


def test_multiple_messages_each_trigger_broadcast(client, db_session):
    schedule = _make_schedule(db_session)
    user = _mock_user()

    with (
        patch("app.routers.websocket.get_sub", return_value="auth0|abc"),
        patch("app.routers.websocket.get_or_link_user", return_value=user),
        patch("app.services.section.get_rich_sections", return_value=[]),
    ):
        with client.websocket_connect(f"/ws/{schedule.schedule_id}?token=good") as ws:
            for _ in range(3):
                ws.send_json({"action": "refresh"})
                payload = ws.receive_json()
                assert payload["type"] == "schedule"


# ---------------------------------------------------------------------------
# Disconnect — lock release
# ---------------------------------------------------------------------------


def test_disconnect_releases_section_lock(client, db_session):
    """When a user disconnects, any lock they hold should be released immediately."""
    schedule = _make_schedule(db_session)
    user = _mock_user(user_id=42)

    now = datetime.now(UTC).replace(tzinfo=None)
    lock = SectionLock(
        section_id=1,
        locked_by=42,
        expires_at=now + timedelta(minutes=2),
    )
    db_session.add(lock)
    db_session.commit()

    with (
        patch("app.routers.websocket.get_sub", return_value="auth0|abc"),
        patch("app.routers.websocket.get_or_link_user", return_value=user),
        patch("app.services.section.get_rich_sections", return_value=[]),
    ):
        with client.websocket_connect(f"/ws/{schedule.schedule_id}?token=good") as ws:
            ws.send_json({"action": "refresh"})
            ws.receive_json()

    db_session.expire_all()
    remaining = db_session.query(SectionLock).filter(SectionLock.locked_by == 42).first()
    assert remaining is None
