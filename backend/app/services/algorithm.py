"""Mock algorithm service for generating draft schedules."""

import random
import time
from datetime import datetime

from app.core.enums import Severity, WarningType
from app.schemas.algorithm_input import AlgorithmInput
from app.schemas.algorithm_output import DraftScheduleResult, RunMetadata, Warning


def generate_schedule(algorithm_input: AlgorithmInput) -> DraftScheduleResult:
    start = datetime.now()
    time.sleep(15)  # Simulate algorithm processing time

    # Mock: assign a fake section ID per required section
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
