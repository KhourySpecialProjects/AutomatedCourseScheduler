from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.semester import Semester
from app.core.enums import ScheduleStatus

if TYPE_CHECKING:
    from app.models.schedule_log import ScheduleLog
    from app.models.section import Section


class Schedule(Base):
    """Represents a course schedule for a given semester and year.
    Can exist as a draft or be finalized as a completed schedule
    that was actually used."""

    __tablename__ = "schedule"

    schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    semester_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(Semester.semester_id), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default=ScheduleStatus.IDLE)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    draft: Mapped[bool] = mapped_column(Boolean, default=True)
    campus: Mapped[int] = mapped_column(ForeignKey("campus.campus_id"), nullable=False)

    # Relationships
    sections: Mapped[list["Section"]] = relationship("Section", back_populates="schedule")
    schedule_log: Mapped["ScheduleLog"] = relationship("ScheduleLog", back_populates="schedule")
    semester: Mapped["Semester"] = relationship("Semester", back_populates="schedules")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Deletion
    active: Mapped[bool] = mapped_column(Boolean, default=True)
