from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.enums import PreferenceLevel

if TYPE_CHECKING:
    from app.models.faculty import Faculty


class MeetingPreference(Base):
    """Represents a faculty member's interest in teaching
    at a specific meeting time. Used by the scheduling algorithm
    to assign time blocks to faculty."""

    __tablename__ = "meeting_preference"

    preference_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    preference: Mapped[PreferenceLevel] = mapped_column(Enum(PreferenceLevel))

    # Foreign Keys
    faculty_nuid: Mapped[int] = mapped_column(Integer, ForeignKey("faculty.nuid"))
    meeting_time: Mapped[int] = mapped_column(
        Integer, ForeignKey("time_block.time_block_id")
    )

    # Relationships
    faculty: Mapped["Faculty"] = relationship(
        "Faculty", back_populates="meeting_preferences"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
