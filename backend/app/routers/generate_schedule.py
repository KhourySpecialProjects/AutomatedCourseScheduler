"""Algorithm router."""

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.algorithm_input import (
    AlgorithmInput,
    AlgorithmParameters,
)
from app.schemas.course import CourseResponse as Course
from app.schemas.faculty import FacultyResponse as Faculty
from app.services.algorithm import generate_schedule

router = APIRouter(prefix="/schedules", tags=["schedules"])


class GenerateScheduleRequest(BaseModel):
    parameters: AlgorithmParameters = AlgorithmParameters()
    # TODO (future): hard/soft constraint overrides


class RegenerateScheduleRequest(BaseModel):
    parameters: AlgorithmParameters = AlgorithmParameters()
    # TODO (future): specify which sections to fill, constraint overrides


def _build_mock_input(parameters: AlgorithmParameters) -> AlgorithmInput:
    # TODO: replace with real DB queries once SSIP-40 is merged
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
        Parameters=parameters,
    )


def _build_mock_partial_input(parameters: AlgorithmParameters) -> AlgorithmInput:
    # TODO: replace with real DB queries once SSIP-40 is merged
    # Load only unassigned sections — existing assigned sections are preserved
    # e.g. query sections where faculty_id IS NULL or time_block_id IS NULL
    return AlgorithmInput(
        OfferedCourses=[
            Course(CourseID=3, SectionCount=1),
        ],
        AllFaculty=[
            Faculty(NUID=1001, MaxLoad=3),
            Faculty(NUID=1002, MaxLoad=4),
        ],
        TimeBlocks=[101, 102, 103],
        CoursePreferences=[],
        TimePreferences=[],
        ConflictGroups=[],
        Parameters=parameters,
    )


def _run_algorithm_task(schedule_id: int):
    algorithm_input = _build_mock_input()
    result = generate_schedule(algorithm_input)

    # TODO:
    # - write result.SectionAssignments back to DB
    # - set schedule.status = ScheduleStatus.COMPLETED
    # - set schedule.status = ScheduleStatus.FAILED on exception


def _run_regenerate_task(schedule_id: int, parameters: AlgorithmParameters):
    # Runs algorithm only on unassigned sections — preserves existing assignments
    _build_mock_partial_input(parameters)

    # TODO: define regenerate_schedule() once regeneration logic is scoped
    # TODO:
    # - merge result.SectionAssignments into existing schedule
    #   (do not overwrite assigned)
    # - set schedule.status = ScheduleStatus.COMPLETED
    # - set schedule.status = ScheduleStatus.FAILED on exception


# Kept schedule id here as per our discussion, may change in future
@router.post("/{schedule_id}/generate", status_code=202)
def run_algorithm(
    schedule_id: int,
    request: GenerateScheduleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # TODO:
    # - raise 404 if schedule not found
    # - raise 409 if schedule.status == ScheduleStatus.RUNNING
    # - set schedule.status = RUNNING, started_at = now(), db.commit()

    background_tasks.add_task(_run_algorithm_task, schedule_id, request.parameters)
    return {"schedule_id": schedule_id, "status": "running"}


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

    background_tasks.add_task(_run_regenerate_task, schedule_id, request.parameters)
    return {"schedule_id": schedule_id, "status": "running"}
