"""Section lock repository — raw DB access."""

from sqlalchemy.orm import Session

from app.models.section_lock import SectionLock


def get_by_section_id(db: Session, section_id: int) -> SectionLock | None:
    """Return the lock for a section if one exists."""
    return db.query(SectionLock).filter(SectionLock.section_id == section_id).first()


def get_by_user_id(db: Session, user_id: int) -> SectionLock | None:
    """Return the lock held by a user if one exists."""
    return db.query(SectionLock).filter(SectionLock.locked_by == user_id).first()


def create(db: Session, section_lock: SectionLock) -> SectionLock:
    """Insert a new section lock."""
    db.add(section_lock)
    db.commit()
    db.refresh(section_lock)
    return section_lock


def save(db: Session, section_lock: SectionLock) -> SectionLock:
    """Update an existing section lock."""
    db.add(section_lock)
    db.commit()
    db.refresh(section_lock)
    return section_lock


def delete(db: Session, section_lock: SectionLock) -> None:
    """Delete a section lock."""
    db.delete(section_lock)
    db.commit()
