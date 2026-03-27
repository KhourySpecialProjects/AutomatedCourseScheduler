from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Integer, String, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.enums import Campus

if TYPE_CHECKING:
    from app.models.section import Section
    from app.models.campus import Campus


class TimeBlock(Base):
    """Represents a schedulable time block slot that can be assigned to a
    section, including the days, time, and location where the section will
    meet."""

    __tablename__ = "time_block"

    time_block_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meeting_days: Mapped[str] = mapped_column(String)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    campus: Mapped[int] = mapped_column(
        ForeignKey("campus.campus_id"), nullable=False)
    block_group: Mapped[str | None] = mapped_column(String(1))

    # Relationships
    sections: Mapped[list["Section"]] = relationship(
        "Section", back_populates="time_block"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
