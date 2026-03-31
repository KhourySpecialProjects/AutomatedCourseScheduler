"""Algorithm router."""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.generate_schedule import (
    GenerateScheduleRequest,
    RegenerateScheduleRequest,
)
from app.services.algorithm import run_algorithm_task, run_regenerate_task

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/generate", status_code=202)
def run_algorithm(
    request: GenerateScheduleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # TODO:
    # - raise 409 if any schedule is currently RUNNING
    # - set schedule.status = RUNNING, started_at = now(), db.commit()

    background_tasks.add_task(run_algorithm_task, request.parameters)
    return {"status": "running"}


# TODO (future): may return a new schedule ID rather than mutating existing
@router.post("/{schedule_id}/regenerate", status_code=202)
def regenerate_algorithm(
    schedule_id: int,
    request: RegenerateScheduleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # TODO:
    # - raise 404 if schedule not found
    # - raise 409 if schedule.status == ScheduleStatus.RUNNING
    # - raise 400 if schedule has no existing sections (nothing to regenerate around)
    # - set schedule.status = RUNNING, started_at = now(), db.commit()

    background_tasks.add_task(run_regenerate_task, schedule_id, request.parameters)
    return {"schedule_id": schedule_id, "status": "running"}


