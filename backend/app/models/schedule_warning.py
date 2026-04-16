from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class ScheduleWarning(Base):
    """Persisted warning from an algorithm run."""

    __tablename__ = "schedule_warning"

    warning_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schedule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schedule.schedule_id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(String(500))
    faculty_nuid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    course_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_block_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
