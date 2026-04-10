"""Section service — business logic."""

from datetime import time

from sqlalchemy.orm import Session

from app.models.section import Section
from app.repositories import course as course_repo
from app.repositories import faculty as faculty_repo
from app.repositories import schedule as schedule_repo
from app.repositories import section as section_repo
from app.repositories import time_block as time_block_repo
from app.schemas.section import (
    CourseInfo,
    CoursePreferenceInfo,
    InstructorInfo,
    MeetingPreferenceInfo,
    SectionCreate,
    SectionRichResponse,
    SectionUpdate,
    TimeBlockInfo,
)


class ScheduleNotFoundError(Exception):
    """Raised when a schedule_id does not exist."""


def require_schedule(db: Session, schedule_id: int) -> None:
    """Ensure the schedule exists (for section API routes only)."""
    if not schedule_repo.schedule_exists(db, schedule_id):
        raise ScheduleNotFoundError


def get_by_id(db: Session, section_id: int) -> Section | None:
    """Return a single section by ID, or None if not found."""
    return section_repo.get_by_id(db, section_id)


def get_all_sections(db: Session, schedule_id: int) -> list[Section]:
    """Return all sections for a schedule (no schedule-existence check)."""
    return section_repo.get_by_schedule(db, schedule_id)


def _fmt_time(t: time) -> str:
    return t.strftime("%I:%M %p").lstrip("0")


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
                room=s.room,
                schedule_id=s.schedule_id,
                course=CourseInfo(
                    course_id=s.course.course_id,
                    name=s.course.name,
                    description=s.course.description,
                    credits=s.course.credits,
                ),
                time_block=TimeBlockInfo(
                    time_block_id=s.time_block.time_block_id,
                    days=s.time_block.meeting_days,
                    start_time=_fmt_time(s.time_block.start_time),
                    end_time=_fmt_time(s.time_block.end_time),
                ),
                instructors=[
                    InstructorInfo(
                        nuid=fa.faculty.nuid,
                        first_name=fa.faculty.first_name,
                        last_name=fa.faculty.last_name,
                        title=fa.faculty.title or "",
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
                                time_block_id=mp.meeting_time,
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


def _validate_create_refs(db: Session, section: SectionCreate) -> None:
    if not schedule_repo.schedule_exists(db, section.schedule_id):
        raise ValueError("ScheduleID is invalid")
    if not course_repo.course_exists(db, section.course_id):
        raise ValueError("CourseID is invalid")
    if not time_block_repo.time_block_exists(db, section.time_block_id):
        raise ValueError("TimeBlockID is invalid")


def _validate_update_refs(db: Session, section: SectionUpdate) -> None:
    fields = section.model_fields_set
    if section.course_id is not None and not course_repo.course_exists(db, section.course_id):
        raise ValueError("CourseID is invalid")
    if section.time_block_id is not None and not time_block_repo.time_block_exists(
        db, section.time_block_id
    ):
        raise ValueError("TimeBlockID is invalid")
    if "course_id" in fields and section.course_id is None:
        raise ValueError("CourseID is invalid")
    if "time_block_id" in fields and section.time_block_id is None:
        raise ValueError("TimeBlockID is invalid")
    if "capacity" in fields and section.capacity is None:
        raise ValueError("Capacity is invalid")
    if "faculty_nuids" in fields:
        for nuid in section.faculty_nuids or []:
            if not faculty_repo.faculty_exists(db, nuid):
                raise ValueError("FacultyNUIDs is invalid")


def create_section(db: Session, section: SectionCreate) -> Section:
    _validate_create_refs(db, section)
    section_obj = Section(
        schedule_id=section.schedule_id,
        time_block_id=section.time_block_id,
        course_id=section.course_id,
        capacity=section.capacity,
        section_number=section.section_number,
    )
    return section_repo.create(db, section_obj)


def update_section(db: Session, section_id: int, section: SectionUpdate) -> Section | None:
    section_obj = section_repo.get_by_id(db, section_id)
    if section_obj is None:
        return None
    _validate_update_refs(db, section)
    if "time_block_id" in section.model_fields_set:
        section_obj.time_block_id = section.time_block_id
    if "course_id" in section.model_fields_set:
        section_obj.course_id = section.course_id
    if "capacity" in section.model_fields_set:
        section_obj.capacity = section.capacity
    if "room" in section.model_fields_set:
        section_obj.room = section.room
    if "crosslisted_section_id" in section.model_fields_set:
        if (
            section.crosslisted_section_id is not None
            and section.crosslisted_section_id == section_obj.section_id
        ):
            raise ValueError("CrosslistedSectionID is invalid")
        if (
            section.crosslisted_section_id is not None
            and section_repo.get_by_id(db, section.crosslisted_section_id) is None
        ):
            raise ValueError("CrosslistedSectionID is invalid")
        section_obj.crosslisted_section_id = section.crosslisted_section_id
    if "faculty_nuids" in section.model_fields_set:
        section_repo.replace_faculty_assignments(
            db, section_obj.section_id, section.faculty_nuids or []
        )
    return section_repo.save(db, section_obj)


def delete_section(db: Session, section_id: int) -> bool:
    section_obj = section_repo.get_by_id(db, section_id)
    if section_obj is None:
        return False
    section_repo.delete(db, section_obj)
    return True
