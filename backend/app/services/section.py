"""Section service — business logic."""

from sqlalchemy.orm import Session

from app.models.section import Section
from app.repositories import section as section_repo


def get_all_sections(db: Session) -> list[Section]:
    """Get all sections."""
    return section_repo.get_all(db)
