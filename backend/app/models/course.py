from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.course_preference import CoursePreference
    from app.models.section import Section


class Course(Base):
    """Represents a course offered by the college."""

    __tablename__ = "course"

    course_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(1000))
    credits: Mapped[int] = mapped_column(Integer)

    # Relationships
    sections: Mapped[list["Section"]] = relationship(
        "Section", back_populates="course")
    course_preferences: Mapped[list["CoursePreference"]] = relationship(
        "CoursePreference", back_populates="course"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
