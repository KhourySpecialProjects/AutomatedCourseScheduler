"""Algorithm router."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import schedule as schedule_repo
from app.schemas.generate_schedule import (
    GenerateScheduleRequest,
    RegenerateScheduleRequest,
)
from app.services.algorithm import run_algorithm_task, run_regenerate_task

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/{schedule_id}/generate", status_code=202)
def run_algorithm(
    schedule_id: int,
    request: GenerateScheduleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not schedule_repo.schedule_exists(db, schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")

    background_tasks.add_task(run_algorithm_task, db, schedule_id, request.parameters)
    return {"schedule_id": schedule_id, "status": "running"}
    # TODO (websocket): when run_algorithm_task completes, broadcast to connected clients:
    #   type: "schedule_regenerated", payload: all rich sections for the generated schedule_id
    #   This requires passing db + schedule_id into the background task and calling
    #   manager.broadcast(schedule_id, {"type": "schedule_regenerated", "payload": [...]})
    background_tasks.add_task(run_algorithm_task, request.parameters)
    return {"status": "running"}


@router.post("/{schedule_id}/regenerate", status_code=202)
def regenerate_algorithm(
    schedule_id: int,
    request: RegenerateScheduleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not schedule_repo.schedule_exists(db, schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")

    background_tasks.add_task(run_regenerate_task, db, schedule_id, request.parameters)
    # TODO (websocket): when run_regenerate_task completes, broadcast to connected clients:
    #   type: "schedule_regenerated", payload: all rich sections for schedule_id
    #   This requires passing db + schedule_id into the background task and calling
    #   manager.broadcast(schedule_id, {"type": "schedule_regenerated", "payload": [...]})
    background_tasks.add_task(run_regenerate_task, schedule_id, request.parameters)
    return {"schedule_id": schedule_id, "status": "running"}
