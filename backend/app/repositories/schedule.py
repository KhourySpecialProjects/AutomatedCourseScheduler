"""Schedule repository — raw DB access."""

from sqlalchemy.orm import Session

from app.models.schedule import Schedule


def get_all(db: Session) -> list[Schedule]:
    return db.query(Schedule).all()


def get_by_id(db: Session, schedule_id: int) -> Schedule | None:
    return db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()

def update(db: Session, schedule_id: int, data: dict) -> Schedule | None:
    '''Update a schedule's metadata (name, complete status, etc.).'''
    schedule = get_by_id(db, schedule_id)
    if schedule is None:
        return None
    for key, value in data.items():
        setattr(schedule, key, value)
    db.commit()
    db.refresh(schedule)
    return schedule

def delete(db: Session, schedule_id: int) -> bool:
    '''Delete a schedule by ID. Returns True if deleted, False if not found.'''
    schedule = get_by_id(db, schedule_id)
    if schedule is None:
        return False
    db.delete(schedule)
    db.commit()
    return True