"""Campus repository — raw DB access."""

from sqlalchemy.orm import Session

from app.models.campus import Campus


def get_all(db: Session, name: str | None = None) -> list[Campus]:
    query = db.query(Campus)
    if name is not None:
        query = query.filter(Campus.name == name)
    return query.all()


def get_by_id(db: Session, campus_id: int) -> Campus | None:
    return db.query(Campus).filter(Campus.campus_id == campus_id).first()


def create(db: Session, data: dict) -> Campus:
    campus = Campus(**data)
    db.add(campus)
    db.commit()
    db.refresh(campus)
    return campus


def update(db: Session, campus_id: int, data: dict) -> Campus | None:
    rows_updated = db.query(Campus).filter(Campus.campus_id == campus_id).update(data)
    db.commit()
    if rows_updated == 0:
        return None
    return get_by_id(db, campus_id)


def delete(db: Session, campus_id: int) -> bool:
    campus = get_by_id(db, campus_id)
    if campus is None:
        return False
    campus.active = False
    db.commit()
    return True
