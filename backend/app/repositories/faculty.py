from sqlalchemy.orm import Session, joinedload

from app.models.course_preference import CoursePreference
from app.models.faculty import Faculty


def get_all(
    db: Session, campus: str | None = None, active_only: bool = False
) -> list[Faculty]:
    query = db.query(Faculty)
    if campus is not None:
        query = query.filter(Faculty.campus == campus)
    if active_only:
        query = query.filter(Faculty.active.is_(True))
    return query.order_by(Faculty.last_name, Faculty.first_name).all()


def get_by_nuid_with_preferences(db: Session, nuid: int) -> Faculty | None:
    return (
        db.query(Faculty)
        .options(
            joinedload(Faculty.course_preferences).joinedload(CoursePreference.course),
            joinedload(Faculty.meeting_preferences),
        )
        .filter(Faculty.nuid == nuid)
        .first()
    )
