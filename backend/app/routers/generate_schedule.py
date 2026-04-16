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
from app.services.connection_manager import manager

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
    manager.broadcast(schedule_id, {"type": "schedule_generated", "payload": {}})
    return {"schedule_id": schedule_id, "status": "running"}


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
    manager.broadcast(schedule_id, {"type": "schedule_regenerated", "payload": {}})

    return {"schedule_id": schedule_id, "status": "running"}
