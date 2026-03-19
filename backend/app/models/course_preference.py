from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.enums import PreferenceLevel

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.faculty import Faculty


class CoursePreference(Base):
    """Represents a faculty member's interest in teaching a specific course.
    Used by the scheduling algorithm to assign courses to faculty."""

    __tablename__ = "course_preference"

    preference_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    preference: Mapped[PreferenceLevel] = mapped_column(Enum(PreferenceLevel))

    # Foreign Keys
    faculty_nuid: Mapped[int] = mapped_column(Integer, ForeignKey("faculty.nuid"))
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("course.course_id"))

    # Relationships
    faculty: Mapped["Faculty"] = relationship(
        "Faculty", back_populates="course_preferences"
    )
    course: Mapped["Course"] = relationship(
        "Course", back_populates="course_preferences"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
