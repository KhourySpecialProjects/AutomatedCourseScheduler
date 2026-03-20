"""Algorithm router."""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/schedules", tags=["schedules"])


def _run_algorithm_task(schedule_id: int):
    # TODO: load data from DB, build AlgorithmInput
    # TODO: call generate_schedule(input)
    # TODO: write results back to DB
    pass


@router.post("/generate", status_code=202)
def run_algorithm(
    schedule_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # TODO: check if algorithm is already running, raise 409 if so
    # TODO: update status in db
    background_tasks.add_task(_run_algorithm_task, schedule_id)
    # Return confirmation
    return {"schedule_id": schedule_id, "status": "running"}
