from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.course_preference import CoursePreference
    from app.models.faculty_assignment import FacultyAssignment
    from app.models.meeting_preference import MeetingPreference


class Faculty(Base):
    """Represents a faculty member whose courses and preferences
    are used to generate the course schedule."""

    __tablename__ = "faculty"

    nuid: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    campus: Mapped[int] = mapped_column(ForeignKey("campus.campus_id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_load: Mapped[int] = mapped_column(Integer, default=3)

    # Relationships
    course_preferences: Mapped[list["CoursePreference"]] = relationship(
        "CoursePreference",
        back_populates="faculty",
        cascade="all, delete-orphan",
    )
    meeting_preferences: Mapped[list["MeetingPreference"]] = relationship(
        "MeetingPreference",
        back_populates="faculty",
        cascade="all, delete-orphan",
    )
    faculty_assignments: Mapped[list["FacultyAssignment"]] = relationship(
        "FacultyAssignment",
        back_populates="faculty",
        cascade="all, delete-orphan",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
