"""Schedule service — business logic."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.schedule import Schedule
from app.repositories import schedule as schedule_repo
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


def get_all(
    db: Session,
    campus_id: int | None = None,
    semester: str | None = None,
    year: int | None = None,
):
    return schedule_repo.get_all(db, campus_id=campus_id, semester=semester, year=year)


def get_by_id(db: Session, schedule_id: int):
    schedule = schedule_repo.get_by_id(db, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


def create(db: Session, data: ScheduleCreate) -> Schedule:
    return schedule_repo.create(db, data.model_dump())


def update(db: Session, schedule_id: int, data: ScheduleUpdate):
    updated = schedule_repo.update(db, schedule_id, data.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return updated


def delete(db: Session, schedule_id: int) -> None:
    success = schedule_repo.delete(db, schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
