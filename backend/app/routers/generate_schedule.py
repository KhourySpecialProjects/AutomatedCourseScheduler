"""Algorithm router."""

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import ScheduleStatus
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
    schedule = schedule_repo.get_by_id(db, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule.status == ScheduleStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Algorithm already running")

    schedule.status = ScheduleStatus.RUNNING
    schedule.started_at = datetime.now(timezone.utc)
    schedule.completed_at = None
    schedule.error_message = None
    db.commit()

    background_tasks.add_task(run_algorithm_task, schedule_id, request.parameters)
    return {"schedule_id": schedule_id, "status": "running"}


@router.post("/{schedule_id}/regenerate", status_code=202)
def regenerate_algorithm(
    schedule_id: int,
    request: RegenerateScheduleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    schedule = schedule_repo.get_by_id(db, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule.status == ScheduleStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Algorithm already running")

    schedule.status = ScheduleStatus.RUNNING
    schedule.started_at = datetime.now(timezone.utc)
    schedule.completed_at = None
    schedule.error_message = None
    db.commit()

    background_tasks.add_task(run_regenerate_task, schedule_id, request.parameters)
    return {"schedule_id": schedule_id, "status": "running"}