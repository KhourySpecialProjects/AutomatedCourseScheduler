"""Websocket router."""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import schedule as schedule_service
from app.services import user as user_service
from app.services.connection_manager import manager

router = APIRouter(prefix="/ws", tags=["websockets"])


@router.websocket("/{schedule_id}")
async def websocket_schedule(
    websocket: WebSocket,
    schedule_id: int,
    token: str,
    db: Session = Depends(get_db),
):
    user = user_service.get_or_link_user(db, "", token)
    # user = db.query(User).filter(User.auth0_sub == auth0_sub).first()
    if not user:
        await websocket.close(code=4001)
        return
    user_id = user.user_id

    await manager.connect(schedule_id, user_id, websocket)

    # schedule = schedule_service.get_by_id(db, schedule_id)
    # await websocket.send_json({
    #     "type": "schedule",
    #     "payload": ScheduleResponse.model_validate(schedule).model_dump()
    # })

    try:
        while True:
            data = await websocket.receive_json()
            schedule = await schedule_service.get_by_id(schedule_id)
            await websocket.send_json({"type": "schedule", "payload": schedule})
            await manager.broadcast(schedule_id, data)
    except WebSocketDisconnect:
        await manager.disconnect(user.user_id)


# test using:
# websocat "ws://localhost:8000/ws/1?token=ey..."
