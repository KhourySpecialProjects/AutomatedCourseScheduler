"""Algorithm service — mock implementation and background tasks."""

import random
import time
from datetime import datetime

from app.core.enums import Severity, WarningType
from app.schemas.algorithm_input import (
    AlgorithmInput,
    AlgorithmParameters,
)
from app.schemas.algorithm_output import DraftScheduleResult, RunMetadata, Warning
from app.schemas.course import CourseResponse as Course
from app.schemas.faculty import FacultyResponse as Faculty


def generate_schedule(algorithm_input: AlgorithmInput) -> DraftScheduleResult:
    start = datetime.now()
    time.sleep(15)  # Simulate algorithm processing time

    section_ids = []
    mock_section_id = 1
    faculty_ids = [f.NUID for f in algorithm_input.AllFaculty]

    for course in algorithm_input.OfferedCourses:
        for _ in range(course.SectionCount):
            section_ids.append(mock_section_id)
            mock_section_id += 1

    stability = round(random.uniform(0.65, 0.95), 2)

    warnings = [
        Warning(
            Type=WarningType.UNPREFERENCED_COURSE,
            SeverityRank=Severity.MEDIUM,
            Message="Mock warning: faculty assigned unpreferenced course",
            FacultyID=faculty_ids[0] if faculty_ids else None,
            CourseID=algorithm_input.OfferedCourses[0].CourseID
            if algorithm_input.OfferedCourses
            else None,
        )
    ]

    end = datetime.now()

    metadata = RunMetadata(
        StartTime=start,
        EndTime=end,
        TotalRunTime=int((end - start).total_seconds() * 1000),
        Version=1,
    )

    return DraftScheduleResult(
        SectionAssignments=section_ids,
        StabilityScore=stability,
        Warnings=warnings,
        Metadata=metadata,
    )


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
    # TODO: replace with real DB queries
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


def run_algorithm_task(schedule_id: int, parameters: AlgorithmParameters):
    algorithm_input = _build_mock_input(parameters)
    result = generate_schedule(algorithm_input)

    # TODO:
    # - write result.SectionAssignments back to DB
    # - set schedule.status = ScheduleStatus.COMPLETED
    # - set schedule.status = ScheduleStatus.FAILED on exception


def run_regenerate_task(schedule_id: int, parameters: AlgorithmParameters):
    # Runs algorithm only on unassigned sections — preserves existing assignments
    result = generate_schedule(_build_mock_partial_input(parameters))

    # TODO: define regenerate_schedule() once regeneration logic is scoped
    # TODO:
    # - merge result.SectionAssignments into existing schedule
    #   (do not overwrite assigned)
    # - set schedule.status = ScheduleStatus.COMPLETED
    # - set schedule.status = ScheduleStatus.FAILED on exception
    pass
