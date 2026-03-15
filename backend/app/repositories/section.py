"""Section repository — raw DB access."""

from sqlalchemy.orm import Session

from app.models.section import Section


def get_all(db: Session) -> list[Section]:
    return db.query(Section).all()
