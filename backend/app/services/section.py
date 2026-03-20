"""Section service — business logic."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.section import Section
from app.repositories import section as section_repo
from app.schemas.section import (
    CourseInfo,
    CoursePreferenceInfo,
    InstructorInfo,
    MeetingPreferenceInfo,
    SectionRichResponse,
    TimeBlockInfo,
)


def get_all_sections(db: Session, schedule_id: int) -> list[Section]:
    """Get all sections, optionally filtered by schedule ID."""
    if schedule_id:
        return section_repo.get_by_schedule(db, schedule_id)
    return section_repo.get_all(db)


def _derive_days(start_time: datetime) -> str:
    weekday = start_time.weekday()
    if weekday == 0:
        return "MWF"
    if weekday == 1:
        return "TTh"
    return start_time.strftime("%A")


def _fmt_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


def get_rich_sections(db: Session, schedule_id: int) -> list[SectionRichResponse]:
    """Return fully-denormalized sections for the row view."""
    sections = section_repo.get_rich_by_schedule(db, schedule_id)
    result = []
    for s in sections:
        result.append(
            SectionRichResponse(
                section_id=s.section_id,
                section_number=s.section_number,
                capacity=s.capacity,
                schedule_id=s.schedule_id,
                course=CourseInfo(
                    course_id=s.course.course_id,
                    name=s.course.name,
                    description=s.course.description,
                    credits=s.course.credits,
                ),
                time_block=TimeBlockInfo(
                    time_block_id=s.time_block.time_block_id,
                    days=_derive_days(s.time_block.start_time),
                    start_time=_fmt_time(s.time_block.start_time),
                    end_time=_fmt_time(s.time_block.end_time),
                    timezone=s.time_block.timezone,
                ),
                instructors=[
                    InstructorInfo(
                        nuid=fa.faculty.nuid,
                        first_name=fa.faculty.first_name,
                        last_name=fa.faculty.last_name,
                        title=fa.faculty.title,
                        email=fa.faculty.email,
                        course_preferences=[
                            CoursePreferenceInfo(
                                course_id=cp.course_id,
                                course_name=cp.course.name,
                                preference=cp.preference.value,
                            )
                            for cp in fa.faculty.course_preferences
                        ],
                        meeting_preferences=[
                            MeetingPreferenceInfo(
                                meeting_time=mp.meeting_time,
                                preference=mp.preference.value,
                            )
                            for mp in fa.faculty.meeting_preferences
                        ],
                    )
                    for fa in s.faculty_assignments
                ],
            )
        )
    return result
