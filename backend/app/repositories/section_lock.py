"""Section lock repository — raw DB access."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.section import Section
from app.models.section_lock import SectionLock


def get_by_section_id(db: Session, section_id: int) -> SectionLock | None:
    """
    Return the lock for a section if one exists.

    Args:
        db: Database session.
        section_id: ID of the section to query.

    Returns:
        SectionLock if one exists, None otherwise.
    """
    return db.query(SectionLock).filter(SectionLock.section_id == section_id).first()


def get_by_user_id(db: Session, user_id: int) -> SectionLock | None:
    """
    Return the lock held by a user if one exists.

    Args:
        db: Database session.
        user_id: ID of the user to query.

    Returns:
        SectionLock if one exists, None otherwise.
    """
    return db.query(SectionLock).filter(SectionLock.locked_by == user_id).first()


def create(db: Session, section_lock: SectionLock) -> SectionLock:
    """
    Insert a new section lock.

    Args:
        db: Database session.
        section_lock: SectionLock object to insert.

    Returns:
        The created SectionLock.
    """
    db.add(section_lock)
    db.commit()
    db.refresh(section_lock)
    return section_lock


def save(db: Session, section_lock: SectionLock) -> SectionLock:
    """
    Update an existing section lock.

    Args:
        db: Database session.
        section_lock: SectionLock object to update.

    Returns:
        The updated SectionLock.
    """
    db.add(section_lock)
    db.commit()
    db.refresh(section_lock)
    return section_lock


def delete(db: Session, section_lock: SectionLock) -> None:
    """
    Delete a section lock.

    Args:
        db: Database session.
        section_lock: SectionLock object to delete.
    """
    db.delete(section_lock)
    db.commit()


def get_active_by_schedule(db: Session, schedule_id: int) -> list[SectionLock]:
    """
    Return all active locks for sections belonging to a schedule.

    Args:
        db: Database session.
        schedule_id: ID of the schedule to query locks for.

    Returns:
        List of active SectionLock objects.
    """
    now = datetime.now(UTC).replace(tzinfo=None)
    return (
        db.query(SectionLock)
        .join(Section, SectionLock.section_id == Section.section_id)
        .filter(Section.schedule_id == schedule_id)
        .filter(SectionLock.expires_at > now)
        .all()
    )
