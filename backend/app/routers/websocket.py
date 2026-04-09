"""Websocket router."""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import section_lock as section_lock_repo
from app.schemas.section import SectionRichResponse
from app.services import section as section_service
from app.services import section_lock as section_lock_service
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
        user = await get_or_link_user(db, sub, token)
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
        user_lock = section_lock_repo.get_by_user_id(db, user_id)
        if user_lock:
            await section_lock_service.release_lock(db, user_lock.section_id, user_id)


# test using:
# websocat "ws://localhost:8000/ws/1?token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImlBTzNaLUFMRmtDQ1NOQXgwYjVWTCJ9.eyJpc3MiOiJodHRwczovL2Rldi1vNmpsOGoya2MyZHZvdnV6LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJhdXRoMHw2OWQwNDBlMmE3YmU3NmVhYjVhYzE2NzEiLCJhdWQiOlsiaHR0cHM6Ly9hcGkuYXV0b3NjaGVkdWxlci5jb20iLCJodHRwczovL2Rldi1vNmpsOGoya2MyZHZvdnV6LnVzLmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE3NzU1NDIxMjcsImV4cCI6MTc3NTYyODUyNywic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImF6cCI6InF6cnpNRTVRcGUwdGFJY1VLSVAzVjFGY1dTNXZqMUQ2In0.rgMH6TgL5rpxVSK3HWKLa92E1lMeQyI0KRH2pJbECu3vwVXngWxuLnHPfJXNyrXPCfPpOGZ0gY-z3Av5QOD_o-8SuXu7keHtf0Y2nIFSgzlMlzkYT-gj3YcN8qJmUTuOt6ZMPjIPYXGUiB2yCMpkPTqYYp04Enzi4WPMa0dRgz1sEY8KBCsTy4Ab1s-sjwUZmTUvBE932NeAGrxKu887GKpEIwGzHlwn-4i85w-iGHbTnLMTRbEqn1xNEImis_bhUQwJVZUqwERpTsypkoPbOLSvg4NblTszwWf92U5cCiCwPN9QqveBak3HfdxTyqH1SechSQOPzqGN4-nCWrfQ4g"
