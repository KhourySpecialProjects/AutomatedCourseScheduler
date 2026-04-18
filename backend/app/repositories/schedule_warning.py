from sqlalchemy.orm import Session

from app.models.schedule_warning import ScheduleWarning


def get_by_schedule(
    db: Session,
    schedule_id: int,
    warning_type: str | None = None,
    severity: str | None = None,
    include_dismissed: bool = False,
) -> list[ScheduleWarning]:
    query = db.query(ScheduleWarning).filter(ScheduleWarning.schedule_id == schedule_id)
    if not include_dismissed:
        query = query.filter(ScheduleWarning.dismissed == False)  # noqa: E712
    if warning_type:
        query = query.filter(ScheduleWarning.type == warning_type)
    if severity:
        query = query.filter(ScheduleWarning.severity == severity)
    return query.all()


def get_by_id(db: Session, warning_id: int) -> ScheduleWarning | None:
    return db.query(ScheduleWarning).filter(ScheduleWarning.warning_id == warning_id).first()


def delete_by_schedule(db: Session, schedule_id: int) -> None:
    """Clear all warnings for a schedule (before a new algorithm run)."""
    db.query(ScheduleWarning).filter(ScheduleWarning.schedule_id == schedule_id).delete()


def create_many(db: Session, warnings: list[ScheduleWarning]) -> None:
    db.add_all(warnings)
