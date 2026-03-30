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
