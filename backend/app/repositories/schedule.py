"""Schedule repository — raw DB access."""

from sqlalchemy.orm import Session

from app.core.enums import Semester
from app.models.schedule import Schedule


def schedule_exists(db: Session, schedule_id: int) -> bool:
    return (
        db.query(Schedule.schedule_id)
        .filter(Schedule.schedule_id == schedule_id)
        .first()
        is not None
    )


def get_all(
    db: Session,
    campus_id: int | None = None,
    semester: str | None = None,
    year: int | None = None,
) -> list[Schedule]:
    query = db.query(Schedule)
    if campus_id is not None:
        query = query.filter(Schedule.campus == campus_id)
    if semester:
        query = query.filter(Schedule.semester == Semester(semester))
    if year:
        query = query.filter(Schedule.year == year)
    return query.all()


def get_by_id(db: Session, schedule_id: int) -> Schedule | None:
    return db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()


def create(db: Session, data: dict) -> Schedule:
    schedule = Schedule(**data)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def update(db: Session, schedule_id: int, data: dict) -> Schedule | None:
    rows_updated = (
        db.query(Schedule).filter(Schedule.schedule_id == schedule_id).update(data)
    )
    db.commit()
    if rows_updated == 0:
        return None
    return get_by_id(db, schedule_id)


def delete(db: Session, schedule_id: int) -> bool:
    """Delete a schedule by ID. Returns True if deleted, False if not found."""
    schedule = get_by_id(db, schedule_id)
    if schedule is None:
        return False
    db.delete(schedule)
    db.commit()
    return True
