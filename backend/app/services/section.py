"""Section service — business logic."""

from datetime import time

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import WarningType
from app.models.faculty_assignment import FacultyAssignment
from app.models.schedule import Schedule
from app.models.section import Section
from app.repositories import comment as comment_repo
from app.repositories import course as course_repo
from app.repositories import faculty as faculty_repo
from app.repositories import schedule as schedule_repo
from app.repositories import schedule_warning as warnings_repo
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
    comment_counts = comment_repo.count_active_by_schedule(db, schedule_id)
    result = []
    for s in sections:
        result.append(
            SectionRichResponse(
                section_id=s.section_id,
                section_number=s.section_number,
                capacity=s.capacity,
                room=s.room,
                schedule_id=s.schedule_id,
                comment_count=comment_counts.get(s.section_id, 0),
                crosslisted_section_id=s.crosslisted_section_id,
                course=CourseInfo(
                    course_id=s.course.course_id,
                    subject=s.course.subject,
                    code=s.course.code,
                    name=s.course.name,
                    description=s.course.description,
                    credits=s.course.credits,
                ),
                time_block=TimeBlockInfo(
                    time_block_id=s.time_block.time_block_id,
                    days=s.time_block.meeting_days,
                    start_time=_fmt_time(s.time_block.start_time),
                    end_time=_fmt_time(s.time_block.end_time),
                )
                if s.time_block
                else None,
                instructors=[
                    InstructorInfo(
                        nuid=fa.faculty.nuid,
                        first_name=fa.faculty.first_name,
                        last_name=fa.faculty.last_name,
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
    if section.faculty_nuids:
        for nuid in section.faculty_nuids:
            if not faculty_repo.faculty_exists(db, nuid):
                raise ValueError("FacultyNUIDs is invalid")


def _validate_update_refs(db: Session, section: SectionUpdate) -> None:
    fields = section.model_fields_set
    if section.course_id is not None and not course_repo.course_exists(db, section.course_id):
        raise ValueError("CourseID is invalid")
    if section.time_block_id is not None and not time_block_repo.time_block_exists(db, section.time_block_id):
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


def _next_section_number(db: Session, schedule_id: int, course_id: int) -> int:
    max_num = db.query(func.max(Section.section_number)).filter(Section.schedule_id == schedule_id, Section.course_id == course_id).scalar()
    return (max_num or 0) + 1


def create_section(db: Session, section: SectionCreate) -> Section:
    _validate_create_refs(db, section)

    capacity = 30 if section.capacity is None else section.capacity
    if capacity < 1:
        raise ValueError("Capacity is invalid")

    section_number = _next_section_number(db, section.schedule_id, section.course_id)

    section_obj = Section(
        schedule_id=section.schedule_id,
        time_block_id=section.time_block_id,
        course_id=section.course_id,
        capacity=capacity,
        section_number=section_number,
    )

    try:
        section_made = section_repo.create(db, section_obj)
    except IntegrityError:
        db.rollback()
        raise ValueError("Could not create this section because it conflicts with an existing section. Please try again.") from None
    if section.faculty_nuids:
        section_repo.replace_faculty_assignments(db, section_made.section_id, section.faculty_nuids)
    saved = section_repo.save(db, section_made)
    detected = error_check(db, saved)
    warnings_repo.sync_section_warnings(db, saved.section_id, saved.schedule_id, detected)
    return {"created": saved, "warnings": detected}


def update_section(db: Session, section_id: int, section: SectionUpdate) -> dict | None:
    """Update a section. If it has a crosslisted partner, copy this section's time block and
    instructors onto the partner row (crosslisted offerings share meeting time and faculty).

    Returns {"updated": section, "warnings": list[WarningType], "partner_ids": list[int]}.
    """
    section_obj = section_repo.get_by_id(db, section_id)
    if section_obj is None:
        return None
    _validate_update_refs(db, section)
    existing_partner_id = section_obj.crosslisted_section_id
    partner_ids_to_broadcast: set[int] = set()
    explicit_uncrosslist = "crosslisted_section_id" in section.model_fields_set and section.crosslisted_section_id is None
    if "time_block_id" in section.model_fields_set:
        section_obj.time_block_id = section.time_block_id
    if "course_id" in section.model_fields_set:
        section_obj.course_id = section.course_id
    if "capacity" in section.model_fields_set:
        section_obj.capacity = section.capacity
    if "room" in section.model_fields_set:
        section_obj.room = section.room
    if "crosslisted_section_id" in section.model_fields_set:
        new_partner_id = section.crosslisted_section_id

        if new_partner_id is not None and new_partner_id == section_obj.section_id:
            raise ValueError("CrosslistedSectionID is invalid")

        partner: Section | None = None
        if new_partner_id is not None:
            partner = section_repo.get_by_id(db, new_partner_id)
            if partner is None or partner.schedule_id != section_obj.schedule_id:
                raise ValueError("CrosslistedSectionID is invalid")
            if partner.crosslisted_section_id not in (None, section_obj.section_id):
                raise ValueError("CrosslistedSectionID is invalid")

        # If we're changing/clearing, detach the existing partner's back-link.
        if existing_partner_id is not None and existing_partner_id != new_partner_id:
            old_partner = section_repo.get_by_id(db, existing_partner_id)
            if old_partner is not None and old_partner.crosslisted_section_id == section_obj.section_id:
                old_partner.crosslisted_section_id = None
                section_repo.save(db, old_partner)
                partner_ids_to_broadcast.add(old_partner.section_id)

        # Legacy: if only a reverse pointer exists and the client explicitly uncrosslists,
        # clear that reverse pointer too.
        if explicit_uncrosslist and existing_partner_id is None:
            reverse = db.query(Section).filter(Section.crosslisted_section_id == section_obj.section_id).first()
            if reverse is not None:
                reverse.crosslisted_section_id = None
                section_repo.save(db, reverse)
                partner_ids_to_broadcast.add(reverse.section_id)

        # Apply the new link bidirectionally.
        section_obj.crosslisted_section_id = new_partner_id
        if partner is not None:
            partner.crosslisted_section_id = section_obj.section_id
            section_repo.save(db, partner)
            partner_ids_to_broadcast.add(partner.section_id)
    if "faculty_nuids" in section.model_fields_set:
        section_repo.replace_faculty_assignments(db, section_obj.section_id, section.faculty_nuids or [])

    saved = section_repo.save(db, section_obj)

    synced_partner_id: int | None = None
    partner_id = saved.crosslisted_section_id
    if partner_id is None and not explicit_uncrosslist:
        # Backward-compat: if only the partner points at this row, still treat it as crosslisted.
        reverse = db.query(Section).filter(Section.crosslisted_section_id == saved.section_id).first()
        partner_id = reverse.section_id if reverse is not None else None

    if partner_id is not None:
        partner = section_repo.get_by_id(db, partner_id)
        if partner is None or partner.schedule_id != saved.schedule_id:
            raise ValueError("CrosslistedSectionID is invalid")
        # Ensure bidirectional pointers exist (including legacy one-way records).
        if partner.crosslisted_section_id != saved.section_id:
            partner.crosslisted_section_id = saved.section_id
            section_repo.save(db, partner)
            partner_ids_to_broadcast.add(partner.section_id)
        if saved.crosslisted_section_id != partner.section_id:
            saved.crosslisted_section_id = partner.section_id
            saved = section_repo.save(db, saved)
            partner_ids_to_broadcast.add(saved.section_id)
        partner.time_block_id = saved.time_block_id
        partner.capacity = saved.capacity
        partner.room = saved.room
        nuids = [
            fa.faculty_nuid
            for fa in db.query(FacultyAssignment)
            .filter(FacultyAssignment.section_id == saved.section_id)
            .order_by(FacultyAssignment.faculty_assignment_id)
            .all()
        ]
        section_repo.replace_faculty_assignments(db, partner.section_id, nuids)
        section_repo.save(db, partner)
        synced_partner_id = partner.section_id
        partner_ids_to_broadcast.add(partner.section_id)

    if synced_partner_id is not None:
        partner_ids_to_broadcast.add(synced_partner_id)

    detected = error_check(db, saved, section)
    warnings_repo.sync_section_warnings(db, saved.section_id, saved.schedule_id, detected)

    return {"updated": saved, "warnings": detected, "partner_ids": sorted(partner_ids_to_broadcast)}


def delete_section(db: Session, section_id: int) -> tuple[bool, list[int]]:
    section_obj = section_repo.get_by_id(db, section_id)
    if section_obj is None:
        return False, []
    partner_ids_to_broadcast: set[int] = set()
    # If this section is crosslisted, clear the partner pointer as well.
    if section_obj.crosslisted_section_id is not None:
        partner = section_repo.get_by_id(db, section_obj.crosslisted_section_id)
        if partner is not None and partner.crosslisted_section_id == section_obj.section_id:
            partner.crosslisted_section_id = None
            section_repo.save(db, partner)
            partner_ids_to_broadcast.add(partner.section_id)
    else:
        reverse = db.query(Section).filter(Section.crosslisted_section_id == section_obj.section_id).first()
        if reverse is not None:
            reverse.crosslisted_section_id = None
            section_repo.save(db, reverse)
            partner_ids_to_broadcast.add(reverse.section_id)
    section_repo.delete(db, section_obj)

    return True, sorted(partner_ids_to_broadcast)


def get_dept_time_block_counts(db: Session, schedule_id: int) -> dict:
    return section_repo.get_dept_time_blocks_counts(db, schedule_id)


def error_check(db: Session, section: Section, updates: SectionUpdate | None = None) -> list[WarningType]:
    if updates is not None and not updates.model_fields_set:
        return []
    warnings = []
    faculty_nuids = section_repo.get_faculty_assignmnets(db, section.section_id)
    crosslist_ids = section_repo.crosslist_group_section_ids(db, section.section_id)

    if section.time_block_id is not None:
        schedule = schedule_repo.get_by_id(db, section.schedule_id)
        course = course_repo.get_by_id(db, section.course_id)
        course_subject = course.name.split(" ", 1)[0]
        if exceeds_meeting_time_capcacity(db, schedule, section.time_block_id, course_subject):
            warnings.append(WarningType.TIME_BLOCK_OVERLOAD)

    for nuid in faculty_nuids:
        other_assignments = [
            a
            for a in faculty_repo.get_assignments(db, nuid, section.schedule_id)
            if a.section_id not in crosslist_ids
        ]
        if section.time_block_id is not None:
            if not faculty_repo.find_meeting_time_preference(db, nuid, section.time_block_id):
                warnings.append(WarningType.UNPREFERENCED_TIME)
            if section_repo.double_booked(db, other_assignments, section.time_block_id):
                warnings.append(WarningType.FACULTY_DOUBLE_BOOKED)
        if not faculty_repo.find_course_preference(db, nuid, section.course_id):
            warnings.append(WarningType.UNPREFERENCED_COURSE)
        f = faculty_repo.get_by_nuid(db, nuid)
        if len(other_assignments) + 1 > f.max_load:
            warnings.append(WarningType.FACULTY_OVERLOAD)

    return warnings


def exceeds_meeting_time_capcacity(db: Session, schedule: Schedule, time_block: int, dept: str) -> bool:
    sections = schedule.sections
    dept_count_total = 0
    dept_time_block_count = 0
    for section in sections:
        course = course_repo.get_by_id(db, section.course_id)
        split_name = course.name.split(" ", 1)
        course_subject = split_name[0]
        if course_subject == dept:
            dept_count_total += 1
            if section.time_block_id == time_block:
                dept_time_block_count += 1

    if dept_count_total == 0 or dept_time_block_count <= 1:
        return False
    time_block_capacity = dept_time_block_count / dept_count_total
    return time_block_capacity >= 0.15
