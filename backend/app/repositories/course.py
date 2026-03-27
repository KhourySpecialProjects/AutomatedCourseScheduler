"""Course repository — raw DB access."""

from sqlalchemy.orm import Session

from app.models.course import Course


def course_exists(db: Session, course_id: int) -> bool:
    return (
        db.query(Course.course_id).filter(Course.course_id == course_id).first()
        is not None
    )
