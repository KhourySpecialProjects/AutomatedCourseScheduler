"""Campus service — business logic."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import campus as campus_repo


def get_all(db: Session, name: str | None = None) -> list:
    return campus_repo.get_all(db, name=name)


def get_by_id(db: Session, campus_id: int):
    campus = campus_repo.get_by_id(db, campus_id)
    if campus is None:
        raise HTTPException(status_code=404, detail="Campus not found")
    return campus


def create(db: Session, campus_data) -> dict:
    return campus_repo.create(db, campus_data.model_dump())


def update(db: Session, campus_id: int, campus_data) -> dict:
    campus = campus_repo.update(
        db, campus_id, campus_data.model_dump(exclude_unset=True)
    )
    if campus is None:
        raise HTTPException(status_code=404, detail="Campus not found")
    return campus


def delete(db: Session, campus_id: int):
    success = campus_repo.delete(db, campus_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campus not found")
