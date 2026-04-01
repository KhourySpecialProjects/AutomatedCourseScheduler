"""Semester repository — raw DB access."""

from sqlalchemy.orm import Session

from app.models.schedule import Schedule
from app.models.semester import Semester


def semester_exists(db: Session, semester_id: int) -> bool:
    return (
        db.query(Semester).filter(Semester.semester_id == semester_id).first()
        is not None
    )


def get_all(db: Session) -> list[Semester]:
    return db.query(Semester).all()


def get_by_id(db: Session, semester_id: int) -> Semester | None:
    return db.query(Semester).filter(Semester.semester_id == semester_id).first()


def create(db: Session, data: dict) -> Semester:
    semester = Semester(**data)
    db.add(semester)
    db.commit()
    db.refresh(semester)
    return semester


def update(db: Session, semester_id: int, data: dict) -> Semester | None:
    rows_updated = (
        db.query(Semester).filter(
            Semester.semester_id == semester_id).update(data)
    )
    db.commit()
    if rows_updated == 0:
        return None
    return get_by_id(db, semester_id)


def delete(db: Session, semester_id: int) -> bool:
    semester = get_by_id(db, semester_id)
    if semester is None:
        return False
    semester.active = False
    db.commit()
    return True


def get_schedules(db: Session, semester: Semester, campus_id: int) -> list[Schedule]:
    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.semester_id == semester.semester_id,
            Schedule.campus == campus_id,
            Schedule.active,
        )
        .all()
    )
    if not schedules:
        raise ValueError(
            f"No schedules found for semester {semester.semester_id} "
            f"and campus {campus_id}"
        )

    return schedules


def get_last_year(db: Session, semester_id: int) -> int | None:
    semester = get_by_id(db, semester_id)
    last_year = (
        db.query(Semester)
        .filter(Semester.season == semester.season, Semester.year == semester.year - 1)
        .first()
    )

    return last_year.semester_id if last_year is not None else None
