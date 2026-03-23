"""Algorithm router."""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.algorithm_input import (
    AlgorithmInput,
    AlgorithmParameters,
    Course,
    Faculty,
)
from app.services.algorithm import generate_schedule

router = APIRouter(prefix="/schedules", tags=["schedules"])


def _build_mock_input() -> AlgorithmInput:
    # TODO: replace with real DB queries
    # e.g. load Schedule -> OfferedCourses, AllFaculty, TimeBlocks, preferences
    return AlgorithmInput(
        OfferedCourses=[
            Course(CourseID=1, SectionCount=2),
            Course(CourseID=2, SectionCount=1),
        ],
        AllFaculty=[
            Faculty(NUID=1001, MaxLoad=3),
            Faculty(NUID=1002, MaxLoad=4),
        ],
        TimeBlocks=[101, 102, 103],
        CoursePreferences=[],
        TimePreferences=[],
        ConflictGroups=[],
        Parameters=AlgorithmParameters(),
    )


def _run_algorithm_task(schedule_id: int):
    algorithm_input = _build_mock_input()
    generate_schedule(algorithm_input)

    # TODO:
    # - write result.SectionAssignments back to DB
    # - set schedule.status = ScheduleStatus.COMPLETED
    # - set schedule.status = ScheduleStatus.FAILED on exception


@router.post("/{schedule_id}/generate", status_code=202)
def run_algorithm(
    schedule_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # TODO:
    # - raise 404 if schedule not found
    # - raise 409 if schedule.status == ScheduleStatus.RUNNING
    # - set schedule.status = RUNNING, started_at = now(), db.commit()

    background_tasks.add_task(_run_algorithm_task, schedule_id)
    return {"schedule_id": schedule_id, "status": "running"}
