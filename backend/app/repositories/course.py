import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.section import Section

_COURSE_NAME_RE = re.compile(r"^[A-Z]{2,4}\s+\d{4}$")


def _validate_course_name(name: str) -> None:
    """Enforce course name format: '{SUBJECT} {course_number}' (e.g. 'CS 2500')."""
    normalized = " ".join(name.strip().split()).upper()
    if not _COURSE_NAME_RE.fullmatch(normalized):
        raise ValueError("Course name must be in format '{SUBJECT} {COURSE_NUMBER}'")


def get_all(db: Session) -> list[Course]:
    return db.query(Course).all()


def get_by_schedule(db: Session, schedule_id: int) -> list[Course]:
    course_ids = (
        select(Section.course_id).where(Section.schedule_id == schedule_id).distinct()
    )
    return db.query(Course).filter(Course.course_id.in_(course_ids)).all()


def get_by_id(db: Session, course_id: int) -> Course | None:
    return db.query(Course).filter(Course.course_id == course_id).first()


def get_section_count(
    db: Session, course_id: int, schedule_id: int | None = None
) -> int:
    query = db.query(func.count(Section.section_id)).filter(
        Section.course_id == course_id
    )
    if schedule_id is not None:
        query = query.filter(Section.schedule_id == schedule_id)
    return query.scalar() or 0


def course_exists(db: Session, course_id: int) -> bool:
    return (
        db.query(Course.course_id).filter(Course.course_id == course_id).first()
        is not None
    )


def get_by_name(db: Session, course_name: str) -> int:
    return db.query(Course).filter(Course.name == course_name).first()


def get_by_ids(db: Session, course_ids: list[int]) -> list[Course]:
    return db.query(Course).filter(Course.course_id.in_(course_ids)).all()
def create(db: Session, course: Course) -> Course:
    _validate_course_name(course.name)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def save(db: Session, course: Course) -> Course:
    _validate_course_name(course.name)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def delete(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()
