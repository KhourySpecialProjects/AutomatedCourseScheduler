"""Schedule repository — raw DB access."""

from sqlalchemy.orm import Session

from app.models.schedule import Schedule


def schedule_exists(db: Session, schedule_id: int) -> bool:
    return (
        db.query(Schedule.schedule_id)
        .filter(Schedule.schedule_id == schedule_id)
        .first()
        is not None
    )
