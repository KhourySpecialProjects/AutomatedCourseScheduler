"""Faculty repository — raw DB access."""

from sqlalchemy.orm import Session

from app.models.faculty import Faculty


def faculty_exists(db: Session, faculty_nuid: int) -> bool:
    return (
        db.query(Faculty.nuid).filter(Faculty.nuid == faculty_nuid).first() is not None
    )
