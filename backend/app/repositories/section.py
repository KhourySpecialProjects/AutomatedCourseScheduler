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


def replace_faculty_assignments(
    db: Session, section_id: int, faculty_nuids: list[int]
) -> None:
    db.query(FacultyAssignment).filter(
        FacultyAssignment.section_id == section_id
    ).delete()
    for nuid in faculty_nuids:
        db.add(FacultyAssignment(faculty_nuid=nuid, section_id=section_id))
