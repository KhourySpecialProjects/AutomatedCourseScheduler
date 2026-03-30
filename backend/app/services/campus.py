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
