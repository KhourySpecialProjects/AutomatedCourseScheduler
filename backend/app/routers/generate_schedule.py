"""Algorithm router."""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/{schedule_id}/generate", status_code=202)
def run_algorithm(
    schedule_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # TODO: query db for schedule_id, raise 404 if not found
    # TODO: check if algorithm is already running, raise 409 if so
    # TODO: update status in db
    # TODO: background_tasks.add_task(...)
    # Return confirmation
    return {"schedule_id": schedule_id, "status": "running"}
