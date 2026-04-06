from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.schedule import Schedule


class Semester(Base):
    """Represents an academic semester e.g. Fall 2026.
    season is a free string (e.g. 'Fall', 'Spring', 'Summer').
    The combination of season + year must be unique.
    """

    __tablename__ = "semester"
    __table_args__ = (UniqueConstraint("season", "year", name="uq_semester_season_year"),)

    semester_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    season: Mapped[str] = mapped_column(String(20), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="semester")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
