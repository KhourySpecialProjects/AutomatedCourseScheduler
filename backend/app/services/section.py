"""Section service — business logic."""

from sqlalchemy.orm import Session

from app.models.section import Section
from app.repositories import section as section_repo


def get_all_sections(db: Session, schedule_id: int) -> list[Section]:
    """Get all sections, optionally filtered by schedule ID."""
    if schedule_id:
        return section_repo.get_by_schedule(db, schedule_id)
    return section_repo.get_all(db)
