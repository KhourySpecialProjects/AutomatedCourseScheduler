from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String
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

    preference_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    meeting_time: Mapped[str] = mapped_column(String(50))
    preference: Mapped[PreferenceLevel] = mapped_column(Enum(PreferenceLevel))

    # Foreign Keys
    faculty_nuid: Mapped[str] = mapped_column(String(50), ForeignKey("faculty.nuid"))

    # Relationships
    faculty: Mapped["Faculty"] = relationship(
        "Faculty", back_populates="meeting_preferences"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
