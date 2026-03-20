"""Mock algorithm service for generating draft schedules."""

import random
from datetime import datetime

from app.schemas.algorithm import (
    AlgorithmInput,
    DraftScheduleResult,
    Preference,
    RunMetadata,
    Section,
    Severity,
    Warning,
    WarningType,
)


def generate_schedule(input: AlgorithmInput) -> DraftScheduleResult:
    start = datetime.now()

    sections = []

    for course in input.OfferedCourses:
        for _i in range(course.SectionCount):
            faculty = random.choice(input.AllFaculty)
            block = random.choice(input.TimeBlocks)
            course_pref = random.choice(list(Preference))
            time_pref = random.choice(list(Preference))
            score = (4 - course_pref.value + 4 - time_pref.value) / 6.0

            sections.append(
                Section(
                    CourseID=course.CourseID,
                    FacultyID=faculty.NUID,
                    BlockID=block.BlockID,
                    CoursePreference=course_pref,
                    TimePreference=time_pref,
                    AssignmentScore=round(score, 2),
                )
            )

    warnings = [
        Warning(
            Type=WarningType.UNPREFERENCED_COURSE,
            SeverityRank=Severity.MEDIUM,
            Message="Mock warning: faculty assigned unpreferenced course",
            FacultyID=sections[0].FacultyID if sections else None,
            CourseID=sections[0].CourseID if sections else None,
        )
    ]

    end = datetime.now()

    metadata = RunMetadata(
        StartTime=start,
        EndTime=end,
        TotalRunTime=int((end - start).total_seconds() * 1000),
        Version=1,
    )

    stability = (
        sum(s.AssignmentScore for s in sections) / len(sections) if sections else 0.0
    )

    return DraftScheduleResult(
        SectionAssignments=sections,
        StabilityScore=round(stability, 2),
        Warnings=warnings,
        RunMetadata=metadata,
    )
