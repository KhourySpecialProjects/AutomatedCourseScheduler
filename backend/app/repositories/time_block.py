"""Time block repository — raw DB access."""

from sqlalchemy.orm import Session

from app.models.time_block import TimeBlock


def time_block_exists(db: Session, time_block_id: int) -> bool:
    return (
        db.query(TimeBlock.time_block_id).filter(TimeBlock.time_block_id == time_block_id).first()
        is not None
    )


def get_by_id(db: Session, time_block_id: int) -> TimeBlock:
    return db.query(TimeBlock).filter(TimeBlock.time_block_id == time_block_id).first()

def get_all(db: Session) -> list[TimeBlock]:
    return db.query(TimeBlock).all()