"""Unit tests for ConnectionManager."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.connection_manager import ConnectionManager


def make_ws():
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


@pytest.fixture
def cm():
    return ConnectionManager()


# ---------------------------------------------------------------------------
# connect
# ---------------------------------------------------------------------------


async def test_connect_calls_accept(cm):
    ws = make_ws()
    await cm.connect(1, 42, ws)
    ws.accept.assert_awaited_once()


async def test_connect_stores_websocket(cm):
    ws = make_ws()
    await cm.connect(1, 42, ws)
    assert ws in cm.connections[1]
    assert cm.connections[1][ws] == 42


async def test_connect_multiple_users_same_schedule(cm):
    ws1, ws2 = make_ws(), make_ws()
    await cm.connect(1, 1, ws1)
    await cm.connect(1, 2, ws2)
    assert len(cm.connections[1]) == 2


async def test_connect_multiple_schedules_are_isolated(cm):
    ws1, ws2 = make_ws(), make_ws()
    await cm.connect(1, 1, ws1)
    await cm.connect(2, 2, ws2)
    assert len(cm.connections[1]) == 1
    assert len(cm.connections[2]) == 1


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------


async def test_disconnect_removes_websocket(cm):
    ws = make_ws()
    await cm.connect(1, 42, ws)
    cm.disconnect(1, ws)
    assert ws not in cm.connections.get(1, {})


async def test_disconnect_cleans_up_empty_schedule(cm):
    ws = make_ws()
    await cm.connect(1, 42, ws)
    cm.disconnect(1, ws)
    assert 1 not in cm.connections


async def test_disconnect_returns_user_id(cm):
    ws = make_ws()
    await cm.connect(1, 42, ws)
    user_id = cm.disconnect(1, ws)
    assert user_id == 42


async def test_disconnect_leaves_other_connections_intact(cm):
    ws1, ws2 = make_ws(), make_ws()
    await cm.connect(1, 1, ws1)
    await cm.connect(1, 2, ws2)
    cm.disconnect(1, ws1)
    assert ws2 in cm.connections[1]
    assert ws1 not in cm.connections[1]


async def test_disconnect_unknown_schedule_does_not_raise(cm):
    ws = make_ws()
    cm.disconnect(99, ws)  # should not raise


async def test_disconnect_unknown_websocket_does_not_raise(cm):
    ws1, ws2 = make_ws(), make_ws()
    await cm.connect(1, 1, ws1)
    cm.disconnect(1, ws2)  # ws2 was never added


# ---------------------------------------------------------------------------
# broadcast
# ---------------------------------------------------------------------------


async def test_broadcast_sends_message_to_all_connections(cm):
    ws1, ws2 = make_ws(), make_ws()
    await cm.connect(1, 1, ws1)
    await cm.connect(1, 2, ws2)
    await cm.broadcast(1, {"type": "test"})
    ws1.send_json.assert_awaited_once_with({"type": "test"})
    ws2.send_json.assert_awaited_once_with({"type": "test"})


async def test_broadcast_does_not_reach_other_schedules(cm):
    ws1, ws2 = make_ws(), make_ws()
    await cm.connect(1, 1, ws1)
    await cm.connect(2, 2, ws2)
    await cm.broadcast(1, {"type": "test"})
    ws1.send_json.assert_awaited_once()
    ws2.send_json.assert_not_called()


async def test_broadcast_to_empty_schedule_does_not_raise(cm):
    await cm.broadcast(99, {"type": "test"})  # should not raise
