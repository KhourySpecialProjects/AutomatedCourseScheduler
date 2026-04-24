"""Section repository — raw DB access."""

from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models.course_preference import CoursePreference
from app.models.faculty import Faculty
from app.models.faculty_assignment import FacultyAssignment
from app.models.schedule import Schedule
from app.models.section import Section
from app.models.semester import Semester


def get_all(db: Session) -> list[Section]:
    return db.query(Section).all()


def get_by_schedule(db: Session, schedule_id: int) -> list[Section]:
    return db.query(Section).filter(Section.schedule_id == schedule_id).all()


def get_rich_by_schedule(db: Session, schedule_id: int) -> list[Section]:
    """Return sections with course,
    time_block, and instructor preferences eager-loaded."""
    return (
        db.query(Section)
        .options(
            joinedload(Section.course),
            joinedload(Section.time_block),
            joinedload(Section.faculty_assignments)
            .joinedload(FacultyAssignment.faculty)
            .joinedload(Faculty.course_preferences)
            .joinedload(CoursePreference.course),
            joinedload(Section.faculty_assignments).joinedload(FacultyAssignment.faculty).joinedload(Faculty.meeting_preferences),
        )
        .filter(Section.schedule_id == schedule_id)
        .all()
    )


def get_by_id(db: Session, section_id: int) -> Section | None:
    return db.query(Section).filter(Section.section_id == section_id).first()


def create(db: Session, section: Section) -> Section:
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


def save(db: Session, section: Section) -> Section:
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


def delete(db: Session, section: Section) -> None:
    db.delete(section)
    db.commit()


def replace_faculty_assignments(db: Session, section_id: int, faculty_nuids: list[int]) -> None:
    db.query(FacultyAssignment).filter(FacultyAssignment.section_id == section_id).delete()
    for nuid in faculty_nuids:
        db.add(FacultyAssignment(faculty_nuid=nuid, section_id=section_id))


def get_faculty_assignmnets(db: Session, section_id: int) -> list[FacultyAssignment]:
    assignments = db.query(FacultyAssignment).filter(FacultyAssignment.section_id == section_id).all()
    instructors = []
    for assignment in assignments:
        instructors.append(assignment.faculty_nuid)
    return instructors


def get_by_instructor(db: Session, instructor_id: int) -> list[FacultyAssignment]:
    current_year = datetime.now().year
    assignments = (
        db.query(FacultyAssignment)
        .join(Section)
        .join(Schedule)
        .join(Semester)
        .filter(
            FacultyAssignment.faculty_nuid == instructor_id,
            Schedule.semester_id == Semester.semester_id,
            Semester.year >= current_year - 3,
        )
        .all()
    )

    return assignments


def double_booked(db: Session, assignments: list[FacultyAssignment], meeting_time: int) -> bool:
    for assignment in assignments:
        section = get_by_id(db, assignment.section_id)
        if section.time_block_id == meeting_time:
            return True
    return False


def crosslist_group_section_ids(db: Session, section_id: int) -> set[int]:
    ids: set[int] = {section_id}
    section = get_by_id(db, section_id)
    if section is None:
        return ids

    if section.crosslisted_section_id is not None:
        ids.add(section.crosslisted_section_id)

    reverse = db.query(Section).filter(Section.crosslisted_section_id == section_id).first()
    if reverse is not None:
        ids.add(reverse.section_id)

    return ids
