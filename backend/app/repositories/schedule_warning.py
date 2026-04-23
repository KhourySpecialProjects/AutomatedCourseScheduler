from sqlalchemy.orm import Session

from app.core.enums import WarningType
from app.models.schedule_warning import ScheduleWarning


def get_by_schedule(
    db: Session,
    schedule_id: int,
    warning_type: str | None = None,
    severity: str | None = None,
    include_dismissed: bool = False,
) -> list[ScheduleWarning]:
    query = db.query(ScheduleWarning).filter(
        ScheduleWarning.schedule_id == schedule_id)
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
    db.query(ScheduleWarning).filter(
        ScheduleWarning.schedule_id == schedule_id).delete()


def get_by_section(db: Session, section_id: int) -> list[ScheduleWarning]:
    return db.query(ScheduleWarning).filter(ScheduleWarning.section_id == section_id).all()


def create_many(db: Session, warnings: list[ScheduleWarning]) -> None:
    db.add_all(warnings)


def sync_section_warnings(
    db: Session,
    section_id: int,
    schedule_id: int,
    detected: list[WarningType],
) -> None:

    existing = get_by_section(db, section_id)
    existing_by_type = {w.type: w for w in existing}
    detected_values = {wt.value for wt in detected}

    for type_str, warning in existing_by_type.items():
        if type_str not in detected_values:
            db.delete(warning)

    for wt in detected:
        if wt.value not in existing_by_type:
            db.add(
                ScheduleWarning(
                    schedule_id=schedule_id,
                    section_id=section_id,
                    type=wt.value,
                    severity=str(wt.severity.value),
                    message=wt.value,
                    dismissed=False,
                )
            )
    db.commit()
