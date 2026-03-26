"""Campus repository — raw DB access."""

from sqlalchemy.orm import Session

# from app.models.campus import Campus


def get_all(
    db: Session,
    campus_id: int | None = None,
    campus_name: str | None = None,
) -> list:
    # TODO: replace with real query once Campus model exists
    # query = db.query(Campus)
    # if campus_id is not None:
    #     query = query.filter(Campus.CampusID == campus_id)
    # if campus_name is not None:
    #     query = query.filter(Campus.CampusName == campus_name)
    # return query.all()
    return []
