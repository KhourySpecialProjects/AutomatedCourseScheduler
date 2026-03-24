"""Course repository — raw DB access."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.section import Section


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
