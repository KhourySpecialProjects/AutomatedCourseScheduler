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
            joinedload(Section.faculty_assignments)
            .joinedload(FacultyAssignment.faculty)
            .joinedload(Faculty.meeting_preferences),
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


def get_dept_time_blocks_counts(db: Session, schedule_id: int) -> dict[str, int]:
    """Dept code -> {time_block_id → section count} for this schedule."""
    sections = get_by_schedule(db, schedule_id)
    department_time_block_counts = {}
    for section in sections:
        dept_code = section.course.name.split(" ", 1)[
            0
        ]  # e.g. "CS" or "HINF" from "CS 1010" or "HINF 5000"
        time_block_id = section.time_block_id
        if time_block_id is not None:
            if dept_code not in department_time_block_counts:
                department_time_block_counts[dept_code] = {}
            department_time_block_counts[dept_code][time_block_id] = (
                department_time_block_counts[dept_code].get(time_block_id, 0) + 1
            )
    return department_time_block_counts
