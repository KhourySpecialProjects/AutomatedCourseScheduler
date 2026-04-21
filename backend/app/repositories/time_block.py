"""Time block repository — raw DB access."""

from sqlalchemy.orm import Session

from app.models.section import Section
from app.models.time_block import TimeBlock


def time_block_exists(db: Session, time_block_id: int) -> bool:
    """Return True if a time block with the given ID exists."""
    return db.query(TimeBlock.time_block_id).filter(TimeBlock.time_block_id == time_block_id).first() is not None


def get_by_id(db: Session, time_block_id: int) -> TimeBlock | None:
    """Return the time block with the given ID, or None if not found."""
    return db.query(TimeBlock).filter(TimeBlock.time_block_id == time_block_id).first()


def get_all(db: Session) -> list[TimeBlock]:
    """Return all time blocks across all campuses."""
    return db.query(TimeBlock).all()


def get_by_campus(db: Session, campus_id: int) -> list[TimeBlock]:
    """Return all time blocks belonging to the given campus."""
    return db.query(TimeBlock).filter(TimeBlock.campus == campus_id).all()


def has_sections(db: Session, time_block_id: int) -> bool:
    """Return True if any section is currently assigned to this time block.

    Used as a guard before deletion — a time block that has sections
    referencing it cannot be safely removed.
    """
    return db.query(Section.section_id).filter(Section.time_block_id == time_block_id).first() is not None


def create(db: Session, time_block: TimeBlock) -> TimeBlock:
    """Persist a new time block and return it with its generated ID."""
    db.add(time_block)
    db.commit()
    db.refresh(time_block)
    return time_block


def save(db: Session, time_block: TimeBlock) -> TimeBlock:
    """Persist changes to an existing time block and return the updated record."""
    db.add(time_block)
    db.commit()
    db.refresh(time_block)
    return time_block


def delete(db: Session, time_block: TimeBlock) -> None:
    """Delete a time block from the database.

    Callers should first check `has_sections()` to ensure no sections
    reference this block before calling delete.
    """
    db.delete(time_block)
    db.commit()
