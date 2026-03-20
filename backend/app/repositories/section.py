"""Section repository — raw DB access."""

from sqlalchemy.orm import Session, joinedload

from app.models.course_preference import CoursePreference
from app.models.faculty import Faculty
from app.models.faculty_assignment import FacultyAssignment
from app.models.section import Section


def get_all(db: Session) -> list[Section]:
    return db.query(Section).all()


def get_by_schedule(db: Session, schedule_id: int) -> list[Section]:
    return db.query(Section).filter(Section.schedule_id == schedule_id).all()


def get_rich_by_schedule(db: Session, schedule_id: int) -> list[Section]:
    """Return sections with course, time_block, and instructor preferences eager-loaded."""
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
