"""Websocket router."""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.section import SectionRichResponse
from app.services import section as section_service
from app.services.connection_manager import manager
from app.services.user import get_or_link_user, get_sub

router = APIRouter(prefix="/ws", tags=["websockets"])


@router.websocket("/{schedule_id}")
async def websocket_schedule(
    websocket: WebSocket,
    schedule_id: int,
    token: str,
    db: Session = Depends(get_db),
):
    try:
        sub = get_sub(token)
    except Exception:
        await websocket.close(code=4001)
        return

    try:
        user = get_or_link_user(db, sub, token)
    except (LookupError, ValueError):
        await websocket.close(code=4001)
        return

    if not user:
        await websocket.close(code=4001)
        return
    user_id = user.user_id

    await manager.connect(schedule_id, user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            data.get("action")  # for now ignore action - just return schedule data

            db.expire_all()
            sections = section_service.get_rich_sections(db, schedule_id)
            payload = {
                "type": "schedule",
                "payload": [SectionRichResponse.model_validate(s).model_dump() for s in sections],
            }
            await manager.broadcast(schedule_id, payload)
    except WebSocketDisconnect:
        manager.disconnect(schedule_id, websocket)


# test using:
# websocat "ws://localhost:8000/ws/1?token="
