from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
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

    nuid: Mapped[str] = mapped_column(String(9), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    phone_number: Mapped[str] = mapped_column(String(15))
    title: Mapped[str] = mapped_column(String(100))
    campus: Mapped[str] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    course_preferences: Mapped[list["CoursePreference"]] = relationship(
        "CoursePreference", back_populates="faculty"
    )
    meeting_preferences: Mapped[list["MeetingPreference"]] = relationship(
        "MeetingPreference", back_populates="faculty"
    )
    faculty_assignments: Mapped[list["FacultyAssignment"]] = relationship(
        "FacultyAssignment", back_populates="faculty"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
