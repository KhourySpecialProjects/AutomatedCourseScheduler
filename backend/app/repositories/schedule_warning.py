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
    # Replace strategy with dismissed preservation:
    #   - drop any row whose type is no longer detected (condition resolved)
    #   - for types still detected: keep dismissed rows, drop non-dismissed duplicates,
    #     and add exactly one non-dismissed row per type (unless a dismissed row already exists).
    # Diff-based reconciliation can't clean up duplicates (error_check can emit the same
    # type once per faculty), so it was orphaning rows.
    existing = get_by_section(db, section_id)
    detected_values = {wt.value for wt in detected}
    dismissed_types: set[str] = set()

    for w in existing:
        if w.type not in detected_values:
            db.delete(w)
        elif w.dismissed:
            dismissed_types.add(w.type)
        else:
            db.delete(w)

    for wt in set(detected):
        if wt.value in dismissed_types:
            continue
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
