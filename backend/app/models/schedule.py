from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.schedule_log import ScheduleLog
    from app.models.section import Section


class Schedule(Base):
    """Represents a course schedule for a given semester and year.
    Can exist as a draft or be finalized as a completed schedule
    that was actually used."""

    __tablename__ = "schedule"

    schedule_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    semester: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(Integer)
    draft: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    sections: Mapped[list["Section"]] = relationship(
        "Section", back_populates="schedule"
    )
    schedule_log: Mapped["ScheduleLog"] = relationship(
        "ScheduleLog", back_populates="schedule"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
