"""Semester service — business logic."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.semester import Semester
from app.repositories import semester as semester_repo
from app.schemas.semester import SemesterCreate, SemesterUpdate


def get_all(
    db: Session,
    campus_id: int | None = None,
    semester: str | None = None,
    year: int | None = None,
):
    return semester_repo.get_all(db)


def get_by_id(db: Session, schedule_id: int):
    semester = semester_repo.get_by_id(db, schedule_id)
    if semester is None:
        raise HTTPException(status_code=404, detail="Semester not found")
    return semester


def create(db: Session, data: SemesterCreate) -> Semester:
    return semester_repo.create(db, data.model_dump())


def update(db: Session, schedule_id: int, data: SemesterUpdate):
    updated = semester_repo.update(
        db, schedule_id, data.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(status_code=404, detail="Semester not found")
    return updated


def delete(db: Session, schedule_id: int) -> None:
    success = semester_repo.delete(db, schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Semester not found")


def get_last_year(db: Session, semester_id: int) -> int | None:
    return semester_repo.get_last_year(db, semester_id)
