from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.schedule import Schedule


class ScheduleLog(Base):
    """Represents a log entry for a schedule, tracking changes
    and modifications made during the scheduling process."""

    __tablename__ = "schedule_log"

    schedule_log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String(500))

    # Foreign Keys
    schedule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schedule.schedule_id")
    )

    # Relationships
    schedule: Mapped["Schedule"] = relationship(
        "Schedule", back_populates="schedule_log"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
