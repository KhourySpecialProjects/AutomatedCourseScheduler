"""Campus service — business logic."""

from sqlalchemy.orm import Session

from app.repositories import campus as campus_repo


def get_all(
    db: Session,
    campus_id: int | None = None,
    campus_name: str | None = None,
) -> list:
    return campus_repo.get_all(db, campus_id=campus_id, campus_name=campus_name)
