from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.faculty_assignment import FacultyAssignment
    from app.models.schedule import Schedule
    from app.models.section_lock import SectionLock
    from app.models.time_block import TimeBlock

if TYPE_CHECKING:
    from app.models.section_lock import SectionLock


class Section(Base):
    """Represents a section offering a course in a schedule
    assigned to a time block."""

    __tablename__ = "section"

    section_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_number: Mapped[int] = mapped_column(Integer)
    capacity: Mapped[int] = mapped_column(Integer)

    # Foreign Keys
    schedule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schedule.schedule_id")
    )
    time_block_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("time_block.time_block_id")
    )
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("course.course_id"))

    # Relationships
    schedule: Mapped[Schedule] = relationship("Schedule", back_populates="sections")
    time_block: Mapped[TimeBlock] = relationship("TimeBlock", back_populates="sections")
    course: Mapped[Course] = relationship("Course", back_populates="sections")
    faculty_assignments: Mapped[list[FacultyAssignment]] = relationship(
        "FacultyAssignment", back_populates="section"
    )
    section_lock: Mapped[SectionLock] = relationship(
        "SectionLock", back_populates="section", uselist=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    # Add crosslisted FK... points to other course 
